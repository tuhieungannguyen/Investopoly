import pygame
import asyncio
import websockets
import threading
import json

WIDTH, HEIGHT = 800, 600
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Investopoly")

room_id = "abc123"
player_name = "Player1"

# WebSocket asyncio
async def connect():
    uri = f"ws://localhost:8000/ws/{room_id}/{player_name}"
    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps({"msg": f"{player_name} joined"}))
        while True:
            response = await websocket.recv()
            print("Received:", response)

# Đảm bảo asyncio chạy song song
def start_ws():
    asyncio.new_event_loop().run_until_complete(connect())

# Khởi động websocket trong thread riêng
ws_thread = threading.Thread(target=start_ws)
ws_thread.start()

# Game loop
running = True
while running:
    screen.fill((255, 255, 255))
    pygame.display.flip()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
pygame.quit()
