import time


def countdown(seconds):

    for i in range(seconds, 0, -1):
        print(f"Photo in {i}...")
        time.sleep(1)


def capture_four_photos(camera, timer):

    photos = []

    for photo_number in range(1, 5):

        print(f"\nPhoto {photo_number}/4")

        countdown(timer)

        filepath = camera.take_photo(photo_number)

        photos.append(filepath)

        if photo_number < 4:
            time.sleep(1)

    return photos