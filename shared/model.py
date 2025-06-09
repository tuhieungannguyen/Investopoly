from pydantic import BaseModel
from typing import List, Dict, Optional

# Game Manage
class Room(BaseModel):
    roomId: str
    roomMember: List[str]
    status: str

class Player(BaseModel):
    player_name: str
    current_position: int
    cash: float
    stocks: Dict[str, int] = {}
    estates: List[str] = []
    saving: float
    net_worth: float
    round_played: int
    pending_bonus: Optional[List[str]] = [] 

class GameManager(BaseModel):
    current_round: int
    current_player: str
    current_played: int
    leader_board: List[Dict[str, float]]

# Property Manage
class Estate(BaseModel):
    name: str
    position: int
    price: float
    rent_price: float
    owner_name: Optional[str] = None
    home_level: int = 0

class Stock(BaseModel):
    name: str
    owner_list: List[str] = []
    industry: str
    start_price: float
    now_price: float
    service_fee: float
    position: int 
    available_units: int
    max_per_player: int
    
class JailStatus(BaseModel):
    player_name: str
    start_jail: int
    end_jail: int
    status: str

# Action Manage
class SavingRecord(BaseModel):
    name: str
    owner: str
    amount: float
    start_round: int
    end_round: int
    isSuccess: bool

class EventRecord(BaseModel):
    name: str
    start: int
    end: int

class ChanceLog(BaseModel):
    name: str
    owner: str
    round: int

class Transaction(BaseModel):
    from_player: str
    to_player: str
    amount: float
    round: int