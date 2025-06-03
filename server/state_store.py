from server.models.room import Room

# Dictionary lưu trữ toàn bộ room
rooms = {}  # room_id -> Room instance

def get_room(room_id):
    if room_id not in rooms:
        rooms[room_id] = Room(room_id)
    return rooms[room_id]