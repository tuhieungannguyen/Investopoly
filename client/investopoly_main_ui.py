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
font_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../shared/CutePixel.ttf'))
font = pygame.font.Font(font_path, 20)
font_title = pygame.font.Font(font_path, 26)

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
event_box = pygame.Rect(168, 230, 402, 400)
leaderboard_box = pygame.Rect(740, 80, 450, 235)
portfolio_box = pygame.Rect(740, 335, 450, 285)
action_bar = pygame.Rect(740, 620, 450, 150)


# ws variable
ws_joined_players = []
ws_leaderboard = []
ws_portfolio = {}



# Define global variable for current round
current_round = None
current_player = None
shock_popup = None  # Global shock popup
quiz_popup = None  # Global quiz popup state
# Define global variable for scroll offset
scroll_offset = 0
saving_popup = None
saving_input_text = ""
stock_prices = {}  #
estate_prices = {}  


########################################################################
## IMAGE
########################################################################
topbar_image_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../shared/ui/bar.png'))
topbar_image = pygame.image.load(topbar_image_path).convert_alpha()
topbar_image = pygame.transform.scale(topbar_image, (1160, 50)) 

profile_image_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../shared/ui/profile.png'))
profile_image = pygame.image.load(profile_image_path).convert_alpha()
profile_image = pygame.transform.scale(profile_image, (portfolio_box.width, portfolio_box.height))


notification_image_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../shared/ui/noti_1.png'))
noti_image = pygame.image.load(notification_image_path).convert_alpha()
noti_image = pygame.transform.scale(noti_image, (event_box.width, event_box.height))
# ====================================
# ADD NOTIFICATION                  ||
# ====================================
def add_notification(notification):
    global ws_notifications
    # Ensure the latest notification is always added and displayed
    if len(ws_notifications) >= 15:
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
                    
                elif message["type"] == "dividend_distributed":
                    # Thông báo chung cho toàn phòng
                    notification = "\n".join(textwrap.wrap(message["message"], width=38))
                    add_notification(notification)
                    print("Dividend distributed:", message["message"])
                    
                elif message["type"] == "stock_service_fee":
                    # Thông báo chung cho toàn phòng
                    notification = "\n".join(textwrap.wrap(message["message"], width=38))
                    add_notification(notification)

                elif message["type"] == "shock_event":
                    global shock_popup
                    shock_popup = {
                        "title": "⚡ Shock Event",
                        "message": message["message"],
                        "stocks": message.get("stocks", []),
                        "estate_effect": message.get("estate_effect", {})
                    }     
              
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
        
                elif message["type"] == "saving_prompt":
                    max_amount = message["max_amount"]
                    saving_popup, saving_input_text
                    saving_popup = {
                        "message": message["message"],
                        "max_amount": max_amount,
                        "room_id": message["room_id"],
                        "player_name": message["player_name"]
                    }
                    saving_input_text = ""
                    
                elif message["type"] == "saving_matured":
                    print("💰 Your saving is matured and can be withdrawn.")
                    saving_popup
                    saving_popup = {
                        "message": "Your saving is matured. Withdraw now?",
                        "max_amount": 0,  # unused
                        "room_id": room_id,
                        "player_name": player_name,
                        "withdraw": True
                    }
                
                elif message["type"] == "stock_for_sale":
                    msg = f"{message['seller']} is selling {message['quantity']} shares of {message['stock']} at ${message['price_per_unit']} each"
                    add_notification(msg)
                    if message["seller"] != player_name:
                        threading.Thread(target=show_buy_stock_from_player_popup, args=(
                            room_id, player_name, message["stock"], message["seller"], message["quantity"], message["price_per_unit"])).start()

                elif message["type"] == "estate_sold":
                    msg = f"{message['seller']} sold {message['estate']} to {message['buyer']} for ${message['price']}"
                    add_notification(msg)

                elif message["type"] == "stock_sold":
                    msg = f"{message['seller']} sold {message['quantity']} {message['stock']} to {message['buyer']} at ${message['price_per_unit']} each"
                    add_notification(msg)      
                    
                elif message["type"] == "estate_for_sale":
                    msg = f"{message['seller']} is selling {message['estate']} for ${message['price']}"
                    add_notification(msg)

                    if message["seller"] != player_name:
                        threading.Thread(target=show_estate_offer_popup, args=(
                            room_id, player_name, message["estate"],
                            message["seller"], message["price"])).start()
                elif message["type"] == "estate_offers_list" and message["seller"] == player_name:
                    offers = message["offers"]  # List of {"buyer": ..., "price": ...}
                    threading.Thread(target=show_select_offer_popup, args=(
                        message["room_id"], player_name, message["estate"], offers)).start()
                elif message["type"] == "estate_offer_received" and message.get("estate"):
                    offers = message["offers"]
                    threading.Thread(target=show_select_offer_popup, args=(
                        room_id, player_name, message["estate"], offers)).start()
                
                elif message["type"] == "stock_for_sale":
                    msg = f"{message['seller']} is selling {message['quantity']} shares of {message['stock']} at ${message['price_per_unit']} each"
                    add_notification(msg)
                    if message["seller"] != player_name:
                        threading.Thread(target=show_buy_stock_from_player_popup, args=(
                            room_id, player_name, message["stock"], message["seller"], message["quantity"], message["price_per_unit"])).start()
                                                    
                # Update host determination logic
                is_host_runtime = determine_host(player_name, ws_joined_players)

            except websockets.ConnectionClosed as e:
                print(f"WebSocket connection closed: {e}")
                break
            except json.JSONDecodeError as e:
                print(f"Error decoding WebSocket message: {e}")
            except Exception as e:
                print(f"Unexpected WebSocket error: {e}")

