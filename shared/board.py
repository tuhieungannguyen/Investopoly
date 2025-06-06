tile_map = [
    "GO", "Real Estate 5", "Tax Checkpoint", "Shock Event", "Stock Corp E", "Jail (Challenge)",
    "Stock Corp D", "Chance", "Stock Corp C", "Real Estate 4", "Quizzes",
    "Real Estate 3", "Stock Corp B", "Savings", "Shock Event", "Jail Visit",
    "Chance", "Real Estate 2", "Stock Corp A", "Real Estate 1"
]

def move_player(current_position: int, steps: int) -> (int, bool): # type: ignore
    """
    Trả về vị trí mới và cờ cho biết có qua GO không.
    """
    new_position = (current_position + steps) % len(tile_map)
    passed_go = (current_position + steps) >= len(tile_map)
    return new_position, passed_go

def get_tile_type(index):
    return tile_map[index]