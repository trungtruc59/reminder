import os
import winsound
import threading

class SoundManager:
    def __init__(self, assets_dir):
        self.assets_dir = assets_dir
        self.sound_file = os.path.join(assets_dir, 'alert.wav')

    def play_sound(self):
        """Phát âm thanh trên thread riêng để không block UI"""
        threading.Thread(target=self._play, daemon=True).start()

    def _play(self):
        try:
            if os.path.exists(self.sound_file):
                # SND_NODEFAULT: Don't beep if file not found
                winsound.PlaySound(self.sound_file, winsound.SND_FILENAME) 
            else:
                winsound.MessageBeep()
        except Exception as e:
            print(f"Error playing sound: {e}")
