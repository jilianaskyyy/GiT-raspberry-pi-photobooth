from picamera2 import Picamera2
import os

# Main folder where all photos are saved on the RPI
PHOTO_FOLDER = "photostrip"

class Camera:

    # Runs once Camera() is created
    def __init__(self, preview_size=(800, 480), still_size=(1920, 1080)):

        # Creates the photo folder, exist_ok=True means no error if it already exists 
        os.makedirs(PHOTO_FOLDER, exist_ok=True)

        # Connect to the RPI camera
        self.camera = Picamera2()

        # Fast, low-res stream used for the live feed on screen.
        self.preview_config = self.camera.create_preview_configuration(
            main={"size": preview_size, "format": "RGB888"}
        )

        # High-res stream only used at the moment a photo is taken.
        self.still_config = self.camera.create_still_configuration(
            main={"size": still_size} # Resolution of each saved photos (Full HD)
        )

        # Starts in preview mode so that the live feed is ready
        self.camera.configure (self.preview_config)

        # Start camera and frames will now stream continuously
        self.camera.start()

    # Set up the camera for preview
    def get_preview_frame(self):
        # Returns a HxWx3 RGB numpy array for the current live frame.
        return self.camera.capture_array()

    def get_preview_frame(self):
        # Current live frame in R,G,B order, which is what MediaPipe expects ? 
        return self.camera.capture_array()[:, :, ::-1].copy()
        
    def take_photo(self, photo_number, folder=PHOTO_FOLDER):

        # Makes sure that this session's folder exists
        os.makedirs(folder, exist_ok=True)

        filepath = os.path.join(folder, "photo_{}.jpg".format(photo_number))

        # Switches to high-res mode, saves the JPEG, then switches back to preview mode
        self.camera.switch_mode_and_capture_file(self.still_config, filepath)

        print("Photo saved: {}".format(filepath))

        return filepath

    def close(self):
        self.camera.stop()
        self.camera.stop()