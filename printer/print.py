"""
Prints the photo strip on a serial (RS232 / TTL) ESC/POS thermal printer.

Test the printer on its own, before wiring it into the UI:
    /usr/bin/python3 printing/printer.py photostrip/strip_print.png
"""

import logging
import sys
import time

from escpos.printer import Serial
from PIL import Image

# python-escpos warns about the "center" option on every band; it's harmless.
logging.getLogger("escpos").setLevel(logging.ERROR)

# Pi 5 header UART (GPIO14/15) is /dev/ttyAMA0 once the serial port is enabled.
# (/dev/serial0 points to the separate debug UART on the Pi 5, so don't use it.)
# If you use a USB-to-serial adapter instead, this is usually /dev/ttyUSB0.
SERIAL_PORT = "/dev/ttyAMA0"

# Check your printer's self-test page for the real baud rate
# (commonly 9600, 19200 or 115200).
BAUDRATE = 9600

# Image is sent in horizontal bands so a small serial buffer doesn't overflow.
BAND_HEIGHT = 96
BAND_DELAY = 0.15      # seconds to wait between bands; raise it if the print is garbled

FEED_LINES = 5         # blank lines pushed out after the strip so you can tear it off
CUT_PAPER = False      # most embedded printers have no cutter


def open_printer(port=SERIAL_PORT, baudrate=BAUDRATE):
    return Serial(
        devfile=port,
        baudrate=baudrate,
        bytesize=8,
        parity="N",
        stopbits=1,
        timeout=1.0,
        dsrdtr=False,   # embedded printers usually have no DSR/DTR lines wired
    )


def print_strip(image_path, printer=None):
    """
    Prints the strip image. `printer` can be passed in for testing
    (e.g. escpos.printer.Dummy); otherwise the serial printer is opened.
    """
    img = Image.open(image_path).convert("1")
    width, height = img.size

    own_printer = printer is None
    p = printer if printer is not None else open_printer()

    try:
        p.hw("INIT")

        for top in range(0, height, BAND_HEIGHT):
            band = img.crop((0, top, width, min(top + BAND_HEIGHT, height)))
            p.image(band, impl="bitImageRaster", fragment_height=BAND_HEIGHT)
            time.sleep(BAND_DELAY)

        p.text("\n" * FEED_LINES)

        if CUT_PAPER:
            p.cut()
    finally:
        if own_printer:
            p.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 printer.py <strip_image>")
        sys.exit(1)

    print("Printing {} on {} @ {} baud...".format(sys.argv[1], SERIAL_PORT, BAUDRATE))
    print_strip(sys.argv[1])
    print("Done.")