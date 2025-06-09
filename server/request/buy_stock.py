from openai import BaseModel
class BuyStockRequest(BaseModel):
    room_id: str
    player_name: str
    amount: int