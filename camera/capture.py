import time
from camera import Camera 
import math

PHOTOS_PER_STRIP = 4
VALID_TIMERS = (3, 5)
PAUSE_BETWEEN_PHOTOS = 1 # 1 second for changing poses

def countdown(seconds, photo_number, on_tick=None, on_frame=None):

    # on_tick(seocnds_left, photo_number): called once each time the number changes
    # ^^ UI can use it to display a big countdown number (if needed)

    # on_frame(): called about 30 times a second so the live preview keeps moving during the countdown instead of freezing

    # time.monotonic acts as a stopwatch
    end = time.monotonic() + seconds 

    # The number currently shown on the screen
    shown = None

    while True:
        remaining = end - time.monotonic()

        if remaining <= 0:
            return

        seconds_left = math.ceil(remaining)

        # Used if there is a screen to show the new number, else it will be printed in the terminal 
        if seconds_left != shown:
            shown = seconds_left 

            if on_tick:
                on_tick(seconds_left, photo_number)
            else:
                print("Photos in {}...".format(seconds_left))

        if on_frame:
            # Refreshes the live preview 
            on_frame()

        time.sleep(0.03)


def capture_four_photos(camera, timer, folder, on_tick=None, on_frame=None):

    # folder: this is where the strip's photos will be saved (one folder per session)

    if timer not in VALID_TIMERS:
        raise ValueError("Invalid timer {}. Must be 3 or 5 seconds.".format(timer))

    # Empty list that will store the 4 file paths 
    photos = []

    for photo_number in range(1, PHOTOS_PER_STRIP + 1):
        print("Photo {}/{}".format(photo_number, PHOTOS_PER_STRIP))

        countdown(timer, photo_number, on_tick, on_frame)
        photos.append(camera.take_photo(photo_number, folder))

        if photo_number < PHOTOS_PER_STRIP:
            # This keeps the preview moving during the pause
            end = time.monotonic() + PAUSE_BETWEEN_PHOTOS
            while time.monotonic() < end:
                if on_frame:
                    on_frame()
                time.sleep(0.03)

    print("All {} photos have been taken.".format(PHOTOS_PER_STRIP))

    # Returns the 4 files paths in order
    return photos 