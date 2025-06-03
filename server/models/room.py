from server.models.tile import Tile

class Room:
    def __init__(self, room_id):
        self.id = room_id
        self.players = {}  # player_id -> Player object
        self.turn_index = 0
        self.turn_order = []
        self.board = self._init_board()

    def next_turn(self):
        if len(self.turn_order) == 0:
            return None
        self.turn_index = (self.turn_index + 1) % len(self.turn_order)
        return self.turn_order[self.turn_index]

    def _init_board(self):
        # Tạo 20 ô theo đúng mô tả game Investopoly
        tiles = []
        layout = [
            ("JAIL", "Jail Visit"),
            ("SHOCK", "Shock Event"),
            ("SAVINGS", "Savings"),
            ("STOCK", "Stock Corp A"),
            ("REAL_ESTATE", "Real Estate 3"),
            ("QUIZ", "Quizzes (Edu)"),
            ("REAL_ESTATE", "Real Estate 4"),
            ("STOCK", "Stock Corp B"),
            ("CHANCE", "Chance"),
            ("STOCK", "Stock Corp C"),
            ("SHOCK", "Shock Event"),
            ("TAX", "Tax Checkpoint"),
            ("REAL_ESTATE", "Real Estate 5"),
            ("GO", "GO"),
            ("JAIL", "Jail (Challenge)"),
            ("REAL_ESTATE", "Real Estate 1"),
            ("STOCK", "Stock Corp A"),
            ("REAL_ESTATE", "Real Estate 2"),
            ("EMPTY", "Empty"),
            ("EMPTY", "Empty")
        ]
        for tile_type, name in layout:
            tiles.append(Tile(tile_type, name))
        return tiles
