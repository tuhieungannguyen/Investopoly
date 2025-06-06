from pydantic import BaseModel

class JoinRoomRequest(BaseModel):
    room_id: str
    player_name: str
