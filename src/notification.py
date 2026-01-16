import os
import threading
import winsound
import time
import queue
from plyer import notification

class NotificationManager:
    def __init__(self, assets_dir):
        self.assets_dir = assets_dir
        self.sound_file = os.path.join(assets_dir, 'alert.wav')
        self.queue = queue.Queue()
        self.running = True
        
        # Start worker thread
        self.worker = threading.Thread(target=self._process_queue, daemon=True)
        self.worker.start()

    def show_toast(self, title, message):
        """Đẩy thông báo vào hàng đợi"""
        self.queue.put((title, message))

    def play_sound(self):
        """Phát âm thanh (được gọi bên trong worker để đồng bộ)"""
        try:
            if os.path.exists(self.sound_file):
                # SND_NODEFAULT: Don't beep if file not found
                winsound.PlaySound(self.sound_file, winsound.SND_FILENAME) 
            else:
                winsound.MessageBeep()
        except Exception as e:
            print(f"Error playing sound: {e}")

    def _process_queue(self):
        while self.running:
            try:
                # Get item, block if empty
                title, message = self.queue.get(timeout=1.0)
                
                # 1. Play Sound
                self.play_sound()
                
                # 2. Show Toast
                app_icon = os.path.join(self.assets_dir, 'icon.ico')
                if not os.path.exists(app_icon):
                    # Debug log
                    print(f"Warning: Icon not found at {app_icon}")
                    app_icon = None # Plyer defaults if None
                
                try:
                    notification.notify(
                        title=title,
                        message=message,
                        app_name="Reminder App",
                        app_icon=app_icon,
                        timeout=5
                    )
                except Exception as e:
                    print(f"Notification Error with Icon: {e}")
                    # Retry without icon
                    try:
                        notification.notify(
                            title=title,
                            message=message,
                            app_name="Reminder App",
                            app_icon=None,
                            timeout=5
                        )
                    except Exception as e2:
                        print(f"Notification Failed completely: {e2}")

                # 3. Wait to prevent overlap
                # Windows notifications stay for ~5s. Let's wait 6s to be safe.
                time.sleep(6)
                
                self.queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Queue Error: {e}")

    def shutdown(self):
        self.running = False
