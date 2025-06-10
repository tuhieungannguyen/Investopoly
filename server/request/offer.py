from pydantic import BaseModel

class OfferRequest(BaseModel):
    room_id: str
    buyer: str
    estate_name: str
    offer_price: float
