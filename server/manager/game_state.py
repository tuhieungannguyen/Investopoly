import asyncio
from random import randint
from typing import Dict, List, Optional
from shared.constants import CHANCE_EVENTS, GO_REWARD, SHOCK_EVENTS, START_MONEY, TILE_MAP,ESTATES  
from shared.model import Room, Player, GameManager, Estate, Stock, JailStatus, SavingRecord, EventRecord, ChanceLog, Transaction
from server.manager.connection import ConnectionManager

class GameState:
    
    # Khởi tạo các biến lưu trữ trạng thái game
    def __init__(self, manager : ConnectionManager):
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
        self.manager = manager
        
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


    # ==================================================
    # GAME LOGIC                                      ||
    # ==================================================
    # Hàm để tung xúc xắc, trả về số ngẫu nhiên từ 1 đến 6
    def roll_dice(self) -> int:
        return randint(1, 6)   
    
    # Hàm để di chuyển người chơi đến ô mới dựa trên số xúc xắc
    def move_player(self, room_id: str, player_name: str, steps: int) -> dict:
        
        # Lấy vị trí cũ
        player = self.players[room_id][player_name]
        old_position = player.current_position
        
        # tính số bước cần di chuyển 
        new_position = (old_position + steps) % len(TILE_MAP)
        print("step", steps)
        print(f"{player_name} moved from {TILE_MAP[old_position]} to {TILE_MAP[new_position]}")
                
        # Kiểm tra xem nếu có phải là 
        # Check if the player passed the GO tile
        if new_position < old_position:
            player.cash += GO_REWARD  # Add $200 to the player's cash
            player.net_worth = player.cash + sum(
                estate.price for estate in self.estates[room_id] if estate.owner_name  == player_name
            )  # Recalculate net worth

            # Update the leaderboard
            self.update_leaderboard(room_id)
            asyncio.create_task(self.manager.broadcast(room_id, {
                    "type": "passed_go",
                    "message": f"{player_name} passed GO and received ${GO_REWARD}",
                    "player": player_name,
                    "amount": GO_REWARD
                }))

        player.current_position = new_position  
        
        

        # Gửi lại portfolio cập nhật cho chính người chơi
        asyncio.create_task(self.manager.send_to_player(room_id, player_name, {
            "type": "portfolio_update",
            "portfolio": player.dict()
        }))
        
        event = self.trigger_chance_if_applicable(room_id, player_name)
        
        if event:
            from server.manager.connection import ConnectionManager
            message = f"{player_name} triggered Chance: {event['name']}"
            try:
                # Nếu bạn có sẵn self.manager thì dùng, nếu không khởi tạo lại
                if hasattr(self, 'manager'):
                    asyncio.create_task(self.manager.broadcast(room_id, {
                        "type": "chance_event",
                        "message": message,
                        "player": player_name,
                        "event": event
                    }))
                else:
                    # fallback nếu self.manager không tồn tại
                    manager = ConnectionManager()
                    asyncio.create_task(manager.broadcast(room_id, {
                        "type": "chance_event",
                        "message": message,
                        "player": player_name,
                        "event": event
                    }))
            except Exception as e:
                print(f"[Broadcast Error]: {e}")

        tile = TILE_MAP[new_position]
        return {
            "name": tile,
            "owner": self.get_tile_owner(room_id, tile),
            "value": self.get_tile_value(tile)
        }

    def update_leaderboard(self, room_id: str):
        self.managers[room_id].leader_board = sorted(
            [
                {"player": p.player_name, "net_worth": p.net_worth}
                for p in self.players[room_id].values()
            ],
            key=lambda x: x["net_worth"],
            reverse=True
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

    def get_state(self, room_id: str) -> dict:
        return {
            "round": self.managers[room_id].current_round,
            "current_player": self.managers[room_id].current_player,
            "players": {k: v.dict() for k, v in self.players[room_id].items()},
        }
    
    def start_game(self, room_id: str):
        room = self.rooms.get(room_id)
        if room:
            room.status = "playing"
            manager = self.managers[room_id]
            manager.current_round = 1
            manager.current_played = 0
            manager.current_player = room.roomMember[0]

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


    # ==================================================
    # PROPERTY                                        ||                        
    # ==================================================
    # ########################################
    #          HELPER FUNCTION
    # ########################################
    # Hàm để lấy chủ sở hữu của ô bất động sản
    def get_tile_owner(self, room_id: str, tile: str) -> Optional[str]:
        for estate in self.estates[room_id]:
            if estate.name == tile:
                return estate.owner_name
        return None

    def get_tile_value(self, tile: str) -> float:
        """
        Trả về giá trị (price) của ô bất động sản nếu tồn tại, ngược lại trả về 0.
        """
        for estate in ESTATES:
            if estate["name"] == tile:
                return estate["price"]
        return 0.0
   
    # ########################################
    #           EVENT 
    # ########################################
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

    def trigger_chance_if_applicable(self, room_id: str, player_name: str):
        player = self.players[room_id][player_name]
        position = player.current_position

        # Nếu không ở ô 3 hoặc 13 thì bỏ qua
        if position not in [3, 13]:
            return None

        import random
        event = random.choice(CHANCE_EVENTS)
        amount = event["amount"]
        event_type = event["type"]

        print(f"🎲 Chance triggered for {player_name}: {event['name']}")

        
        if  amount == 0:
            # Lưu trạng thái xử lý sau
            if not hasattr(player, "pending_bonus"):
                player.pending_bonus = []
            player.pending_bonus.append(event["name"])
            print(f"   🔖 Bonus effect '{event['name']}' stored for later.")
        elif event_type == "plus":
            player.cash += amount
            player.net_worth += amount
            print(f"   +${amount} added.")
        elif event_type == "minus":
            deduction = min(player.cash, amount)
            player.cash -= deduction
            player.net_worth = max(0, player.net_worth - amount)
            print(f"   -${amount} deducted.")
        
        # Lưu vào log sự kiện
        self.chances[room_id].append(
            ChanceLog(
                name=event["name"],
                owner=player_name,
                round=self.managers[room_id].current_round
            )
        )

        # Cập nhật leaderboard sau thay đổi tài sản
        self.update_leaderboard(room_id)

        return event

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
    
    # ########################################
    #           JAIL
    # ########################################

    def put_in_jail(self, room_id: str, player_name: str):
        jail_status = JailStatus(
            player_name=player_name,
            start_jail=self.managers[room_id].current_round,
            end_jail=self.managers[room_id].current_round + 3,
            status=True
        )
        self.jails[room_id][player_name] = jail_status

    # ########################################
    #           ESTATE
    # ########################################
    def buy_estate(self, room_id: str, player_name: str):
        player = self.players[room_id][player_name]
        print(f"{player.current_position} position")
        
        position = player.current_position
        tile_name = TILE_MAP[position]
        print(f"{tile_name} tile_name")


        # Tìm estate đúng ô người chơi đang đứng
        estate = next((e for e in self.estates[room_id] if e.name == tile_name), None)
        print(f"{estate} - estate")
        if not estate:
            return {"success": False, "message": f"{tile_name} không phải bất động sản."}
        if estate.owner_name is not None:
            return {"success": False, "message": f"{tile_name} đã có chủ sở hữu."}
        if player.cash < estate.price:
            return {"success": False, "message": "Không đủ tiền để mua bất động sản."}

        # Cập nhật sở hữu và tài sản
        player.cash -= estate.price
        estate.owner_name  = player_name
        player.estates.append(estate.name)

        
        # broadcast to all players
        self.update_leaderboard(room_id)
        message = f"{player_name} has purchased {tile_name} for ${estate.price}."
        asyncio.create_task(self.manager.broadcast(room_id, {
            "type": "estate_purchased",
            "player": player_name,
            "message": message,
            "tile": tile_name,
            "price": estate.price,
            "leaderboard": self.managers[room_id].leader_board
        }))
        
        # send to player
        asyncio.create_task(self.manager.send_to_player(room_id, player_name, {
        "type": "portfolio_update",
        "portfolio": player.dict()
        }))

        return {"success": True, "message": f"Transaction Successful"}
   
    def upgrade_estate(self, room_id: str, player_name: str, estate_name: str, upgrade_cost: float):
        player = self.players[room_id][player_name]
        if player.cash >= upgrade_cost:
            player.cash -= upgrade_cost
            for est in self.estates[room_id]:
                if est.name == estate_name:
                    est.home_level += 1
                    break

    # ########################################
    #           STOCK
    # ########################################

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

    # ########################################
    #           SAVING
    # ########################################

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

    # ########################################
    #           UNUSE
    # ########################################
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
    
# #######################################
#        STATISTICS
# #######################################
    def print_game_state(self, room_id: str):
        if room_id not in self.rooms:
            print(f"❌ Room {room_id} không tồn tại.")
            return

        print(f"\n🧾 --- TRẠNG THÁI PHÒNG '{room_id}' ---")
        room = self.rooms[room_id]
        print(f"- Trạng thái phòng: {room.status}")
        print(f"- Thành viên: {', '.join(room.roomMember)}")

        manager = self.managers[room_id]
        print(f"- Vòng hiện tại: {manager.current_round}")
        print(f"- Người đang chơi: {manager.current_player}")
        print(f"- Số người đã chơi vòng này: {manager.current_played}")

        print("\n👤 --- DANH SÁCH NGƯỜI CHƠI ---")
        for player in self.players[room_id].values():
            print(f"• {player.player_name}:")
            print(f"   - Vị trí: {TILE_MAP[player.current_position]} ({player.current_position})")
            print(f"   - Cash: ${player.cash}")
            print(f"   - Saving: ${player.saving}")
            print(f"   - Net Worth: ${player.net_worth}")
            print(f"   - Đã chơi vòng: {player.round_played}")
            print(f"   - Cổ phiếu: {player.stocks if player.stocks else 'Không có'}")
            print(f"   - BĐS sở hữu: {player.estates if player.estates else 'Không có'}")

        print("\n🏠 --- DANH SÁCH BẤT ĐỘNG SẢN ---")
        for est in self.estates[room_id]:
            print(f"• {est.name} (vị trí {est.position}): giá ${est.price}, thuê ${est.rent_price}, chủ: {est.owner_name or 'chưa có'}")

        print("\n📈 --- CỔ PHIẾU ---")
        if self.stocks[room_id]:
            for stock in self.stocks[room_id].values():
                print(f"• {stock.name}: ${stock.now_price}, sở hữu bởi {', '.join(stock.owner_list)}")
        else:
            print("Chưa có cổ phiếu nào được giao dịch.")

        print("\n📊 --- BẢNG XẾP HẠNG ---")
        for i, entry in enumerate(manager.leader_board, 1):
            print(f"{i}. {entry['player']} - Net Worth: ${entry['net_worth']}")

        print("\n📄 --- GHI NHỚ GIAO DỊCH ---")
        for txn in self.transactions[room_id]:
            print(f"• Round {txn.round}: {txn.from_player} → {txn.to_player} ${txn.amount}")
