import firebase_admin
from firebase_admin import credentials, firestore
from cryptography.fernet import Fernet
import os
import datetime
import base64

class CloudService:
    def __init__(self, key_path=None, secret_key_path=None):
        self.enabled = False
        self.key_path = key_path or os.getenv("FIREBASE_KEY_PATH", "firebase-key.json")
        self.secret_key_path = secret_key_path or os.getenv("SECRET_KEY_PATH", "secret.key")
        self._init_encryption()
        
        if os.path.exists(self.key_path):
            try:
                # Validate JSON structure first
                import json
                with open(self.key_path, 'r') as f:
                    json.load(f)
                
                cred = credentials.Certificate(self.key_path)
                try:
                    firebase_admin.initialize_app(cred)
                except ValueError:
                    pass
                
                db_id = os.getenv("FIREBASE_DATABASE_ID", "(default)")
                self.db = firestore.client(database_id=db_id)
                self.enabled = True
                print(f"[OK] Firebase Cloud Service Initialized (Project: {firebase_admin.get_app().project_id}, DB: {db_id})")
            except json.JSONDecodeError:
                print(f"[FAIL] Firebase Key '{self.key_path}' is not a valid JSON file.")
            except Exception as e:
                print(f"[FAIL] Firebase Init Error: {e}")
        else:
            print(f"[WARN] Firebase key '{self.key_path}' not found. Cloud features disabled.")

    def _init_encryption(self):
        """Initializes or loads the symmetric encryption key."""
        if not os.path.exists(self.secret_key_path):
            key = Fernet.generate_key()
            with open(self.secret_key_path, "wb") as key_file:
                key_file.write(key)
            print("[OK] New Encryption Key Generated")
        
        with open(self.secret_key_path, "rb") as key_file:
            self.fernet = Fernet(key_file.read())

    def upload_user_data(self, user_id, username, role):
        """Uploads user metadata to Firestore."""
        if not self.enabled: return False
        try:
            doc_ref = self.db.collection('users').document(str(user_id))
            doc_ref.set({
                'username': username,
                'role': role,
                'added_on': datetime.datetime.now()
            })
            return True
        except Exception as e:
            print(f"Error uploading to Firestore: {e}")
            return False

    def upload_biometric_sample(self, user_id, file_path):
        """Encrypts, encodes to Base64, and uploads to Firestore (Free Plan Bypass)."""
        if not self.enabled: return False
        try:
            filename = os.path.basename(file_path)
            # Read local file
            with open(file_path, "rb") as f:
                data = f.read()
            
            # 1. Encrypt data
            encrypted_data = self.fernet.encrypt(data)
            
            # 2. Convert to Base64 string for storage in Firestore
            b64_data = base64.b64encode(encrypted_data).decode('utf-8')
            
            # 3. Save to Firestore 'biometric_samples' collection
            # Document ID is a combination of user_id and filename to prevent collisions
            doc_id = f"{user_id}_{filename.replace('.', '_')}"
            self.db.collection('biometric_samples').document(doc_id).set({
                'user_id': user_id,
                'filename': filename,
                'data': b64_data,
                'timestamp': datetime.datetime.now()
            })
            return True
        except Exception as e:
            print(f"Error saving sample to Firestore: {e}")
            return False

    def download_and_decrypt_sample(self, user_id, filename, dest_path):
        """Downloads from Firestore, decodes, and decrypts."""
        if not self.enabled: return False
        try:
            doc_id = f"{user_id}_{filename.replace('.', '_')}"
            doc = self.db.collection('biometric_samples').document(doc_id).get()
            
            if not doc.exists:
                print(f"Sample {doc_id} not found in cloud.")
                return False
                
            b64_data = doc.to_dict().get('data')
            
            # 1. Decode Base64
            encrypted_data = base64.b64decode(b64_data)
            
            # 2. Decrypt
            decrypted_data = self.fernet.decrypt(encrypted_data)
            
            with open(dest_path, "wb") as f:
                f.write(decrypted_data)
            return True
        except Exception as e:
            print(f"Error retrieving sample from Firestore: {e}")
            return False

    def log_access_event(self, user_id, status, confidence, action):
        """Syncs an access log entry to Firestore."""
        if not self.enabled: return False
        try:
            self.db.collection('access_logs').add({
                'user_id': user_id,
                'status': status,
                'confidence': confidence,
                'action': action,
                'timestamp': datetime.datetime.now()
            })
            return True
        except Exception as e:
            print(f"Error logging to Firestore: {e}")
            return False

    def sync_dataset_from_cloud(self, dest_dir="dataset", access_service=None):
        """Downloads all biometric samples from Firestore and restores local DB."""
        if not self.enabled: 
            print("[FAIL] Cloud Sync: Service disabled.")
            return False
        try:
            print("[INFO] Cloud Sync: Starting download...")
            os.makedirs(dest_dir, exist_ok=True)
            
            # DIAGNOSTIC: List all collections
            try:
                collections = [c.id for c in self.db.collections()]
                print(f"[DEBUG] Collections found in Firestore: {collections}")
                if not collections:
                    print("[WARN] No collections found. Your database might be empty or the ID is wrong.")
            except Exception as ce:
                print(f"[DEBUG] Could not list collections: {ce}")

            # 1. Fetch all user metadata
            print("[INFO] Cloud Sync: Fetching user metadata...")
            users_docs = self.db.collection('users').get()
            
            if access_service:
                print("[INFO] Cloud Sync: Restoring local user database...")
                for doc in users_docs:
                    u_data = doc.to_dict()
                    # Add to local SQLite (id is usually handled by document ID in my logic, 
                    # but here we use the numeric ID from the Firestore document content)
                    username = u_data.get('username')
                    role = u_data.get('role', 'authorized')
                    # Force sync to local DB if not exists
                    if username:
                        access_service.add_user(username, role)

            # 2. Fetch biometric samples
            print("[INFO] Cloud Sync: Fetching biometric samples...")
            docs = self.db.collection('biometric_samples').get()
            count = 0

            if not docs:
                print("[WARN] Cloud Sync: No biometric samples found in 'biometric_samples' collection.")

            for doc in docs:
                data = doc.to_dict()
                user_id = data.get('user_id')
                filename = data.get('filename')
                b64_data = data.get('data')
                
                if not b64_data or not filename: continue
                
                local_path = os.path.join(dest_dir, filename)
                
                # Decode and Decrypt
                try:
                    encrypted_data = base64.b64decode(b64_data)
                    decrypted_data = self.fernet.decrypt(encrypted_data)
                    
                    with open(local_path, "wb") as f:
                        f.write(decrypted_data)
                    count += 1
                except Exception as de:
                    print(f"Error decrypting {filename}: {de}")
            
            print(f"[OK] Cloud Sync: Downloaded {count} samples.")
            return count
        except Exception as e:
            print("\n" + "!"*50)
            print(f"CRITICAL FIREBASE SYNC ERROR: {e}")
            print("!"*50 + "\n")
            return -1 # Use -1 to indicate a hard error
