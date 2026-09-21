from picamera2 import Picamera2
import os
import time


PHOTO_FOLDER = "photostrip"

class Camera:

    def __init__(self):

        # Creates a folder for the photos if it doesn't already exist
        os.makedirs(PHOTO_FOLDER, exist_ok=True)

        # Create camera
        self.camera = Picamera2 ()

        # Configuring the camera for still photos
        config = self.camera.create_still_configuration(
            main={"size": (1920, 1080)}
        )

        self.camera.configure(config)

        # Starts the camera
        self.camera.start()

        time.sleep(2)

    def take_photo(self, photo_number):

        # Takes the photo and save it to the folder 
        filename = "photo_{}.jpg".format(photo_number)
        filepath = os.path.join(PHOTO_FOLDER, filename)

        self.camera.capture_file(filepath)

        print("Photo saved: {}".format(filepath))

        return filepath

    def close(self):

        # Stops the camera
        self.camera.stop()