
# server/logic/end_game.py

def calculate_net_worth(player):
    return (
        player.cash
        + sum([re.value for re in player.real_estates])
        + sum([stock.unit_price * stock.quantity for stock in player.stocks])
        + sum([saving.amount + saving.interest for saving in player.savings if saving.is_mature])
    )

def calculate_roi(player, initial_cash=2000):
    net_worth = calculate_net_worth(player)
    roi = (net_worth - initial_cash) / initial_cash * 100
    return round(roi, 2), net_worth

def determine_winner(players):
    results = []

    for player in players:
        roi, net_worth = calculate_roi(player)
        results.append({
            "name": player.name,
            "roi": roi,
            "net_worth": round(net_worth, 2)
        })

    # Find the winner
    winner = max(results, key=lambda p: p["net_worth"])

    return {
        "winner": winner["name"],
        "results": results
    }


# Example test block
if __name__ == "__main__":
    class MockStock:
        def __init__(self, unit_price, quantity):
            self.unit_price = unit_price
            self.quantity = quantity

    class MockRE:
        def __init__(self, value):
            self.value = value

    class MockSaving:
        def __init__(self, amount, interest, is_mature):
            self.amount = amount
            self.interest = interest
            self.is_mature = is_mature

    class Player:
        def __init__(self, name, cash, real_estates, stocks, savings):
            self.name = name
            self.cash = cash
            self.real_estates = real_estates
            self.stocks = stocks
            self.savings = savings

    p1 = Player("Lan", 500, [MockRE(300)], [MockStock(200, 2)], [MockSaving(500, 60, True)])
    p2 = Player("An", 800, [MockRE(200)], [MockStock(150, 3)], [MockSaving(500, 0, False)])

    result = determine_winner([p1, p2])
    print(result)