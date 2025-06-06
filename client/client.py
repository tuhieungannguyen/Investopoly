import asyncio
import pygame
import websockets
import threading
import json

# --- Config ---
ROOM_ID = "demo1"
PLAYER_NAME = "PlayerA"
WS_URL = f"ws://localhost:8000/ws/{ROOM_ID}/{PLAYER_NAME}"

# --- Khởi tạo Pygame ---
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption(f"Investopoly - {PLAYER_NAME}")
font = pygame.font.SysFont(None, 30)

messages = [f"Đang kết nối tới phòng {ROOM_ID}..."]

# --- Vẽ thông báo ---
def draw_screen():
    screen.fill((255, 255, 255))
    y = 30
    for msg in messages[-18:]:
        text = font.render(msg, True, (0, 0, 0))
        screen.blit(text, (30, y))
        y += 28
    pygame.display.flip()

# --- Xử lý broadcast từ server ---
def handle_message(data: dict):
    msg_type = data.get("type")
    if msg_type == "player_joined":
        messages.append(f">>> {data['player']} đã tham gia.")
    elif msg_type == "game_started":
        messages.append(f">>> Trò chơi bắt đầu. Người chơi đầu tiên: {data['current_player']}")
    elif msg_type == "player_rolled":
        r = data['result']
        messages.append(f"{r['player']} tung xúc xắc: {r['dice']} → {r['tile']}")
        if r['effect']:
            messages.append(f"  ↳ {r['effect']}")
    elif msg_type == "next_turn":
        messages.append(f"==> Lượt tiếp theo: {data['current_player']} (Vòng {data['round']})")
    elif msg_type == "game_ended":
        messages.append("🎯 Trò chơi kết thúc! Bảng xếp hạng:")
        for rank, p in enumerate(data["leaderboard"], 1):
            messages.append(f"  #{rank}: {p['player']} - ${p['net_worth']}")
    else:
        messages.append(f"[Server]: {data}")

# --- Kết nối WebSocket ---
async def listen_websocket():
    async with websockets.connect(WS_URL) as ws:
        while True:
            raw = await ws.recv()
            try:
                msg = json.loads(raw)
                handle_message(msg)
            except:
                messages.append(f"[Raw] {raw}")

def start_ws_thread():
    asyncio.run(listen_websocket())

# --- Khởi chạy WebSocket trong luồng nền ---
threading.Thread(target=start_ws_thread, daemon=True).start()

# --- Main loop Pygame ---
clock = pygame.time.Clock()
running = True
while running:
    draw_screen()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    clock.tick(30)

pygame.quit()
