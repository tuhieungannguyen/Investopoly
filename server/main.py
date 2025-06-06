from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
from typing import Dict, List
from shared.model import Room, Player, GameManager, Estate, Stock, JailStatus, SavingRecord, EventRecord, ChanceLog, Transaction
from server.manager.connection import ConnectionManager
from server.manager.game_state import GameState
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Quản lý kết nối WebSocket ===
manager = ConnectionManager()
# === Quản lý trạng thái game theo từng phòng ===
state = GameState()

@app.websocket("/ws/{room_id}/{player_name}")
async def game_room(websocket: WebSocket, room_id: str, player_name: str):
    await manager.connect(room_id, player_name, websocket)

    if room_id not in state.rooms:
        state.init_room(room_id, [player_name])
    elif player_name not in state.players[room_id]:
        state.players[room_id][player_name] = Player(
            player_name=player_name, current_position=0, cash=2000, saving=0, net_worth=2000, round_played=0
        )
        state.rooms[room_id].roomMember.append(player_name)

    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "broadcast":
                await manager.broadcast(room_id, data)
            elif action == "notify":  # gửi riêng cho một người
                target = data.get("target")
                await manager.send_to_player(room_id, target, data)
            else:
                await manager.broadcast(room_id, {"from": player_name, "data": data})
    except WebSocketDisconnect:
        manager.disconnect(room_id, player_name)
