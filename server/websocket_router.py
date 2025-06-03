from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
import json

from server.game_controller import handle_action

router = APIRouter()
active_connections: Dict[str, List[WebSocket]] = {}

@router.websocket("/ws/{room_id}/{player_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, player_id: str):
    await websocket.accept()
    print(f"[WS] {player_id} connected to room {room_id}")

    if room_id not in active_connections:
        active_connections[room_id] = []
    active_connections[room_id].append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            print(f"[WS][{room_id}] From {player_id}:", message)

            action = message.get("action")
            payload = message.get("payload", {})

            # Gọi controller xử lý
            response = await handle_action(room_id, player_id, action, payload)

            # Gửi kết quả trả về cho tất cả trong phòng
            await broadcast(room_id, response)

    except WebSocketDisconnect:
        print(f"[WS] {player_id} disconnected from room {room_id}")
        active_connections[room_id].remove(websocket)

async def broadcast(room_id: str, message: dict):
    if room_id in active_connections:
        text = json.dumps(message)
        for ws in active_connections[room_id]:
            await ws.send_text(text)
