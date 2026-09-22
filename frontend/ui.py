import pygame


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

        self.running = True
        self.current_screen = "home"

        self.timer = 0
        self.countdown_start = 0
        self.photo_number = 1
        self.photo_taken = False

        self.captured_photos = []

    def draw_text(self, text, font, x, y):
        surface = font.render(text, True, (0, 0, 0))
        self.screen.blit(surface, (x, y))

    def draw_camera_feed(self):
        """Blits the live preview frame as the screen background."""
        frame = self.camera.get_preview_frame()

        # capture_array gives HxWx3; pygame surfaces want WxHx3.
        surface = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
        surface = pygame.transform.scale(surface, (self.width, self.height))

        self.screen.blit(surface, (0, 0))

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

    def draw_timer_select(self):
        self.draw_camera_feed()

        self.draw_text(
            "CHOOSE COUNTDOWN",
            self.title_font,
            220,
            80
        )

        self.draw_text(
            "Press 3 for 3 seconds",
            self.text_font,
            260,
            220
        )

        self.draw_text(
            "Press 5 for 5 seconds",
            self.text_font,
            260,
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
                    self.current_screen = "review"

                else:
                    self.countdown_start = pygame.time.get_ticks()
                    self.photo_taken = False

        elif self.current_screen == "review":
            self.draw_review()

        pygame.display.flip()

    def start_new_round(self, timer):
        self.timer = timer
        self.photo_number = 1
        self.photo_taken = False
        self.captured_photos = []
        self.countdown_start = pygame.time.get_ticks()
        self.current_screen = "countdown"

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                self.running = False

            elif self.current_screen == "home":

                if event.key == pygame.K_SPACE:
                    self.current_screen = "timer_select"

            elif self.current_screen == "timer_select":

                if event.key == pygame.K_3:
                    self.start_new_round(3)

                elif event.key == pygame.K_5:
                    self.start_new_round(5)

            elif self.current_screen == "review":

                if event.key == pygame.K_SPACE:
                    # Confirm — placeholder for printing/QR step.
                    self.current_screen = "home"

                elif event.key == pygame.K_0:
                    # Retake — back to timer select, drop this round's photos.
                    self.captured_photos = []
                    self.photo_number = 1
                    self.photo_taken = False
                    self.current_screen = "timer_select"

    def run(self):
        clock = pygame.time.Clock()

        while self.running:
            for event in pygame.event.get():
                self.handle_event(event)

            self.draw()

            clock.tick(60)

        pygame.quit()