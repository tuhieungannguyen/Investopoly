from fastapi import Body, FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
from typing import Dict, List

from fastapi.responses import JSONResponse

from server.request.buy_estate import BuyEstateRequest
from server.request.buy_stock import BuyStockRequest
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
state = GameState(manager)

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
                
            elif action == "saving_deposit":
                room_id = data["room_id"]
                player_name = data["player_name"]
                amount = data["amount"]

                result = state.process_saving_deposit(room_id, player_name, amount)

                # Gửi cập nhật đến player
                await manager.send_to_player(room_id, player_name, {
                    "type": "saving_result",
                    "success": result["success"],
                    "message": result["message"],
                    "portfolio": result.get("portfolio", {})
                })

                # Gửi leaderboard update nếu thành công
                if result["success"]:
                    await manager.broadcast(room_id, {
                        "type": "leaderboard_update",
                        "leaderboard": state.managers[room_id].leader_board
                    })
            elif action == "saving_deposit":
                room_id = data["room_id"]
                player_name = data["player_name"]
                amount = float(data["amount"])
                result = state.process_saving_deposit(room_id, player_name, amount)
                await connection.send_json({
                    "type": "saving_deposit_result",
                    "success": result["success"],
                    "message": result["message"],
                    "portfolio": result.get("portfolio", {})
                })

            elif action == "saving_withdraw":
                room_id = data["room_id"]
                player_name = data["player_name"]
                result = state.withdraw_saving(room_id, player_name)
                await connection.send_json({
                    "type": "saving_withdraw_result",
                    "success": result["success"],
                    "message": result["message"],
                    "amount": result.get("amount", 0),
                    "interest": result.get("interest", 0),
                    "portfolio": result.get("portfolio", {})
                })

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
    tile = await state.move_player(room_id, player_name, dice_roll)

    # Broadcast updated leaderboard
    await manager.broadcast(room_id, {
        "type": "leaderboard_update",
        "leaderboard": state.managers[room_id].leader_board
    })

    # Process tile effects
    owner = state.get_tile_owner(room_id, tile)
    
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


@app.post("/quiz/answer")
async def submit_quiz_answer(
    room_id: str = Body(...),
    player_name: str = Body(...),
    question_id: int = Body(...),
    answer_index: int = Body(...)
):
    correct = state.handle_quiz_answer(room_id, player_name, question_id, answer_index)
    return {"correct": correct}


@app.post("/buy_stock")
async def buy_stock_api(request: BuyStockRequest):
    room_id = request.room_id
    player_name = request.player_name
    amount = request.amount

    
    print(room_id, player_name, amount)
    
    # kiểm tra room và player tồn tại
    if room_id not in state.players or player_name not in state.players[room_id]:
        raise HTTPException(status_code=404, detail="Room or player not found.")

    result = state.buy_stock(room_id, player_name, amount)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return {"message": result["message"]}


@app.post("/saving")
async def deposit_saving(
    room_id: str = Body(...),
    player_name: str = Body(...),
    amount: float = Body(...)
):
    # Kiểm tra phòng và người chơi
    if room_id not in state.players or player_name not in state.players[room_id]:
        raise HTTPException(status_code=404, detail="Room or player not found.")

    # Xử lý gửi tiết kiệm
    result = state.process_saving_deposit(room_id, player_name, amount)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    # Gửi cập nhật portfolio cho người chơi
    await manager.send_to_player(room_id, player_name, {
        "type": "portfolio_update",
        "portfolio": result["portfolio"]
    })

    # Cập nhật bảng xếp hạng cho cả phòng
    await manager.broadcast(room_id, {
        "type": "leaderboard_update",
        "leaderboard": state.managers[room_id].leader_board
    })

    return {"message": result["message"]}


@app.post("/api/saving/deposit")
async def deposit_saving(room_id: str, player_name: str, amount: float):
    result = state.process_saving_deposit(room_id, player_name, amount)
    if result["success"]:
        await state.manager.send_to_player(room_id, player_name, {
            "type": "portfolio_update",
            "portfolio": result["portfolio"]
        })
    return result
