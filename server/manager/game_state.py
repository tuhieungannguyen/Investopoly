from random import randint
from typing import Dict, List, Optional
from shared.constants import CHANCE_EVENTS, GO_REWARD, SHOCK_EVENTS, START_MONEY, TILE_MAP,ESTATES  
from shared.model import Room, Player, GameManager, Estate, Stock, JailStatus, SavingRecord, EventRecord, ChanceLog, Transaction

class GameState:
    
    # Khởi tạo các biến lưu trữ trạng thái game
    def __init__(self):
        self.rooms: Dict[str, Room] = {}
        self.players: Dict[str, Dict[str, Player]] = {}
        self.managers: Dict[str, GameManager] = {}
        self.estates: Dict[str, List[Estate]] = {}
        self.stocks: Dict[str, Dict[str, Stock]] = {}
        self.jails: Dict[str, Dict[str, JailStatus]] = {}
        self.saving_records: Dict[str, List[SavingRecord]] = {}
        self.events: Dict[str, List[EventRecord]] = {}
        self.chances: Dict[str, List[ChanceLog]] = {}
        self.transactions: Dict[str, List[Transaction]] = {}
        
        

    def init_room(self, room_id: str, members: List[str]):
        self.rooms[room_id] = Room(roomId=room_id, roomMember=members, status="waiting")
        self.players[room_id] = {
            name: Player(player_name=name, current_position=0, cash=START_MONEY, saving=0, net_worth=START_MONEY, round_played=0)
            for name in members
        }
        self.managers[room_id] = GameManager(
            current_round=1,
            current_player=members[0],
            current_played=0,
            leader_board=[]
        )
        self.estates[room_id] = [
        Estate(
        name=e["name"],
        owner=None,
        value=e["price"],
        position=e["position"],
        price=e["price"],
        rent_price=e["rent_price"]
        )
            for e in ESTATES
        ]
        self.stocks[room_id] = {}
        self.jails[room_id] = {}
        self.saving_records[room_id] = []
        self.events[room_id] = []
        self.chances[room_id] = []
        self.transactions[room_id] = []

    # Hàm để tung xúc xắc, trả về số ngẫu nhiên từ 1 đến 6
    def roll_dice(self) -> int:
        return randint(1, 6)
    
    # Hàm để di chuyển người chơi đến ô mới dựa trên số xúc xắc
    def move_player(self, room_id: str, player_name: str, steps: int) -> dict:
        player = self.players[room_id][player_name]
        old_position = player.current_position
        new_position = (old_position + steps) % len(TILE_MAP)

        # Check if the player passed the GO tile
        if new_position < old_position:
            player.cash += GO_REWARD  # Add $200 to the player's cash
            player.net_worth = player.cash + sum(
                estate.value for estate in self.estates[room_id] if estate.owner == player_name
            )  # Recalculate net worth

            # Update the leaderboard
            self.update_leaderboard(room_id)

        player.current_position = new_position

        tile = TILE_MAP[new_position]
        return {
            "name": tile,
            "owner": self.get_tile_owner(room_id, tile),
            "value": self.get_tile_value(tile)
        }

    # Hàm để lấy chủ sở hữu của ô bất động sản
    def get_tile_owner(self, room_id: str, tile: str) -> Optional[str]:
        for estate in self.estates[room_id]:
            if estate.name == tile:
                return estate.owner
        return None

    def get_tile_value(self, tile: str) -> float:
        """
        Trả về giá trị (price) của ô bất động sản nếu tồn tại, ngược lại trả về 0.
        """
        for estate in ESTATES:
            if estate["name"] == tile:
                return estate["price"]
        return 0.0
   
    # Random shock event
    def apply_shock_event(self, room_id: str, player_name: str) -> str:
        import random
        event = random.choice(SHOCK_EVENTS)
        self.events[room_id].append(EventRecord(name=event["name"], start=event["start"], end=event["end"]))
        # Cập nhật giá trị cổ phiếu, bất động sản dựa trên event
        return f"Sự kiện shock: {event['name']}"


    # Apply chance event
    def apply_chance_event(self, room_id: str, player_name: str) -> str:
        import random
        player = self.players[room_id][player_name]
        chance = random.choice(CHANCE_EVENTS)
        if chance["type"] == "plus":
            player.cash += chance["amount"]
        elif chance["type"] == "minus":
            player.cash = max(0, player.cash - chance["amount"])
        self.chances[room_id].append(ChanceLog(name=chance["name"], owner=player_name, round=self.managers[room_id].current_round))
        return f"Cơ hội: {chance['name']}"

    # Vao tu 
    def put_in_jail(self, room_id: str, player_name: str):
        jail_status = JailStatus(
            player_name=player_name,
            start_jail=self.managers[room_id].current_round,
            end_jail=self.managers[room_id].current_round + 3,
            status=True
        )
        self.jails[room_id][player_name] = jail_status

    # 
    def buy_estate(self, room_id: str, player_name: str):
        player = self.players[room_id][player_name]
        position = player.current_position
        tile_name = TILE_MAP[position]

        # Tìm estate đúng ô người chơi đang đứng
        estate = next((e for e in self.estates[room_id] if e.name == tile_name), None)

        if not estate:
            return {"success": False, "message": f"{tile_name} không phải bất động sản."}
        if estate.owner is not None:
            return {"success": False, "message": f"{tile_name} đã có chủ sở hữu."}
        if player.cash < estate.price:
            return {"success": False, "message": "Không đủ tiền để mua bất động sản."}

        # Cập nhật sở hữu và tài sản
        player.cash -= estate.price
        estate.owner = player_name
        player.net_worth += estate.price

        self.update_leaderboard(room_id)

        return {"success": True, "message": f"{player_name} đã mua {tile_name} với giá {estate.price}$."}


    def update_leaderboard(self, room_id: str):
        self.managers[room_id].leader_board = sorted(
            [
                {"player": p.player_name, "net_worth": p.net_worth}
                for p in self.players[room_id].values()
            ],
            key=lambda x: x["net_worth"],
            reverse=True
        )

    def upgrade_estate(self, room_id: str, player_name: str, estate_name: str, upgrade_cost: float):
        player = self.players[room_id][player_name]
        if player.cash >= upgrade_cost:
            player.cash -= upgrade_cost
            for est in self.estates[room_id]:
                if est.name == estate_name:
                    est.home_level += 1
                    break

    def buy_stock(self, room_id: str, player_name: str, stock_name: str, amount: int):
        stock = self.stocks[room_id][stock_name]
        player = self.players[room_id][player_name]
        total_price = stock.now_price * amount
        if player.cash >= total_price:
            player.cash -= total_price
            player.stocks[stock_name] = player.stocks.get(stock_name, 0) + amount
            stock.owner_list.append(player_name)
            stock.now_price *= 1.02  # tăng giá 2%
            self.transactions[room_id].append(Transaction(from_=player_name, to="market", amount=total_price, round=self.managers[room_id].current_round))

    def save_money(self, room_id: str, player_name: str, amount: float):
        player = self.players[room_id][player_name]
        if player.cash >= amount:
            player.cash -= amount
            player.saving += amount
            self.saving_records[room_id].append(
                SavingRecord(
                    name=f"saving-{player_name}",
                    owner=player_name,
                    amount=amount,
                    start_round=self.managers[room_id].current_round,
                    end_round=self.managers[room_id].current_round + 3,
                    isSuccess=True
                )
            )

    def next_turn(self, room_id: str):
        members = self.rooms[room_id].roomMember
        manager = self.managers[room_id]
        current_index = members.index(manager.current_player)
        next_index = (current_index + 1) % len(members)
        manager.current_player = members[next_index]
        manager.current_played += 1

        # Nếu tất cả đã chơi trong round
        if manager.current_played >= len(members):
            manager.current_round += 1
            manager.current_played = 0

    def get_state(self, room_id: str) -> dict:
        return {
            "round": self.managers[room_id].current_round,
            "current_player": self.managers[room_id].current_player,
            "players": {k: v.dict() for k, v in self.players[room_id].items()},
        }
    
    def add_player_to_room(self, room_id: str, player_name: str):
        if room_id not in self.rooms:
            self.init_room(room_id, [player_name])
        elif player_name not in self.players[room_id]:
            self.players[room_id][player_name] = Player(
                player_name=player_name,
                current_position=0,
                cash=START_MONEY,
                saving=0,
                net_worth=START_MONEY,
                round_played=0
            )
            self.rooms[room_id].roomMember.append(player_name)

    def start_game(self, room_id: str):
        room = self.rooms.get(room_id)
        if room:
            room.status = "playing"
            manager = self.managers[room_id]
            manager.current_round = 1
            manager.current_played = 0
            manager.current_player = room.roomMember[0]

    def process_turn(self, room_id: str) -> dict:
        """
        Hàm này có thể được gọi khi người chơi click 'Roll Dice'.
        Nó xử lý: tung xúc xắc → di chuyển → xử lý ô hiện tại.
        """
        current_player = self.managers[room_id].current_player
        dice = self.roll_dice()
        tile = self.move_player(room_id, current_player, dice)
        result = self.apply_tile_effect(room_id, current_player, tile)
        # self.players[room_id][current_player].round_played += 1
        return {
            "player": current_player,
            "dice": dice,
            "tile": tile,
            "effect": result
        }

    def end_turn(self, room_id: str):
        """Gọi sau khi người chơi kết thúc lượt để sang người kế tiếp."""
        manager = self.managers[room_id]
        players = self.rooms[room_id].roomMember
        idx = players.index(manager.current_player)
        next_idx = (idx + 1) % len(players)
        manager.current_player = players[next_idx]
        manager.current_played += 1

        if manager.current_played >= len(players):
            manager.current_round += 1
            manager.current_played = 0

    def end_game(self, room_id: str) -> dict:
        
        """
        Kết thúc ván chơi → tính tài sản ròng → xếp hạng người chơi.
        """
        final_scores = []
        for player in self.players[room_id].values():
            # Tính tài sản ròng = cash + saving + cổ phiếu + bất động sản (tạm tính)
            stock_value = sum([
                self.stocks[room_id][name].now_price * qty
                for name, qty in player.stocks.items()
                if name in self.stocks[room_id]
            ])
            estate_value = sum(e.value for e in self.estates[room_id] if e.owner == player.player_name)

            player.net_worth = round(player.cash + player.saving + stock_value + estate_value, 2)

            final_scores.append({
                "player": player.player_name,
                "net_worth": player.net_worth,
                "cash": player.cash,
                "saving": player.saving,
                "stock_value": stock_value,
                "estate_count": len(player.estates)
            })

        leaderboard = sorted(final_scores, key=lambda x: x["net_worth"], reverse=True)
        self.managers[room_id].leader_board = leaderboard
        self.rooms[room_id].status = "finished"

        return {
            "leaderboard": leaderboard,
            "summary": final_scores
        }

    def get_player_position(self, room_id: str, player_name: str) -> Optional[int]:
        """
        Trả về vị trí hiện tại của người chơi trong phòng.
        
        :param room_id: ID của phòng
        :param player_name: Tên người chơi
        :return: Vị trí trên bản đồ (0-based index), hoặc None nếu không tìm thấy
        """
        if room_id in self.players and player_name in self.players[room_id]:
            return self.players[room_id][player_name].current_position
        return None
    def apply_tile_effect(self, room_id: str, player_name: str, tile: str) -> Optional[str]:
        """
        This function is simplified. You'll need to implement full detail per tile type.
        """
        if "Shock" in tile:
            return self.apply_shock_event(room_id, player_name)
        elif "Chance" in tile:
            return self.apply_chance_event(room_id, player_name)
        elif "Jail" in tile:
            self.put_in_jail(room_id, player_name)
            return f"{player_name} vào tù"
        return None
