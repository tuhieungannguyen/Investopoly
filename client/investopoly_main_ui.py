import threading
import pygame
import sys
import websockets
import asyncio
import json
import requests
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../shared')))
from constants import TILE_MAP

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
event_box = pygame.Rect(850, 80, 325, 250)
leaderboard_box = pygame.Rect(850, 350, 325, 250)
portfolio_box = pygame.Rect(850, 620, 320, 260)
action_bar = pygame.Rect(20, 900, 1160, 70)

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
            if isinstance(item, dict):
                text = f"{item.get('player_name', 'Unknown')} - Position: {item.get('current_position', 'Unknown')}"
            else:
                text = str(item)
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

def draw_map(surface):
    pygame.draw.rect(surface, WHITE, map_area)
    pygame.draw.rect(surface, BLACK, map_area, 2)

    tile_width = map_area.width // 5
    tile_height = map_area.height // 5

    # Vẽ các ô theo hình chữ nhật
    for i, tile in enumerate(TILE_MAP):
        if i < 5:  # Cột bên trái (đi lên)
            x = map_area.x
            y = map_area.y + map_area.height - (i + 1) * tile_height
        elif i < 10:  # Hàng trên cùng (đi sang phải)
            x = map_area.x + (i - 5) * tile_width
            y = map_area.y
        elif i < 15:  # Cột bên phải (đi xuống)
            x = map_area.x + map_area.width - tile_width
            y = map_area.y + (i - 10) * tile_height
        else:  # Hàng dưới cùng (đi sang trái)
            x = map_area.x + map_area.width - (i - 15 + 1) * tile_width
            y = map_area.y + map_area.height - tile_height

        tile_rect = pygame.Rect(x, y, tile_width, tile_height)
        pygame.draw.rect(surface, LIGHT_GRAY, tile_rect)
        pygame.draw.rect(surface, BLACK, tile_rect, 1)

        label = font.render(tile, True, BLACK)
        surface.blit(label, label.get_rect(center=tile_rect.center))

def draw_map_with_players(surface, players):
    # Load the board image as the map
    board_image_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../shared/ui/board_new.png'))
    board_image = pygame.image.load(board_image_path)
    board_image = pygame.transform.scale(board_image, (800, 800))
    surface.blit(board_image, (map_area.x, map_area.y))

    # Load avatars using absolute path
    shared_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../shared/avt'))
    avatars = [
        pygame.image.load(os.path.join(shared_path, f"{i}.png")) for i in range(1, len(players) + 1)
    ]

    # Define tile dimensions based on the scaled board
    corner_tile_size = (172, 172)  # Corner tiles
    vertical_tile_size = (172, 115)  # Vertical tiles
    horizontal_tile_size = (115, 172)  # Horizontal tiles

    for idx, player in enumerate(players):
        if isinstance(player, dict) and "current_position" in player:
            position = player["current_position"]

            if position == 0:  # GO
                x, y = map_area.x, map_area.y + 800 - corner_tile_size[1]
            elif position < 5:  # Left column (going up)
                x, y = map_area.x, map_area.y + 800 - (position * vertical_tile_size[1]) - corner_tile_size[1]
            elif position == 5:  # Jail Visit
                x, y = map_area.x, map_area.y
            elif position < 10:  # Top row (going right)
                x, y = map_area.x + ((position - 6) * horizontal_tile_size[0]) + corner_tile_size[0], map_area.y
            elif position == 10:  # Quizzes (Education)
                x, y = map_area.x + 800 - corner_tile_size[0], map_area.y
            elif position < 15:  # Right column (going down)
                x, y = map_area.x + 800 - vertical_tile_size[0], map_area.y + ((position - 11) * vertical_tile_size[1]) + corner_tile_size[1]
            elif position == 15:  # Jail (Challenge)
                x, y = map_area.x + 800 - corner_tile_size[0], map_area.y + 800 - corner_tile_size[1]
            else:  # Bottom row (going left)
                x, y = map_area.x + 800 - ((position - 15) * horizontal_tile_size[0]) - corner_tile_size[0], map_area.y + 800 - horizontal_tile_size[1]

            avatar = pygame.transform.scale(avatars[idx], (corner_tile_size[0] // 3, corner_tile_size[1] // 3))
            surface.blit(avatar, (x + corner_tile_size[0] // 4, y + corner_tile_size[1] // 4))

def run_ui(room_id, player_name, joined_players, is_host, leaderboard=None, portfolio=None):
    if not pygame.get_init():
        pygame.init()
    if not pygame.display.get_init():
        pygame.display.init()

    # Adjust the window size to match the board dimensions
    screen = pygame.display.set_mode((1200, 1000))
    pygame.display.set_caption("Investopoly - Main Game UI")

    threading.Thread(target=lambda: asyncio.run(listen_ws(room_id, player_name)), daemon=True).start()
    running = True
    start_btn = pygame.Rect(850, 920, 120, 50)  # Adjusted position for the start button

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
        draw_map_with_players(screen, ws_joined_players or joined_players)
        draw_box(event_box, "Notification", screen, ws_joined_players or joined_players)
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
