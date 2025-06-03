import pygame

class HostDashboard:
    def __init__(self, screen, state_manager, start_game_callback):
        self.screen = screen
        self.state_manager = state_manager
        self.start_game_callback = start_game_callback
        self.font = pygame.font.SysFont("Arial", 24)
        self.running = True

    def draw_button(self, rect, text, color=(70, 130, 180)):
        pygame.draw.rect(self.screen, color, rect)
        pygame.draw.rect(self.screen, (0, 0, 0), rect, 2)
        label = self.font.render(text, True, (255, 255, 255))
        label_rect = label.get_rect(center=rect.center)
        self.screen.blit(label, label_rect)

    def draw_player_stats(self, x, y):
        self.screen.blit(self.font.render("Player Stats:", True, (0, 0, 0)), (x, y))
        offset = 40
        for pid, pdata in self.state_manager.players.items():
            text = f"{pid} | Cash: {pdata.get('cash', 0)} | NW: {pdata.get('net_worth', 0)}"
            self.screen.blit(self.font.render(text, True, (0, 0, 0)), (x, y + offset))
            offset += 30

    def draw_market_controls(self, x, y):
        self.screen.blit(self.font.render("Market Controls (stub):", True, (0, 0, 0)), (x, y))
        self.screen.blit(self.font.render("- Market crash, interest, inflation...", True, (100, 0, 0)), (x, y + 30))
        # Bạn có thể thêm nút hoặc input ở đây nếu muốn điều chỉnh giá/biến cố

    def loop(self):
        clock = pygame.time.Clock()
        start_btn = pygame.Rect(100, 100, 200, 50)

        while self.running:
            self.screen.fill((230, 230, 250))
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if start_btn.collidepoint(event.pos):
                        self.start_game_callback()
                        return

            self.draw_button(start_btn, "Start Game")
            self.draw_player_stats(100, 180)
            self.draw_market_controls(500, 180)

            pygame.display.flip()
            clock.tick(30)
