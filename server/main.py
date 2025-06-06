from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
from typing import Dict, List

from fastapi.responses import JSONResponse

from server.request.create_room import CreateRoomRequest
from server.request.create_room import CreateRoomRequest
from server.request.join_room import JoinRoomRequest
from server.request.roll_dice import RollDiceRequest
from server.request.end_game import EndGameRequest
from server.request.start_game import StartGameRequest

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

    # ✅ Gửi danh sách người chơi hiện tại ngay sau khi kết nối
    await manager.send_to_player(room_id, player_name, {
        "type": "player_joined",
        "player": player_name,
        "players": list(state.players[room_id].keys()),
        "portfolio": state.players[room_id][player_name].model_dump(),  # ✅ sửa đúng người mới
        "leaderboard": [
            {"player": p.player_name, "net_worth": p.net_worth}
            for p in state.players[room_id].values()
        ]
    })

    # ✅ Gửi cho người khác biết có người mới
    for other in state.players[room_id]:
        if other != player_name:
            await manager.send_to_player(room_id, other, {
                "type": "player_joined",
                "player": player_name,
                "players": list(state.players[room_id].keys()),
                "portfolio": state.players[room_id][other].dict(),
                "leaderboard": [
                    {"player": p.player_name, "net_worth": p.net_worth}
                    for p in state.players[room_id].values()
                ]
            })


    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "broadcast":
                await manager.broadcast(room_id, data)
            elif action == "notify":
                target = data.get("target")
                await manager.send_to_player(room_id, target, data)
            else:
                await manager.broadcast(room_id, {"from": player_name, "data": data})
    except WebSocketDisconnect:
        manager.disconnect(room_id, player_name)


@app.post("/join")
async def join_game(request: JoinRoomRequest):
    room_id = request.room_id
    player_name = request.player_name

    state.add_player_to_room(room_id, player_name)

    return {"message": f"{player_name} joined room {room_id}"}


@app.post("/start")
async def start_game(request: StartGameRequest):

    room_id = request.room_id

    state.start_game(room_id)

    await manager.broadcast(room_id, {
        "type": "game_started",
        "round": 1,
        "current_player": state.managers[room_id].current_player
    })

    return {"message": f"Game in room {room_id} started"}

@app.post("/roll")
async def roll_dice(request: RollDiceRequest):
    room_id = request.room_id
    player_name = request.player_name

    # Kiểm tra lượt hợp lệ
    if state.managers[room_id].current_player != player_name:
        return JSONResponse(status_code=403, content={"error": "Not your turn"})

    result = state.process_turn(room_id)

    await manager.broadcast(room_id, {
        "type": "player_rolled",
        "result": result
    })

    state.end_turn(room_id)

    await manager.broadcast(room_id, {
        "type": "next_turn",
        "round": state.managers[room_id].current_round,
        "current_player": state.managers[room_id].current_player
    })

    return {"message": "Turn processed", "result": result}

@app.post("/end")
async def end_game(request: EndGameRequest):

    room_id = request.room_id

    summary = state.end_game(room_id)

    await manager.broadcast(room_id, {
        "type": "game_ended",
        "leaderboard": summary["leaderboard"],
        "summary": summary["summary"]
    })

    return {"message": "Game ended", "results": summary}

@app.get("/status/{room_id}")
async def get_status(room_id: str):
    if room_id not in state.rooms:
        return JSONResponse(status_code=404, content={"error": "Room not found"})
    return state.get_state(room_id)

@app.post("/create")
async def create_room(body: CreateRoomRequest):
    room_id = body.room_id
    host_name = body.host_name

    if room_id in state.rooms:
        return JSONResponse(status_code=400, content={"error": "Room already exists"})

    state.init_room(room_id, [host_name])
    return {"message": f"Room {room_id} created by {host_name}"}