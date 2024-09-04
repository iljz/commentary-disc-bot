import socket
from PIL import ImageGrab
import io
import time

HOST = '127.0.0.1'  # Server's IP address
PORT = 65432        # Server's port
interval = 20       # Interval in seconds

def capture_and_send():
    # Capture the screen
    screenshot = ImageGrab.grab()
    
    # Convert to bytes
    byte_io = io.BytesIO()
    screenshot.save(byte_io, format='PNG')
    byte_data = byte_io.getvalue()

    # Get the size of the byte data
    image_size = len(byte_data)
    
    try:
        # Connect to the server and send the image data
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            s.sendall(image_size.to_bytes(4, byteorder='big'))
            s.sendall(byte_data)
        print(f"Screenshot sent at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        print(f"Error sending screenshot: {e}")

def main():
    print("Starting periodic screenshot capture and send...")
    while True:
        capture_and_send()
        time.sleep(interval)

if __name__ == '__main__':
    main()