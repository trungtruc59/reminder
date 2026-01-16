import threading
import time
import uuid

class Reminder:
    def __init__(self, interval_minutes, message, on_finish_callback=None):
        self.id = str(uuid.uuid4())
        self.interval_seconds = int(interval_minutes * 60)
        self.interval_minutes = interval_minutes
        self.message = message
        self.remaining_seconds = self.interval_seconds
        self.is_running = False
        self.on_finish_callback = on_finish_callback

    def start(self):
        self.is_running = True

    def stop(self):
        self.is_running = False
        # Optional: Reset on stop? Or pause? 
        # Requirement: "Stop" usually means pause or stop. Let's keep state.
        self.remaining_seconds = self.interval_seconds

    def tick(self):
        if self.is_running:
            if self.remaining_seconds > 0:
                self.remaining_seconds -= 1
            else:
                # Timer finished
                if self.on_finish_callback:
                    self.on_finish_callback(self)
                # Auto reset logic: after notification, restart cycle immediately?
                # User req: "tự động reset bộ đếm... chạy lên kế tiếp cho nhắc nhở kế tiếp"
                self.remaining_seconds = self.interval_seconds

class TimerManager:
    def __init__(self, on_tick_callback):
        self.reminders = []
        self.on_tick_callback = on_tick_callback # Called every second with updated state
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def add_reminder(self, minutes, message, on_finish):
        reminder = Reminder(minutes, message, on_finish)
        self.reminders.append(reminder)
        return reminder

    def remove_reminder(self, reminder_id):
        self.reminders = [r for r in self.reminders if r.id != reminder_id]

    def _run_loop(self):
        while not self.stop_event.is_set():
            start_time = time.time()
            
            # Tick all active reminders
            for reminder in self.reminders:
                reminder.tick()
            
            # Notify UI to update
            if self.on_tick_callback:
                self.on_tick_callback() # UI pulls data from self.reminders
            
            # Precise timing: sleep enough to reach next second boundary
            elapsed = time.time() - start_time
            sleep_time = max(0, 1.0 - elapsed)
            time.sleep(sleep_time)

    def shutdown(self):
        self.stop_event.set()
        if self.thread.is_alive():
            self.thread.join(1.0)
