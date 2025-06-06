from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rooms = {}  # room_id: {"players": [], "state": {...}}

@app.websocket("/ws/{room_id}/{player_name}")
async def game_room(websocket: WebSocket, room_id: str, player_name: str):
    await websocket.accept()
    if room_id not in rooms:
        rooms[room_id] = {"players": [], "connections": [], "state": {}}
    rooms[room_id]["players"].append(player_name)
    rooms[room_id]["connections"].append(websocket)

    try:
        while True:
            data = await websocket.receive_json()
            # Xử lý lệnh client gửi tới (di chuyển, sự kiện...)
            for ws in rooms[room_id]["connections"]:
                await ws.send_json(data)
    except:
        rooms[room_id]["players"].remove(player_name)
        rooms[room_id]["connections"].remove(websocket)
