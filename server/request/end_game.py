from pydantic import BaseModel

class EndGameRequest(BaseModel):
    room_id: str
