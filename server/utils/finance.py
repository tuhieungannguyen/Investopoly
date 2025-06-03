def calculate_net_worth(player):
    """
    Tính tổng tài sản của người chơi:
    cash + stock + real_estate + savings
    """
    return (
        player.cash +
        player.portfolio.get("stock", 0) +
        player.portfolio.get("real_estate", 0) +
        player.portfolio.get("savings", 0)
    )
