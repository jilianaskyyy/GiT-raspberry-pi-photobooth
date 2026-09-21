from camera import RPICamera
from picamera2 import Picamera2
from camera.capture import capture_four_photos

def main():

    camera = RPICamera()

    try:
        timer = 3

        print("Starting camera test ...")

        photos = capture_four_photos(camera, timer)

        print("\nPhotos captured:")

        for photo in photos:
            print(photo)

    finally:
        camera.close()
        print("Camera closed.")

if __name__ == "__main__":
    main()