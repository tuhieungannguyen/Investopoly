import pygame
import sys
import random
import threading
import websocket
import json

# -------------------
#  Cấu hình chung
# -------------------
WINDOW_WIDTH  = 1024
WINDOW_HEIGHT = 768
FPS = 30

# Màu sắc (R, G, B)
WHITE       = (255, 255, 255)
BLACK       = (  0,   0,   0)
GRAY        = (200, 200, 200)
DARK_GRAY   = (120, 120, 120)
GREEN       = ( 46, 125,  50)
LIGHT_GREEN = (200, 230, 200)
LIGHT_BLUE  = (227, 242, 253)
LIGHT_RED   = (255, 235, 238)
YELLOW      = (255, 235,  59)
PURPLE      = (243, 229, 245)
ORANGE      = (255, 242, 204)
LIGHT_YELLOW= (255, 253, 231)

# Font
pygame.font.init()
FONT_SMALL  = pygame.font.SysFont('Arial', 16)
FONT_MEDIUM = pygame.font.SysFont('Arial', 20)
FONT_LARGE  = pygame.font.SysFont('Arial', 24)
FONT_XLARGE = pygame.font.SysFont('Arial', 32)

# -------------------
#  Lớp Tile
# -------------------
class Tile:
    def __init__(self, rect, text, type_):
        """
        rect: pygame.Rect(x, y, width, height)
        text: chuỗi hiển thị trên ô (có thể \n xuống dòng)
        type_: một trong ['GO', 'REAL_ESTATE', 'STOCK', 'SAVINGS', 'SHOCK', 'CHANCE', 'QUIZ', 'TAX', 'JAIL', 'EMPTY']
        """
        self.rect = rect
        self.text = text
        self.type_ = type_
    
    def draw(self, surface):
        # Chọn màu nền tuỳ theo type
        if self.type_ == 'GO':
            color = ORANGE
        elif self.type_ == 'REAL_ESTATE':
            color = LIGHT_GREEN
        elif self.type_ == 'STOCK':
            color = ORANGE
        elif self.type_ == 'SAVINGS':
            color = LIGHT_BLUE
        elif self.type_ == 'SHOCK':
            color = LIGHT_RED
        elif self.type_ == 'CHANCE':
            color = PURPLE
        elif self.type_ == 'QUIZ':
            color = LIGHT_YELLOW
        elif self.type_ == 'TAX':
            color = GRAY
        elif self.type_ == 'JAIL':
            color = DARK_GRAY
        else:  # 'EMPTY' hoặc không xác định
            color = WHITE
        
        # Vẽ ô
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 2)
        
        # Vẽ text xuống giữa ô
        if self.text:
            lines = self.text.split('\n')
            for i, line in enumerate(lines):
                label = FONT_SMALL.render(line, True, BLACK)
                label_rect = label.get_rect()
                label_rect.center = (
                    self.rect.x + self.rect.width // 2,
                    self.rect.y + 15 + i * 18
                )
                surface.blit(label, label_rect)

# -------------------
#  Lớp Button
# -------------------
class Button:
    def __init__(self, rect, text, callback, bg_color=LIGHT_BLUE, fg_color=BLACK):
        """
        rect: pygame.Rect
        text: label trên button
        callback: hàm gọi khi click
        bg_color: background color
        fg_color: text color
        """
        self.rect = rect
        self.text = text
        self.callback = callback
        self.bg_color = bg_color
        self.fg_color = fg_color
    
    def draw(self, surface):
        pygame.draw.rect(surface, self.bg_color, self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 2)
        label = FONT_MEDIUM.render(self.text, True, self.fg_color)
        label_rect = label.get_rect(center=self.rect.center)
        surface.blit(label, label_rect)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                # Gọi callback
                self.callback()

# -------------------
#  Hàm ví dụ callback cho các button
# -------------------
def roll_dice_action():
    global player_portfolio
    print('[DEBUG] roll_dice_action callback called')
    send_action('roll_dice')

def buy_sell_action():
    global current_popup, player_portfolio
    print('[DEBUG] buy_sell_action callback called')
    send_action('buy_sell')
    current_popup = Popup('Giao dịch tài sản', 'Đã gửi yêu cầu mua/bán lên backend!\n(Nhấn Đóng để tắt)')

def end_turn_action():
    print('[DEBUG] end_turn_action callback called')
    send_action('end_turn')
    print('>>> End Turn button clicked')

# -------------------
#  Thiết lập Pygame cơ bản
# -------------------
pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Investopoly - Pygame Frontend & UX")
clock = pygame.time.Clock()

