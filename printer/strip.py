from PIL import Image, ImageDraw, ImageFont, ImageOps

# Thermal printer widths in dots: 58mm paper is usually 384, 80mm paper is 576.
PRINTER_WIDTH = 384

# Each photo is center-cropped to this width:height ratio before stacking.
PHOTO_ASPECT = (4, 3)

# Spacing is defined for a 384 px wide strip and scaled for other widths.
GAP = 12      # white space between photos
MARGIN = 12   # white border around the whole strip

# Shown under the photos when there is no logo image.
FOOTER_TEXT = "GIRLS IN TECH"

# The logo is scaled to fit inside this share of the strip width / height.
LOGO_MAX_WIDTH_SHARE = 0.92
LOGO_MAX_HEIGHT_SHARE = 0.4


def _scaled(value, width):
    return max(1, round(value * width / PRINTER_WIDTH))


def _font(size):
    for name in ("DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass

    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _make_footer(width, inner_width, logo_path, footer_text):
    """Returns an RGB image (strip-wide, white) holding the logo or the footer text."""
    pad = _scaled(10, width)

    if logo_path:
        try:
            logo = Image.open(logo_path).convert("RGBA")

            # Put the logo on white so transparent areas don't turn black.
            canvas = Image.new("RGBA", logo.size, "white")
            canvas.alpha_composite(logo)
            logo = canvas.convert("RGB")

            max_w = int(inner_width * LOGO_MAX_WIDTH_SHARE)
            max_h = int(width * LOGO_MAX_HEIGHT_SHARE)
            scale = min(max_w / logo.width, max_h / logo.height)
            logo = logo.resize(
                (max(1, int(logo.width * scale)), max(1, int(logo.height * scale))),
                Image.LANCZOS
            )

            footer = Image.new("RGB", (width, logo.height + 2 * pad), "white")
            footer.paste(logo, ((width - logo.width) // 2, pad))
            return footer

        except (FileNotFoundError, OSError):
            pass    # fall through to the text footer

    if not footer_text:
        return None

    font = _font(_scaled(30, width))
    box = font.getbbox(footer_text)
    text_w, text_h = box[2] - box[0], box[3] - box[1]

    footer = Image.new("RGB", (width, text_h + 2 * pad), "white")
    ImageDraw.Draw(footer).text(
        ((width - text_w) // 2 - box[0], pad - box[1]),
        footer_text, fill="black", font=font
    )
    return footer


def make_strip(photo_paths, output_path, width=PRINTER_WIDTH,
               aspect=PHOTO_ASPECT, dither=True, logo_path=None,
               footer_text=FOOTER_TEXT):
    """
    Stacks photos top-to-bottom into one strip image, with a logo (or the
    footer text) underneath.

    photo_paths: list of image file paths (the 4 captured photos)
    output_path: where to save the strip (.png, or .jpg for the online copy)
    width:       strip width in pixels (384 for the printer, bigger online)
    aspect:      (w, h) ratio each photo is center-cropped to
    dither:      True -> black & white with dithering (what thermal
                 printers need). False -> keep colour (for the digital copy).
    logo_path:   image (ideally a transparent PNG) shown at the bottom.
                 If missing or unreadable, footer_text is drawn instead.
    footer_text: text for the bottom when there is no logo; "" for no footer.

    Returns output_path.
    """
    gap = _scaled(GAP, width)
    margin = _scaled(MARGIN, width)

    inner_width = width - 2 * margin
    photo_height = round(inner_width * aspect[1] / aspect[0])

    tiles = []
    for path in photo_paths:
        img = Image.open(path).convert("RGB")
        # Center-crop to the target ratio, then resize to the strip width.
        img = ImageOps.fit(img, (inner_width, photo_height), Image.LANCZOS)
        tiles.append(img)

    footer = _make_footer(width, inner_width, logo_path, footer_text)
    footer_space = (footer.height + gap) if footer is not None else 0

    total_height = (
        2 * margin + len(tiles) * photo_height + (len(tiles) - 1) * gap + footer_space
    )
    strip = Image.new("RGB", (width, total_height), "white")

    y = margin
    for tile in tiles:
        strip.paste(tile, (margin, y))
        y += photo_height + gap

    if footer is not None:
        strip.paste(footer, (0, y))

    if dither:
        # Grayscale + contrast boost, then 1-bit with Floyd-Steinberg dithering.
        strip = ImageOps.autocontrast(strip.convert("L"))
        strip = strip.convert("1")

    if output_path.lower().endswith((".jpg", ".jpeg")):
        strip.convert("RGB").save(output_path, quality=92)
    else:
        strip.save(output_path)

    return output_path