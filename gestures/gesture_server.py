"""
Reads live frames the UI process saves to disk, runs MediaPipe gesture
detection on them, and writes the result back to disk.

Run this with the 3.11 venv (the one with mediapipe installed):
    source venv/bin/activate
    python3 gestures/gesture_server.py

Runs alongside main.py (which stays on system Python 3.13), which writes
frames and reads gestures through the same two files.
"""

import os
import time

import numpy as np

from gesture import GestureDetector

FRAME_PATH = "/tmp/photobooth_frame.npy"
GESTURE_PATH = "/tmp/photobooth_gesture.txt"


def main():
    print("Gesture server starting...")
    detector = GestureDetector()
    print("Gesture server ready. Waiting for frames.")

    last_mtime = 0

    while True:
        if os.path.exists(FRAME_PATH):
            mtime = os.path.getmtime(FRAME_PATH)

            if mtime != last_mtime:
                last_mtime = mtime

                try:
                    frame = np.load(FRAME_PATH)
                except Exception:
                    # Caught mid-write by the other process, just retry next loop.
                    time.sleep(0.05)
                    continue

                gesture = detector.detect_gesture(frame)

                with open(GESTURE_PATH, "w") as f:
                    f.write(gesture if gesture else "")

        time.sleep(0.1)


if __name__ == "__main__":
    main()