# -------------------
#  Tạo bàn cờ 20 ô (6×5 grid, dùng 20 vị trí xung quanh)
# -------------------
TILE_SIZE = 100
GAP = 2
COLUMNS = 6
ROWS    = 5

# Xác định toạ độ khung vẽ bàn cờ (600×600)
BOARD_WIDTH  = COLUMNS * TILE_SIZE + (COLUMNS - 1) * GAP
BOARD_HEIGHT = ROWS    * TILE_SIZE + (ROWS    - 1) * GAP
BOARD_LEFT   = 20
BOARD_TOP    = 80

# Danh sách layout (col, row, text, type_)
layout = [
    # Hàng trên (row=0, col 0→5)
    (0, 0, "Jail\nVisit",     "JAIL"),
    (1, 0, "Shock\nEvent",    "SHOCK"),
    (2, 0, "Savings",         "SAVINGS"),
    (3, 0, "Stock\nCorp A",   "STOCK"),
    (4, 0, "Real Estate 3",   "REAL_ESTATE"),
    (5, 0, "Quizzes\n(Edu)",  "QUIZ"),

    # Cột phải (col=5, row 1→3)
    (5, 1, "Real Estate 4",   "REAL_ESTATE"),
    (5, 2, "Stock\nCorp B",   "STOCK"),
    (5, 3, "Chance",          "CHANCE"),

    # Hàng dưới (row=4, col 5→0)
    (5, 4, "Stock\nCorp C",   "STOCK"),
    (4, 4, "Shock\nEvent",    "SHOCK"),
    (3, 4, "Tax\nCheckpoint", "TAX"),
    (2, 4, "Real Estate 5",   "REAL_ESTATE"),
    (1, 4, "GO",              "GO"),
    (0, 4, "Jail\n(Chal)",     "JAIL"),

    # Cột trái (col=0, row 3→1)
    (0, 3, "Real Estate 1",   "REAL_ESTATE"),
    (0, 2, "Stock\nCorp A",   "STOCK"),
    (0, 1, "Real Estate 2",   "REAL_ESTATE"),
]

tiles = []
for col, row, text, type_ in layout:
    x = BOARD_LEFT + col * (TILE_SIZE + GAP)
    y = BOARD_TOP  + row * (TILE_SIZE + GAP)
    rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
    tiles.append(Tile(rect, text, type_))

# -------------------
#  Tạo sidebar (phần bên phải) rộng 350 px, cao = BOARD_HEIGHT
# -------------------
SIDEBAR_LEFT   = BOARD_LEFT + BOARD_WIDTH + 20
SIDEBAR_TOP    = BOARD_TOP
SIDEBAR_WIDTH  = WINDOW_WIDTH - SIDEBAR_LEFT - 20   # lề phải 20 px
SIDEBAR_HEIGHT = BOARD_HEIGHT

# -------------------
#  Các button trong sidebar
# -------------------
buttons = []
btn_width  = SIDEBAR_WIDTH - 40  # lề 20 px hai bên
btn_height = 50
btn_x = SIDEBAR_LEFT + 20
btn_y = SIDEBAR_TOP + 200

# Roll Dice button
buttons.append(Button(
    rect=pygame.Rect(btn_x, btn_y, btn_width, btn_height),
    text="Roll Dice",
    callback=roll_dice_action
))
# Buy/Sell button
buttons.append(Button(
    rect=pygame.Rect(btn_x, btn_y + btn_height + 20, btn_width, btn_height),
    text="Buy / Sell",
    callback=buy_sell_action
))
# End Turn button
buttons.append(Button(
    rect=pygame.Rect(btn_x, btn_y + 2*(btn_height + 20), btn_width, btn_height),
    text="End Turn",
    callback=end_turn_action
))

# -------------------
#  Dummy data cho Net Worth Chart (giá trị mẫu của 1 người chơi)
# -------------------
player_portfolio = {
    "cash": 1200,
    "stock_value": 800,
    "real_estate_value": 1500,
    "savings_value": 500
}

