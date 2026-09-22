import time

def countdown(seconds):

    for i in range(seconds, 0, -1):
        print("Photo in {}...".format(i))
        time.sleep(1)

# to be changed
def capture_four_photos(camera, timer):

    if timer not in [3, 5]:
        print("Invalid timer. Timer must be either 3 or 5 seconds")

    photos = []

    for photo_number in range(1, 5):

        print("\nPhoto {}/4".format(photo_number))

        countdown(timer)

        filepath = camera.take_photo(photo_number)

        photos.append(filepath)

        if photo_number < 4:
            time.sleep(1)

    return photos