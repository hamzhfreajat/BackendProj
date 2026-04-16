import pyautogui
import time

print("Move your mouse to the desired position. Printing coordinates every 2 seconds...")
print("Press Ctrl+C to stop.\n")

try:
    while True:
        x, y = pyautogui.position()
        print(f"Mouse position: x={x}, y={y}")
        time.sleep(2)
except KeyboardInterrupt:
    print("\nStopped.")
