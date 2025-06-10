import sys
import pygame
import requests
import threading
import asyncio
import websockets
import json
import investopoly_main_ui
import os  # <-- Import os module

# --- Config ---
SERVER_HOST = os.getenv('SERVER_HOST', 'duong.dat-jang.id.vn')
# SERVER_HOST = os.getenv('SERVER_HOST', 'localhost')
SERVER_PORT = os.getenv('SERVER_PORT', '8000')
SERVER = f"http://{SERVER_HOST}:{SERVER_PORT}"
WS_URL_BASE = f"ws://{SERVER_HOST}:{SERVER_PORT}/ws"

# --- Colors ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
BLUE = (0, 100, 255)
GREEN = (0, 150, 0)
RED = (200, 0, 0)
LIGHT_GRAY = (230, 230, 230)

# --- Flags and State ---
should_switch_to_ui = False
is_host = False
room_id = ''
player_name = ''
active_input = None
status = ''
joined_players = []
leaderboard = []
portfolio = {}
messages = []

# --- Init Pygame ---
pygame.init()
font_title = pygame.font.SysFont(None, 32, bold=True)
font = pygame.font.SysFont(None, 28)
big_font = pygame.font.SysFont(None, 44)
screen = pygame.display.set_mode((600, 300))
pygame.display.set_caption("Investopoly")

# --- Input Boxes ---
input_box_room = pygame.Rect(220, 120, 240, 36)
input_box_name = pygame.Rect(220, 180, 240, 36)
btn_create = pygame.Rect(270, 250, 150, 40)

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):  # Khi chạy từ PyInstaller .exe
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)
# --- Draw Lobby UI ---
def draw_lobby():
    screen.fill(WHITE)
    # Replace title text with an image
    margin = 20
    title_image = pygame.image.load(resource_path("shared/ui/INVESTOPOLY.png")).convert_alpha()

    # Tính chiều rộng mới có trừ margin 2 bên
    scaled_width = screen.get_width() - 2 * margin
    scaled_height = screen.get_height() // 4

    title_image = pygame.transform.scale(title_image, (scaled_width, scaled_height))

    # Vẽ hình với margin 2 bên
    screen.blit(title_image, (margin, 20))

    screen.blit(font.render("Room ID:", True, BLACK), (100, 130))
    screen.blit(font.render("Your Name:", True, BLACK), (100, 190))
    pygame.draw.rect(screen, GRAY, input_box_room)
    pygame.draw.rect(screen, GRAY, input_box_name)
    screen.blit(font.render(room_id, True, BLACK), (input_box_room.x + 5, input_box_room.y + 5))
    screen.blit(font.render(player_name, True, BLACK), (input_box_name.x + 5, input_box_name.y + 5))

    pygame.draw.rect(screen, BLUE, btn_create)
    screen.blit(font.render("Create or Join", True, WHITE), (btn_create.x + 10, btn_create.y + 10))
    screen.blit(font.render(status, True, RED if "lỗi" in status.lower() else GREEN), (50, 340))

    pygame.display.flip()

# --- WebSocket Listener ---
async def connect_and_listen(room_id, player_name):
    global should_switch_to_ui, is_host, leaderboard, portfolio, joined_players

    uri = f"{WS_URL_BASE}/{room_id}/{player_name}"
    async with websockets.connect(uri) as ws:
        try:
            requests.post(f"{SERVER}/join", json={"room_id": room_id, "player_name": player_name})
        except Exception as e:
            print("❗ Failed to join room:", e)

        ui_launched = False  
        
        while True:
            raw = await ws.recv()
            try:
                data = json.loads(raw)
                t = data.get("type")

                if t == "player_joined":
                    joined_players = data["players"]
                    messages.append(f">>> {data['player']} đã tham gia.")
                    leaderboard = [(p["player"], p["net_worth"]) for p in data.get("leaderboard", [])]
                    portfolio = data.get("portfolio", {})
                    
                    if data['player'] == player_name:
                        is_host = (player_name == joined_players[0])
                        print("✅ Received player data.")
                        should_switch_to_ui = True  # Trigger screen switch
                        ui_launched = True
            except Exception as e:
                messages.append(f"[Lỗi nhận WS]: {e}")

# --- Start WS Thread ---
def start_ws_thread():
    threading.Thread(target=lambda: asyncio.run(connect_and_listen(room_id, player_name)), daemon=True).start()

# --- Main Loop ---
def main():
    global room_id, player_name, active_input, status, should_switch_to_ui

    clock = pygame.time.Clock()
    running = True

    while running:
        draw_lobby()

        if should_switch_to_ui:
            print("🔄 Switching to main UI...")
            pygame.display.quit()
            pygame.display.init()
            pygame.font.init()
            investopoly_main_ui.run_ui(room_id, player_name, joined_players, is_host, leaderboard, portfolio)
            running = False
            break

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if input_box_room.collidepoint(event.pos):
                    active_input = "room"
                elif input_box_name.collidepoint(event.pos):
                    active_input = "name"
                elif btn_create.collidepoint(event.pos):
                    if room_id and player_name:
                        try:
                            r = requests.post(f"{SERVER}/create", json={"room_id": room_id, "host_name": player_name})
                            if r.status_code == 200:
                                status = f"Room {room_id} create"
                                print(f"✅ Room {room_id} created successfully.")
                            elif "exists" in r.text or r.status_code == 400:
                                status = f"Room {room_id} existed. Joining..."
                                print(f"⚠️ Room {room_id} already exists. Joining...")
                            else:
                                status = "❗ Lỗi tạo phòng"
                                print(f"❗ Error creating room {room_id}: {r.text}")
                            start_ws_thread()
                        except Exception as e:
                            status = f"❗ Lỗi kết nối: {e}"
                            print(f"❗ Connection error: {e}")

            elif event.type == pygame.KEYDOWN:
                if active_input == "room":
                    if event.key == pygame.K_BACKSPACE:
                        room_id = room_id[:-1]
                    else:
                        room_id += event.unicode
                elif active_input == "name":
                    if event.key == pygame.K_BACKSPACE:
                        player_name = player_name[:-1]
                    else:
                        player_name += event.unicode

        clock.tick(30)

    pygame.quit()

# --- Run ---
if __name__ == "__main__":
    main()
