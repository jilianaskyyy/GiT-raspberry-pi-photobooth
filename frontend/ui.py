import threading

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

# Upload / print settings
PRINT_ENABLED = False                   # False = skip the printer (handy when testing upload + QR)
STRIP_PATH = "photostrip/strip_print.png"
QR_PATH = "photostrip/qr.png"
QR_TIMEOUT_MS = 45000                   # QR screen returns to home by itself after this long


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

        # Upload / print job state (the work runs in background threads)
        self.job_message = ""
        self.job_done = False
        self.job_error = None
        self.print_error = False
        self.print_lock = threading.Lock()
        self.qr_surface = None
        self.qr_shown_at = 0
    # ------------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------------

    def draw_text(self, text, font, x, y):
        surface = font.render(text, True, (0, 0, 0))
        self.screen.blit(surface, (x, y))

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

    def draw_camera_feed(self):
        """Blits the live preview frame as the screen background."""
        frame = self.pump_camera()

        # Picamera2 "RGB888" is actually BGR in memory; pygame wants RGB.
        rgb = frame[:, :, ::-1].copy()

        surface = pygame.surfarray.make_surface(rgb.swapaxes(0, 1))
        surface = pygame.transform.scale(surface, (self.width, self.height))

        self.screen.blit(surface, (0, 0))

    def draw_text_centered(self, text, font, y):
        surface = font.render(text, True, (0, 0, 0))
        x = (self.width - surface.get_width()) // 2
        self.screen.blit(surface, (x, y))
        
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

    def draw_processing(self):
        self.pump_camera()
        self.screen.fill((255, 250, 236))

        self.draw_text_centered("PLEASE WAIT", self.title_font, 150)
        self.draw_text_centered(self.job_message, self.text_font, 240)

    def draw_qr(self):
        self.pump_camera()
        self.screen.fill((255, 250, 236))

        self.draw_text_centered("SCAN TO GET YOUR PHOTOS", self.title_font, 25)

        if self.qr_surface is not None:
            self.screen.blit(self.qr_surface, ((self.width - 300) // 2, 90))

        self.draw_text_centered("Thumbs up when you're done", self.text_font, 400)

        if self.print_error:
            self.draw_text_centered(
                "(Printer unavailable - your photos are still online)",
                self.small_font,
                440
            )

    def draw_error(self):
        self.pump_camera()
        self.screen.fill((255, 250, 236))

        self.draw_text_centered("SOMETHING WENT WRONG", self.title_font, 110)
        self.draw_text_centered("We couldn't upload your photos.", self.text_font, 200)
        self.draw_text_centered(str(self.job_error)[:70], self.small_font, 245)
        self.draw_text_centered(
            "Thumbs up = try again      Fist = start over",
            self.text_font,
            330
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

    def retake_photos(self):
        self.captured_photos = []
        self.photo_number = 1
        self.photo_taken = False
        self.change_screen("timer_select")
 
    def go_home(self):
        self.captured_photos = []
        self.photo_number = 1
        self.photo_taken = False
        self.change_screen("home")

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
            self.print_error = False
 
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
 
            self.job_message = "Making your QR code..."
            make_qr(session_id, save_as=QR_PATH)
 
            self.job_done = True
 
        except Exception as error:
            print("Upload failed:", error)
            self.job_error = error
 
    def run_print_job(self, photos):
        # Independent of the upload: a printer problem never blocks the QR code.
        try:
            from printing.strip import make_strip
            from printing.printer import print_strip
 
            make_strip(photos, STRIP_PATH)
 
            # One print at a time, in case a new round finishes while this one prints.
            with self.print_lock:
                print_strip(STRIP_PATH)
 
        except Exception as error:
            print("Print failed:", error)
            self.print_error = True
 
    def show_qr(self):
        try:
            image = pygame.image.load(QR_PATH)
            self.qr_surface = pygame.transform.scale(image, (300, 300))
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