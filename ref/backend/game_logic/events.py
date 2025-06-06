import random

shock_events = [
    {
        "name": "Global Pandemic",
        "effect": {
            "stocks": {"VCB": -0.2, "VIC": -0.2, "FPT": -0.3, "GAS": -0.3, "SAB": -0.4},
            "real_estate": -0.3
        }
    },
    # ... (thêm các sự kiện shock khác như trong mô tả)
]

chance_events = [
    {"name": "Trúng số", "cash": +600},
    {"name": "Bị cướp", "cash": -100},
    {"name": "Thừa kế", "cash": +500},
    {"name": "Bị kiện", "cash": -100},
    # ... (thêm các chance khác)
]

def trigger_shock(player, stock_prices, real_estates):
    event = random.choice(shock_events)
    for stock, delta in event["effect"]["stocks"].items():
        if stock in stock_prices:
            stock_prices[stock] *= (1 + delta)
    # Giảm hoặc tăng giá bất động sản
    for estate in real_estates:
        estate["value"] *= (1 + event["effect"]["real_estate"])
    return event

def trigger_chance(player):
    event = random.choice(chance_events)
    player["cash"] += event["cash"]
    return event

def handle_jail(player):
    player["in_jail"] = True
    player["jail_turns"] = 3

