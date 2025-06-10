from pydantic import BaseModel

class SavingDepositRequest(BaseModel):
    room_id: str
    player_name: str
    amount: float