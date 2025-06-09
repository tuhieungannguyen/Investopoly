from fastapi import WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_rooms = {}  # room_id: {"players": [], "sockets": {player_name: websocket}}

    async def connect(self, room_id: str, player_name: str, websocket: WebSocket):
        await websocket.accept()
        if room_id not in self.active_rooms:
            self.active_rooms[room_id] = {"players": [], "sockets": {}}
        self.active_rooms[room_id]["players"].append(player_name)
        self.active_rooms[room_id]["sockets"][player_name] = websocket

    def disconnect(self, room_id: str, player_name: str):
        try:
            if room_id in self.active_rooms and player_name in self.active_rooms[room_id]["sockets"]:
                del self.active_rooms[room_id]["sockets"][player_name]

                # Nếu phòng không còn người → có thể cleanup
                if not self.active_rooms[room_id]["sockets"]:
                    del self.active_rooms[room_id]
        except Exception as e:
            print(f"[Disconnect Error] player {player_name} in room {room_id}: {e}")

    async def broadcast(self, room_id: str, message: dict):
        if room_id in self.active_rooms:
            for ws in self.active_rooms[room_id]["sockets"].values():
                await ws.send_json(message)

    async def send_to_player(self, room_id: str, player_name: str, message: dict):
        if room_id in self.active_rooms and player_name in self.active_rooms[room_id]["sockets"]:
            await self.active_rooms[room_id]["sockets"][player_name].send_json(message)
