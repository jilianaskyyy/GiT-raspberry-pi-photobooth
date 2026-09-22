from camera.camera import Camera
from ui.ui import PhotoboothUI

def main():

    camera = Camera()

    try:
        ui = PhotoboothUI(camera)
        ui.run()

    finally:
        camera.close()


if __name__ == "__main__":
    main()