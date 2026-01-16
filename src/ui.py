import os
from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import (
    QSystemTrayIcon, QWidget, QVBoxLayout, QHBoxLayout, 
    QFrame, QSizePolicy, QMenu, QMessageBox, QApplication
)

from qfluentwidgets import (
    FluentWindow, SubtitleLabel, CaptionLabel, PushButton, 
    PrimaryPushButton, StrongBodyLabel, CardWidget, 
    ScrollArea, LineEdit, SpinBox, SwitchButton, 
    setTheme, Theme, FluentIcon as FIF, InfoBar, InfoBarPosition
)

# Fix relative imports
try:
    from logic import TimerManager
    from notification import NotificationManager
except ImportError:
    from src.logic import TimerManager
    from src.notification import NotificationManager

# Signal Bridge to safeguard threading
class LogicBridge(QObject):
    tick = pyqtSignal()
    finished = pyqtSignal(object) # Passes reminder object

class ReminderCard(CardWidget):
    """
    Custom Card for a single reminder. 
    Inherits from Fluent CardWidget for native look.
    """
    def __init__(self, reminder, parent=None, on_delete=None):
        super().__init__(parent)
        self.reminder = reminder
        self.on_delete = on_delete
        
        # Layout
        self.hLayout = QHBoxLayout(self)
        self.hLayout.setContentsMargins(20, 10, 20, 10)
        self.hLayout.setSpacing(15)
        
        # Icon (Optional, just purely decorative)
        # self.iconWidget = IconWidget(FIF.RINGER)
        
        # Info
        self.vLayout = QVBoxLayout()
        self.lblMessage = StrongBodyLabel(reminder.message, self)
        self.lblInterval = CaptionLabel(f"Lặp lại mỗi {reminder.interval_minutes} phút", self)
        self.lblInterval.setTextColor("#808080", "#a0a0a0") # Light/Dark grey
        
        self.vLayout.addWidget(self.lblMessage)
        self.vLayout.addWidget(self.lblInterval)
        
        self.hLayout.addLayout(self.vLayout)
        self.hLayout.addStretch(1)
        
        # Countdown Label
        self.lblCountdown = SubtitleLabel("00:00", self)
        self.lblCountdown.setTextColor("#0067c0", "#4cc2ff") # Accent color
        self.hLayout.addWidget(self.lblCountdown)
        
        # Controls
        self.btnToggle = PushButton("Start", self)
        self.btnToggle.setFixedWidth(80)
        self.btnToggle.clicked.connect(self.toggle_timer)
        self.hLayout.addWidget(self.btnToggle)
        
        self.btnDelete = PushButton("X", self)
        self.btnDelete.setFixedWidth(40)
        self.btnDelete.clicked.connect(self.delete_self)
        self.hLayout.addWidget(self.btnDelete)
        
        self.update_ui()

    def toggle_timer(self):
        if self.reminder.is_running:
            self.reminder.stop()
            self.btnToggle.setText("Start")
        else:
            self.reminder.start()
            self.btnToggle.setText("Stop")
        self.update_ui()

    def delete_self(self):
        if self.on_delete:
            self.on_delete(self.reminder.id)

    def update_ui(self):
        total = self.reminder.remaining_seconds
        h = total // 3600
        m = (total % 3600) // 60
        s = total % 60
        
        if h > 0:
            time_str = f"{h}:{m:02}:{s:02}"
        else:
            time_str = f"{m:02}:{s:02}"
            
        self.lblCountdown.setText(time_str)
        if not self.reminder.is_running:
             self.lblCountdown.setTextColor("#808080", "#808080")
        else:
             self.lblCountdown.setTextColor("#0067c0", "#4cc2ff")


