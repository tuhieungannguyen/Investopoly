import random
from server.logic.event import handle_tile_event
from server.utils.finance import calculate_net_worth

def roll_dice():
    return random.randint(1, 6)

def process_turn(player, room, board):
    dice = roll_dice()
    new_pos = (player.position + dice) % len(board)
    player.position = new_pos
    tile = board[new_pos]

    event_msg = handle_tile_event(player, tile)

    return {
        "dice": dice,
        "new_pos": new_pos,
        "tile_type": tile.type,
        "tile_name": tile.name,
        "event_msg": event_msg,
        "net_worth": calculate_net_worth(player)
    }
