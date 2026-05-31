import winsound
import threading
import time

class SoundService:
    def __init__(self):
        self.is_playing = False
        self._lock = threading.Lock()

    def play_siren(self, duration_sec=3):
        """Plays a siren sound in a separate thread."""
        with self._lock:
            if self.is_playing:
                return
            self.is_playing = True
        
        threading.Thread(target=self._siren_worker, args=(duration_sec,), daemon=True).start()

    def _siren_worker(self, duration_sec):
        end_time = time.time() + duration_sec
        try:
            while time.time() < end_time:
                # Alternating high/low frequencies for siren effect
                winsound.Beep(1000, 250)
                winsound.Beep(600, 250)
        except Exception as e:
            print(f"SoundService Error: {e}")
        finally:
            with self._lock:
                self.is_playing = False

if __name__ == "__main__":
    service = SoundService()
    print("Playing test siren...")
    service.play_siren(2)
    time.sleep(3)
