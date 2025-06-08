from openai import BaseModel


class BuyEstateRequest(BaseModel):
    room_id: str
    player_name: str