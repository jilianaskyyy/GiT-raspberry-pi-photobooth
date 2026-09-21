from picamera2 import Picamera2
import os
import time 

PHOTO_FOLDER = "photos"

class Camera:
    def __init__(self):

        # Create camera
        self.camera = Picamera2()

        # Configure camera for still photos
        config = self.camera.create_still_configuration(
            main={"size": (1920, 1080)}
        )

        self.camera.configure (config)

        # Start camera
        self.camera.start()

        # Allocated time for the camera to initialise
        time.sleep(2)

    def take_photo(self, photo_number):
        filename = "photo_{}.jpg".format(photo_number)
        filepath = os.path.join(PHOTO_FOLDER, filename)

        self.camera.capture_file(filepath)

        print("Photo {} saved: {}".format(photo_number, filepath))

        return filepath

    def close(self):
        self.camera.stop()