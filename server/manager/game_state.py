import asyncio
import builtins
from random import randint
import random
from typing import Awaitable, Dict, List, Optional
from shared.constants import CHANCE_EVENTS, GO_REWARD, SHOCK_EVENTS, START_MONEY, STOCKS, TILE_MAP,ESTATES, QUIZ_BANK, REWARD_AMOUNT, TAX_AMOUNT
from shared.model import Room, Player, GameManager, Estate, Stock, JailStatus, SavingRecord, EventRecord, ChanceLog, Transaction
from server.manager.event_sink import EventSink, NullEventSink


def print(*args, **kwargs):
    try:
        builtins.print(*args, **kwargs)
    except UnicodeEncodeError:
        safe_args = [
            str(arg).encode("ascii", errors="replace").decode("ascii")
            for arg in args
        ]
        builtins.print(*safe_args, **kwargs)

class GameState:
    
    # Khởi tạo các biến lưu trữ trạng thái game
    def __init__(self, event_sink: Optional[EventSink] = None):
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
        self.event_sink = event_sink or NullEventSink()
        self.manager = self.event_sink
        self.stock_revenue: Dict[str, Dict[str, float]] = {}  

    def _dispatch(self, awaitable: Awaitable[None]):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(awaitable)
        return loop.create_task(awaitable)
        
        
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
        self.stocks[room_id] = {
            stock["name"]: Stock(
                name=stock["name"],
                industry=stock["industry"],
                start_price=stock["start_price"],
                now_price=stock["now_price"],
                service_fee=stock["service_fee"],
                owner_list=[],
                position=stock["position"],
                available_units=stock["available_units"],
                max_per_player=stock["max_per_player"]
            )
            for stock in STOCKS
        }
        self.jails[room_id] = {}
        self.saving_records[room_id] = []
        self.events[room_id] = []
        self.chances[room_id] = []
        self.transactions[room_id] = []
        self.stock_revenue[room_id] = {stock["name"]: 0.0 for stock in STOCKS}


    # ==================================================
    # GAME LOGIC                                      ||
    # ==================================================
    # Hàm để tung xúc xắc, trả về số ngẫu nhiên từ 1 đến 6
    def roll_dice(self) -> int:
        return randint(1, 6)   
 
    
    # Hàm để di chuyển người chơi đến ô mới dựa trên số xúc xắc
    async def move_player(self, room_id: str, player_name: str, steps: int) -> dict:
        
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
            player.net_worth = self.calculate_net_worth(room_id,player_name)

            # Update the leaderboard
            self.update_leaderboard(room_id)
            self._dispatch(self.manager.send_to_player(room_id, player_name, {
            "type": "portfolio_update",
            "portfolio": player.model_dump()
            }))
            self._dispatch(self.manager.broadcast(room_id, {
                    "type": "passed_go",
                    "message": f"{player_name} passed GO and received ${GO_REWARD}",
                    "player": player_name,
                    "amount": GO_REWARD
                }))

        player.current_position = new_position  
        
        # Process tile effects
        if new_position == 10:
            self.send_quiz_question(room_id, player_name)
            await self.manager.broadcast(room_id, {
            "type": "quiz_start",
            "player": player_name,
            "message": f"{player_name} is attempting a quiz!"
        })
        
        await self.handle_tile_18_penalty(room_id, player_name)
             
        # rent estate
        await self.handle_estate_rent(room_id, player_name)        
        await self.charge_stock_service_fee(room_id, player_name)
        
        await self.handle_saving_tile(room_id, player_name)
        saving_result = self.check_saving_maturity(room_id, player_name)
        if saving_result["total_received"] > 0:
            await self.manager.broadcast(room_id, {
                "type": "saving_matured",
                "message": saving_result["message"],
                "player": player_name,
                "amount": saving_result["total_received"],
                "interest": saving_result["interest_earned"]
            })
        shock_result = self.trigger_shock_if_applicable(room_id, player_name)
        if shock_result:
            print(f"⚠️ Shock triggered: {shock_result['description']}")
        event = self.trigger_chance_if_applicable(room_id, player_name)
        
        if event:
            await self.manager.broadcast(room_id, {
                "type": "chance_event",
                "message": f"{player_name} triggered Chance: {event['name']}",
                "player": player_name,
                "event": event
            })

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
        print(f"[Next Turn] Before: Played={manager.current_played}, Total={len(members)}")
        current_index = members.index(manager.current_player)
        next_index = (current_index + 1) % len(members)
        manager.current_player = members[next_index]
        manager.current_played += 1
        
        print(f"[Next Turn] After: Played={manager.current_played}, Round={manager.current_round}")
         
        # Nếu tất cả đã chơi trong round
        if manager.current_played >= len(members):
            print("[Next Turn] 🔄 All played - distribute dividends")
            manager.current_round += 1
            manager.current_played = 0
            self._dispatch(self.distribute_stock_dividends(room_id))  
            self._dispatch(self.check_and_handle_round_completion(room_id))

            
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
            "players": {k: v.model_dump() for k, v in self.players[room_id].items()},
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
            estate_value = sum(e.price for e in self.estates[room_id] if e.owner_name == player.player_name)

            player.net_worth = self.calculate_net_worth(room_id,player.player_name)


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


    async def check_game_end_condition(self, room_id: str) -> bool:
        """
        Kiểm tra điều kiện kết thúc game (15 rounds) và broadcast kết quả
        
        :param room_id: ID của phòng
        :return: True nếu game kết thúc, False nếu chưa
        """
        if room_id not in self.managers:
            return False
        
        manager = self.managers[room_id]
        
        # Kiểm tra nếu đã đủ 15 round
        if manager.current_round >= 15:
            print(f"🎯 Game in room {room_id} has reached 15 rounds. Ending game...")
            
            # Gọi hàm end_game để tính toán kết quả cuối
            final_results = self.end_game(room_id)
            
            # Broadcast thông báo kết thúc game
            await self.manager.broadcast(room_id, {
                "type": "game_ended",
                "message": "🎉 Game has ended after 15 rounds!",
                "final_results": final_results,
                "winner": final_results["leaderboard"][0]["player"] if final_results["leaderboard"] else "No winner",
                "total_rounds": manager.current_round
            })
            
            # Gửi portfolio cuối cùng cho từng người chơi
            for player_name, player in self.players[room_id].items():
                await self.manager.send_to_player(room_id, player_name, {
                    "type": "final_portfolio",
                    "portfolio": player.model_dump(),
                    "rank": next((i+1 for i, p in enumerate(final_results["leaderboard"]) 
                                if p["player"] == player_name), len(final_results["leaderboard"]))
                })
            
            return True
        
        return False

    async def check_and_handle_round_completion(self, room_id: str):
        """
        Kiểm tra khi hoàn thành một round và xử lý logic kết thúc game
        Gọi hàm này sau khi distribute_stock_dividends
        """
        manager = self.managers[room_id]
        
        # Log trạng thái hiện tại
        print(f"📊 Round {manager.current_round} completed in room {room_id}")
        
        # Kiểm tra điều kiện kết thúc
        game_ended = await self.check_game_end_condition(room_id)
        
        if not game_ended:
            # Broadcast thông báo bắt đầu round mới
            await self.manager.broadcast(room_id, {
                "type": "new_round_started",
                "message": f"🔄 Round {manager.current_round} has started!",
                "current_round": manager.current_round,
                "remaining_rounds": 15 - manager.current_round,
                "current_player": manager.current_player
            })
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
    #           SHOCK EVENT 
    # ########################################
    def apply_shock_event(self, room_id: str, player_name: str) -> str:
        import random

        event = random.choice(SHOCK_EVENTS)
        name = event["name"]
        description = event["description"]
        effect_stock = event["effect_stock"]
        effect_estate = event["effect_estate"]

        # Ghi nhận event
        self.events[room_id].append(EventRecord(
            name=name,
            start=self.managers[room_id].current_round,
            end=self.managers[room_id].current_round + 3
        ))

        # Cập nhật cổ phiếu
        updated_stocks = []
        for effect in effect_stock:
            stock_name = effect["name"]
            delta = effect["amount"]

            if stock_name in self.stocks[room_id]:
                stock = self.stocks[room_id][stock_name]
                stock.now_price = max(1, round(stock.now_price * (1 + delta / 100), 2))
                updated_stocks.append({
                    **stock.model_dump(),
                    "base_price": stock.start_price
                })

        # Cập nhật bất động sản
        updated_estates = []
        for estate in self.estates[room_id]:
            changed = False
            if effect_estate.get("value", 0) != 0:
                estate.price = max(1, round(estate.price * (1 + effect_estate["value"] / 100), 2))
                changed = True
            if effect_estate.get("rent", 0) != 0:
                estate.rent_price = max(1, round(estate.rent_price * (1 + effect_estate["rent"] / 100), 2))
                changed = True
            if changed:
                updated_estates.append({
                    "name": estate.name,
                    "price": estate.price,
                    "rent_price": estate.rent_price
                })

        # Cập nhật tài sản ròng và gửi portfolio
        for p in self.players[room_id].values():
            p.net_worth = self.calculate_net_worth(room_id, p.player_name)
            self._dispatch(self.manager.send_to_player(room_id, p.player_name, {
                "type": "portfolio_update",
                "portfolio": p.model_dump()
            }))

        self.update_leaderboard(room_id)

        # Broadcast đến cả phòng
        self._dispatch(self.manager.broadcast(room_id, {
            "type": "shock_event",
            "message": f"⚡ Shock Event: {name} - {description}",
            "stocks": updated_stocks,
            "updated_estates": updated_estates
        }))

        return f"Shock Event Triggered: {name}"

    def trigger_shock_if_applicable(self, room_id: str, player_name: str) -> Optional[dict]:
        player = self.players[room_id][player_name]
        position = player.current_position

        # Giả sử ô shock là ô số 5 và 15
        if position not in [7, 17]:
            return None

        result_msg = self.apply_shock_event(room_id, player_name)
        return {"event": "shock", "description": result_msg}
    
    
    # ########################################
    #          CHANCE EVENT 
    # ########################################
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
            player.net_worth = self.calculate_net_worth(room_id,  player_name)

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
        self._dispatch(self.manager.broadcast(room_id, {
            "type": "estate_purchased",
            "player": player_name,
            "message": message,
            "tile": tile_name,
            "price": estate.price,
            "leaderboard": self.managers[room_id].leader_board
        }))
        
        # send to player
        self._dispatch(self.manager.send_to_player(room_id, player_name, {
        "type": "portfolio_update",
        "portfolio": player.model_dump()
        }))

        return {"success": True, "message": f"Transaction Successful"}
   
    async def handle_estate_rent(self, room_id: str, player_name: str):
        player = self.players[room_id][player_name]
        position = player.current_position
        tile_name = TILE_MAP[position]

        # Tìm bất động sản tại ô đó
        estate = next((e for e in self.estates[room_id] if e.position == position), None)
        if not estate or not estate.owner_name:
            return  # Không phải bất động sản hoặc chưa có chủ

        if estate.owner_name == player_name:
            return  # Người chơi là chủ sở hữu → không cần trả

        rent = estate.rent_price

        # Trừ tiền người chơi
        amount_to_pay = min(player.cash, rent)
        player.cash -= amount_to_pay
        player.net_worth = self.calculate_net_worth(room_id,player_name)

        # Cộng tiền cho chủ mảnh đất
        owner = self.players[room_id][estate.owner_name]
        owner.cash += amount_to_pay
        owner.net_worth += amount_to_pay

        # Cập nhật leaderboard
        self.update_leaderboard(room_id)

        # Gửi thông báo giao dịch cho cả phòng
        message = f"{player_name} paid ${amount_to_pay} rent to {estate.owner_name} for landing on {tile_name}."
        await self.manager.broadcast(room_id, {
            "type": "estate_rent_paid",
            "message": message,
            "payer": player_name,
            "owner": estate.owner_name,
            "amount": amount_to_pay,
            "tile": tile_name
        })

        # Gửi cập nhật leaderboard
        await self.manager.broadcast(room_id, {
            "type": "leaderboard_update",
            "leaderboard": self.managers[room_id].leader_board
        })

        # Gửi cập nhật portfolio cho cả 2
        await self.manager.send_to_player(room_id, player_name, {
            "type": "portfolio_update",
            "portfolio": player.model_dump()
        })

        await self.manager.send_to_player(room_id, estate.owner_name, {
            "type": "portfolio_update",
            "portfolio": owner.model_dump()
        })
       
    def upgrade_estate(self, room_id: str, player_name: str, estate_name: str, upgrade_cost: float):
        player = self.players[room_id][player_name]
        if player.cash >= upgrade_cost:
            player.cash -= upgrade_cost
            for est in self.estates[room_id]:
                if est.name == estate_name:
                    est.home_level += 1
                    break
    
    async def list_estate_for_sale(self, room_id: str, seller: str, estate_name: str, asking_price: float):
    # Kiểm tra sở hữu
        player = self.players[room_id][seller]
        if estate_name not in player.estates:
            return {"success": False, "message": "Bạn không sở hữu bất động sản này."}
        
        estate = next((e for e in self.estates[room_id] if e.name == estate_name), None)
        if not estate:
            return {"success": False, "message": "Không tìm thấy bất động sản."}

        # Broadcast để mọi người đấu giá hoặc mua
        await self.manager.broadcast(room_id, {
            "type": "estate_for_sale",
            "message": f"{seller} is selling {estate_name} for ${asking_price}",
            "seller": seller,
            "estate": estate_name,
            "price": asking_price
        })

        return {"success": True, "message": "Estate listed for sale."}
    
    async def buy_estate_from_player(self, room_id: str, buyer: str, seller: str, estate_name: str, offered_price: float):
        buyer_player = self.players[room_id][buyer]
        seller_player = self.players[room_id][seller]

        if buyer_player.cash < offered_price:
            return {"success": False, "message": "Bạn không đủ tiền để mua."}

        estate = next((e for e in self.estates[room_id] if e.name == estate_name and e.owner_name == seller), None)
        if not estate:
            return {"success": False, "message": "Không tìm thấy bất động sản cần bán."}

        # Giao dịch
        buyer_player.cash -= offered_price
        seller_player.cash += offered_price

        buyer_player.estates.append(estate.name)
        seller_player.estates.remove(estate.name)
        estate.owner_name = buyer

        # Cập nhật tài sản
        buyer_player.net_worth = self.calculate_net_worth(room_id, buyer)
        seller_player.net_worth = self.calculate_net_worth(room_id, seller)
        self.update_leaderboard(room_id)

        # Broadcast kết quả
        await self.manager.broadcast(room_id, {
            "type": "estate_sold",
            "message": f"{seller} sold {estate_name} to {buyer} for ${offered_price}",
            "buyer": buyer,
            "seller": seller,
            "estate": estate_name,
            "price": offered_price
        })

        # Gửi cập nhật portfolio
        for name in [buyer, seller]:
            await self.manager.send_to_player(room_id, name, {
                "type": "portfolio_update",
                "portfolio": self.players[room_id][name].model_dump()
            })

        return {"success": True, "message": f"Bạn đã mua {estate_name} với giá ${offered_price}"}
        
    async def receive_estate_offer(self, room_id, buyer, estate_name, offer_price):
    # Lưu vào biến tạm thời nếu chưa có
        if not hasattr(self, "estate_offers"):
            self.estate_offers = {}
        
        key = (room_id, estate_name)
        if key not in self.estate_offers:
            self.estate_offers[key] = []

        self.estate_offers[key].append({
            "buyer": buyer,
            "price": offer_price
        })

        # Gửi thông báo về cho người bán
        estate = next((e for e in self.estates[room_id] if e.name == estate_name), None)
        seller = estate.owner_name if estate else None
        if seller:
            await self.manager.send_to_player(room_id, seller, {
                "type": "estate_offer_received",
                "estate": estate_name,
                "offers": self.estate_offers[key]
            })

        return {"success": True, "message": "Offer sent to seller."}
    
    async def finalize_estate_transaction(self, room_id, seller, estate_name, chosen_buyer, price):
        key = (room_id, estate_name)
        if key not in self.estate_offers:
            return {"success": False, "message": "Không có offer nào được gửi."}

        offers = self.estate_offers[key]
        offer = next((o for o in offers if o["buyer"] == chosen_buyer), None)

        if not offer:
            return {"success": False, "message": "Không tìm thấy offer từ người mua này."}

        # Giao dịch
        return await self.buy_estate_from_player(room_id, buyer=chosen_buyer, seller=seller,
                                        estate_name=estate_name, offered_price=price)

   
    # ########################################
    #           STOCK
    # ########################################

    def buy_stock(self, room_id: str, player_name: str, quantity: int):
        player = self.players[room_id][player_name]
        current_position = player.current_position

        # Check if standing on a stock tile
        stock = next((s for s in self.stocks[room_id].values() if s.position == current_position), None)
     
        print("stock: ", stock)
        if not stock:
            return {"success": False, "message": "Not on a stock tile."}
        # Check availability
        if stock.available_units < quantity:
             return {"success": False, "message":"Not enough stock available."}

        # Check player's current holdings
        owned = player.stocks.get(stock.name, 0)
        if owned + quantity > stock.max_per_player:
            return {"success": False, "message": f"Cannot own more than {stock.max_per_player} units."}

        total_price = stock.now_price * quantity
        if player.cash < total_price:
            return {"success": False, "message":"Not enough cash."}

        # Deduct money
        player.cash -= total_price

        # Add stock to player's portfolio
        player.stocks[stock.name] = owned + quantity

        # Add player to stock owner list
        if player_name not in stock.owner_list:
            stock.owner_list.append(player_name)

        # Decrease availability
        stock.available_units -= quantity

        # Increase stock price by 2%
        old_price = stock.now_price
        stock.now_price *= 1.02
        # Update net worth
        player.net_worth = self.calculate_net_worth(room_id,player_name)


        # Update leaderboard
        self.update_leaderboard(room_id)

        # Broadcast
        self._dispatch(self.manager.broadcast(room_id, {
            "type": "stock_purchased",
            "message": f"{player_name} bought {quantity} of {stock.name} at ${round(old_price, 2)} each.",
            "stock":  stock.model_dump(),
            "player": player_name
        }))

        # Update portfolio
        self._dispatch(self.manager.send_to_player(room_id, player_name, {
            "type": "portfolio_update",
            "portfolio": player.model_dump()
        }))

        return {"success": True, "message": f"Successfully bought {quantity} of {stock.name}."}
            
    async def charge_stock_service_fee(self, room_id: str, player_name: str):
        player = self.players[room_id][player_name]
        current_pos = player.current_position

        # Tìm cổ phiếu tương ứng với vị trí
        stock = next((s for s in self.stocks[room_id].values() if s.position == current_pos), None)
        if not stock:
            return  # Không ở ô cổ phiếu → bỏ qua

        fee = stock.service_fee
        actual_fee = min(fee, player.cash)
        player.cash -= actual_fee
        player.net_worth = self.calculate_net_worth(room_id,player_name)


        # Lưu doanh thu cổ phiếu
        self.stock_revenue[room_id][stock.name] += actual_fee

        # Broadcast cập nhật
        await self.manager.broadcast(room_id, {
            "type": "stock_service_fee",
            "message": f"{player_name} paid ${actual_fee} service fee for landing on {stock.name} stock tile.",
            "player": player_name,
            "stock": stock.name,
            "amount": actual_fee
        })

        self.update_leaderboard(room_id)
        await self.manager.broadcast(room_id, {
            "type": "leaderboard_update",
            "leaderboard": self.managers[room_id].leader_board
        })
        await self.manager.send_to_player(room_id, player_name, {
            "type": "portfolio_update",
            "portfolio": player.model_dump()
        })
        
        
    async def distribute_stock_dividends(self, room_id: str):
        manager = self.managers[room_id]
        for stock_name, revenue in self.stock_revenue[room_id].items():
            EPS = revenue / 5
            dividend_per_share = EPS * 0.3

            for player_name in self.players[room_id]:
                player = self.players[room_id][player_name]
                shares = player.stocks.get(stock_name, 0)
                if shares > 0:
                    dividend = round(dividend_per_share * shares, 2)
                    player.cash += dividend
                    player.net_worth = self.calculate_net_worth(room_id,player_name)


                    # Gửi portfolio update
                    await self.manager.send_to_player(room_id, player_name, {
                        "type": "portfolio_update",
                        "portfolio": player.model_dump()
                    })

            # Gửi broadcast cổ tức
            await self.manager.broadcast(room_id, {
                "type": "dividend_distributed",
                "message": f"Stock {stock_name}: EPS = ${EPS:.2f}, Dividend = ${dividend_per_share:.2f}"
            })

            self.stock_revenue[room_id][stock_name] = 0  # Reset
        self.update_leaderboard(room_id)


    async def list_stock_for_sale(self, room_id: str, seller: str, stock_name: str, quantity: int, price_per_unit: float):
        player = self.players[room_id][seller]
        if player.stocks.get(stock_name, 0) < quantity:
            return {"success": False, "message": "Bạn không có đủ cổ phiếu để bán."}

        await self.manager.broadcast(room_id, {
            "type": "stock_for_sale",
            "message": f"{seller} is selling {quantity} shares of {stock_name} at ${price_per_unit}/unit",
            "stock": stock_name,
            "seller": seller,
            "quantity": quantity,
            "price_per_unit": price_per_unit
        })

        return {"success": True, "message": "Stock listed for sale."}

    
    async def buy_stock_from_player(self, room_id: str, buyer: str, seller: str, stock_name: str, quantity: int, price_per_unit: float):
        buyer_player = self.players[room_id][buyer]
        seller_player = self.players[room_id][seller]

        total_price = quantity * price_per_unit
        if buyer_player.cash < total_price:
            return {"success": False, "message": "Không đủ tiền để mua cổ phiếu."}
        if seller_player.stocks.get(stock_name, 0) < quantity:
            return {"success": False, "message": "Người bán không có đủ cổ phiếu."}

        # Giao dịch
        buyer_player.cash -= total_price
        seller_player.cash += total_price

        seller_player.stocks[stock_name] -= quantity
        buyer_player.stocks[stock_name] = buyer_player.stocks.get(stock_name, 0) + quantity

        buyer_player.net_worth = self.calculate_net_worth(room_id, buyer)
        seller_player.net_worth = self.calculate_net_worth(room_id, seller)
        self.update_leaderboard(room_id)

        # Broadcast giao dịch
        await self.manager.broadcast(room_id, {
            "type": "stock_sold",
            "message": f"{seller} sold {quantity} of {stock_name} to {buyer} at ${price_per_unit}/unit",
            "stock": stock_name,
            "buyer": buyer,
            "seller": seller,
            "quantity": quantity,
            "price_per_unit": price_per_unit
        })

        for name in [buyer, seller]:
            self._dispatch(self.manager.send_to_player(room_id, name, {
                "type": "portfolio_update",
                "portfolio": self.players[room_id][name].model_dump()
            }))

        return {"success": True, "message": "Stock purchase successful"}

    
    # ########################################
    #           QUIZ
    # ########################################
    def send_quiz_question(self, room_id: str, player_name: str):
        quiz = random.choice(QUIZ_BANK)
        self._dispatch(self.manager.send_to_player(room_id, player_name, {
            "type": "quiz_question",
            "question_id": quiz["id"],
            "question": quiz["question"],
            "options": quiz["options"]
        }))
        return quiz["id"]

