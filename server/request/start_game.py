from pydantic import BaseModel

class StartGameRequest(BaseModel):
    room_id: str
