class Offer:
    def __init__(self, from_id, to_id, asset_type, amount):
        self.from_id = from_id
        self.to_id = to_id
        self.asset_type = asset_type  # e.g. "stock", "real_estate"
        self.amount = amount
