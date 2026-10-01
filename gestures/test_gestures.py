import cv2
from gesture import GestureDetector


# Create our gesture detector
detector = GestureDetector()


# Open the camera
cap = cv2.VideoCapture(0)


while True:

    # Read one frame from the camera
    success, frame = cap.read()

    if not success:
        print("Could not read camera.")
        break


    # Detect the gesture
    gesture = detector.detect_gesture(frame)


    # Display the detected gesture on the screen
    if gesture is not None:

        cv2.putText(
            frame,
            gesture,
            (50, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.5,
            (0, 255, 0),
            3
        )

    else:

        cv2.putText(
            frame,
            "NO GESTURE",
            (50, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.5,
            (0, 255, 0),
            3
        )


    # Show the camera
    cv2.imshow("Gesture Detection", frame)


    # Press Q to quit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


# Close the camera
cap.release()
cv2.destroyAllWindows()
