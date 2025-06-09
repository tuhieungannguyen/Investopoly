import threading
import pygame
import sys
import websockets
import asyncio
import json
import requests
import os
import sys
import textwrap
import aiohttp
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



# --- Config ---
# SERVER_HOST = os.getenv('SERVER_HOST', 'duong.dat-jang.id.vn')
SERVER_HOST = os.getenv('SERVER_HOST', 'localhost')
SERVER_PORT = os.getenv('SERVER_PORT', '8000')
SERVER = f"http://{SERVER_HOST}:{SERVER_PORT}"
WS_URL_BASE = f"ws://{SERVER_HOST}:{SERVER_PORT}/ws"


# Vị trí layout
top_bar = pygame.Rect(20, 20, 1160, 50)
# top_bar = pygame.Rect(x, y , chieu ngang, chieu doc)
map_area = pygame.Rect(20, 80, 850, 600)
event_box = pygame.Rect(630, 80, 300, 250)
leaderboard_box = pygame.Rect(630, 350, 550, 330)
portfolio_box = pygame.Rect(950, 80, 230, 250)
action_bar = pygame.Rect(20, 700, 1160, 70)



# ws variable
ws_joined_players = []
ws_leaderboard = []
ws_portfolio = {}



# Define global variable for current round
current_round = None
current_player = None

quiz_popup = None  # Global quiz popup state
# Define global variable for scroll offset
scroll_offset = 0




# ====================================
# ADD NOTIFICATION                  ||
# ====================================
def add_notification(notification):
    global ws_notifications
    # Ensure the latest notification is always added and displayed
    if len(ws_notifications) >= 5:
        ws_notifications.pop(0)  # Remove the oldest notification
    ws_notifications.append(notification)  # Add the new notification


# ===================================
#  DETERMINE HOST                  ||
# ===================================
def determine_host(player_name, joined_players):
    if joined_players and isinstance(joined_players[0], dict):
        return player_name == joined_players[0].get('player_name')
    return player_name == joined_players[0] if joined_players else False


