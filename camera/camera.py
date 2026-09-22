from picamera2 import Picamera2
import os


PHOTO_FOLDER = "photostrip"

class Camera:
    def __init__(self, preview_size=(800, 480), still_size=(1920, 1080)):

        os.makedirs(PHOTO_FOLDER, exist_ok=True)

        # Creates a folder for the photos if it doesn't already exist
        os.makedirs(PHOTO_FOLDER, exist_ok=True)

        # Fast, low-res stream used for the live feed on screen.
        self.preview_config = self.camera.create_preview_configuration(
            main={"size": preview_size, "format": "RGB888"}
        )

        # High-res stream only used at the moment a photo is taken.
        self.still_config = self.camera.create_still_configuration(
            main={"size": still_size}
        )

        self.camera.configure (self.preview_config)

        # Starts the camera
        self.camera.start()

        # Set up the camera for preview
        def get_preview_frame(self):
        #Returns a HxWx3 RGB numpy array for the current live frame.
            return self.camera.capture_array()
        
    def take_photo(self, photo_number):

        # Takes the photo and save it to the folder 
        filename = "photo_{}.jpg".format(photo_number)
        filepath = os.path.join(PHOTO_FOLDER, filename)

        self.camera.switch_mode_and_capture_file(self.still_config, filepath)

        print("Photo saved: {}".format(filepath))

        return filepath

    def close(self):

        # Stops the camera
        self.camera.stop()