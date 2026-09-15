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

    def draw_camera(self):
        self.screen.fill((0, 0, 0))

        self.draw_text(
            "Camera Preview",
            self.text_font,
            20,
            20
        )

        pygame.draw.rect(
            self.screen,
            (80, 80, 80),
            (100, 70, 600, 320)
        )

        self.draw_text(
            "Camera Feed",
            self.text_font,
            320,
            215
        )

    def draw_countdown(self, number):
        self.screen.fill((0, 0, 0))

        self.draw_text(
            str(number),
            self.title_font,
            390,
            200
        )

    def draw_review(self):
        self.screen.fill((255, 250, 236))

        self.draw_text(
            "Review Photo",
            self.title_font,
            270,
            50
        )

        pygame.draw.rect(
            self.screen,
            (220, 220, 220),
            (200, 120, 400, 250)
        )

        pygame.draw.rect(
            self.screen,
            (255, 200, 50),
            (100, 400, 250, 60)
        )

        pygame.draw.rect(
            self.screen,
            (230, 230, 230),
            (450, 400, 250, 60)
        )

        self.draw_text(
            "CONFIRM",
            self.button_font,
            155,
            415
        )

        self.draw_text(
            "RETAKE",
            self.button_font,
            515,
            415
        )

    def draw(self):
        if self.current_screen == "home":
            self.draw_home()

        elif self.current_screen == "camera":
            self.draw_camera()

        elif self.current_screen == "countdown":
            self.draw_countdown(3)

        elif self.current_screen == "review":
            self.draw_review()

        pygame.display.flip()

    def handle_event(self, event):

        if event.type == pygame.QUIT:
            self.running = False

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                self.running = False

            elif event.key == pygame.K_1:
                self.current_screen = "home"

            elif event.key == pygame.K_2:
                self.current_screen = "camera"

            elif event.key == pygame.K_3:
                self.current_screen = "countdown"

            elif event.key == pygame.K_4:
                self.current_screen = "review"

    def run(self):

        clock = pygame.time.Clock()

        while self.running:

            for event in pygame.event.get():
                self.handle_event(event)

            self.draw()

            clock.tick(60)

        pygame.quit()

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