import PyInstaller.__main__
import os

# Đảm bảo đường dẫn tuyệt đối
base_path = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(base_path, 'assets', 'icon.ico')
main_script = os.path.join(base_path, 'src', 'main.py')

if not os.path.exists(icon_path):
    print("WARNING: icon.ico not found in assets/. Using default icon.")
    icon_option = []
else:
    icon_option = [f'--icon={icon_path}']

PyInstaller.__main__.run([
    main_script,
    '--name=ReminderApp',
    '--onefile',
    '--windowed',  # Ẩn console
    '--add-data=assets;assets', # Copy thư mục assets vào exe
    *icon_option,
])
