class ClientHandler:
    def __init__(self, state_manager):
        self.state_manager = state_manager

    def handle(self, message):
        msg_type = message.get("type")

        if msg_type == "turn_result":
            player_id = message["player_id"]
            result = message["payload"]
            print(f"[TURN] Player {player_id} rolled {result['dice']} → tile {result['tile_name']} ({result['tile_type']})")
            print(f"[EVENT] {result['event_msg']} | Net Worth: {result['net_worth']}")
            self.state_manager.update_player(player_id, result)

        elif msg_type == "next_turn":
            current_turn = message["current_turn"]
            print(f"[TURN] Now it's {current_turn}'s turn.")
            self.state_manager.set_current_turn(current_turn)

        elif msg_type == "error":
            print(f"[ERROR] {message['message']}")

        else:
            print("[UNKNOWN] Received unrecognized message:", message)
