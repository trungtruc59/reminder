import os
import wave
import struct
import math
from PIL import Image, ImageDraw

def create_beep_wav(filename='assets/alert.wav', duration=0.5, frequency=440.0):
    """Tạo file wav đơn giản"""
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    amplitude = 16000
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1) # Mono
        wav_file.setsampwidth(2) # 2 bytes per sample (16-bit)
        wav_file.setframerate(sample_rate)
        
        for i in range(n_samples):
            t = float(i) / sample_rate
            value = int(amplitude * math.sin(2.0 * math.pi * frequency * t))
            data = struct.pack('<h', value)
            wav_file.writeframes(data)
    print(f"Created audio: {filename}")

def create_icon(filename='assets/icon.ico'):
    """Tạo icon đơn giản"""
    size = (64, 64)
    image = Image.new('RGBA', size, color=(0, 0, 0, 0)) # Transparent background
    draw = ImageDraw.Draw(image)
    
    # Vẽ hình tròn màu xanh
    draw.ellipse((4, 4, 60, 60), fill=(0, 150, 255), outline=(255, 255, 255), width=2)
    # Vẽ chữ R (Reminder)
    # Do không load font, vẽ hình chữ nhật đơn giản tượng trưng đồng hồ
    draw.rectangle((28, 10, 36, 32), fill='white')
    draw.rectangle((28, 30, 48, 30), fill='white') # Kim giờ
    
    image.save(filename, format='ICO')
    print(f"Created icon: {filename}")

if __name__ == "__main__":
    if not os.path.exists('assets'):
        os.makedirs('assets')
        
    try:
        create_beep_wav()
    except Exception as e:
        print(f"Failed to create wav: {e}")

    try:
        create_icon()
    except Exception as e:
        print(f"Failed to create icon: {e}")
