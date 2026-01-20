import threading
import time
import datetime

class WorkDayMonitor:
    def __init__(self, on_tick_callback, on_alert_callback):
        self.on_tick_callback = on_tick_callback # Updates UI clock/status
        self.on_alert_callback = on_alert_callback # Triggers Popups
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.running = False
        
        # State
        self.last_minute_checked = -1

    def start(self):
        if not self.running:
            self.running = True
            # Reset thread if needed or just start monitoring flag
            if not self.thread.is_alive():
                self.stop_event.clear()
                self.thread = threading.Thread(target=self._run_loop, daemon=True)
                self.thread.start()

    def stop(self):
        self.running = False
        # We don't necessarily kill the thread, just stop logic
        # But to be clean:
        pass

    def _run_loop(self):
        while not self.stop_event.is_set():
            if self.running:
                now = datetime.datetime.now()
                h = now.hour
                m = now.minute
                s = now.second
                
                # Check Work Hours (8:00 - 17:00)
                # Note: 17:00 is technically end, so we run until 16:59:59? 
                # Or include 17:00? User said "8h đến 17 giờ chiều". Let's assume inclusive of 17:00 event or stops AT 17:00.
                
                is_work_time = 8 <= h < 17 # 08:00:00 to 16:59:59.
                # If h=17 and m=0 and s=0, we might want end day alert.
                
                # We only trigger alerts once per minute (at 00 seconds)
                if m != self.last_minute_checked:
                    self.last_minute_checked = m
                    
                    if 8 <= h <= 17:
                        # 1. Lunch Break at 12:00
                        if h == 12 and m == 0:
                            self.on_alert_callback("Nghỉ trưa thôi!", "Đã 12 giờ rồi, hãy nghỉ ngơi và ăn trưa nhé.")
                        
                        # 2. Hourly Rest (Every hour at minute 00, except 12:00)
                        elif m == 0 and h != 12:
                            # Avoid 8:00 start if just started? Maybe. 
                            # But request said "mỗi 1h sẽ có một thông báo".
                            if 8 <= h <= 16: # Don't alert at 17:00 (End day handles it) or maybe yes?
                                # Let's say 9, 10, 11, 13, 14, 15, 16.
                                self.on_alert_callback("Nghỉ giải lao!", f"Đã {h} giờ rồi. Hãy đứng dậy vươn vai 5 phút nhé.")
                                
                        # 3. End Day at 17:00
                        elif h == 17 and m == 0:
                            self.on_alert_callback("Tan làm!", "Đã 17 giờ. Kết thúc ngày làm việc vui vẻ!")
            
            # Tick UI every second (for clock or status)
            if self.on_tick_callback:
                self.on_tick_callback()

            time.sleep(1)

    def shutdown(self):
        self.stop_event.set()
        if self.thread.is_alive():
            self.thread.join(1.0)
