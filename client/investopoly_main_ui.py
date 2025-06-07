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

# Define global variable for current round
current_round = None
current_player = None

async def listen_ws(room_id, player_name):
    global ws_joined_players, ws_leaderboard, ws_portfolio, ws_notifications, current_player, current_round
    ws_notifications = []  # Initialize notifications list
    uri = f"ws://localhost:8000/ws/{room_id}/{player_name}"
    async with websockets.connect(uri) as ws:
        while True:
            try:
                data = await ws.recv()
                message = json.loads(data)

                if message["type"] == "game_started":
                    ws_notifications.append(f"Notification: {message['message']}\nRound: {message['round']}\nCurrent Player: {message['current_player']}")
                    current_player = message["current_player"]
                    current_round = message["round"]

                elif message["type"] == "next_turn":
                    ws_notifications.append(f"Notification: {message['message']}")
                    current_player = message["current_player"]
                    current_round = message["round"]

                elif message["type"] == "player_rolled":
                    ws_notifications.append(f"Notification: {message['message']}")

                elif message["type"] == "player_joined":
                    ws_notifications.append(f"{message['player']} joined the room.")
                    ws_joined_players = message["players"]
                    # Validate leaderboard data before updating
                    if "leaderboard" in message and message["leaderboard"]:
                        print("Received leaderboard data:", message["leaderboard"])  # Debug log
                        ws_leaderboard = message["leaderboard"]

            except Exception as e:
                print(f"WebSocket error: {e}")

def draw_box(rect, title, surface, items=None, is_dict=False):
    pygame.draw.rect(surface, LIGHT_GRAY, rect)
    pygame.draw.rect(surface, BLACK, rect, 2)
    surface.blit(font_title.render(title, True, BLACK), (rect.x + 10, rect.y + 10))

    if not items:
        return

    if title == "Notification":
        for i, item in enumerate(items):
            if isinstance(item, dict):
                text = f"Notification: {item.get('player_name', 'Unknown')} - Position: {item.get('current_position', 'Unknown')}"
            else:
                text = f"Notification: {str(item)}"
            surface.blit(font.render(text, True, BLACK), (rect.x + 10, rect.y + 40 + i * 25))
    elif title == "Leaderboard":
        for i, item in enumerate(items):
            if isinstance(item, dict):
                text = f"{item.get('player', 'Unknown')} - Net Worth: ${item.get('net_worth', 'Unknown'):.2f}"
            else:
                text = str(item)
            surface.blit(font.render(text, True, BLACK), (rect.x + 10, rect.y + 40 + i * 25))
    else:
        if is_dict:
            lines = []
            def fmt_money(key, value):
                return f"{key.replace('_', ' ').capitalize()}: ${float(value):,.2f}"

            for key in ["cash", "saving", "net_worth", "current_position", "round_played", "stocks", "estates"]:
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



def draw_top_bar(surface, room, player, round):
    pygame.draw.rect(surface, BLUE, top_bar)
    pygame.draw.rect(surface, BLACK, top_bar, 2)
    label = font_title.render(f"Room: {room} | Player: {player} | Round: {round}", True, WHITE)
    surface.blit(label, (top_bar.x + 20, top_bar.y + 10))

def draw_action_buttons(surface):
    pygame.draw.rect(surface, GRAY, action_bar)
    pygame.draw.rect(surface, BLACK, action_bar, 2)
    buttons = ["Roll Dice", "Buy", "Sell", "End Turn"]
    button_image_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../shared/ui/button_1.png'))
    button_image = pygame.image.load(button_image_path)

    # Scale the button image proportionally to fit the button area
    image_width, image_height = button_image.get_size()
    scale_factor = min(150 / image_width, 40 / image_height)
    scaled_width = int(image_width * scale_factor)
    scaled_height = int(image_height * scale_factor)
    button_image = pygame.transform.scale(button_image, (scaled_width, scaled_height))

    for i, label in enumerate(buttons):
        rect = pygame.Rect(50 + i * 200, action_bar.y + 15, 150, 40)
        # Center the button image within the rect
        image_x = rect.x + (rect.width - scaled_width) // 2
        image_y = rect.y + (rect.height - scaled_height) // 2
        surface.blit(button_image, (image_x, image_y))
        # Center the text within the rect
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

def run_ui(room_id, player_name, joined_players, _, leaderboard=None, portfolio=None):
    global current_player
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
            elif e.type == pygame.MOUSEBUTTONDOWN:
                if is_host_runtime and start_btn and start_btn.collidepoint(e.pos):
                    try:
                        print("Host clicked the START button.")  # Debug log
                        response = requests.post(f"http://localhost:8000/start", json={"room_id": room_id})
                        if response.status_code == 200:
                            print("Game started successfully.")
                            start_btn = None  # Remove the START button after the game starts
                        else:
                            print(f"[Error] Backend response: {response.text}")
                    except Exception as err:
                        print(f"[Error] Failed to start game: {err}")

        # Define current_players before using it
        current_players = ws_joined_players if ws_joined_players else joined_players

        # Debug log for player_name and current_players
        # print(f"Player name: {player_name}")
        # print(f"Current players: {current_players}")

        # Update host determination logic
        if current_players and isinstance(current_players[0], dict):
            is_host_runtime = (player_name == current_players[0].get('player_name'))
        else:
            is_host_runtime = (player_name == current_players[0]) if current_players else False

        # print(f"Is host runtime: {is_host_runtime}")

        # Vẽ UI
        draw_top_bar(screen, room_id, player_name, current_round)
        draw_map_with_players(screen, ws_joined_players or joined_players)
        draw_box(event_box, "Notification", screen, ws_notifications)  # Display notifications
        draw_box(leaderboard_box, "Leaderboard", screen, ws_leaderboard or leaderboard)
        draw_box(portfolio_box, "Player Property", screen, ws_portfolio or portfolio, is_dict=True)
        draw_action_buttons(screen)

        # Nút start chỉ nếu là host
        if is_host_runtime and start_btn:
            # print("Displaying START button for host.")  # Debug log
            pygame.draw.rect(screen, GREEN, start_btn)
            pygame.draw.rect(screen, BLACK, start_btn, 2)
            text = font.render("START", True, WHITE)
            screen.blit(text, text.get_rect(center=start_btn.center))

        # Display "Roll Dice" button if it's the current player's turn
        if player_name == current_player:
            roll_button = pygame.Rect(50, action_bar.y + 15, 150, 40)
            pygame.draw.rect(screen, GREEN, roll_button)
            pygame.draw.rect(screen, BLACK, roll_button, 2)
            text = font.render("Roll Dice", True, WHITE)
            screen.blit(text, text.get_rect(center=roll_button.center))

            # Handle click event for "Roll Dice" button
            for e in events:
                if e.type == pygame.MOUSEBUTTONDOWN and roll_button.collidepoint(e.pos):
                    try:
                        response = requests.post("http://localhost:8000/roll", json={"room_id": room_id, "player_name": player_name})
                        if response.status_code != 200:
                            print("Error rolling dice:", response.json())
                    except Exception as err:
                        print(f"Error sending roll request: {err}")

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
    sys.exit()
