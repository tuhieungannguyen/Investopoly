import threading
import pygame
import sys
import websockets
import asyncio
import json
import requests

pygame.init()
screen = pygame.display.set_mode((1200, 800))
pygame.display.set_caption("Investopoly - Main Game UI")
clock = pygame.time.Clock()
font = pygame.font.SysFont('Arial', 20)
font_title = pygame.font.SysFont('Arial', 26, bold=True)

# Màu
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
BLUE = (100, 149, 237)
LIGHT_GRAY = (230, 230, 230)
GREEN = (34, 139, 34)

# Vị trí layout
top_bar = pygame.Rect(20, 20, 1160, 50)
map_area = pygame.Rect(20, 80, 850, 600)
event_box = pygame.Rect(890, 80, 290, 150)
leaderboard_box = pygame.Rect(890, 250, 290, 200)
portfolio_box = pygame.Rect(890, 470, 290, 210)
action_bar = pygame.Rect(20, 700, 1160, 70)

# Dữ liệu mẫu
event_logs = ["Game started", "Player1 rolled 6", "Player1 landed on GO"]
leaderboard = [("Player1", 4500), ("Player2", 3800), ("Player3", 3600)]
portfolio = {
    "Cash": 1200,
    "Stocks": 800,
    "Real Estate": 1500,
    "Savings": 500
}
# ws variable
ws_joined_players = []
ws_leaderboard = []
ws_portfolio = {}

async def listen_ws(room_id, player_name):
    global ws_joined_players, ws_leaderboard, ws_portfolio
    uri = f"ws://localhost:8000/ws/{room_id}/{player_name}"
    async with websockets.connect(uri) as ws:
        while True:
            try:
                data = json.loads(await ws.recv())
                if data["type"] == "player_joined":
                    ws_joined_players = data["players"]
                    ws_leaderboard = [(p["player"], p["net_worth"]) for p in data.get("leaderboard", [])]
                    if data["player"] == player_name:
                        ws_portfolio = data.get("portfolio", {})
            except Exception as e:
                print("[WebSocket Error]", e)
                break
def draw_box(rect, title, surface, items=None, is_dict=False):
    pygame.draw.rect(surface, LIGHT_GRAY, rect)
    pygame.draw.rect(surface, BLACK, rect, 2)
    surface.blit(font_title.render(title, True, BLACK), (rect.x + 10, rect.y + 10))

    if not items:
        return

    if is_dict:
        lines = []

        # Format các trường đặc biệt đẹp hơn
        def fmt_money(key, value):
            return f"{key.replace('_', ' ').capitalize()}: ${float(value):,.2f}"

        for key in [
            "cash", "saving", "net_worth",
            "current_position", "round_played", "stocks", "estates"
        ]:
            val = items.get(key, "-")

            if isinstance(val, (int, float)) and key != "current_position":
                line = fmt_money(key, val)
            elif isinstance(val, dict):
                line = f"{key.capitalize()}: {len(val)}"
            elif isinstance(val, list):
                line = f"{key.capitalize()}: {len(val)}"
            else:
                line = f"{key.replace('_', ' ').capitalize()}: {val}"

            lines.append(line)

        for i, line in enumerate(lines):
            text = font.render(line, True, BLACK)
            surface.blit(text, (rect.x + 10, rect.y + 40 + i * 22))
    else:
        for i, item in enumerate(items):
            text = f"{item[0]} - ${item[1]}"
            surface.blit(font.render(text, True, BLACK), (rect.x + 10, rect.y + 40 + i * 25))



def draw_top_bar(surface, room, player):
    pygame.draw.rect(surface, BLUE, top_bar)
    pygame.draw.rect(surface, BLACK, top_bar, 2)
    label = font_title.render(f"Room: {room} | Player: {player}", True, WHITE)
    surface.blit(label, (top_bar.x + 20, top_bar.y + 10))

def draw_action_buttons(surface):
    pygame.draw.rect(surface, GRAY, action_bar)
    pygame.draw.rect(surface, BLACK, action_bar, 2)
    buttons = ["Roll Dice", "Buy/Sell", "End Turn"]
    for i, label in enumerate(buttons):
        rect = pygame.Rect(50 + i * 200, action_bar.y + 15, 150, 40)
        pygame.draw.rect(surface, GREEN, rect)
        pygame.draw.rect(surface, BLACK, rect, 2)
        text = font.render(label, True, WHITE)
        surface.blit(text, text.get_rect(center=rect.center))

def draw_map_placeholder(surface):
    pygame.draw.rect(surface, WHITE, map_area)
    pygame.draw.rect(surface, BLACK, map_area, 2)
    label = font_title.render("MAP HERE", True, GRAY)
    surface.blit(label, label.get_rect(center=map_area.center))
def run_ui(room_id, player_name, joined_players, is_host, leaderboard=None, portfolio=None):
    if not pygame.get_init():
        pygame.init()
    if not pygame.display.get_init():
        pygame.display.init()
    
    screen = pygame.display.set_mode((1200, 800))
    pygame.display.set_caption("Investopoly - Main Game UI")
    threading.Thread(target=lambda: asyncio.run(listen_ws(room_id, player_name)), daemon=True).start()
    running = True
    start_btn = pygame.Rect(950, 720, 180, 50)  # Khai báo ở đầu

    while running:
        screen.fill(WHITE)
        events = pygame.event.get()

        for e in events:
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.MOUSEBUTTONDOWN and is_host:
                if start_btn.collidepoint(e.pos):
                    try:
                        requests.post(f"http://localhost:8000/start", json={"room_id": room_id})
                    except Exception as err:
                        print(f"[Error] Failed to start game: {err}")

        # Vẽ UI
        draw_top_bar(screen, room_id, player_name)
        draw_map_placeholder(screen)
        draw_box(event_box, "Players", screen, ws_joined_players or joined_players)
        draw_box(leaderboard_box, "Leaderboard", screen, ws_leaderboard or leaderboard)
        draw_box(portfolio_box, "Player Property", screen, ws_portfolio or portfolio, is_dict=True)
        draw_action_buttons(screen)

        # Nút start chỉ nếu là host
        if is_host:
            pygame.draw.rect(screen, GREEN, start_btn)
            pygame.draw.rect(screen, BLACK, start_btn, 2)
            text = font.render("START", True, WHITE)
            screen.blit(text, text.get_rect(center=start_btn.center))

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
    sys.exit()
