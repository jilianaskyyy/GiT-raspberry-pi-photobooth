from picamera2 import Picamera2
import os
import time


PHOTO_FOLDER = "photos"


class Camera:

    def __init__(self):

        os.makedirs(PHOTO_FOLDER, exist_ok=True)

        self.camera = Picamera2()

        config = self.camera.create_still_configuration(
            main={"size": (1920, 1080)}
        )

        self.camera.configure(config)
        self.camera.start()

        time.sleep(2)

    def take_photo(self, photo_number):

        filename = f"photo_{photo_number}.jpg"
        filepath = os.path.join(PHOTO_FOLDER, filename)

        self.camera.capture_file(filepath)

        print(f"Photo saved: {filepath}")

        return filepath

    def close(self):

        self.camera.stop()