def show_buy_stock_from_player_popup(room_id, player_name, stock_name, seller, max_quantity, price_per_unit):
    import tkinter as tk
    def on_submit():
        try:
            qty = int(quantity_entry.get())
            if qty < 1 or qty > max_quantity:
                print("Quantity out of range.")
                return
            root.destroy()
            payload = {
                "room_id": room_id,
                "buyer": player_name,
                "seller": seller,
                "stock": stock_name,
                "quantity": qty,
                "price_per_unit": float(price_per_unit)
            }
            url = f"http://{SERVER_HOST}:8000/api/stock/buy_from_player"
            response = requests.post(url, json=payload)
            print(response.json().get("message", "Buy stock response"))
        except Exception as e:
            print(f"❌ Error buying stock: {e}")

    root = tk.Tk()
    root.title("Buy Stock From Player")
    root.geometry("300x180")
    tk.Label(root, text=f"Buy {stock_name} from {seller}").pack()
    tk.Label(root, text=f"Price per unit: ${price_per_unit}").pack()
    tk.Label(root, text=f"Max quantity: {max_quantity}").pack()
    tk.Label(root, text="Quantity:").pack()
    quantity_entry = tk.Entry(root)
    quantity_entry.pack()
    tk.Button(root, text="Buy", command=on_submit).pack(pady=10)
    root.mainloop()


# Helper function to enable purchase buttons
def enable_purchase_button(item_type):
    if item_type == "estate":
        print("Enable estate purchase button")  # Replace with actual UI logic
    elif item_type == "stock":
        print("Enable stock purchase button")  # Replace with actual UI logic

def show_offer_popup(self, seller, estate_name, min_price):
    def submit_offer():
        try:
            offer = float(entry.get())
            if offer >= min_price:
                self.send_json({
                    "action": "notify",
                    "target": "server",
                    "type": "estate_offer",
                    "buyer": self.player_name,
                    "estate": estate_name,
                    "price": offer,
                    "room_id": self.room_id
                })
                top.destroy()
            else:
                messagebox.showerror("Lỗi", f"Giá phải >= {min_price}")
        except:
            messagebox.showerror("Lỗi", "Nhập số hợp lệ")

    top = tk.Toplevel(self.root)
    top.title("Gửi đề nghị mua")
    tk.Label(top, text=f"Mua {estate_name} từ {seller}, giá gốc ${min_price}").pack()
    entry = tk.Entry(top)
    entry.pack()
    tk.Button(top, text="Gửi đề nghị", command=submit_offer).pack()

# ===================================
#  DRAW BOX                        ||
# ===================================
def draw_box(rect, title, surface, items=None, is_dict=False):
    global scroll_offset
    # pygame.draw.rect(surface, LIGHT_GRAY, rect)
    # pygame.draw.rect(surface, BLACK, rect, 2)
    surface.blit(font_title.render(title, True, BLACK), (rect.x + 10, rect.y + 10))
    
    if title == "Portfolio":
        # Vẽ nền là hình ảnh thay vì khung mặc định
        surface.blit(profile_image, (rect.x, rect.y))
    elif title == "Notification":
        surface.blit(noti_image, (rect.x, rect.y))
    else:
        pygame.draw.rect(surface, LIGHT_GRAY, rect)
        pygame.draw.rect(surface, BLACK, rect, 2)
        surface.blit(font_title.render(title, True, BLACK), (rect.x + 10, rect.y + 10))
        
    if not items:
        return

    max_items = (rect.height - 40) // 25

    if title == "Notification":
        start_index = max(0, len(items) - max_items)
        end_index = len(items)
        y_offset = rect.y + 70
        for i, item in enumerate(items[start_index:end_index]):
            wrapped_lines = textwrap.wrap(item, width=50)
            for line in wrapped_lines:
                surface.blit(font.render(line, True, BLACK), (rect.x + 20, y_offset))
                y_offset += 20

    elif title == "Leaderboard":
        start_index = max(0, len(items) - max_items)
        end_index = len(items)
        for i, item in enumerate(items[start_index:end_index]):
            if isinstance(item, dict):
                text = f"{item.get('player', 'Unknown')} - Net Worth: ${item.get('net_worth', 0):,.2f}"
            else:
                text = str(item)
            surface.blit(font.render(text, True, BLACK), (rect.x + 10, rect.y + 40 + i * 25))

    else:
        if is_dict and isinstance(items, dict):
            lines = []

            def fmt_money(key, value):
                return f"{key.replace('_', ' ').capitalize()}: ${float(value):,.2f}"

            for key in ["cash", "saving", "net_worth", "current_position", "round_played", "stocks", "estates"]:
                val = items.get(key, "-")

                if isinstance(val, (int, float)) and key not in ["current_position", "round_played"]:
                    lines.append(fmt_money(key, val))

                elif key == "current_position":
                    tile_index = int(val)
                    tile_name = TILE_MAP[tile_index] if tile_index < len(TILE_MAP) else "Unknown"
                    lines.append(f"Current position: {tile_name} ({tile_index})")

                # elif key == "round_played":
                    # lines.append(f"Round played: {val}")

                elif key == "stocks" and isinstance(val, dict):
                    lines.append("Stocks:")
                    if not val:
                        lines.append(" - None")
                    else:
                        for stock_name, quantity in val.items():
                            price = stock_prices.get(stock_name, 0)
                            total_value = round(quantity * price, 2)
                            lines.append(f" - {stock_name}: {quantity} @ ${price:.2f} → ${total_value:.2f}")

                elif key == "estates" and isinstance(val, list):
                    lines.append("Estates:")
                    if not val:
                        lines.append(" - None")
                    else:
                        for estate_name in val:
                            price = estate_prices.get(estate_name, 0)
                            lines.append(f" - {estate_name} (${price:.2f})")

            # Render the lines
                    y_start = rect.y + 40 if title != "Portfolio" else rect.y + 60
                    for i, line in enumerate(lines):
                        text = font.render(line, True, BLACK)
                        surface.blit(text, (rect.x + 20, y_start + i * 22))

        elif isinstance(items, list):
            start_index = max(0, len(items) - max_items)
            end_index = len(items)
            for i, item in enumerate(items[start_index:end_index]):
                if isinstance(item, dict):
                    text = f"{item.get('player_name', 'Unknown')} - Position: {item.get('current_position', 'Unknown')}"
                else:
                    text = str(item)
                surface.blit(font.render(text, True, BLACK), (rect.x + 10, rect.y + 40 + i * 25))