# ===================================
#  LISTEN WS                        ||  
# ===================================
async def listen_ws(room_id, player_name):
    global ws_joined_players, ws_leaderboard, ws_portfolio, ws_notifications, current_player, current_round
    ws_notifications = []  # Initialize notifications list
    uri = f"ws://{SERVER_HOST}:8000/ws/{room_id}/{player_name}"
    async with websockets.connect(uri) as ws:
        while True:
            try:
                data = await ws.recv()
                message = json.loads(data)

                if message["type"] == "game_started":
                    raw_notification = f"{message['message']}\nCurrent Player: {message['current_player']}"
                    notification = "\n".join(textwrap.wrap(raw_notification, width=50))  # Wrap text to 50 characters per line
                    add_notification(notification)
                    current_player = message["current_player"]
                    current_round = message["round"]

                elif message["type"] == "next_turn":
                    current_round = message["round"]
                    current_player = message["current_player"]
                    raw_notification = f"{message['message']}"
                    notification = "\n".join(textwrap.wrap(raw_notification, width=50))
                    add_notification(notification)

                elif message["type"] == "player_rolled":
                    notification = f"Notification: {message['message']}"
                    add_notification(notification)
                    for player in ws_joined_players:
                        if player["player_name"] == message["player"]:
                            player["current_position"] = message["tile"]["name"]

                    # Enable purchase buttons if applicable
                    if message.get("can_buy_estate"):
                        enable_purchase_button("estate")
                    if message.get("can_buy_stock"):
                        enable_purchase_button("stock")

                elif message["type"] == "player_joined":
                    raw_notification = f"{message['player']} joined the room."
                    notification = "\n".join(textwrap.wrap(raw_notification, width=30))
                    add_notification(notification)
                    ws_joined_players = message["players"]
                    # Validate leaderboard data before updating
                    if "leaderboard" in message and message["leaderboard"]:
                        print("Received leaderboard data:", message["leaderboard"])  # Debug log
                        ws_leaderboard = message["leaderboard"]

                elif message["type"] == "update_positions":
                    # Update player positions on the map
                    players = message["players"]
                    for player in players:
                        for p in ws_joined_players:
                            if p["player_name"] == player["player_name"]:
                                p["current_position"] = player["current_position"]
                                break
                            
                elif message["type"] == "quiz_start":
                    raw_notification = f"{message['message']}"
                    notification = "\n".join(textwrap.wrap(raw_notification, width=30))
                    add_notification(notification)

                elif message["type"] == "quiz_question":
                    global quiz_popup
                    quiz_popup = {
                        "question_id": message["question_id"],
                        "question": message["question"],
                        "options": message["options"]
                    }

                elif message["type"] == "error":
                    # Handle error messages from the server
                    raw_notification = f"Error: {message['message']}"
                    notification = "\n".join(textwrap.wrap(raw_notification, width=30))
                    add_notification(notification)

                elif message["type"] == "leaderboard_update":
                    # Update the leaderboard data
                    ws_leaderboard = message["leaderboard"]
                    print("Leaderboard updated:", ws_leaderboard)  # Debug log
                    
                elif message["type"] == "chance_event":
                    event_name = message.get("event", {}).get("name", "Unknown")
                    raw_notification = f"{message['player']} triggered Chance Event: {event_name}"
                    add_notification(raw_notification)
                    
                elif message["type"] == "estate_purchased":
                    # Thông báo chung cho toàn phòng
                    notification = "\n".join(textwrap.wrap(message["message"], width=38))
                    add_notification(notification)

                    # Cập nhật bảng xếp hạng
                    if "leaderboard" in message:
                        ws_leaderboard = message["leaderboard"]

                    # Nếu có cập nhật danh mục người chơi (optional)
                    if message.get("player") == player_name:
                        print(f"You purchased {message.get('tile')} for ${message.get('price')}")
                        
                elif message["type"] == "stock_purchased":
                    # Thông báo chung cho toàn phòng
                    notification = "\n".join(textwrap.wrap(message["message"], width=38))
                    add_notification(notification)

                        
                elif message["type"] == "portfolio_update":
                    if message.get("portfolio"):
                        ws_portfolio = message["portfolio"]
                        print("📦 Portfolio updated:", ws_portfolio)
                        
                elif message["type"] == "passed_go":
                    raw_notification = f"{message['player']} passed GO and received ${message['amount']}"
                    add_notification(raw_notification)
                    
                elif message["type"] == "quiz_result":
                    raw_notification = message['message']
                    add_notification(raw_notification)
                    
                    
                elif message["type"] == "tile_penalty":
                    raw_notification = message["message"]
                    print("💸 Transaction received:", raw_notification)
                    add_notification(raw_notification)
                    
                elif message["type"] == "estate_rent_paid":
                    raw_notification = message["message"]
                    add_notification(raw_notification)

                    # Cập nhật leaderboard nếu có
                    if "leaderboard" in message:
                        ws_leaderboard = message["leaderboard"]

                    # Nếu player là người chơi hiện tại, cập nhật portfolio của họ
                    if message.get("payer") == player_name:
                        ws_portfolio = message.get("payer_portfolio", {})
                    elif message.get("owner") == player_name:
                        ws_portfolio = message.get("owner_portfolio", {})

                    print("💸 Rent Transaction received:", raw_notification)
                            

                # Update host determination logic
                is_host_runtime = determine_host(player_name, ws_joined_players)

            except websockets.ConnectionClosed as e:
                print(f"WebSocket connection closed: {e}")
                break
            except json.JSONDecodeError as e:
                print(f"Error decoding WebSocket message: {e}")
            except Exception as e:
                print(f"Unexpected WebSocket error: {e}")


# Helper function to enable purchase buttons
def enable_purchase_button(item_type):
    if item_type == "estate":
        print("Enable estate purchase button")  # Replace with actual UI logic
    elif item_type == "stock":
        print("Enable stock purchase button")  # Replace with actual UI logic


