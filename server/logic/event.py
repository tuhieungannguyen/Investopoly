def handle_tile_event(player, tile):
    if tile.type == "SHOCK":
        player.cash = max(0, player.cash - 100)
        return "Shock event: You lost $100!"
    elif tile.type == "CHANCE":
        player.cash += 100
        return "Chance card: You gained $100!"
    elif tile.type == "TAX":
        tax = min(200, player.cash)
        player.cash -= tax
        return f"Tax checkpoint: You paid ${tax} in tax."
    elif tile.type == "QUIZ":
        return "Quiz Time! Answer correctly to earn a reward."
    elif tile.type == "GO":
        player.cash += 200
        return "GO tile: You received $200!"
    elif tile.type == "SAVINGS":
        player.portfolio["savings"] += 50
        player.cash -= 50
        return "Savings: You deposited $50."
    else:
        return "Normal tile. Nothing happened."
