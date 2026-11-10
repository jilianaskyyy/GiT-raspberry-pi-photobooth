import json
import os
import threading
import time

import numpy as np
import pygame

# ----------------------------------------------------------------------
# Settings
# ----------------------------------------------------------------------

# How long a gesture must be held before it counts (avoids accidental triggers).
HOLD_MS = 800

# After any screen change, ignore gestures for this long so a gesture you're
# still holding doesn't instantly trigger the next screen.
COOLDOWN_MS = 1500

# Run gesture detection at most this often.
DETECT_EVERY_MS = 150

# Shows the detected gesture in the corner. Handy while tuning; off for the TV.
SHOW_GESTURE_DEBUG = False

# Shared files used to talk to gesture_server.py (runs in the 3.11 venv).
FRAME_PATH = "/tmp/photobooth_frame.npy"
GESTURE_PATH = "/tmp/photobooth_gesture.txt"
HAND_JSON_PATH = "/tmp/photobooth_hand.json"      # hand points, written by gesture_server.py

# What to draw on top of the camera view
SHOW_HAND_DOTS = True          # the 21 hand points and the lines joining them
SHOW_ACTION_LABEL = True       # "Thumbs up", "3 fingers"... at the top of the camera view
SHOW_HOLD_BAR = True           # small bar that fills while a gesture is being held

FLASH_ENABLED = True           # white flash when a photo is taken
FLASH_MS = 450                 # how long the flash takes to fade away
HAND_STALE_SECONDS = 1.0       # ignore hand data older than this (e.g. server stopped)

# Upload / print settings
PRINT_ENABLED = True                    # False = skip the printer (handy when testing upload + QR)
STRIP_PATH = "photostrip/strip_print.png"          # black & white, for the printer
STRIP_COLOR_PATH = "photostrip/strip_color.jpg"    # colour copy that goes online
STRIP_ONLINE_WIDTH = 768                           # online strip width in px
QR_PATH = "photostrip/qr.png"
QR_TIMEOUT_MS = 45000                   # QR screen returns to home by itself after this long

# ----------------------------------------------------------------------
# Display. The whole UI is drawn on a fixed 1920x1080 canvas; pygame scales
# it to whatever the TV really is (1080p, 4K, ...).
# ----------------------------------------------------------------------

SCREEN_W = 1920
SCREEN_H = 1080

# Run in a normal window while developing:  PHOTOBOOTH_WINDOWED=1 python3 main.py
WINDOWED = os.environ.get("PHOTOBOOTH_WINDOWED") == "1"

# assets/ sits next to main.py (this file is in frontend/).
ASSET_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets"
)

# Logo shown at the bottom of the strip (transparent PNG). If this file is
# missing, the text "GIRLS IN TECH" is used instead.
STRIP_LOGO = os.path.join(ASSET_DIR, "git_logo.png")

# Colours
PURPLE = (108, 52, 184)
LAVENDER = (206, 190, 238)
WHITE = (255, 255, 255)
INK = (34, 28, 56)

# ----------------------------------------------------------------------
# Layout (all in 1920x1080 pixels). Camera boxes are 5:3, the same shape as
# the camera preview, so the picture is never stretched.
# ----------------------------------------------------------------------

CAM_BIG = pygame.Rect(330, 240, 1260, 756)      # timer, countdown, review
CAM_HOME = pygame.Rect(590, 500, 740, 444)      # home (its top follows the logo)
CAM_QR = pygame.Rect(930, 375, 735, 441)        # qr
QR_PANEL = pygame.Rect(200, 255, 660, 660)      # white panel holding the QR code
QR_SIZE = 600

# Review photo slots (4:3, like the printed strip), sized to fit inside CAM_BIG
SLOT_GAP = 26
SLOT_W = (CAM_BIG.w - 100 - 3 * SLOT_GAP) // 4
SLOT_H = SLOT_W * 3 // 4
SLOT_TOP = CAM_BIG.y + int(CAM_BIG.h * 0.26)

# Speech bubbles inside the big camera box
BUBBLE_BIG_TOP = CAM_BIG.bottom - 210
BUBBLE_COUNT_TOP = CAM_BIG.bottom - 100

# (max width, max height). The small logo must stay shorter than the gap
# above the camera frame (about 215 px) or it will be covered by it.
LOGO_BIG_MAX = (1300, 430)      # home screen
LOGO_SMALL_MAX = (1040, 190)    # every other screen