# ===================================
#  DRAW BOX                        ||
# ===================================
def draw_box(rect, title, surface, items=None, is_dict=False):
    global scroll_offset
    pygame.draw.rect(surface, LIGHT_GRAY, rect)
    pygame.draw.rect(surface, BLACK, rect, 2)
    surface.blit(font_title.render(title, True, BLACK), (rect.x + 10, rect.y + 10))

    if not items:
        return

    # Always display the latest notifications
    max_items = (rect.height - 40) // 25
    start_index = max(0, len(items) - max_items)
    end_index = len(items)

    if title == "Notification":
        y_offset = rect.y + 40
        max_width = rect.width - 20 
        for i, item in enumerate(items[start_index:end_index]):
            # Split the item into multiple lines if it contains '\n'
            wrapped_lines = textwrap.wrap(item, width=38)  # Wrap here instead of earlier
            for line in wrapped_lines:
                surface.blit(font.render(line, True, BLACK), (rect.x + 10, y_offset))
                y_offset += 20
    elif title == "Leaderboard":
        for i, item in enumerate(items[start_index:end_index]):
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
            for i, item in enumerate(items[start_index:end_index]):
                if isinstance(item, dict):
                    text = f"{item.get('player_name', 'Unknown')} - Position: {item.get('current_position', 'Unknown')}"
                else:
                    text = str(item)
                surface.blit(font.render(text, True, BLACK), (rect.x + 10, rect.y + 40 + i * 25))


# ===================================
#  DRAW QUIZ POPUP                 ||
# ===================================
def draw_quiz_popup(surface, quiz_data, room_id, player_name):
    popup_rect = pygame.Rect(300, 200, 600, 300)
    pygame.draw.rect(surface, WHITE, popup_rect)
    pygame.draw.rect(surface, BLACK, popup_rect, 3)

    question = quiz_data["question"]
    options = quiz_data["options"]
    question_id = quiz_data["question_id"]

    wrapped_question = textwrap.wrap(question, width=60)
    for i, line in enumerate(wrapped_question):
        text = font.render(line, True, BLACK)
        surface.blit(text, (popup_rect.x + 20, popup_rect.y + 20 + i * 25))

    button_rects = []
    for i, opt in enumerate(options):
        btn_rect = pygame.Rect(popup_rect.x + 50, popup_rect.y + 100 + i * 40, 500, 35)
        pygame.draw.rect(surface, LIGHT_GRAY, btn_rect)
        pygame.draw.rect(surface, BLACK, btn_rect, 2)
        text = font.render(opt, True, BLACK)
        surface.blit(text, (btn_rect.x + 10, btn_rect.y + 5))
        button_rects.append((btn_rect, i))

    # Handle button click
    for event in pygame.event.get(pygame.MOUSEBUTTONDOWN):
        mouse_pos = pygame.mouse.get_pos()
        for rect, idx in button_rects:
            if rect.collidepoint(mouse_pos):
                # Call coroutine in separate thread-safe context
                def submit_answer():
                    asyncio.run(send_quiz_answer(room_id, player_name, question_id, idx))
                threading.Thread(target=submit_answer).start()

                global quiz_popup
                
                quiz_popup = None
                
# ===================================
#  DRAW TOP BAR                    ||
# ===================================
def draw_top_bar(surface, room, player, round):
    pygame.draw.rect(surface, BLUE, top_bar)
    pygame.draw.rect(surface, BLACK, top_bar, 2)
    label = font_title.render(f"Room: {room} | Player: {player} | Round: {round}", True, WHITE)
    surface.blit(label, (top_bar.x + 20, top_bar.y + 10))