# -------------------
#  Hàm vẽ Net Worth Chart (bar chart đơn giản)
# -------------------
def draw_net_worth_chart(surface, x, y, width, height, portfolio):
    """
    Vẽ một biểu đồ đơn giản hiển thị cash, stock, RE, savings.
    - portfolio: dict {"cash": int, "stock_value": int, "real_estate_value": int, "savings_value": int}
    """
    # Vẽ khung
    chart_rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(surface, WHITE, chart_rect)
    pygame.draw.rect(surface, BLACK, chart_rect, 2)
    # Tiêu đề
    title = FONT_MEDIUM.render("Net Worth Breakdown", True, BLACK)
    surface.blit(title, (x + 10, y + 10))
    
    # Tính tổng net worth
    total = sum(portfolio.values())
    if total == 0:
        total = 1  # tránh chia 0

    # Danh sách tuples (“label”, value, color)
    bars = [
        ("Cash", portfolio["cash"], LIGHT_YELLOW),
        ("Stock", portfolio["stock_value"], LIGHT_BLUE),
        ("Real Estate", portfolio["real_estate_value"], LIGHT_GREEN),
        ("Savings", portfolio["savings_value"], PURPLE)
    ]
    # Vẽ từng cột
    bar_width = (width - 40) // len(bars)  # chừa lề 20 px hai bên
    max_bar_height = height - 70  # chừa tiêu đề + khoảng trống
    
    for i, (label, value, color) in enumerate(bars):
        # Tỉ lệ chiều cao
        h = int(value / total * max_bar_height)
        bx = x + 20 + i * (bar_width + 10)
        by = y + height - 20 - h
        pygame.draw.rect(surface, color, (bx, by, bar_width, h))
        pygame.draw.rect(surface, BLACK, (bx, by, bar_width, h), 1)
        # Vẽ tên bên dưới cột
        lbl = FONT_SMALL.render(label, True, BLACK)
        lbl_rect = lbl.get_rect(center=(bx + bar_width//2, y + height - 10))
        surface.blit(lbl, lbl_rect)
        # Vẽ giá trị lên trên cột
        val_lbl = FONT_SMALL.render(str(value), True, BLACK)
        val_rect = val_lbl.get_rect(center=(bx + bar_width//2, by - 10))
        surface.blit(val_lbl, val_rect)

# -------------------
#  Hàm vẽ thông tin người chơi trong sidebar
# -------------------
def draw_player_info(surface, x, y, portfolio):
    """
    surface: surface cần vẽ
    x, y: top-left góc của vùng info
    portfolio: dict như player_portfolio
    """
    title = FONT_LARGE.render("Player Info", True, BLACK)
    surface.blit(title, (x, y))
    # Vẽ từng dòng thông tin
    offset_y = 40
    for key, value in portfolio.items():
        line = f"{key.replace('_',' ').title()}: {value}"
        lbl = FONT_MEDIUM.render(line, True, BLACK)
        surface.blit(lbl, (x, y + offset_y))
        offset_y += 30

# -------------------
#  Lớp Popup đơn giản
# -------------------
class Popup:
    def __init__(self, title, message, on_close=None):
        self.title = title
        self.message = message
        self.on_close = on_close
        self.width = 400
        self.height = 220
        self.rect = pygame.Rect(
            (WINDOW_WIDTH - self.width) // 2,
            (WINDOW_HEIGHT - self.height) // 2,
            self.width, self.height
        )
        self.close_btn_rect = pygame.Rect(
            self.rect.x + self.width//2 - 60, self.rect.y + self.height - 60, 120, 40
        )
        self.visible = True

    def draw(self, surface):
        # Nền mờ
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0,0,0,120))
        surface.blit(overlay, (0,0))
        # Khung popup
        pygame.draw.rect(surface, WHITE, self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 2)
        # Tiêu đề
        title_lbl = FONT_LARGE.render(self.title, True, BLACK)
        surface.blit(title_lbl, (self.rect.x + 20, self.rect.y + 20))
        # Nội dung
        lines = self.message.split('\n')
        for i, line in enumerate(lines):
            msg_lbl = FONT_MEDIUM.render(line, True, BLACK)
            surface.blit(msg_lbl, (self.rect.x + 20, self.rect.y + 70 + i*30))
        # Nút đóng
        pygame.draw.rect(surface, LIGHT_BLUE, self.close_btn_rect)
        pygame.draw.rect(surface, BLACK, self.close_btn_rect, 2)
        btn_lbl = FONT_MEDIUM.render("Đóng", True, BLACK)
        btn_lbl_rect = btn_lbl.get_rect(center=self.close_btn_rect.center)
        surface.blit(btn_lbl, btn_lbl_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.close_btn_rect.collidepoint(event.pos):
                self.visible = False
                if self.on_close:
                    self.on_close()

# -------------------
#  Biến popup toàn cục
# -------------------
current_popup = None

# Biến lưu WebSocket client
ws = None

def on_message(wsapp, message):
    global player_portfolio
    print('[WS] Received:', message)
    data = json.loads(message)
    # Giả sử backend trả về {'player_portfolio': {...}}
    if 'player_portfolio' in data:
        player_portfolio.update(data['player_portfolio'])
        print('[WS] Updated player_portfolio:', player_portfolio)

def on_error(wsapp, error):
    print('[WS] Error:', error)

def on_close(wsapp, close_status_code, close_msg):
    print('[WS] Closed')

def on_open(wsapp):
    print('[WS] Connected')

def start_ws():
    global ws
    ws = websocket.WebSocketApp(
        'ws://localhost:8000/ws',  # Đổi lại đúng địa chỉ backend của bạn
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.run_forever()

# Gửi action lên backend
def send_action(action, payload=None):
    global ws
    if ws and ws.sock and ws.sock.connected:
        msg = {'action': action}
        if payload:
            msg['payload'] = payload
        ws.send(json.dumps(msg))
    else:
        print('[WS] Not connected!')

# -------------------
#  Vòng lặp chính
# -------------------
def main_loop():
    global current_popup
    # In ra vị trí và kích thước button khi khởi tạo
    for btn in buttons:
        print(f"[DEBUG] Button '{btn.text}' at {btn.rect}")
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            # Nếu có popup và popup đang mở, chỉ chuyển event cho popup
            if current_popup and current_popup.visible:
                current_popup.handle_event(event)
                continue
            # Nếu không có popup, xử lý event cho button/tile như cũ
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                print(f"[DEBUG] Mouse clicked at: {mx}, {my}")  # Debug vị trí chuột
                # Kiểm tra click vào button trước
                for btn in buttons:
                    print(f"[DEBUG] Checking button '{btn.text}' at {btn.rect}")  # Debug vùng button
                    btn.handle_event(event)
                # Sau đó mới kiểm tra tile
                for tile in tiles:
                    if tile.rect.collidepoint(mx, my):
                        print("Clicked on tile:", tile.text, "| type =", tile.type_)
                        # Popup cho quiz
                        if tile.type_ == "QUIZ":
                            current_popup = Popup("Quiz", "Bạn đã vào ô Quiz!\nCâu hỏi sẽ hiện ở đây.")
                        elif tile.type_ == "SHOCK":
                            current_popup = Popup("Shock Event", "Bạn gặp sự kiện bất ngờ!\nNội dung sẽ hiện ở đây.")
                        elif tile.type_ == "CHANCE":
                            current_popup = Popup("Chance", "Bạn nhận được cơ hội!\nNội dung sẽ hiện ở đây.")
                        break
        # Vẽ nền chính
        screen.fill(GREEN)
        # Vẽ bàn cờ (tiles)
        for tile in tiles:
            tile.draw(screen)
        # Vẽ phần sidebar
        sidebar_rect = pygame.Rect(SIDEBAR_LEFT, SIDEBAR_TOP, SIDEBAR_WIDTH, SIDEBAR_HEIGHT)
        pygame.draw.rect(screen, LIGHT_GRAY := (230, 230, 230), sidebar_rect)
        pygame.draw.rect(screen, BLACK, sidebar_rect, 2)
        # Vẽ dòng tiêu đề (ví dụ tên game)
        title = FONT_XLARGE.render("Investopoly", True, BLACK)
        screen.blit(title, (SIDEBAR_LEFT + 20, SIDEBAR_TOP + 10))
        # Vẽ thông tin người chơi
        draw_player_info(screen, SIDEBAR_LEFT + 20, SIDEBAR_TOP + 60, player_portfolio)
        # Vẽ các button
        for btn in buttons:
            btn.draw(screen)
        # Vẽ Net Worth Chart ở dưới cùng
        chart_x = SIDEBAR_LEFT + 10
        chart_y = SIDEBAR_TOP + 400
        chart_w = SIDEBAR_WIDTH - 20
        chart_h = 300
        draw_net_worth_chart(screen, chart_x, chart_y, chart_w, chart_h, player_portfolio)
        # Nếu có popup, vẽ popup lên trên cùng
        if current_popup and current_popup.visible:
            current_popup.draw(screen)
        # Update màn hình
        pygame.display.flip()
        clock.tick(FPS)

# Khởi động WebSocket ở thread riêng khi start game
if __name__ == '__main__':
    ws_thread = threading.Thread(target=start_ws, daemon=True)
    ws_thread.start()
    main_loop()