# name -> (file in assets/, height on screen in px)
HANDS = {
    "thumbs_up": ("hand_thumbs_up.png", 300),
    "three": ("hand_three_fingers.png", 300),
    "open": ("hand_open.png", 330),
    "fist": ("hand_fist.png", 260),
}

HAND_BOTTOM = SCREEN_H + 20                     # hands sit on the bottom edge, slightly cut off

# Text shown at the top of the camera view for each gesture
GESTURE_LABELS = {
    "THUMBS_UP": "Thumbs up",
    "THREE_FINGERS": "3 fingers",
    "OPEN_HAND": "Open hand",
    "IS_FIST": "Closed fist",
}

# Which gestures do something on each screen (the hold bar only fills for these)
SCREEN_GESTURES = {
    "home": {"THUMBS_UP"},
    "timer_select": {"THREE_FINGERS", "OPEN_HAND"},
    "review": {"THUMBS_UP", "IS_FIST"},
    "qr": {"THUMBS_UP"},
    "error": {"THUMBS_UP", "IS_FIST"},
}

# Which of the 21 hand points are joined by a line (MediaPipe's hand skeleton)
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),            # thumb
    (0, 5), (5, 6), (6, 7), (7, 8),            # index finger
    (5, 9), (9, 10), (10, 11), (11, 12),       # middle finger
    (9, 13), (13, 14), (14, 15), (15, 16),     # ring finger
    (13, 17), (17, 18), (18, 19), (19, 20),    # little finger
    (0, 17),                                   # edge of the palm
]


# ----------------------------------------------------------------------
# Small drawing helpers
# ----------------------------------------------------------------------

def render_outlined(font, text, fill, outline, thickness):
    """Text with a thick outline, like the SNAPPI logo."""
    base = font.render(text, True, fill)
    edge = font.render(text, True, outline)
    w, h = base.get_size()

    surf = pygame.Surface((w + 2 * thickness, h + 2 * thickness), pygame.SRCALPHA)

    for dx in range(-thickness, thickness + 1, 2):
        for dy in range(-thickness, thickness + 1, 2):
            if dx * dx + dy * dy <= thickness * thickness:
                surf.blit(edge, (thickness + dx, thickness + dy))

    surf.blit(base, (thickness, thickness))
    return surf


def scale_to_width(surface, width):
    height = max(1, int(surface.get_height() * width / surface.get_width()))
    return pygame.transform.smoothscale(surface, (width, height))


def fit_within(surface, max_w, max_h):
    """Scales a surface to fit inside max_w x max_h, keeping its shape."""
    scale = min(max_w / surface.get_width(), max_h / surface.get_height())
    size = (max(1, int(surface.get_width() * scale)), max(1, int(surface.get_height() * scale)))
    return pygame.transform.smoothscale(surface, size)


def scale_to_height(surface, height):
    width = max(1, int(surface.get_width() * height / surface.get_height()))
    return pygame.transform.smoothscale(surface, (width, height))