class ReminderWindow(FluentWindow):
    def __init__(self, assets_dir):
        super().__init__()
        self.assets_dir = assets_dir
        self.notification_manager = NotificationManager(assets_dir)
        
        # Thread Bridge
        self.bridge = LogicBridge()
        self.bridge.tick.connect(self.on_tick_ui)
        self.bridge.finished.connect(self.on_reminder_finish_ui)
        
        # Pass emit functions to TimerManager
        # NOTE: signal.emit is thread-safe!
        self.timer_manager = TimerManager(lambda: self.bridge.tick.emit())
        # We need to hook the 'finish' callback slightly differently since Logic passes 'reminder'
        # Logic.py expects: on_finish(reminder)
        # We pass: lambda r: self.bridge.finished.emit(r)
        
        # Initialize Window
        self.setWindowTitle("Periodic Reminder")
        self.resize(600, 700)
        self.setWindowIcon(QIcon(os.path.join(assets_dir, 'icon.ico')))
        
        # Center Screen
        desktop = QApplication.screens()[0].availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(int(w/2 - 300), int(h/2 - 350))
        
        # Setup UI
        setTheme(Theme.DARK) # Force dark for now or 'AUTO'
        
        self.init_ui()
        self.init_tray()
        
        self.cards = {}

    def init_ui(self):
        # Create a central widget that FluentWindow navigates to (or just use it as a simple window)
        # FluentWindow is a NavigationWindow by default. For a simple app, 
        # let's just use the main central layout or add a single "Home" interface.
        
        self.homeInterface = QWidget(self)
        self.homeInterface.setObjectName("homeInterface")
        self.addSubInterface(self.homeInterface, FIF.HOME, "Danh sách")
        
        layout = QVBoxLayout(self.homeInterface)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header
        headerLayout = QHBoxLayout()
        title = SubtitleLabel("Nhắc nhở của bạn", self.homeInterface)
        headerLayout.addWidget(title)
        headerLayout.addStretch(1)
        
        btnAdd = PrimaryPushButton(FIF.ADD, "Thêm mới", self.homeInterface)
        btnAdd.clicked.connect(self.open_add_dialog)
        headerLayout.addWidget(btnAdd)
        
        layout.addLayout(headerLayout)
        
        # Scroll Area for Cards
        self.scrollArea = ScrollArea(self.homeInterface)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setStyleSheet("background: transparent; border: none;") # Transparent
        
        self.scrollContent = QWidget()
        self.scrollContent.setStyleSheet("background: transparent;")
        self.vCardLayout = QVBoxLayout(self.scrollContent)
        self.vCardLayout.setContentsMargins(0, 0, 0, 0)
        self.vCardLayout.setSpacing(10)
        self.vCardLayout.addStretch(1) # Push cards up
        
        self.scrollArea.setWidget(self.scrollContent)
        layout.addWidget(self.scrollArea)
        
        # Footer
        footerLayout = QHBoxLayout()
        self.switchOntop = SwitchButton(self.homeInterface)
        self.switchOntop.setText("Ghim trên cùng (Always on Top)")
        self.switchOntop.checkedChanged.connect(self.toggle_ontop)
        
        footerLayout.addWidget(self.switchOntop)
        footerLayout.addStretch(1)
        layout.addLayout(footerLayout)

    def open_add_dialog(self):
        # Using a simple custom Dialog or just inputs
        # For simplicity in PyQt, let's create a separate Dialog window
        self.show_add_popup()
        
    def show_add_popup(self):
        d = QWidget()
        d.resize(300, 200)
        d.setWindowTitle("Thêm nhắc nhở")
        # We can use MessageBox or just a small Fluent Window, 
        # but let's just add directly for now or use a persistent bottom sheet if library supported.
        # Let's simple input:
        
        # Note: In a real app, use a proper Dialog class.
        pass 
        # Wait, let's allow adding via the main UI logic for now to keep it concise?
        # Or better, create a small method to add mock data or prompt user?
        # Let's implement a quick custom dialog using MessageBox is ugly. 
        # I'll create a simple input card at the top temporarily or a separate window.
        
        from PyQt6.QtWidgets import QDialog
        
        dlg = QDialog(self)
        dlg.setWindowTitle("Thêm nhắc nhở")
        dlg.resize(300, 200)
        
        vbox = QVBoxLayout(dlg)
        
        txtMsg = LineEdit(dlg)
        txtMsg.setPlaceholderText("Nội dung nhắc nhở")
        vbox.addWidget(txtMsg)
        
        numMin = SpinBox(dlg)
        numMin.setRange(1, 1440)
        numMin.setValue(30)
        vbox.addWidget(numMin)
        
        btnSave = PrimaryPushButton("Lưu", dlg)
        btnSave.clicked.connect(lambda: [self.add_reminder(numMin.value(), txtMsg.text()), dlg.accept()])
        vbox.addWidget(btnSave)
        
        dlg.exec()

    def add_reminder(self, minutes, message):
        if not message: return
        
        # Wrapper to bridge signal
        callback = lambda r: self.bridge.finished.emit(r)
        
        reminder = self.timer_manager.add_reminder(minutes, message, callback)
        
        # Create Card
        card = ReminderCard(reminder, on_delete=self.delete_reminder)
        # Insert before the stretch (last item)
        count = self.vCardLayout.count()
        self.vCardLayout.insertWidget(count - 1, card)
        
        self.cards[reminder.id] = card
        
        InfoBar.success(
            title='Thành công',
            content=f"Đã thêm nhắc nhở '{message}'",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2000,
            parent=self
        )

    def delete_reminder(self, r_id):
        self.timer_manager.remove_reminder(r_id)
        if r_id in self.cards:
            card = self.cards[r_id]
            card.deleteLater() # Qt Cleanup
            del self.cards[r_id]

    def on_tick_ui(self):
        for card in self.cards.values():
            card.update_ui()

    def on_reminder_finish_ui(self, reminder):
        # Notification
        self.notification_manager.show_toast("Đã đến giờ!", reminder.message)
        
        if self.switchOntop.isChecked():
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
            self.show()
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint) # Reset after showing? 
            # User wants "Always on top", so maybe keep it?
            # Actually just bringing to front is enough usually.
            self.activateWindow()

    def toggle_ontop(self, checked):
        if checked:
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
        self.show()

    def init_tray(self):
        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setIcon(QIcon(os.path.join(self.assets_dir, 'icon.ico')))
        
        menu = QMenu()
        restoreAction = QAction("Mở lại", self)
        restoreAction.triggered.connect(self.showNormal)
        quitAction = QAction("Thoát", self)
        quitAction.triggered.connect(self.quit_app)
        
        menu.addAction(restoreAction)
        menu.addAction(quitAction)
        
        self.trayIcon.setContextMenu(menu)
        self.trayIcon.show()
        
        # Handle double click
        self.trayIcon.activated.connect(self.on_tray_activated)

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.showNormal()

    def closeEvent(self, event):
        # Minimize to tray instead of closing
        event.ignore()
        self.hide()
        self.trayIcon.showMessage(
            "Reminder App",
            "Ứng dụng vẫn chạy ngầm ở đây!",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )

    def quit_app(self):
        self.timer_manager.shutdown()
        QApplication.quit()
