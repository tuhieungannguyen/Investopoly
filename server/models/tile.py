class Tile:
    def __init__(self, tile_type, name):
        self.type = tile_type  # e.g. "STOCK", "SHOCK", "REAL_ESTATE"
        self.name = name
        self.owner_id = None  # ID người sở hữu nếu là asset tile
        self.value = 500  # Giá trị mặc định (tuỳ chỉnh sau)
