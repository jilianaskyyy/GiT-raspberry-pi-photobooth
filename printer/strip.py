from PIL import Image, ImageOps

# Thermal printer widths in dots: 58mm paper is usually 384, 80mm paper is 576.
PRINTER_WIDTH = 384

# Each photo is center-cropped to this width:height ratio before stacking.
PHOTO_ASPECT = (4, 3)

GAP = 12      # white space between photos, in pixels
MARGIN = 12   # white border around the whole strip


def make_strip(photo_paths, output_path, width=PRINTER_WIDTH,
               aspect=PHOTO_ASPECT, dither=True):
    """
    Stacks photos top-to-bottom into one strip image.

    photo_paths: list of image file paths (the 4 captured photos)
    output_path: where to save the strip
    width:       strip width in pixels (match your printer)
    aspect:      (w, h) ratio each photo is center-cropped to
    dither:      True -> black & white with dithering (what thermal
                 printers need). False -> keep colour (for the digital copy).

    Returns output_path.
    """
    inner_width = width - 2 * MARGIN
    photo_height = round(inner_width * aspect[1] / aspect[0])

    tiles = []
    for path in photo_paths:
        img = Image.open(path).convert("RGB")
        # Center-crop to the target ratio, then resize to the strip width.
        img = ImageOps.fit(img, (inner_width, photo_height), Image.LANCZOS)
        tiles.append(img)

    total_height = (
        2 * MARGIN + len(tiles) * photo_height + (len(tiles) - 1) * GAP
    )
    strip = Image.new("RGB", (width, total_height), "white")

    y = MARGIN
    for tile in tiles:
        strip.paste(tile, (MARGIN, y))
        y += photo_height + GAP

    if dither:
        # Grayscale + contrast boost, then 1-bit with Floyd-Steinberg dithering.
        strip = ImageOps.autocontrast(strip.convert("L"))
        strip = strip.convert("1")

    strip.save(output_path)
    return output_path