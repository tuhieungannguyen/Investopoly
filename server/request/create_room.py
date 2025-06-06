from openai import BaseModel


class CreateRoomRequest(BaseModel):
    room_id: str
    host_name: str