# ===================================
#  DRAW CHART                      ||
# ===================================

def draw_leaderboard_chart(surface, rect, leaderboard_data):
    if not leaderboard_data:
        return

    # Clear background
    # pygame.draw.rect(surface, LIGHT_GRAY, rect)
    # pygame.draw.rect(surface, BLACK, rect, 2)

    # Load avatars
    shared_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../shared/avt'))
    avatars = [pygame.image.load(os.path.join(shared_path, f"{i+1}.png")).convert_alpha()
               for i in range(len(leaderboard_data))]

    # Color config (the order must match the player index)
    bar_colors = [(92, 150, 92), (18, 51, 86), (250, 175, 64), (217, 113, 66),(98, 26, 29), (127, 63, 151)]
 

    max_width = rect.width
    max_height = rect.height
    
    # Calculate dynamic bar width and spacing based on number of players (4-6 players)
    num_players = len(leaderboard_data)
    total_spacing = max_width * 0.1  # 10% of width for outer margins
    available_width = max_width - total_spacing
    
    # Calculate spacing between bars (smaller spacing for more players)
    spacing_between = available_width * 0.15 / (num_players - 1) if num_players > 1 else 0
    
    # Calculate bar width
    bar_width = (available_width - spacing_between * (num_players - 1)) / num_players
    bar_width = max(40, min(80, int(bar_width)))  # Limit bar width between 40-80px
    
    # Recalculate spacing to center everything
    total_bars_width = bar_width * num_players + spacing_between * (num_players - 1)
    start_x_offset = (max_width - total_bars_width) / 2
    
    top_padding = 40
    bottom_padding = 40

    # Handle both tuple and dictionary formats
    try:
        # Check if data contains tuples or dictionaries
        first_item = leaderboard_data[0]
        if isinstance(first_item, tuple):
            # Assume tuple format: (player_name, net_worth) or similar
            max_networth = max(item[1] if len(item) > 1 else 0 for item in leaderboard_data)
        else:
            # Dictionary format
            max_networth = max(item.get("net_worth", 0) for item in leaderboard_data)
    except (IndexError, ValueError, TypeError):
        max_networth = 0
    
    scale = (max_height - top_padding - bottom_padding - 60) / max_networth if max_networth > 0 else 1

    for idx, item in enumerate(leaderboard_data):
        x = rect.x + start_x_offset + idx * (bar_width + spacing_between)
        
        # Handle both tuple and dictionary formats
        if isinstance(item, tuple):
            # Assume tuple format: (player_name, net_worth)
            player_name = item[0] if len(item) > 0 else f"P{idx+1}"
            networth = item[1] if len(item) > 1 else 0
        else:
            # Dictionary format
            networth = item.get("net_worth", 0)
            player_name = item.get("player", f"P{idx+1}")

        bar_height = int(networth * scale)
        y = rect.y + rect.height - bottom_padding - bar_height

        # Draw bar
        pygame.draw.rect(surface, bar_colors[idx % len(bar_colors)],
                         (x, y, bar_width, bar_height))

        # Draw avatar on top
        avatar = pygame.transform.scale(avatars[idx], (40, 40))
        surface.blit(avatar, (x + (bar_width - 40)//2, y - 60 ))

        # Draw networth
        net_text = font.render(f"${networth:,.0f}", True, bar_colors[idx % len(bar_colors)])
        surface.blit(net_text, (x + (bar_width - net_text.get_width()) // 2, y - 20))

        # Draw name below
        name_text = font.render(player_name, True, bar_colors[idx % len(bar_colors)])
        surface.blit(name_text, (x + (bar_width - name_text.get_width()) // 2, rect.y + rect.height - 30))
        
# ===================================
#  DRAW SELL ESTATE POPUP          ||
# ===================================
def show_sell_estate_popup(room_id, player_name):
    import tkinter as tk

    def on_submit():
        estate_name = estate_entry.get()
        price = price_entry.get()
        root.destroy()
        try:
            payload = {
                "room_id": room_id,
                "seller": player_name,
                "estate": estate_name,
                "price": float(price)
            }
            url = f"http://{SERVER_HOST}:8000/api/estate/list_for_sale"
            response = requests.post(url, json=payload)
            print(response.json().get("message", "Unknown response"))
        except Exception as e:
            print(f"❌ Sell estate error: {e}")

    root = tk.Tk()
    root.title("Sell Estate")
    root.geometry("300x200")
    tk.Label(root, text="Estate Name:").pack()
    estate_entry = tk.Entry(root)
    estate_entry.pack()
    tk.Label(root, text="Asking Price ($):").pack()
    price_entry = tk.Entry(root)
    price_entry.pack()
    tk.Button(root, text="Sell", command=on_submit).pack(pady=10)
    root.mainloop()


# ===================================
#  SELECT OFFER POPUP          ||
# ===================================
def show_select_offer_popup(room_id, seller, estate, offers):
    import tkinter as tk

    def accept_offer(buyer, price):
        root.destroy()
        payload = {
            "room_id": room_id,
            "seller": seller,
            "chosen_buyer": buyer,
            "estate_name": estate,
            "price": price
        }
        url = f"http://{SERVER_HOST}:8000/api/estate/accept_offer"
        try:
            response = requests.post(url, json=payload)
            print(response.json().get("message", "Offer accepted."))
        except Exception as e:
            print(f"❌ Error accepting offer: {e}")

    root = tk.Tk()
    root.title("Select Offer")
    root.geometry("350x300")
    tk.Label(root, text=f"Select offer for {estate}:").pack()

    for offer in offers:
        text = f"{offer['buyer']} offered ${offer['price']}"
        tk.Button(root, text=text, command=lambda o=offer: accept_offer(o["buyer"], o["price"])).pack(pady=2)

    root.mainloop()

# ===================================
#  DRAW OFFER POPUP          ||
# ===================================
def show_estate_offer_popup(room_id, player_name, estate_name, seller, asking_price):
    import tkinter as tk

    def on_submit():
        try:
            offer = float(entry.get())
            if offer < asking_price:
                print("Offer must be at least asking price.")
                return
            root.destroy()
            payload = {
                "room_id": room_id,
                "buyer": player_name,
                "estate_name": estate_name,      # PHẢI LÀ "estate_name"
                "offer_price": offer,
            }
            url = f"http://{SERVER_HOST}:8000/api/estate/offer"
            response = requests.post(url, json=payload)
            print(response.json().get("message", "Sent offer."))
        except Exception as e:
            print(f"❌ Error submitting offer: {e}")

    root = tk.Tk()
    root.title("Make Offer")
    root.geometry("300x150")
    tk.Label(root, text=f"{estate_name} listed at ${asking_price}\nEnter your offer:").pack()
    entry = tk.Entry(root)
    entry.pack()
    tk.Button(root, text="Submit", command=on_submit).pack(pady=10)
    root.mainloop()


# ===================================
#  DRAW STOCK ESTATE POPUP          ||
# ===================================
def show_sell_stock_popup(room_id, player_name):
    import tkinter as tk

    def on_submit():
        stock = stock_entry.get()
        quantity = quantity_entry.get()
        price = price_entry.get()
        root.destroy()
        try:
            payload = {
                "room_id": room_id,
                "seller": player_name,
                "stock": stock,
                "quantity": int(quantity),
                "price_per_unit": float(price)
            }
            url = f"http://{SERVER_HOST}:8000/api/stock/list_for_sale"
            response = requests.post(url, json=payload)
            print(response.json().get("message", "Unknown response"))
        except Exception as e:
            print(f"❌ Sell stock error: {e}")

    root = tk.Tk()
    root.title("Sell Stock")
    root.geometry("300x250")
    tk.Label(root, text="Stock Name:").pack()
    stock_entry = tk.Entry(root)
    stock_entry.pack()
    tk.Label(root, text="Quantity:").pack()
    quantity_entry = tk.Entry(root)
    quantity_entry.pack()
    tk.Label(root, text="Price Per Unit ($):").pack()
    price_entry = tk.Entry(root)
    price_entry.pack()
    tk.Button(root, text="Sell", command=on_submit).pack(pady=10)
    root.mainloop()


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
    # Vẽ hình ảnh nền topbar
    surface.blit(topbar_image, (top_bar.x, top_bar.y))

    # Hiển thị thông tin trên thanh bar
    room_text = font_title.render(f"ROOM {room}", True, WHITE)
    player_text = font_title.render(f"PLAYER {player}", True, WHITE)
    round_text = font_title.render(f"ROUND {round}", True, WHITE)

    # Vị trí text trên thanh bar (dựa trên layout của hình bạn gửi)
    surface.blit(room_text, (top_bar.x + 30, top_bar.y + 12))
    surface.blit(round_text, (top_bar.x + 950, top_bar.y + 12))
    # Vẽ avatar của người chơi bên cạnh "PLAYER ..."
    if ws_joined_players:
        # Tìm index của player
        player_index = next((i for i, p in enumerate(ws_joined_players) if p.get("player_name") == player), None)
        if player_index is not None:
            shared_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../shared/avt'))
            avatar_path = os.path.join(shared_path, f"{player_index + 1}.png")
            if os.path.exists(avatar_path):
                avatar_image = pygame.image.load(avatar_path).convert_alpha()
                avatar_image = pygame.transform.scale(avatar_image, (30, 30))  # Kích thước nhỏ gọn

                # Vị trí avatar + chữ
                avatar_x = top_bar.x + 470
                avatar_y = top_bar.y + 10
                surface.blit(avatar_image, (avatar_x, avatar_y))

                # Vẽ tên cạnh avatar (cách phải ra 40px)
                surface.blit(player_text, (avatar_x + 40, avatar_y + 5))

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
# CONFIRM DEPOSITE                   ||
# =====================================
async def send_ws_saving_deposit(room_id, player_name, amount):
    uri = f"ws://{SERVER_HOST}:8000/ws/{room_id}/{player_name}"
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({
            "action": "saving_deposit",
            "room_id": room_id,
            "player_name": player_name,
            "amount": amount
        }))
                
def confirm_saving_deposit():
    global saving_popup, saving_input_text
    try:
        amount = float(saving_input_text)
        max_amount = saving_popup["max_amount"]
        room_id = saving_popup["room_id"]
        player_name = saving_popup["player_name"]

        if 0 < amount <= max_amount:
            def send_deposit():
                asyncio.run(send_ws_saving_deposit(room_id, player_name, amount))
            threading.Thread(target=send_deposit).start()
        else:
            print("Invalid saving amount.")
    except Exception as e:
        print(f"Error parsing saving amount: {e}")

    saving_popup = None
    saving_input_text = ""

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
        threading.Thread(target=lambda: asyncio.run(send_buy_request(room_id, player_name))).start()
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
#  DRAW Saving POPUP                ||
# ===================================  
async def send_ws_saving_withdraw(room_id, player_name):
    uri = f"ws://{SERVER_HOST}:8000/ws/{room_id}/{player_name}"
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({
            "action": "saving_withdraw",
            "room_id": room_id,
            "player_name": player_name
        }))
def draw_saving_popup(surface, popup_data):
    if popup_data.get("withdraw", False):
        # Show withdraw confirmation button
        button_rect = pygame.Rect(popup_rect.x + 240, popup_rect.y + 190, 120, 35)
        pygame.draw.rect(surface, GRAY, button_rect)
        pygame.draw.rect(surface, BLACK, button_rect, 2)
        btn_text = font.render("Withdraw", True, BLACK)
        surface.blit(btn_text, btn_text.get_rect(center=button_rect.center))

        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN and button_rect.collidepoint(pygame.mouse.get_pos()):
                room_id = popup_data["room_id"]
                player_name = popup_data["player_name"]
                def send_withdraw():
                    asyncio.run(send_ws_saving_withdraw(room_id, player_name))
                threading.Thread(target=send_withdraw).start()
                saving_popup = None
    else:
        popup_rect = pygame.Rect(300, 200, 600, 250)
        pygame.draw.rect(surface, WHITE, popup_rect)
        pygame.draw.rect(surface, BLACK, popup_rect, 3)

        title = "Savings Deposit"
        message = popup_data["message"]
        max_amount = popup_data["max_amount"]

        title_text = font_title.render(title, True, (0, 100, 200))
        surface.blit(title_text, (popup_rect.x + 20, popup_rect.y + 20))

        # Description
        msg_lines = textwrap.wrap(message, 60)
        for i, line in enumerate(msg_lines):
            line_text = font.render(line, True, BLACK)
            surface.blit(line_text, (popup_rect.x + 20, popup_rect.y + 60 + i * 25))

        # Input box
        global saving_input_text
        input_rect = pygame.Rect(popup_rect.x + 100, popup_rect.y + 140, 400, 35)
        pygame.draw.rect(surface, WHITE, input_rect)
        pygame.draw.rect(surface, BLACK, input_rect, 2)
        input_text = font.render(saving_input_text, True, BLACK)
        surface.blit(input_text, (input_rect.x + 10, input_rect.y + 5))

        # OK button
        button_rect = pygame.Rect(popup_rect.x + 240, popup_rect.y + 190, 120, 35)
        pygame.draw.rect(surface, GRAY, button_rect)
        pygame.draw.rect(surface, BLACK, button_rect, 2)
        btn_text = font.render("Confirm", True, BLACK)
        surface.blit(btn_text, btn_text.get_rect(center=button_rect.center))

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    saving_input_text = saving_input_text[:-1]
                elif event.key == pygame.K_RETURN:
                    confirm_saving_deposit()
                else:
                    if event.unicode.isdigit():
                        saving_input_text += event.unicode

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if button_rect.collidepoint(pygame.mouse.get_pos()):
                    confirm_saving_deposit()

# ===================================
#  DRAW SHOCK POPUP                ||
# ===================================  
def draw_shock_popup(surface, popup_data):
    popup_rect = pygame.Rect(150, 150, 900, 400)
    pygame.draw.rect(surface, WHITE, popup_rect)
    pygame.draw.rect(surface, BLACK, popup_rect, 3)

    title = popup_data["title"]
    message = popup_data["message"]
    stocks = popup_data.get("stocks", [])
    estate_effect = popup_data.get("estate_effect", {})

    # Title
    title_text = font_title.render(title, True, (200, 0, 0))
    surface.blit(title_text, (popup_rect.x + 20, popup_rect.y + 20))

    # Wrapped message
    wrapped_lines = textwrap.wrap(message, width=100)
    for i, line in enumerate(wrapped_lines):
        line_text = font.render(line, True, BLACK)
        surface.blit(line_text, (popup_rect.x + 20, popup_rect.y + 60 + i * 25))

    # Stock Effects
    stock_start_y = popup_rect.y + 60 + len(wrapped_lines) * 25 + 10
    if stocks:
        surface.blit(font_title.render("Stock Effects:", True, BLACK), (popup_rect.x + 20, stock_start_y))
        for i, s in enumerate(stocks):
            base_price = s.get("base_price") or s.get("start_price") or s.get("now_price", 1)
            now_price = s.get("now_price", 1)
            delta = round((now_price - base_price) / base_price * 100, 2) if base_price else 0
            color = (0, 150, 0) if delta > 0 else (200, 0, 0)
            sign = "+" if delta > 0 else ""
            stock_line = f"{s['name']} → ${now_price:.2f} ({sign}{delta:.2f}%)"
            surface.blit(font.render(stock_line, True, color), (popup_rect.x + 40, stock_start_y + 30 + i * 22))

    # Estate Effects
    estate_y = stock_start_y + 30 + len(stocks) * 22 + 10
    if estate_effect:
        surface.blit(font_title.render("Estate Effects:", True, BLACK), (popup_rect.x + 20, estate_y))
        value_delta = estate_effect.get("value", 0)
        rent_delta = estate_effect.get("rent", 0)
        v_sign = "+" if value_delta > 0 else ""
        r_sign = "+" if rent_delta > 0 else ""
        v_text = f"Value change: {v_sign}{value_delta}%"
        r_text = f"Rent change: {r_sign}{rent_delta}%"
        surface.blit(font.render(v_text, True, BLACK), (popup_rect.x + 40, estate_y + 30))
        surface.blit(font.render(r_text, True, BLACK), (popup_rect.x + 40, estate_y + 55))

    # OK Button
    button_rect = pygame.Rect(popup_rect.x + 380, popup_rect.y + 340, 140, 35)
    pygame.draw.rect(surface, GRAY, button_rect)
    pygame.draw.rect(surface, BLACK, button_rect, 2)
    text = font.render("OK", True, BLACK)
    surface.blit(text, text.get_rect(center=button_rect.center))

    # Handle click to dismiss popup
    for event in pygame.event.get(pygame.MOUSEBUTTONDOWN):
        if button_rect.collidepoint(pygame.mouse.get_pos()):
            global shock_popup
            shock_popup = None

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
        print("Sell button clicked")
        # Mở popup chọn bán gì
        import tkinter as tk

        def on_sell_estate():
            root.destroy()
            show_sell_estate_popup(room_id, player_name)

        def on_sell_stock():
            root.destroy()
            show_sell_stock_popup(room_id, player_name)

        root = tk.Tk()
        root.title("Sell Options")
        root.geometry("300x150")
        tk.Label(root, text="What do you want to sell?").pack(pady=10)
        tk.Button(root, text="Sell Estate", command=on_sell_estate).pack(pady=5)
        tk.Button(root, text="Sell Stock", command=on_sell_stock).pack(pady=5)
        root.mainloop()
    elif button_label == "Deposit":
        print("Deposit button clicked")
        # Trigger saving manually (optional - or just open a popup)
        if ws_portfolio and ws_portfolio.get("cash", 0) > 0:
            global saving_popup, saving_input_text
            saving_popup = {
                "message": "How much do you want to save?",
                "max_amount": ws_portfolio.get("cash", 0)
            }
            saving_input_text = ""
    elif button_label == "End Turn":
        # Logic to handle End Turn action
        print("End Turn button clicked")
        asyncio.run(send_end_turn_request(room_id, player_name))


# ==================================
# DRAW ACTION BUTTON
# ==================================
def draw_action_buttons(surface, room_id, player_name, is_host_runtime, game_started, current_player, events):
    """
    Unified action buttons handler - handles all button drawing and click logic
    """
    # Vẽ nền action_bar
    # pygame.draw.rect(surface, GRAY, action_bar)
    # pygame.draw.rect(surface, BLACK, action_bar, 2)

    # Load all button images with correct proportions
    ui_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../shared/ui'))
    
    # Button proportions: roll:buy:sell:deposit:end = 145:85:80:120:430
    # Using a base height of 40px, calculate widths proportionally
    base_height = 65
    button_widths = {
        'roll': 145,
        'buy': 85,
        'sell': 80,
        'deposit': 120,
        'start': 430,
        'end': 430
    }
    
    button_images = {}
    for key in ['roll', 'buy', 'sell', 'deposit', 'start', 'end']:
        try:
            image = pygame.image.load(os.path.join(ui_path, f'{key}.png'))
            # Scale to correct proportions
            width = button_widths[key]
            button_images[key] = pygame.transform.scale(image, (width, base_height))
        except pygame.error as e:
            print(f"Warning: Could not load {key}.png - {e}")
            # Create fallback colored rectangle if image not found
            fallback = pygame.Surface((button_widths[key], base_height))
            fallback.fill((100, 100, 100))
            button_images[key] = fallback

    # Get mouse state once
    mouse_pos = pygame.mouse.get_pos()
    mouse_clicked = any(e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 for e in events)

    # Button definitions with conditions
    buttons = []
    
    # Row 1: Game action buttons (only show if game started)
    if game_started:
        # Calculate positions for row 1 buttons with their actual widths
        current_x = action_bar.x + 10
        row1_buttons = [
            {'label': 'Roll Dice', 'image_key': 'roll', 'action': 'roll_dice', 'player_only': True, 'width': 145},
            {'label': 'Buy', 'image_key': 'buy', 'action': 'buy', 'player_only': False, 'width': 85},
            {'label': 'Sell', 'image_key': 'sell', 'action': 'sell', 'player_only': False, 'width': 80},
            {'label': 'Deposit', 'image_key': 'deposit', 'action': 'deposit', 'player_only': False, 'width': 120}
        ]
        
        for btn_config in row1_buttons:
            # Special handling for Roll Dice - only show for current player
            if btn_config['player_only'] and player_name != current_player:
                continue
                
            btn_rect = pygame.Rect(current_x, action_bar.y + 5, btn_config['width'], base_height)
            
            buttons.append({
                'rect': btn_rect,
                'label': btn_config['label'],
                'image': button_images[btn_config['image_key']],
                'action': btn_config['action'],
                'enabled': True
            })
            
            # Move to next position with small spacing
            current_x += btn_config['width'] + 5

    # Row 2: Main action button (END TURN width = 430)
    main_rect = pygame.Rect(action_bar.x + 10, action_bar.y + 75, 430, base_height)
    
    if not game_started and is_host_runtime:
        # START button for host before game starts
        buttons.append({
            'rect': main_rect,
            'label': "START",
            'image': button_images['start'],
            'action': 'start_game',
            'enabled': True
        })
    elif game_started:
        # END TURN button during game
        buttons.append({
            'rect': main_rect,
            'label': "END TURN",
            'image': button_images['end'],
            'action': 'end_turn',
            'enabled': True
        })

    # Draw and handle all buttons
    for button in buttons:
        rect = button['rect']
        image = button['image']
        action = button['action']
        enabled = button['enabled']
        
        # Draw button image (already contains text)
        surface.blit(image, rect.topleft)
        
        # Handle click
        if enabled and rect.collidepoint(mouse_pos) and mouse_clicked:
            handle_button_action(action, room_id, player_name)
            
def handle_button_action(action, room_id, player_name):
    """
    Centralized button action handler
    """
    try:
        if action == 'start_game':
            response = requests.post(f"http://{SERVER_HOST}:8000/start", json={"room_id": room_id})
            if response.status_code == 200:
                print("✅ Game started successfully")
            else:
                print("❌ Failed to start game:", response.text)
                
        elif action == 'roll_dice':
            response = requests.post(f"http://{SERVER_HOST}:8000/roll", 
                                   json={"room_id": room_id, "player_name": player_name})
            if response.status_code == 200:
                print("✅ Dice rolled successfully")
            else:
                print("❌ Error rolling dice:", response.json())
                
        elif action == 'end_turn':
            asyncio.run(send_end_turn_request(room_id, player_name))
            
        elif action == 'buy':
            handle_button_click('Buy', room_id, player_name)
            
        elif action == 'sell':
            handle_button_click('Sell', room_id, player_name)
            
        elif action == 'deposit':
            handle_button_click('Deposit', room_id, player_name)
            
    except Exception as e:
        print(f"❌ Error handling {action}: {e}")
            
            
# =========================================
#  DRAW MAP WITH PLAYERS
# =========================================
def draw_map_with_players(surface, players):
    # Load the board image as the map
    board_image_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../shared/ui/board_new.png'))
    board_image = pygame.image.load(board_image_path)
    board_image = pygame.transform.scale(board_image, (700, 700))
    surface.blit(board_image, (map_area.x, map_area.y))

    # Load avatars using absolute path
    shared_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../shared/avt'))
    avatars = [
        pygame.image.load(os.path.join(shared_path, f"{i}.png")) for i in range(1, len(players) + 1)
    ]

    # Define tile dimensions based on the scaled board
    corner_tile_size = (151, 151)  # Corner tiles
    vertical_tile_size = (151, 101)  # Vertical tiles
    horizontal_tile_size = (101, 151)  # Horizontal tiles

    for idx, player in enumerate(players):
        if isinstance(player, dict) and "current_position" in player:
            position = int(player["current_position"])

            if position == 0:  # GO
                x, y = map_area.x, map_area.y + 700 - corner_tile_size[1]
            elif position < 5:  # Left column (going up)
                x, y = map_area.x, map_area.y + 700 - (position * vertical_tile_size[1]) - corner_tile_size[1]
            elif position == 5:  # Jail Visit
                x, y = map_area.x, map_area.y
            elif position < 10:  # Top row (going right)
                x, y = map_area.x + ((position - 6) * horizontal_tile_size[0]) + corner_tile_size[0], map_area.y
            elif position == 10:  # Quizzes (Education)
                x, y = map_area.x + 700 - corner_tile_size[0], map_area.y
            elif position < 15:  # Right column (going down)
                x, y = map_area.x + 700 - vertical_tile_size[0], map_area.y + ((position - 11) * vertical_tile_size[1]) + corner_tile_size[1]
            elif position == 15:  # Jail (Challenge)
                x, y = map_area.x + 700 - corner_tile_size[0], map_area.y + 700 - corner_tile_size[1]
            else:  # Bottom row (going left)
                x, y = map_area.x + 700 - ((position - 15) * horizontal_tile_size[0]) - corner_tile_size[0], map_area.y + 700 - horizontal_tile_size[1]

            
            avatar = pygame.transform.scale(avatars[idx], (corner_tile_size[0] // 3, corner_tile_size[1] // 3))
            surface.blit(avatar, (x + corner_tile_size[0] // 4, y + corner_tile_size[1] // 4))


# =========================================
#  RUN UI
# =========================================
def run_ui(room_id, player_name, joined_players, _, leaderboard=None, portfolio=None):
    global current_player
    global current_room
    if not pygame.get_init():
        pygame.init()
    if not pygame.display.get_init():
        pygame.display.init()

    # Adjust the window size to match the board dimensions
    screen = pygame.display.set_mode((1200, 800))
    pygame.display.set_caption("Investopoly - Main Game UI")

    threading.Thread(target=lambda: asyncio.run(listen_ws(room_id, player_name)), daemon=True).start()
    running = True
    # start_btn = pygame.Rect(950, 720, 120, 50)  # Adjusted position for the start button
    # is_host_runtime = determine_host(player_name, joined_players)
    while running:
        screen.fill(WHITE)
        events = pygame.event.get()

        # for e in events:
        #     if e.type == pygame.QUIT:
        #         running = False
        #     elif e.type == pygame.MOUSEBUTTONDOWN:
        #         if is_host_runtime and start_btn and start_btn.collidepoint(e.pos):
        #             try:
        #                 print("Host clicked the START button.")  # Debug log
        #                 response = requests.post(f"http://{SERVER_HOST}:8000/start", json={"room_id": room_id})
        #                 if response.status_code == 200:
        #                     print("Game started successfully.")
        #                     start_btn = None  # Remove the START button after the game starts
        #                 else:
        #                     print(f"[Error] Backend response: {response.text}")
        #             except Exception as err:
        #                 print(f"[Error] Failed to start game: {err}")

        #     elif e.type == pygame.MOUSEBUTTONDOWN:
        #         if e.button == 4:  # Scroll up
        #             scroll_offset = max(0, scroll_offset - 1)
        #         elif e.button == 5:  # Scroll down
        #             max_items = (event_box.height - 40) // 25
        #             scroll_offset = min(len(ws_notifications) - max_items, scroll_offset + 1)

        for e in events:
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.MOUSEBUTTONDOWN:
                if e.button == 4:  # Scroll up
                    scroll_offset = max(0, scroll_offset - 1)
                elif e.button == 5:  # Scroll down
                    max_items = (event_box.height - 40) // 25
                    scroll_offset = min(len(ws_notifications) - max_items, scroll_offset + 1)

        # Define current_players before using it
        current_players = ws_joined_players if ws_joined_players else joined_players

        # Update host determination logic
        if current_players and isinstance(current_players[0], dict):
            is_host_runtime = (player_name == current_players[0].get('player_name'))
        else:
            is_host_runtime = (player_name == current_players[0]) if current_players else False
            
            
        # Define current_players before using it
        # current_players = ws_joined_players if ws_joined_players else joined_players

        # Debug log for player_name and current_players
        # print(f"Player name: {player_name}")
        # print(f"Current players: {current_players}")

        # # Update host determination logic
        # if current_players and isinstance(current_players[0], dict):
        #     is_host_runtime = (player_name == current_players[0].get('player_name'))
        # else:
        #     is_host_runtime = (player_name == current_players[0]) if current_players else False

        # print(f"Is host runtime: {is_host_runtime}")
        
        # Vẽ UI
        game_started = current_round is not None

        # Vẽ UI
        # draw_top_bar(screen, room_id, player_name, current_round)
        # draw_map_with_players(screen, ws_joined_players or joined_players)
        # draw_box(event_box, "Notification", screen, ws_notifications)  # Display notifications
        # draw_leaderboard_chart(screen, leaderboard_box, ws_leaderboard or leaderboard)
        # draw_box(portfolio_box, "Portfolio", screen, ws_portfolio or portfolio, is_dict=True)
        # draw_action_buttons(screen, room_id, player_name, is_host_runtime, current_round is not None)
        draw_top_bar(screen, room_id, player_name, current_round)
        draw_map_with_players(screen, ws_joined_players or joined_players)
        draw_box(event_box, "Notification", screen, ws_notifications)
        draw_leaderboard_chart(screen, leaderboard_box, ws_leaderboard or leaderboard)
        draw_box(portfolio_box, "Portfolio", screen, ws_portfolio or portfolio, is_dict=True)

        # Nút start chỉ nếu là host
        # if is_host_runtime and start_btn:
        #     # print("Displaying START button for host.")  # Debug log
        #     pygame.draw.rect(screen, GREEN, start_btn)
        #     pygame.draw.rect(screen, BLACK, start_btn, 2)
        #     text = font.render("START", True, WHITE)
        #     screen.blit(text, text.get_rect(center=start_btn.center))
        
        draw_action_buttons(screen, room_id, player_name, is_host_runtime, game_started, current_player, events)


        if quiz_popup:
            draw_quiz_popup(screen, quiz_popup, room_id, player_name)
        if shock_popup:
            draw_shock_popup(screen, shock_popup)
        if saving_popup:
            draw_saving_popup(screen, saving_popup)
            
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
    sys.exit()
