class Player:
    def __init__(self, player_id, name):
        self.id = player_id
        self.name = name
        self.position = 0  # tile index
        self.cash = 1500
        self.portfolio = {
            "stock": 0,
            "real_estate": 0,
            "savings": 0
        }
        self.socket = None  # optional: có thể dùng để lưu WebSocket nếu cần
