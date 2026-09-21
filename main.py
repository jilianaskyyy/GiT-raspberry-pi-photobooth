from capture import capture_four_photos

timer = 3 

photos = capture_four_photos(timer)

print("\nPhotos taken:")

for photo in photos:
    print(photo)
