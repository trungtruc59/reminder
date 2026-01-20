import sys
import os
from PyQt6.QtWidgets import QApplication
from ui import DashboardWindow

# High DPI scaling
if hasattr(sys, 'frozen'):
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(sys._MEIPASS, 'PyQt6', 'Qt6', 'plugins')

def main():
    # Enable High DPI scaling
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    os.environ["QT_SCALE_FACTOR"] = "1"
    
    app = QApplication(sys.argv)
    
    # Path setup
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assets_dir = os.path.join(base_path, 'assets')

    window = DashboardWindow(assets_dir)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
