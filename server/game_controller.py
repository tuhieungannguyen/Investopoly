from server.state_store import get_room
from server.models.player import Player
from server.logic.game import process_turn
from server.models.room import Room

# Dictionary lưu các phòng chơi đang hoạt động
rooms = {}  # room_id -> Room instance

def get_room(room_id):
    if room_id not in rooms:
        rooms[room_id] = Room(room_id)
    return rooms[room_id]

async def handle_action(room_id: str, player_id: str, action: str, payload: dict):
    room = get_room(room_id)

    # Nếu người chơi chưa có trong room, tạo mới
    if player_id not in room.players:
        room.players[player_id] = Player(player_id, name=f"Player {player_id}")
        room.turn_order.append(player_id)

    player = room.players[player_id]

    # Xử lý từng hành động
    if action == "roll_dice":
        result = process_turn(player, room, room.board)
        return {
            "type": "turn_result",
            "player_id": player_id,
            "payload": result
        }

    elif action == "end_turn":
        next_player = room.next_turn()
        return {
            "type": "next_turn",
            "current_turn": next_player
        }

    else:
        return {
            "type": "error",
            "message": f"Unknown action: {action}"
        }