# Xử lý câu trả lời từ người chơi
    def handle_quiz_answer(self, room_id: str, player_name: str, question_id: int, answer_index: int) -> bool:
        player = self.players[room_id][player_name]
        quiz = next((q for q in QUIZ_BANK if q["id"] == question_id), None)

        if not quiz:
            return False

        correct = (quiz["correct_index"] == answer_index)

        if correct:
            player.cash += REWARD_AMOUNT
            player.net_worth = self.calculate_net_worth(room_id,player_name)
            result_msg = f"{player_name} answered quiz correctly and earned ${REWARD_AMOUNT}!"
        else:
            result_msg = f"{player_name} answered quiz incorrectly."

        # Cập nhật lại leaderboard
        self.update_leaderboard(room_id)

        # Gửi thông báo đến tất cả người chơi
        self._dispatch(self.manager.broadcast(room_id, {
            "type": "quiz_result",
            "player": player_name,
            "correct": correct,
            "message": result_msg
        }))

        # Cập nhật portfolio người chơi
        self._dispatch(self.manager.send_to_player(room_id, player_name, {
            "type": "portfolio_update",
            "portfolio": player.model_dump()
        }))

        return correct
    
    
    # ########################################
    #           SAVING
    # ########################################

    async def handle_saving_tile(self, room_id: str, player_name: str):
        player = self.players[room_id][player_name]
        current_round = self.managers[room_id].current_round

        # Kiểm tra nếu người chơi đang ở ô 8
        if player.current_position != 8:
            return

        # Gửi yêu cầu popup nhập số tiền tiết kiệm
        await self.manager.send_to_player(room_id, player_name, {
            "type": "saving_prompt",
            "message": "You landed on the Saving tile. How much do you want to save?",
            "max_amount": player.cash,
            "room_id": room_id,
            "player_name": player_name 
        })
        
        
    def process_saving_deposit(self, room_id: str, player_name: str, amount: float) -> dict:
        try:
            player = self.players[room_id][player_name]
            
            # Kiểm tra số tiền hợp lệ
            if amount <= 0:
                return {"success": False, "message": "Amount must be positive"}
            
            if amount > player.cash:
                return {"success": False, "message": "Insufficient cash"}
            
            # Thực hiện gửi tiết kiệm
            player.cash -= amount
            player.saving += amount  # ✅ Cộng vào saving
            
            # Tính lại net worth
            player.net_worth = self.calculate_net_worth(room_id, player_name)
            
            # Lưu record với đủ thông tin
            current_round = self.managers[room_id].current_round
            self.saving_records[room_id].append(
                SavingRecord(
                    owner=player_name,
                    amount=amount,
                    start_round=current_round,
                    end_round=current_round + 3,  # ✅ Thêm end_round
                    isSuccess=True  # ✅ Đang active
                )
            )
            
            # Debug log
            print(f"💰 {player_name} deposited ${amount}. New saving: ${player.saving}, Cash: ${player.cash}")
            
            return {
                "success": True,
                "message": f"Successfully deposited ${amount:.2f} to savings",
                "portfolio": player.model_dump()
            }
            
        except Exception as e:
            print(f"❌ Saving deposit error: {e}")
            return {"success": False, "message": str(e)}

    def withdraw_saving(self, room_id: str, player_name: str) -> dict:
        player = self.players[room_id][player_name]
        current_round = self.managers[room_id].current_round
        total_received = 0
        interest_earned = 0

        matured_records = []
        for record in self.saving_records[room_id]:
            if record.owner == player_name and record.isSuccess:
                matured = current_round >= record.end_round
                amount = record.amount
                if matured:
                    interest = round(amount * 0.04, 2)
                    total = amount + interest
                    interest_earned += interest
                else:
                    total = amount  # no interest
                total_received += total
                record.isSuccess = False
                matured_records.append(record)

        if total_received > 0:
            player.saving = 0
            player.cash += total_received
            player.net_worth = self.calculate_net_worth(room_id, player_name)
            self.update_leaderboard(room_id)

            return {
                "success": True,
                "message": f"Withdrawn ${total_received} (Interest: ${interest_earned})",
                "amount": total_received,
                "interest": interest_earned,
                "portfolio": player.model_dump()
            }
        return {"success": False, "message": "No savings to withdraw."}
        
    def check_saving_maturity(self, room_id: str, player_name: str):
        player = self.players[room_id][player_name]
        current_round = self.managers[room_id].current_round

        matured = []
        remaining = []

        for saving in self.saving_records[room_id]:
            if saving.owner == player_name:
                if current_round >= saving.end_round and saving.isSuccess:
                    matured.append(saving)
                else:
                    remaining.append(saving)

        total_interest = 0
        for s in matured:
            interest = round(s.amount * 0.04 * 3, 2)  # 4%/round * 3 rounds
            total = s.amount + interest
            player.cash += total
            player.saving -= s.amount
            total_interest += interest

        # Xóa các khoản tiết kiệm đã đáo hạn
        self.saving_records[room_id] = remaining + [
            s for s in self.saving_records[room_id]
            if s.owner != player_name or not s.isSuccess or current_round < s.end_round
        ]

        # Cập nhật tài sản ròng và leaderboard
        player.net_worth = self.calculate_net_worth(room_id, player_name)
        self.update_leaderboard(room_id)

        return {
            "total_received": sum(s.amount for s in matured),
            "interest_earned": total_interest,
            "message": f"{player_name} received ${sum(s.amount for s in matured)} + ${total_interest} interest from savings."
        }

    # ########################################
    #           TAX PENALTY
    # ########################################
    async def handle_tile_18_penalty(self, room_id: str, player_name: str):
        player = self.players[room_id][player_name]

        # Nếu người chơi đang ở ô 18
        if player.current_position == 18:
            penalty_amount = TAX_AMOUNT
            player.cash = max(0, player.cash - penalty_amount)
            player.net_worth = self.calculate_net_worth(room_id,player_name)

            # Cập nhật leaderboard
            self.update_leaderboard(room_id)

            # Gửi broadcast thông báo
            await self.manager.broadcast(room_id, {
                "type": "tile_penalty",
                "message": f"{player_name} landed on penalty tile and lost ${penalty_amount}.",
                "player": player_name,
                "amount": penalty_amount
            })

            # Gửi cập nhật portfolio
            await self.manager.send_to_player(room_id, player_name, {
                "type": "portfolio_update",
                "portfolio": player.model_dump()
            })

            # Gửi cập nhật leaderboard
            await self.manager.broadcast(room_id, {
                "type": "leaderboard_update",
                "leaderboard": self.managers[room_id].leader_board
            })
        
    

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


    def calculate_net_worth(self, room_id: str, player_name: str) -> float:
        player = self.players[room_id][player_name]

        # Tính tổng giá trị cổ phiếu
        stock_value = sum(
            self.stocks[room_id][stock_name].now_price * quantity
            for stock_name, quantity in player.stocks.items()
            if stock_name in self.stocks[room_id]
        )

        # Tính tổng giá trị bất động sản sở hữu
        estate_value = sum(
            estate.price
            for estate in self.estates[room_id]
            if estate.owner_name == player_name
        )

        # Tài sản ròng = Tiền mặt + Giá trị cổ phiếu + Bất động sản + Tiết kiệm
        net_worth = player.cash + stock_value + estate_value + player.saving

        return round(net_worth, 2)

    def get_game_progress(self, room_id: str) -> dict:
        """
        Trả về thông tin tiến độ game hiện tại
        """
        if room_id not in self.managers:
            return {"error": "Room not found"}
        
        manager = self.managers[room_id]
        return {
            "current_round": manager.current_round,
            "max_rounds": 15,
            "progress_percentage": (manager.current_round / 15) * 100,
            "remaining_rounds": 15 - manager.current_round,
            "current_player": manager.current_player,
            "players_played_this_round": manager.current_played,
            "total_players": len(self.rooms[room_id].roomMember)
    }


