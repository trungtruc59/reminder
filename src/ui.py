# Restored Content for src/ui.py

import os
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QObject, QTimer, QUrl
from PyQt6.QtGui import QIcon, QDesktopServices, QAction
from PyQt6.QtWidgets import (
    QSystemTrayIcon, QWidget, QVBoxLayout, QHBoxLayout, 
    QFrame, QSizePolicy, QMenu, QMessageBox, QApplication, QDialog, QLabel, QPushButton
)

from qfluentwidgets import (
    FluentWindow, SubtitleLabel, CaptionLabel, PushButton, 
    PrimaryPushButton, StrongBodyLabel, CardWidget, 
    ScrollArea, SwitchButton, setTheme, Theme, FluentIcon as FIF, 
    InfoBar, InfoBarPosition, TitleLabel, BodyLabel
)

# Fix relative imports
try:
    from logic import WorkDayMonitor
    from notification import SoundManager
except ImportError:
    from src.logic import WorkDayMonitor
    from src.notification import SoundManager

# Signal Bridge to safeguard threading
class LogicBridge(QObject):
    tick = pyqtSignal()
    alert = pyqtSignal(str, str) # title, message

class CustomPopup(QDialog):
    """Custom centered popup with Icon and Message"""
    def __init__(self, title, message, assets_dir, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(400, 250)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        
        # Style
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                border: 1px solid #444;
                border-radius: 10px;
            }
            QLabel {
                color: white;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Icon
        icon_lbl = QLabel(self)
        # Try to load icon
        if os.path.exists(os.path.join(assets_dir, 'icon.ico')):
             pixmap = QIcon(os.path.join(assets_dir, 'icon.ico')).pixmap(64, 64)
             icon_lbl.setPixmap(pixmap)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_lbl)
        
        # Message
        msg_lbl = TitleLabel(title, self)
        msg_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(msg_lbl)
        
        body_lbl = BodyLabel(message, self)
        body_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body_lbl.setWordWrap(True)
        layout.addWidget(body_lbl)
        
        # Button
        btn = PrimaryPushButton("OK, Đã rõ", self)
        btn.setFixedWidth(120)
        btn.clicked.connect(self.accept)
        
        h_layout = QHBoxLayout()
        h_layout.addStretch()
        h_layout.addWidget(btn)
        h_layout.addStretch()
        layout.addLayout(h_layout)

class DashboardWindow(FluentWindow):
    def __init__(self, assets_dir):
        super().__init__()
        self.assets_dir = assets_dir
        self.sound_manager = SoundManager(assets_dir)
        
        # Thread Bridge
        self.bridge = LogicBridge()
        self.bridge.tick.connect(self.on_tick_ui)
        self.bridge.alert.connect(self.show_custom_popup)
        
        # Logic
        self.monitor = WorkDayMonitor(
            on_tick_callback=lambda: self.bridge.tick.emit(),
            on_alert_callback=lambda t, m: self.bridge.alert.emit(t, m)
        )
        
        # Initialize Window
        self.setWindowTitle("Trợ lý công việc")
        self.resize(500, 400) # Compact size
        self.setWindowIcon(QIcon(os.path.join(assets_dir, 'icon.ico')))
        
        # Center Screen
        desktop = QApplication.screens()[0].availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(int(w/2 - 250), int(h/2 - 200))
        
        # Setup UI
        setTheme(Theme.DARK) 
        
        self.init_ui()
        self.init_tray()

    def init_ui(self):
        self.homeInterface = QWidget(self)
        self.homeInterface.setObjectName("homeInterface")
        self.addSubInterface(self.homeInterface, FIF.HOME, "Dashboard")
        
        layout = QVBoxLayout(self.homeInterface)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(30)
        
        # Header / Status Code
        self.lblStatus = SubtitleLabel("Sẵn sàng làm việc", self.homeInterface)
        self.lblStatus.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lblStatus.setTextColor("#a0a0a0", "#a0a0a0")
        layout.addWidget(self.lblStatus)
        
        # Clock (Realtime)
        self.lblClock = TitleLabel("00:00:00", self.homeInterface)
        self.lblClock.setStyleSheet("font-size: 48px; font-weight: bold;")
        self.lblClock.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lblClock)

        # Big Start Button (Standard Windows 11 Style)
        # Using PrimaryPushButton with standard Fluent styles
        self.btnStart = PrimaryPushButton("Bắt đầu làm việc", self.homeInterface)
        self.btnStart.setIcon(FIF.PLAY)
        self.btnStart.setFixedSize(200, 50) # Standard large button
        self.btnStart.clicked.connect(self.toggle_work_day)
        
        # Center contents
        layout.addWidget(self.btnStart, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Footer Note
        lblNote = CaptionLabel("Tự động nhắc nhở nghỉ giải lao mỗi giờ & nghỉ trưa lúc 12:00", self.homeInterface)
        lblNote.setTextColor("#606060", "#606060")
        lblNote.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lblNote)

    def toggle_work_day(self):
        if not self.monitor.running:
            self.monitor.start()
            self.btnStart.setText("Dừng làm việc")
            self.btnStart.setIcon(FIF.PAUSE)
            self.lblStatus.setText("Đang theo dõi công việc...")
            self.lblStatus.setTextColor("#00cf99", "#00cf99")
            
            InfoBar.success(
                title='Đã kích hoạt',
                content="Chúc bạn một ngày làm việc hiệu quả!",
                orient=Qt.Orientation.Horizontal,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        else:
            self.monitor.stop()
            self.btnStart.setText("Bắt đầu làm việc")
            self.btnStart.setIcon(FIF.PLAY)
            self.lblStatus.setText("Đã dừng theo dõi")
            self.lblStatus.setTextColor("#a0a0a0", "#a0a0a0")

    def on_tick_ui(self):
        # Update Clock
        import datetime
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self.lblClock.setText(now)

    def show_custom_popup(self, title, message):
        # 1. Play Sound
        self.sound_manager.play_sound()
        
        # 2. Show Popup
        # Ensure window is visible/restored if minimized?
        # User said "hiện lên 1 popup giữa màn hình". 
        # Usually good to ensure app context is front?
        # Or just show the dialog standalone.
        
        popup = CustomPopup(title, message, self.assets_dir, self)
        
        # Center popup on screen, not just parent
        desktop = QApplication.screens()[0].availableGeometry()
        x = (desktop.width() - popup.width()) // 2
        y = (desktop.height() - popup.height()) // 2
        popup.move(x, y)
        
        popup.exec()

    def init_tray(self):
        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setIcon(QIcon(os.path.join(self.assets_dir, 'icon.ico')))
        
        menu = QMenu()
        restoreAction = QAction("Mở Dashboard", self)
        restoreAction.triggered.connect(self.showNormal)
        quitAction = QAction("Thoát hoàn toàn", self)
        quitAction.triggered.connect(self.quit_app)
        
        menu.addAction(restoreAction)
        menu.addAction(quitAction)
        
        self.trayIcon.setContextMenu(menu)
        self.trayIcon.show()
        self.trayIcon.activated.connect(self.on_tray_activated)

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.showNormal()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.trayIcon.showMessage(
            "Work Assistant",
            "Ứng dụng đang chạy ngầm để nhắc nhở bạn.",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )

    def quit_app(self):
        self.monitor.shutdown()
        QApplication.quit()
