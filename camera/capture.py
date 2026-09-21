import time
from camera import Camera 

def countdown(seconds):

    # Countdown 
    for i in range(seconds, 0, -1):
        print("Photo in {}...".format(i))
        time.sleep(1)

def capture_four_photos(timer):

    # timer: 
    # 3 = 3 second countdown
    # 5 = 5 second countdown 

    if timer not in [3, 5]:
        print("Invalid timer. Please choose 3 or 5 seconds.")
        return []

    camera = Camera()
    photos = []

    try:
        for photo_number in range(1, 5):
            print("Photo {}/4".format(photo_number))

            # Countdown
            countdown(timer)

            # Take photo
            filepath = camera.take_photo(photo_number)

            # Save filepath 
            photos.append(filepath)

            # Small delay before next photo 
            if photo_number < 4:
                time.sleep(1)

        print("\nAll 4 photos have been taken.")

        return photos

    finally:
        camera.close()