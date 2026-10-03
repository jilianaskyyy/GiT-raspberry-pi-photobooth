from camera.camera import Camera
from frontend.ui import PhotoboothUI
from gestures.gesture import GestureDetector

def main(): 

    camera = Camera()
    gesture = GestureDetector()

    try:
        ui = PhotoboothUI(camera, gesture)
        ui.run()

    finally:
        camera.close()


if __name__ == "__main__":
    main()