# ==================================
# SEND BUY REQUEST                 ||
# ==================================
async def send_buy_request(room_id, player_name):
    url = f"http://{SERVER_HOST}:8000/buy_estate"
    payload = {
        "room_id": room_id,
        "player_name": player_name,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                print(data["message"])
            else:
                print(f"Failed to buy estate: {response.status}")

# =====================================
# SEND SELL REQUEST                  ||
# =====================================
async def send_sell_request(room_id, player_name):
    # Example logic to send a sell request to the server
    async with websockets.connect(f"ws://{SERVER_HOST}:8000/ws/{room_id}/{player_name}") as ws:
        await ws.send(json.dumps({"action": "sell", "player_name": player_name}))


# =====================================
#  END TURN REQUEST                  ||
# =====================================
async def send_end_turn_request(room_id, player_name):
    url = f"http://{SERVER_HOST}:8000/end_turn"
    payload = {
        "room_id": room_id,
        "player_name": player_name
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                print(data["message"])
                # Update the current player and round based on server response
                global current_player, current_round
                current_player = data.get("current_player", current_player)
                current_round = data.get("round", current_round)
            else:
                print(f"Failed to end turn: {response.status}")

# =====================================
#  SEND ANSWER REQUEST               ||
# =====================================

async def send_quiz_answer(room_id, player_name, question_id, answer_index):
    url = f"http://{SERVER_HOST}:8000/quiz/answer"
    payload = {
        "room_id": room_id,
        "player_name": player_name,
        "question_id": question_id,
        "answer_index": answer_index
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                print(data.get("message", "Quiz answer submitted."))
            else:
                print(f"❌ Failed to submit quiz answer: {response.status}")

# =====================================
#  SHOW BUY POP UP                   ||
# =====================================
def show_buy_popup(room_id, player_name):
    import tkinter as tk

    def on_buy_estate():
        root.destroy()
        asyncio.run(send_buy_request(room_id, player_name))

    def on_buy_stock():
        root.destroy()
        show_stock_purchase_popup(room_id, player_name)

    root = tk.Tk()
    root.title("Buy Options")
    window_width, window_height = 300, 150

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = int((screen_width / 2) - (window_width / 2))
    y = int((screen_height / 2) - (window_height / 2))
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")

    tk.Label(root, text="Choose what to buy:").pack(pady=10)
    tk.Button(root, text="Buy Estate", command=on_buy_estate, width=20).pack(pady=5)
    tk.Button(root, text="Buy Stock", command=on_buy_stock, width=20).pack(pady=5)

    root.mainloop()
 
# ===================================
#  SHOW STOCK POPUP                ||
# ===================================             
                    
def show_stock_purchase_popup(room_id, player_name):
    import tkinter as tk
    from tkinter import simpledialog

#    Cập nhật lại geometry với vị trí
    def submit_stock_purchase():
        quantity = quantity_entry.get()
        root.destroy()
        try:
            asyncio.run(send_stock_purchase(room_id, player_name, int(quantity)))
        except Exception as e:
            print(f"❌ Stock buy error: {e}")

    root = tk.Tk()
    root.title("Buy Stock")
    window_width, window_height = 300, 150

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = int((screen_width / 2) - (window_width / 2))
    y = int((screen_height / 2) - (window_height / 2))
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")


    tk.Label(root, text="Quantity:").pack()
    quantity_entry = tk.Entry(root)
    quantity_entry.pack()

    tk.Button(root, text="Buy", command=submit_stock_purchase).pack()
    root.mainloop()                    
                  
# ===================================
#  CALL BUY STOCK API              ||
# ===================================                   
async def send_stock_purchase(room_id, player_name, quantity):
    url = f"http://{SERVER_HOST}:8000/buy_stock"
    payload = {
        "room_id": room_id,
        "player_name": player_name,
        "amount": quantity
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            if response.status == 200:
                print("✅ Stock purchased")
            else:
                print(f"❌ Failed to buy stock: {response.status}")     
                               
# ===================================
#  HANDLE BUTTON                   ||
# ===================================
def handle_button_click(button_label, room_id, player_name):
    if button_label == "Buy":
        # Logic to handle Buy action
        print("Buy button clicked")
        # asyncio.run(send_buy_request(room_id, player_name))
        show_buy_popup(room_id, player_name)
    elif button_label == "Sell":
        # Logic to handle Sell action
        print("Sell button clicked")
        asyncio.run(send_sell_request(room_id, player_name))
    elif button_label == "End Turn":
        # Logic to handle End Turn action
        print("End Turn button clicked")
        asyncio.run(send_end_turn_request(room_id, player_name))


# ==================================
# DRAW ACTION BUTTON
# ==================================
def draw_action_buttons(surface, room_id, player_name):
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

        # Check for button click
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = pygame.mouse.get_pressed()
        if rect.collidepoint(mouse_pos) and mouse_click[0]:
            handle_button_click(label, room_id, player_name)


# =========================================
#  DRAW MAP WITH PLAYERS
# =========================================
def draw_map_with_players(surface, players):
    # Load the board image as the map
    board_image_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../shared/ui/board_new.png'))
    board_image = pygame.image.load(board_image_path)
    board_image = pygame.transform.scale(board_image, (600, 600))
    surface.blit(board_image, (map_area.x, map_area.y))

    # Load avatars using absolute path
    shared_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../shared/avt'))
    avatars = [
        pygame.image.load(os.path.join(shared_path, f"{i}.png")) for i in range(1, len(players) + 1)
    ]

    # Define tile dimensions based on the scaled board
    corner_tile_size = (129, 129)  # Corner tiles
    vertical_tile_size = (129, 86)  # Vertical tiles
    horizontal_tile_size = (86, 129)  # Horizontal tiles

    for idx, player in enumerate(players):
        if isinstance(player, dict) and "current_position" in player:
            position = int(player["current_position"])

            if position == 0:  # GO
                x, y = map_area.x, map_area.y + 600 - corner_tile_size[1]
            elif position < 5:  # Left column (going up)
                x, y = map_area.x, map_area.y + 600 - (position * vertical_tile_size[1]) - corner_tile_size[1]
            elif position == 5:  # Jail Visit
                x, y = map_area.x, map_area.y
            elif position < 10:  # Top row (going right)
                x, y = map_area.x + ((position - 6) * horizontal_tile_size[0]) + corner_tile_size[0], map_area.y
            elif position == 10:  # Quizzes (Education)
                x, y = map_area.x + 600 - corner_tile_size[0], map_area.y
            elif position < 15:  # Right column (going down)
                x, y = map_area.x + 600 - vertical_tile_size[0], map_area.y + ((position - 11) * vertical_tile_size[1]) + corner_tile_size[1]
            elif position == 15:  # Jail (Challenge)
                x, y = map_area.x + 600 - corner_tile_size[0], map_area.y + 600 - corner_tile_size[1]
            else:  # Bottom row (going left)
                x, y = map_area.x + 600 - ((position - 15) * horizontal_tile_size[0]) - corner_tile_size[0], map_area.y + 600 - horizontal_tile_size[1]

            
            avatar = pygame.transform.scale(avatars[idx], (corner_tile_size[0] // 3, corner_tile_size[1] // 3))
            surface.blit(avatar, (x + corner_tile_size[0] // 4, y + corner_tile_size[1] // 4))


# =========================================
#  RUN UI
# =========================================
def run_ui(room_id, player_name, joined_players, _, leaderboard=None, portfolio=None):
    global current_player
    if not pygame.get_init():
        pygame.init()
    if not pygame.display.get_init():
        pygame.display.init()

    # Adjust the window size to match the board dimensions
    screen = pygame.display.set_mode((1200, 800))
    pygame.display.set_caption("Investopoly - Main Game UI")

    threading.Thread(target=lambda: asyncio.run(listen_ws(room_id, player_name)), daemon=True).start()
    running = True
    start_btn = pygame.Rect(850, 720, 120, 50)  # Adjusted position for the start button

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
                        response = requests.post(f"http://{SERVER_HOST}:8000/start", json={"room_id": room_id})
                        if response.status_code == 200:
                            print("Game started successfully.")
                            start_btn = None  # Remove the START button after the game starts
                        else:
                            print(f"[Error] Backend response: {response.text}")
                    except Exception as err:
                        print(f"[Error] Failed to start game: {err}")

            elif e.type == pygame.MOUSEBUTTONDOWN:
                if e.button == 4:  # Scroll up
                    scroll_offset = max(0, scroll_offset - 1)
                elif e.button == 5:  # Scroll down
                    max_items = (event_box.height - 40) // 25
                    scroll_offset = min(len(ws_notifications) - max_items, scroll_offset + 1)

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
        draw_box(portfolio_box, "Portfolio", screen, ws_portfolio or portfolio, is_dict=True)
        draw_action_buttons(screen, room_id, player_name)

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
                        response = requests.post(f"http://{SERVER_HOST}:8000/roll", json={"room_id": room_id, "player_name": player_name})
                        if response.status_code != 200:
                            print("Error rolling dice:", response.json())
                    except Exception as err:
                        print(f"Error sending roll request: {err}")

        if quiz_popup:
            draw_quiz_popup(screen, quiz_popup, room_id, player_name)
            
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
    sys.exit()