def crop_to_aspect(surface, aspect):
    """Centre-crops a surface to width/height == aspect."""
    w, h = surface.get_size()

    if w / h > aspect:
        new_w = int(h * aspect)
        rect = pygame.Rect((w - new_w) // 2, 0, new_w, h)
    else:
        new_h = int(w / aspect)
        rect = pygame.Rect(0, (h - new_h) // 2, w, new_h)

    return surface.subsurface(rect).copy()


def trim_transparent(surface):
    """Crops away empty (transparent) margins so the logo sits where we place it."""
    rect = surface.get_bounding_rect()

    if rect.width == 0 or rect.height == 0:
        return surface

    return surface.subsurface(rect).copy()


def load_asset_image(filename):
    """Loads assets/<filename>, or returns None if it isn't there yet."""
    path = os.path.join(ASSET_DIR, filename)

    try:
        return pygame.image.load(path).convert_alpha()
    except (pygame.error, FileNotFoundError):
        return None


def load_font(filename, size, bold=False):
    path = os.path.join(ASSET_DIR, "fonts", filename)

    try:
        return pygame.font.Font(path, size)
    except (pygame.error, FileNotFoundError, OSError):
        font = pygame.font.Font(None, size)
        font.set_bold(bold)
        return font


def make_fallback_background(w, h):
    """Simple sky + brick wall, used until assets/background.png exists."""
    surf = pygame.Surface((w, h))
    top, bottom = (112, 96, 190), (232, 130, 170)

    for y in range(h):
        t = y / h
        colour = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        pygame.draw.line(surf, colour, (0, y), (w, y))

    brick_h, brick_w = 36, 96
    wall_top = h - 6 * brick_h

    pygame.draw.rect(surf, (150, 80, 170), (0, wall_top - 8, w, 8))

    for row in range(6):
        y = wall_top + row * brick_h
        offset = (brick_w // 2) if row % 2 else 0

        for x in range(-brick_w, w + brick_w, brick_w):
            pygame.draw.rect(
                surf,
                (250, 128, 128),
                (x + offset, y, brick_w - 4, brick_h - 4),
                border_radius=3
            )

    return surf


class PhotoboothUI:
    def __init__(self, camera):
        pygame.init()

        self.camera = camera

        self.width = SCREEN_W
        self.height = SCREEN_H

        flags = pygame.SCALED | (pygame.RESIZABLE if WINDOWED else pygame.FULLSCREEN)
        self.screen = pygame.display.set_mode((self.width, self.height), flags)

        if not WINDOWED:
            pygame.mouse.set_visible(False)

        pygame.display.set_caption("Snappi - Raspberry Pi Photobooth")

        # Fonts: pixel.ttf for headings/countdown, body.ttf for the speech bubbles.
        self.pixel_digit = load_font("pixel.ttf", 300, bold=True)
        self.pixel_heading = load_font("pixel.ttf", 64, bold=True)
        self.pixel_title = load_font("pixel.ttf", 200, bold=True)
        self.pixel_sub = load_font("pixel.ttf", 44, bold=True)
        self.body_font = load_font("body.ttf", 42)
        self.small_font = load_font("body.ttf", 32)
        self.debug_font = load_font("body.ttf", 28)

        # Artwork (anything missing falls back to a drawn stand-in).
        self.background = self.load_background()
        self.logo_big, self.logo_small = self.load_logos()
        self.hands = self.load_hands()
        self.digit_cache = {}

        self.running = True
        self.current_screen = "home"

        self.timer = 0
        self.countdown_start = 0
        self.photo_number = 1
        self.photo_taken = False

        self.captured_photos = []

        # Review screen thumbnails (built once per round, not every frame)
        self.review_thumbs = []
        self.review_thumbs_key = None

        # Gesture state
        self.last_frame_write = 0
        self.last_detect_time = 0
        self.detected_gesture = None    # last gesture read from gesture_server.py
        self.candidate_gesture = None   # gesture currently being "held"
        self.candidate_start = 0
        self.cooldown_until = 0

        # Camera flash: a white layer that fades out after each photo
        self.flash_start = None
        self.flash_surface = pygame.Surface((self.width, self.height))
        self.flash_surface.fill(WHITE)

        # Hand points + gesture for the overlay (from gesture_server.py)
        self.hand_points = None
        self.hand_gesture = None
        self.hand_read_at = 0

        # Upload / print job state (the work runs in background threads)
        self.job_message = ""
        self.job_done = False
        self.job_error = None
        self.print_state = "idle"       # idle / printing / done / error
        self.print_lock = threading.Lock()
        self.qr_surface = None
        self.qr_shown_at = 0

    # ------------------------------------------------------------------
    # Loading artwork
    # ------------------------------------------------------------------

    def load_background(self):
        image = load_asset_image("background.png")

        if image is None:
            return make_fallback_background(self.width, self.height)

        image = image.convert()

        if image.get_size() != (self.width, self.height):
            image = pygame.transform.smoothscale(image, (self.width, self.height))

        return image

    def load_logos(self):
        logo = load_asset_image("logo.png")

        if logo is None:
            title = render_outlined(self.pixel_title, "SNAPPI", WHITE, PURPLE, 8)
            sub = render_outlined(
                self.pixel_sub, "A RASPBERRY PI PHOTOBOOTH", WHITE, PURPLE, 3
            )

            w = max(title.get_width(), sub.get_width())
            h = title.get_height() + sub.get_height() + 10

            logo = pygame.Surface((w, h), pygame.SRCALPHA)
            logo.blit(title, ((w - title.get_width()) // 2, 0))
            logo.blit(sub, ((w - sub.get_width()) // 2, title.get_height() + 10))

        # Optional flatter logo for the inner screens; falls back to logo.png.
        logo_small = load_asset_image("logo_small.png") or logo

        logo = trim_transparent(logo)
        logo_small = trim_transparent(logo_small)

        return fit_within(logo, *LOGO_BIG_MAX), fit_within(logo_small, *LOGO_SMALL_MAX)

    def load_hands(self):
        hands = {}

        for key, (filename, height) in HANDS.items():
            image = load_asset_image(filename)

            if image is not None:
                hands[key] = scale_to_height(image, height)

        return hands

    # ------------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------------

    def draw_background(self):
        self.screen.blit(self.background, (0, 0))

    def draw_logo(self, big=False):
        if big:
            rect = self.logo_big.get_rect(midtop=(self.width // 2, 40))
            self.screen.blit(self.logo_big, rect)
        else:
            rect = self.logo_small.get_rect(midtop=(self.width // 2, 14))
            self.screen.blit(self.logo_small, rect)

        return rect

    def draw_hand(self, key, x, anchor="left"):
        image = self.hands.get(key)

        if image is None:
            return

        rect = image.get_rect()

        if anchor == "left":
            rect.left = x
        else:
            rect.right = x

        rect.bottom = HAND_BOTTOM
        self.screen.blit(image, rect)

    def draw_bubble(self, lines, center_x, top, font=None):
        """White rounded speech-bubble with centred text lines."""
        font = font or self.body_font

        surfaces = [font.render(line, True, INK) for line in lines]
        line_gap = 6
        pad_x, pad_y = 30, 18

        w = max(s.get_width() for s in surfaces) + 2 * pad_x
        h = sum(s.get_height() for s in surfaces) + line_gap * (len(surfaces) - 1) + 2 * pad_y

        rect = pygame.Rect(0, 0, w, h)
        rect.midtop = (center_x, top)

        pygame.draw.rect(self.screen, WHITE, rect, border_radius=26)

        y = rect.top + pad_y

        for s in surfaces:
            self.screen.blit(s, (rect.centerx - s.get_width() // 2, y))
            y += s.get_height() + line_gap

        return rect

    def blit_fit(self, surface, center, max_width):
        """Blits a surface centred, shrinking it if it is wider than max_width."""
        if surface.get_width() > max_width:
            surface = scale_to_width(surface, max_width)

        self.screen.blit(surface, surface.get_rect(center=center))

    def draw_panel(self, rect):
        pygame.draw.rect(self.screen, WHITE, rect, border_radius=36)
        pygame.draw.rect(self.screen, PURPLE, rect, width=6, border_radius=36)

    def get_digit(self, number):
        if number not in self.digit_cache:
            self.digit_cache[number] = render_outlined(
                self.pixel_digit, str(number), WHITE, PURPLE, 14
            )

        return self.digit_cache[number]

    def pump_camera(self):
        """
        Grabs the newest camera frame and periodically saves it for
        gesture_server.py. Must run on EVERY screen, otherwise the gesture
        server keeps re-reporting the last gesture from a stale frame.
        """
        frame = self.camera.get_preview_frame()

        now = pygame.time.get_ticks()

        if now - self.last_frame_write > 150:
            self.last_frame_write = now

            try:
                np.save(FRAME_PATH, frame)
            except Exception:
                pass

        return frame

    def read_hand_state(self):
        """Reads the hand points file (at most ~20 times a second)."""
        now = pygame.time.get_ticks()

        if now - self.hand_read_at < 50:
            return

        self.hand_read_at = now

        try:
            with open(HAND_JSON_PATH, "r") as f:
                data = json.load(f)
        except (FileNotFoundError, ValueError, OSError):
            data = None

        if not data or time.time() - data.get("t", 0) > HAND_STALE_SECONDS:
            self.hand_points = None
            self.hand_gesture = None
            return

        self.hand_points = data.get("landmarks")
        self.hand_gesture = data.get("gesture")

    def draw_hand_overlay(self, rect):
        """Hand dots + skeleton, the gesture name and the hold bar, on top of the camera view."""
        self.read_hand_state()

        if not self.hand_points:
            return      # no hand in view: draw nothing

        # The points are 0-1 across the camera image, so they map straight onto rect.
        points = [
            (rect.x + x * rect.w, rect.y + y * rect.h) for x, y in self.hand_points
        ]

        if SHOW_HAND_DOTS:
            self.screen.set_clip(rect)

            for a, b in HAND_CONNECTIONS:
                pygame.draw.line(self.screen, WHITE, points[a], points[b], 7)
                pygame.draw.line(self.screen, PURPLE, points[a], points[b], 3)

            for x, y in points:
                pygame.draw.circle(self.screen, WHITE, (x, y), 11)
                pygame.draw.circle(self.screen, PURPLE, (x, y), 7)

            self.screen.set_clip(None)

        if SHOW_ACTION_LABEL:
            label = GESTURE_LABELS.get(self.hand_gesture, "Hand detected")
            surface = self.small_font.render(label, True, INK)

            pill = pygame.Rect(0, 0, max(surface.get_width() + 56, 200), 56)
            pill.midtop = (rect.centerx, rect.top + 16)

            pygame.draw.rect(self.screen, WHITE, pill, border_radius=28)
            self.screen.blit(surface, surface.get_rect(center=pill.center))

            if (SHOW_HOLD_BAR
                    and self.hand_gesture in SCREEN_GESTURES.get(self.current_screen, ())
                    and self.hand_gesture == self.candidate_gesture):
                progress = (pygame.time.get_ticks() - self.candidate_start) / HOLD_MS
                progress = max(0.0, min(1.0, progress))

                bar = pygame.Rect(0, 0, pill.width, 12)
                bar.midtop = (pill.centerx, pill.bottom + 8)

                pygame.draw.rect(self.screen, WHITE, bar, border_radius=6)
                pygame.draw.rect(
                    self.screen, PURPLE,
                    (bar.x, bar.y, int(bar.width * progress), bar.height),
                    border_radius=6
                )

    def draw_camera_feed(self, rect, overlay=True):
        """Draws the live preview inside rect, with a white + purple frame."""
        frame = self.pump_camera()

        # Picamera2 "RGB888" is actually BGR in memory; pygame wants RGB.
        rgb = frame[:, :, 2::-1].copy()

        surface = pygame.surfarray.make_surface(rgb.swapaxes(0, 1))
        surface = pygame.transform.scale(surface, rect.size)

        self.screen.blit(surface, rect.topleft)

        if overlay:
            self.draw_hand_overlay(rect)

        pygame.draw.rect(self.screen, WHITE, rect.inflate(16, 16), width=8)
        pygame.draw.rect(self.screen, PURPLE, rect.inflate(30, 30), width=7)

    def draw_flash(self):
        """White flash that fades out quickly, like a camera flash."""
        if self.flash_start is None:
            return

        progress = (pygame.time.get_ticks() - self.flash_start) / FLASH_MS

        if progress >= 1:
            self.flash_start = None
            return

        # (1 - progress) squared: bright at first, then fades fast.
        self.flash_surface.set_alpha(int(255 * (1 - progress) ** 2))
        self.screen.blit(self.flash_surface, (0, 0))

    def draw_gesture_debug(self):
        if SHOW_GESTURE_DEBUG:
            text = "Gesture: {}".format(self.detected_gesture)
            surface = self.debug_font.render(text, True, INK)

            rect = surface.get_rect(topleft=(24, 20)).inflate(20, 10)
            pygame.draw.rect(self.screen, WHITE, rect, border_radius=12)
            self.screen.blit(surface, surface.get_rect(center=rect.center))

    # ------------------------------------------------------------------
    # Screens
    # ------------------------------------------------------------------

    def draw_home(self):
        self.draw_background()
        logo_rect = self.draw_logo(big=True)

        # Camera sits just under the logo, however tall the logo turns out.
        cam = CAM_HOME.copy()
        cam.top = logo_rect.bottom + 45
        self.draw_camera_feed(cam)

        self.draw_bubble(["Show a thumbs", "up to start"], 365, 600)
        self.draw_hand("thumbs_up", 190)

    def draw_timer_select(self):
        self.draw_background()
        self.draw_logo()
        self.draw_camera_feed(CAM_BIG)

        self.draw_bubble(
            ["Hold up 3 fingers for 3 seconds", "Hold up 5 fingers for 5 seconds"],
            self.width // 2,
            BUBBLE_BIG_TOP
        )

        self.draw_hand("three", 120)
        self.draw_hand("open", self.width - 120, anchor="right")

    def draw_countdown(self, number):
        self.draw_background()
        self.draw_logo()
        self.draw_camera_feed(CAM_BIG, overlay=False)

        digit = self.get_digit(number)
        self.screen.blit(digit, digit.get_rect(center=CAM_BIG.center))

        self.draw_bubble(
            ["Photo {} of 4".format(self.photo_number)],
            self.width // 2,
            BUBBLE_COUNT_TOP
        )

    def build_review_thumbs(self):
        # Retakes save over the same file names, so the file's modified time
        # is part of the key; otherwise the old photos stay on screen.
        key = tuple(
            (path, os.path.getmtime(path) if os.path.exists(path) else 0)
            for path in self.captured_photos
        )

        if key == self.review_thumbs_key:
            return

        thumbs = []

        for path in self.captured_photos:
            try:
                image = pygame.image.load(path).convert()
                image = crop_to_aspect(image, SLOT_W / SLOT_H)
                thumbs.append(pygame.transform.smoothscale(image, (SLOT_W, SLOT_H)))
            except Exception as error:
                print("Couldn't load photo for review:", error)
                thumbs.append(None)

        self.review_thumbs = thumbs
        self.review_thumbs_key = key

    def draw_review(self):
        self.build_review_thumbs()

        self.draw_background()
        self.draw_logo()
        self.draw_camera_feed(CAM_BIG)

        total_w = 4 * SLOT_W + 3 * SLOT_GAP
        start_x = (self.width - total_w) // 2

        for i in range(4):
            x = start_x + i * (SLOT_W + SLOT_GAP)
            slot = pygame.Rect(x, SLOT_TOP, SLOT_W, SLOT_H)

            pygame.draw.rect(self.screen, WHITE, slot.inflate(20, 20), border_radius=6)

            thumb = self.review_thumbs[i] if i < len(self.review_thumbs) else None

            if thumb is not None:
                self.screen.blit(thumb, slot.topleft)
            else:
                pygame.draw.rect(self.screen, PURPLE, slot)

        self.draw_bubble(
            ["Hold up thumbs up to confirm", "Hold up closed fist to retake"],
            self.width // 2,
            BUBBLE_BIG_TOP
        )

        self.draw_hand("thumbs_up", 150)
        self.draw_hand("fist", self.width - 150, anchor="right")

    def draw_spinner(self, center_x, y):
        active = (pygame.time.get_ticks() // 250) % 5

        for i in range(5):
            colour = PURPLE if i == active else LAVENDER
            x = center_x + (i - 2) * 64 - 20
            pygame.draw.rect(self.screen, colour, (x, y, 40, 40), border_radius=6)

    def draw_processing(self):
        self.pump_camera()

        self.draw_background()
        self.draw_logo()

        panel = pygame.Rect(0, 0, 1100, 400)
        panel.center = (self.width // 2, 520)
        self.draw_panel(panel)

        heading = self.pixel_heading.render("SAVING YOUR PHOTOS", True, PURPLE)
        self.blit_fit(heading, (panel.centerx, panel.top + 110), panel.width - 100)

        message = self.body_font.render(self.job_message, True, INK)
        self.blit_fit(message, (panel.centerx, panel.top + 210), panel.width - 100)

        self.draw_spinner(panel.centerx, panel.top + 290)

    def draw_qr(self):
        self.draw_background()
        self.draw_logo()

        self.draw_panel(QR_PANEL)

        if self.qr_surface is not None:
            self.screen.blit(
                self.qr_surface, self.qr_surface.get_rect(center=QR_PANEL.center)
            )

        self.draw_camera_feed(CAM_QR)

        self.draw_bubble(
            ["Hold thumbs up once you have", "finished scanning"],
            CAM_QR.centerx,
            CAM_QR.bottom + 45
        )

        if PRINT_ENABLED:
            if self.print_state == "printing":
                note = "Printing your strip..."
            elif self.print_state == "done":
                note = "Your strip is printed!"
            elif self.print_state == "error":
                note = "Printer unavailable - your photos are still online"
            else:
                note = None

            if note:
                self.draw_bubble([note], QR_PANEL.centerx, QR_PANEL.bottom + 18, font=self.small_font)

        self.draw_hand("thumbs_up", self.width - 70, anchor="right")

    def draw_error(self):
        self.pump_camera()

        self.draw_background()
        self.draw_logo()

        panel = pygame.Rect(0, 0, 1200, 380)
        panel.center = (self.width // 2, 470)
        self.draw_panel(panel)

        heading = self.pixel_heading.render("OOPS!", True, PURPLE)
        self.blit_fit(heading, (panel.centerx, panel.top + 90), panel.width - 100)

        line = self.body_font.render("We couldn't save your photos.", True, INK)
        self.blit_fit(line, (panel.centerx, panel.top + 190), panel.width - 100)

        detail = self.small_font.render(str(self.job_error)[:80], True, (110, 100, 140))
        self.blit_fit(detail, (panel.centerx, panel.top + 270), panel.width - 100)

        self.draw_bubble(
            ["Hold up thumbs up to try again", "Hold up closed fist to start over"],
            self.width // 2,
            730
        )

        self.draw_hand("thumbs_up", 150)
        self.draw_hand("fist", self.width - 150, anchor="right")

    def draw(self):
        if self.current_screen == "home":
            self.draw_home()

        elif self.current_screen == "timer_select":
            self.draw_timer_select()

        elif self.current_screen == "countdown":
            elapsed = (pygame.time.get_ticks() - self.countdown_start) / 1000
            remaining = self.timer - int(elapsed)

            if remaining > 0:
                self.draw_countdown(remaining)

            else:
                if not self.photo_taken:
                    self.photo_taken = True

                    filepath = self.camera.take_photo(self.photo_number)
                    self.captured_photos.append(filepath)

                    if FLASH_ENABLED:
                        self.flash_start = pygame.time.get_ticks()

                    self.photo_number += 1

                if self.photo_number > 4:
                    self.change_screen("review")

                else:
                    self.countdown_start = pygame.time.get_ticks()
                    self.photo_taken = False

        elif self.current_screen == "review":
            self.draw_review()

        elif self.current_screen == "processing":
            self.draw_processing()

            if self.job_error:
                self.change_screen("error")

            elif self.job_done:
                self.show_qr()

        elif self.current_screen == "qr":
            self.draw_qr()

            if pygame.time.get_ticks() - self.qr_shown_at > QR_TIMEOUT_MS:
                self.go_home()

        elif self.current_screen == "error":
            self.draw_error()

        self.draw_gesture_debug()
        self.draw_flash()

        pygame.display.flip()

    # ------------------------------------------------------------------
    # Actions (shared by keyboard and gestures)
    # ------------------------------------------------------------------

    def change_screen(self, screen_name):
        """Switch screens and reset gesture state so nothing double-triggers."""
        self.current_screen = screen_name
        self.candidate_gesture = None
        self.cooldown_until = pygame.time.get_ticks() + COOLDOWN_MS

    def start_new_round(self, timer):
        self.timer = timer
        self.photo_number = 1
        self.photo_taken = False
        self.captured_photos = []
        self.review_thumbs_key = None
        self.countdown_start = pygame.time.get_ticks()
        self.change_screen("countdown")

    def retake_photos(self):
        self.captured_photos = []
        self.review_thumbs_key = None
        self.photo_number = 1
        self.photo_taken = False
        self.change_screen("timer_select")

    def go_home(self):
        self.captured_photos = []
        self.photo_number = 1
        self.photo_taken = False
        self.change_screen("home")

    # ------------------------------------------------------------------
    # Confirm -> upload to Supabase, make the QR code, print the strip.
    # The slow work runs in background threads so the window never freezes.
    # ------------------------------------------------------------------

    def confirm_photos(self):
        self.start_upload_job(also_print=True)

    def start_upload_job(self, also_print):
        self.job_message = "Getting ready..."
        self.job_done = False
        self.job_error = None

        photos = list(self.captured_photos)

        self.change_screen("processing")

        threading.Thread(
            target=self.run_upload_job, args=(photos,), daemon=True
        ).start()

        if also_print and PRINT_ENABLED:
            self.print_state = "printing"

            threading.Thread(
                target=self.run_print_job, args=(photos,), daemon=True
            ).start()

    def run_upload_job(self, photos):
        try:
            # Imported here so the app still starts even if the Supabase
            # credentials (.env) or packages are missing on this machine.
            from session.session import new_session
            from storage.upload import save_photo
            from qr.qr_generator import make_qr

            session_id = new_session()

            for number, path in enumerate(photos, start=1):
                self.job_message = "Uploading photo {}/{}...".format(
                    number, len(photos)
                )
                save_photo(session_id, number, path)

            # The photo strip (all 4 photos + logo) goes online as a 5th picture.
            # If making it fails, the 4 photos are still saved, so carry on.
            try:
                from printer.strip import make_strip

                self.job_message = "Adding your photo strip..."
                make_strip(
                    photos, STRIP_COLOR_PATH,
                    width=STRIP_ONLINE_WIDTH, dither=False, logo_path=STRIP_LOGO
                )
                save_photo(session_id, len(photos) + 1, STRIP_COLOR_PATH)

            except Exception as error:
                print("Photo strip upload skipped:", error)

            self.job_message = "Making your QR code..."
            make_qr(session_id, save_as=QR_PATH)

            self.job_done = True

        except Exception as error:
            print("Upload failed:", error)
            self.job_error = error

    def run_print_job(self, photos):
        # Independent of the upload: a printer problem never blocks the QR code.
        try:
            from printer.strip import make_strip
            from printer.printer import print_strip

            make_strip(photos, STRIP_PATH, logo_path=STRIP_LOGO)

            # One print at a time, in case a new round finishes while this one prints.
            with self.print_lock:
                print_strip(STRIP_PATH)

            self.print_state = "done"

        except Exception as error:
            print("Print failed:", error)
            self.print_state = "error"

    def show_qr(self):
        try:
            image = pygame.image.load(QR_PATH).convert()
            self.qr_surface = pygame.transform.scale(image, (QR_SIZE, QR_SIZE))
        except Exception as error:
            print("Couldn't load QR code:", error)
            self.job_error = error
            self.change_screen("error")
            return

        self.qr_shown_at = pygame.time.get_ticks()
        self.change_screen("qr")

    # ------------------------------------------------------------------
    # Gestures — read from the file gesture_server.py writes to.
    # ------------------------------------------------------------------

    def read_latest_gesture(self):
        try:
            with open(GESTURE_PATH, "r") as f:
                text = f.read().strip()
                return text if text else None
        except FileNotFoundError:
            return None

    def update_gestures(self):
        """
        Polls the gesture file a few times a second. A gesture only fires
        after being seen steadily for HOLD_MS.
        """
        # No gesture input while photos are being taken or uploaded.
        if self.current_screen in ("countdown", "processing"):
            return

        now = pygame.time.get_ticks()

        if now < self.cooldown_until:
            return

        if now - self.last_detect_time < DETECT_EVERY_MS:
            return

        self.last_detect_time = now

        gesture = self.read_latest_gesture()
        self.detected_gesture = gesture

        # Nothing seen, or the gesture changed: restart the hold timer.
        if gesture is None or gesture != self.candidate_gesture:
            self.candidate_gesture = gesture
            self.candidate_start = now
            return

        # Same gesture, held long enough: trigger it.
        if now - self.candidate_start >= HOLD_MS:
            self.handle_gesture(gesture)

    def handle_gesture(self, gesture):
        if self.current_screen == "home":
            if gesture == "THUMBS_UP":
                self.change_screen("timer_select")

        elif self.current_screen == "timer_select":
            if gesture == "THREE_FINGERS":
                self.start_new_round(3)

            elif gesture == "OPEN_HAND":
                self.start_new_round(5)

        elif self.current_screen == "review":
            if gesture == "THUMBS_UP":
                self.confirm_photos()

            elif gesture == "IS_FIST":
                self.retake_photos()

        elif self.current_screen == "qr":
            if gesture == "THUMBS_UP":
                self.go_home()

        elif self.current_screen == "error":
            if gesture == "THUMBS_UP":
                self.start_upload_job(also_print=False)

            elif gesture == "IS_FIST":
                self.go_home()

    # ------------------------------------------------------------------
    # Keyboard (kept as a fallback for testing)
    # ------------------------------------------------------------------

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                self.running = False

            elif self.current_screen == "home":

                if event.key == pygame.K_SPACE:
                    self.change_screen("timer_select")

            elif self.current_screen == "timer_select":

                if event.key == pygame.K_3:
                    self.start_new_round(3)

                elif event.key == pygame.K_5:
                    self.start_new_round(5)

            elif self.current_screen == "review":

                if event.key == pygame.K_SPACE:
                    self.confirm_photos()

                elif event.key == pygame.K_0:
                    self.retake_photos()

            elif self.current_screen == "qr":

                if event.key == pygame.K_SPACE:
                    self.go_home()

            elif self.current_screen == "error":

                if event.key == pygame.K_SPACE:
                    self.start_upload_job(also_print=False)

                elif event.key == pygame.K_0:
                    self.go_home()

    def run(self):
        clock = pygame.time.Clock()

        while self.running:
            for event in pygame.event.get():
                self.handle_event(event)

            self.draw()
            self.update_gestures()

            clock.tick(60)

        pygame.quit()