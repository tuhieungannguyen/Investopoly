from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
from typing import Dict, List

from fastapi.responses import JSONResponse

from server.request.buy_estate import BuyEstateRequest
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
        "players": [
            {
                "player_name": p.player_name,
                "current_position": p.current_position
            } for p in state.players[room_id].values()
        ],
        "portfolio": state.players[room_id][player_name].model_dump(),
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
                "players": [
                    {
                        "player_name": p.player_name,
                        "current_position": p.current_position
                    } for p in state.players[room_id].values()
                ],
                "portfolio": state.players[room_id][other].model_dump(),
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

    # Broadcast game start notification
    await manager.broadcast(room_id, {
        "type": "game_started",
        "message": "Game has started!",
        "round": 1,
        "current_player": state.managers[room_id].current_player
    })

    return {"message": f"Game in room {room_id} started"}

@app.post("/roll")
async def roll_dice(request: RollDiceRequest):
    room_id = request.room_id
    player_name = request.player_name

    # Check if the room exists
    if room_id not in state.managers:
        return JSONResponse(status_code=404, content={"error": "Room not found"})

    # Check if it's the player's turn
    if state.managers[room_id].current_player != player_name:
        return JSONResponse(status_code=403, content={"error": "Not your turn"})

    # Check if the player has already rolled this round
    if state.players[room_id][player_name].round_played >= state.managers[room_id].current_round:
        return JSONResponse(status_code=403, content={"error": "You have already rolled this round"})

    # Roll the dice
    dice_roll = state.roll_dice()

    # Update player position
    tile = state.move_player(room_id, player_name, dice_roll)

    # Broadcast updated leaderboard
    await manager.broadcast(room_id, {
        "type": "leaderboard_update",
        "leaderboard": state.managers[room_id].leader_board
    })

    # Process tile effects
    owner = state.get_tile_owner(room_id, tile)
    transaction = None
    if owner and owner != player_name:
        rent = state.get_tile_value(room_id, tile) * 0.2
        state.players[room_id][player_name].cash -= rent
        state.players[room_id][owner].cash += rent
        transaction = Transaction(
            amount=rent,
            description=f"Player {player_name} paid {rent} to {owner} for {tile}"
        )
        state.transactions[room_id].append(transaction)

    # Check if the player can buy the estate or stock
    can_buy_estate = not owner and state.get_tile_value(tile["name"]) > 0
    can_buy_stock = tile["name"] in state.stocks[room_id] and state.stocks[room_id][tile["name"]].available > 0

    # Mark the player as having played this round
    state.players[room_id][player_name].round_played = state.managers[room_id].current_round

    # Broadcast roll result and updated position
    await manager.broadcast(room_id, {
        "type": "player_rolled",
        "player": player_name,
        "dice": dice_roll,
        "tile": tile,
        "message": f"Player {player_name} rolled a {dice_roll}",
        "can_buy_estate": can_buy_estate,
        "can_buy_stock": can_buy_stock
    })

    # Broadcast updated positions
    await manager.broadcast(room_id, {
        "type": "update_positions",
        "players": [
            {
                "player_name": p.player_name,
                "current_position": p.current_position
            } for p in state.players[room_id].values()
        ]
    })

    # Return tile information to the player
    return {
        "message": "Roll processed",
        "dice": dice_roll,
        "tile": tile,
        "transaction": transaction.model_dump() if transaction else None,
        "can_buy_estate": can_buy_estate,
        "can_buy_stock": can_buy_stock
    }

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
    
    state.print_game_state(room_id)
    return state.get_state(room_id)

@app.get("/debug/print_state/{room_id}")
async def debug_print_state(room_id: str):
    if room_id not in state.rooms:
        return JSONResponse(status_code=404, content={"error": "Room not found"})

    import io
    import sys

    # Redirect stdout để capture nội dung in
    old_stdout = sys.stdout
    buffer = io.StringIO()
    sys.stdout = buffer

    try:
        state.print_game_state(room_id)
    finally:
        sys.stdout = old_stdout

    output = buffer.getvalue()
    return {"room_id": room_id, "state": output}

@app.post("/create")
async def create_room(body: CreateRoomRequest):
    room_id = body.room_id
    host_name = body.host_name

    if room_id in state.rooms:
        return JSONResponse(status_code=400, content={"error": "Room already exists"})

    state.init_room(room_id, [host_name])
    return {"message": f"Room {room_id} created by {host_name}"}

@app.post("/end_turn")
async def end_turn(request: Request):
    body = await request.json()
    room_id = body["room_id"]
    player_name = body["player_name"]

    # Check if it's the player's turn
    if state.managers[room_id].current_player != player_name:
        return JSONResponse(status_code=403, content={"error": "Not your turn"})

    # Move to the next player's turn
    state.next_turn(room_id)

    # Broadcast the next turn
    await manager.broadcast(room_id, {
        "type": "next_turn",
        "round": state.managers[room_id].current_round,
        "current_player": state.managers[room_id].current_player,
        "message": f"It's {state.managers[room_id].current_player}'s turn"
    })

    return {"message": "Turn ended"}

@app.post("/buy_estate")
async def buy_estate(body: BuyEstateRequest):

    room_id = body.room_id
    player_name = body.player_name

    current_position = state.get_player_position(room_id, player_name)
    # Process the purchase
    result = state.buy_estate(room_id, player_name)

    if result["success"]:
        # Broadcast the purchase to other players
        await manager.broadcast(room_id, {
            "type": "estate_purchased",
            "player": player_name,
            "message": result["message"],
            "leaderboard": state.managers[room_id].leader_board
        })

    return result