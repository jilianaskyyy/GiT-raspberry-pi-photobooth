import os

import numpy as np
import pygame

# How long a gesture must be held before it counts (avoids accidental triggers).
HOLD_MS = 800

# After any screen change, ignore gestures for this long so a gesture you're
# still holding doesn't instantly trigger the next screen.
COOLDOWN_MS = 1500

# Run gesture detection at most this often.
DETECT_EVERY_MS = 150

# Shows the detected gesture in the corner. Handy while tuning; set False later.
SHOW_GESTURE_DEBUG = True

# Shared files used to talk to gesture_server.py (runs in the 3.11 venv).
FRAME_PATH = "/tmp/photobooth_frame.npy"
GESTURE_PATH = "/tmp/photobooth_gesture.txt"


class PhotoboothUI:
    def __init__(self, camera):
        pygame.init()

        self.camera = camera

        self.width = 800
        self.height = 480

        self.screen = pygame.display.set_mode(
            (self.width, self.height),
            pygame.RESIZABLE
        )

        pygame.display.set_caption("Raspberry Pi Photobooth")

        self.title_font = pygame.font.Font(None, 60)
        self.button_font = pygame.font.Font(None, 40)
        self.text_font = pygame.font.Font(None, 32)
        self.small_font = pygame.font.Font(None, 26)

        self.running = True
        self.current_screen = "home"

        self.timer = 0
        self.countdown_start = 0
        self.photo_number = 1
        self.photo_taken = False

        self.captured_photos = []

        # Gesture state
        self.last_frame_write = 0
        self.last_detect_time = 0
        self.detected_gesture = None    # last gesture read from gesture_server.py
        self.candidate_gesture = None   # gesture currently being "held"
        self.candidate_start = 0
        self.cooldown_until = 0

    # ------------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------------

    def draw_text(self, text, font, x, y):
        surface = font.render(text, True, (0, 0, 0))
        self.screen.blit(surface, (x, y))

    def draw_camera_feed(self):
        """Blits the live preview frame as the screen background, and
        periodically saves it for gesture_server.py to pick up."""
        frame = self.camera.get_preview_frame()

        now = pygame.time.get_ticks()

        if now - self.last_frame_write > 150:
            self.last_frame_write = now

            try:
                np.save(FRAME_PATH, frame)
            except Exception:
                pass

        # Picamera2 "RGB888" is actually BGR in memory; pygame wants RGB.
        rgb = frame[:, :, ::-1].copy()

        surface = pygame.surfarray.make_surface(rgb.swapaxes(0, 1))
        surface = pygame.transform.scale(surface, (self.width, self.height))

        self.screen.blit(surface, (0, 0))

    def draw_gesture_debug(self):
        if SHOW_GESTURE_DEBUG:
            self.draw_text(
                "Gesture: {}".format(self.detected_gesture),
                self.small_font,
                10,
                10
            )

    def draw_home(self):
        self.draw_camera_feed()

        self.draw_text(
            "PHOTOBOOTH",
            self.title_font,
            280,
            70
        )

        pygame.draw.rect(
            self.screen,
            (255, 200, 50),
            (250, 300, 300, 80)
        )

        self.draw_text(
            "START",
            self.button_font,
            360,
            325
        )

        self.draw_text(
            "Show a thumbs up to start",
            self.text_font,
            270,
            400
        )

    def draw_timer_select(self):
        self.draw_camera_feed()

        self.draw_text(
            "CHOOSE COUNTDOWN",
            self.title_font,
            220,
            80
        )

        self.draw_text(
            "3 fingers (or press 3) = 3 seconds",
            self.text_font,
            210,
            220
        )

        self.draw_text(
            "Open hand (or press 5) = 5 seconds",
            self.text_font,
            210,
            270
        )

    def draw_countdown(self, number):
        self.draw_camera_feed()

        self.draw_text(
            str(number),
            self.title_font,
            390,
            200
        )

        self.draw_text(
            f"Photo {self.photo_number}/4",
            self.text_font,
            330,
            280
        )

    def draw_review(self):
        self.draw_camera_feed()

        self.draw_text(
            "REVIEW PHOTOS",
            self.title_font,
            260,
            40
        )

        positions = [50, 230, 410, 590]

        for i, filepath in enumerate(self.captured_photos):
            thumb = pygame.image.load(filepath)
            thumb = pygame.transform.scale(thumb, (160, 120))
            self.screen.blit(thumb, (positions[i], 120))

            self.draw_text(
                "PHOTO {}".format(i + 1),
                self.text_font,
                positions[i] + 30,
                250
            )

        pygame.draw.rect(
            self.screen,
            (255, 200, 50),
            (100, 350, 250, 60)
        )

        pygame.draw.rect(
            self.screen,
            (230, 230, 230),
            (450, 350, 250, 60)
        )

        self.draw_text(
            "CONFIRM",
            self.button_font,
            155,
            365
        )

        self.draw_text(
            "RETAKE",
            self.button_font,
            515,
            365
        )

        self.draw_text(
            "Thumbs up = confirm      Fist = retake",
            self.text_font,
            220,
            430
        )

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

                    self.photo_number += 1

                if self.photo_number > 4:
                    self.change_screen("review")

                else:
                    self.countdown_start = pygame.time.get_ticks()
                    self.photo_taken = False

        elif self.current_screen == "review":
            self.draw_review()

        self.draw_gesture_debug()

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
        self.countdown_start = pygame.time.get_ticks()
        self.change_screen("countdown")

    def confirm_photos(self):
        # Placeholder for the printing / QR code step.
        self.change_screen("home")

    def retake_photos(self):
        self.captured_photos = []
        self.photo_number = 1
        self.photo_taken = False
        self.change_screen("timer_select")

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
        # No gesture input while photos are being taken.
        if self.current_screen == "countdown":
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

    def run(self):
        clock = pygame.time.Clock()

        while self.running:
            for event in pygame.event.get():
                self.handle_event(event)

            self.draw()
            self.update_gestures()

            clock.tick(60)

        pygame.quit()