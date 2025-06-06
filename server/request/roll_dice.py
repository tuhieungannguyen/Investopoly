from pydantic import BaseModel

class RollDiceRequest(BaseModel):
    room_id: str
    player_name: str
