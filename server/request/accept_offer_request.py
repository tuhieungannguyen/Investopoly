from pydantic import BaseModel

class AcceptOfferRequest(BaseModel):
    room_id: str
    seller: str
    estate_name: str
    chosen_buyer: str
    price: float