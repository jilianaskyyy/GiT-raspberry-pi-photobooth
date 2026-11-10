"""
Reads live frames the UI process saves to disk, runs MediaPipe hand detection
on them, and writes the result back to disk.

Run this with the 3.11 venv (the one with mediapipe installed):
    source venv/bin/activate
    python3 gestures/gesture_server.py

Runs alongside main.py (which stays on system Python 3.13). The two programs
talk through files in /tmp:

    photobooth_frame.npy     UI  -> server   newest camera frame
    photobooth_gesture.txt   server -> UI    gesture name only (used for the controls)
    photobooth_hand.json     server -> UI    gesture name + the 21 hand points
                                             (used to draw the dots and the label)
"""

import json
import os
import time

import numpy as np

# Keep whichever import already works in your project.
try:
    from gesture import GestureDetector
except ImportError:
    from gesture_detector import GestureDetector

FRAME_PATH = "/tmp/photobooth_frame.npy"
GESTURE_PATH = "/tmp/photobooth_gesture.txt"
HAND_JSON_PATH = "/tmp/photobooth_hand.json"


def write_hand_json(gesture, points):
    """
    Writes the hand data in one go: write to a temporary file, then rename it,
    so the UI never reads a half-written file.
    """
    data = {
        "t": time.time(),         # lets the UI ignore old data if this program stops
        "gesture": gesture,       # e.g. "THUMBS_UP", or None
        "landmarks": points,      # 21 [x, y] pairs between 0 and 1, or None
    }

    temp_path = HAND_JSON_PATH + ".tmp"

    with open(temp_path, "w") as f:
        json.dump(data, f)

    os.replace(temp_path, HAND_JSON_PATH)


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

                # Same two steps detect_gesture() does, but we keep the hand
                # points so the UI can draw them.
                hand, _ = detector.process_frame(frame)

                if hand is None:
                    gesture = None
                    points = None
                else:
                    gesture = detector.classify_gesture(hand)
                    points = [[round(p.x, 4), round(p.y, 4)] for p in hand.landmark]

                with open(GESTURE_PATH, "w") as f:
                    f.write(gesture if gesture else "")

                write_hand_json(gesture, points)

        time.sleep(0.02)


if __name__ == "__main__":
    main()