# SOC System - Biometric Surveillance v2.0

A professional-grade biometric security system featuring real-time face recognition, liveness detection, cloud synchronization, and watermarked security auditing.

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- A webcam
- Gmail account (for SMTP alerts)
- Firebase Project (for cloud storage)

### 1. Installation
Clone the repository and install the required dependencies:
```bash
pip install -r requirements.txt
```

### 2. Configuration
Create a `.env` file in the root directory (or update the existing one) with your credentials:
```env
# Alert Service Credentials (SMTP)
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password
RECEIVER_EMAIL=alert-recipient@gmail.com

# Firebase Configuration
FIREBASE_KEY_PATH=firebase-key.json
SECRET_KEY_PATH=secret.key
```
> **Note:** For Gmail, you must use an **App Password**, not your regular password.

### 3. Firebase Setup
Place your Firebase service account key file in the root directory and rename it to `firebase-key.json` (or update the path in `.env`).

### 4. Running the Application
Execute the main script to launch the GUI:
```bash
python run.py
```

## 🛠 Key Features
- **DNN Face Detection**: Uses ResNet-10 SSD for high-accuracy face detection.
- **LBPH Recognition**: Local Binary Patterns Histograms for identity verification.
- **Anti-Spoofing**: MediaPipe-powered eye-blink detection and texture analysis.
- **Security Auditing**: Automatic watermarking (DCT-based) of intruder captures for tampering detection.
- **Cloud Integration**: Real-time logging and biometric sample backup via Firebase Firestore.
- **GDPR Compliant**: Local data encryption (AES-256) and log cleanup features.

## 📂 Project Structure
- `.\run.py`: Application entry point.
- `.\src\`: Source code (GUI, Core services, and Cloud integration).
- `.\models\`: Pre-trained DNN models for face detection.
- `.\data\`: Local SQLite database, JSON logs, and watermarked captures.
- `.\dataset\`: Captured face samples for training.
