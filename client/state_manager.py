class StateManager:
    def __init__(self):
        self.players = {}  # player_id -> state dict
        self.current_turn = None

    def update_player(self, player_id, data):
        if player_id not in self.players:
            self.players[player_id] = {}
        self.players[player_id].update(data)

    def get_player(self, player_id):
        return self.players.get(player_id, {})

    def set_current_turn(self, player_id):
        self.current_turn = player_id

    def is_my_turn(self, my_id):
        return self.current_turn == my_id
