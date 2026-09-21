from camera import Camera
from capture import capture_four_photos


def main():

    camera = Camera()

    try:
        timer = 3

        photos = capture_four_photos(camera, timer)

        print("\nPhotos captured:")

        for photo in photos:
            print(photo)

    finally:
        camera.close()


if __name__ == "__main__":
    main()