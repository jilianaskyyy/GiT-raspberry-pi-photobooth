import pygame


class PhotoboothUI:
    def __init__(self):
        pygame.init()

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

    def draw_text(self, text, font, x, y):
        surface = font.render(text, True, (0, 0, 0))
        self.screen.blit(surface, (x, y))

    def draw_home(self):
        self.screen.fill((255, 250, 236))

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
        self.screen.fill((255, 250, 236))

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
        self.screen.fill((0, 0, 0))

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
        self.screen.fill((255, 250, 236))

        self.draw_text(
            "REVIEW PHOTOS",
            self.title_font,
            260,
            40
        )

        # Temporary placeholders for 4 photos
        pygame.draw.rect(
            self.screen,
            (220, 220, 220),
            (50, 120, 160, 120)
        )

        pygame.draw.rect(
            self.screen,
            (220, 220, 220),
            (230, 120, 160, 120)
        )

        pygame.draw.rect(
            self.screen,
            (220, 220, 220),
            (410, 120, 160, 120)
        )

        pygame.draw.rect(
            self.screen,
            (220, 220, 220),
            (590, 120, 160, 120)
        )

        self.draw_text(
            "PHOTO 1",
            self.text_font,
            90,
            170
        )

        self.draw_text(
            "PHOTO 2",
            self.text_font,
            270,
            170
        )

        self.draw_text(
            "PHOTO 3",
            self.text_font,
            450,
            170
        )

        self.draw_text(
            "PHOTO 4",
            self.text_font,
            630,
            170
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

                    print(f"Photo {self.photo_number} taken!")

                    self.photo_number += 1

                if self.photo_number > 4:
                    self.current_screen = "review"

                else:
                    self.countdown_start = pygame.time.get_ticks()
                    self.photo_taken = False

        elif self.current_screen == "review":
            self.draw_review()

        pygame.display.flip()

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
                    self.timer = 3
                    self.photo_number = 1
                    self.photo_taken = False
                    self.countdown_start = pygame.time.get_ticks()
                    self.current_screen = "countdown"

                elif event.key == pygame.K_5:
                    self.timer = 5
                    self.photo_number = 1
                    self.photo_taken = False
                    self.countdown_start = pygame.time.get_ticks()
                    self.current_screen = "countdown"

            elif self.current_screen == "review":

                if event.key == pygame.K_SPACE:
                    self.current_screen = "home"

                elif event.key == pygame.K_0:
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


if __name__ == "__main__":
    ui = PhotoboothUI()
    ui.run()