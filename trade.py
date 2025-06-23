class Trade:
    def __init__(self, entry_date, entry_price):
        self.entry_date = entry_date
        self.entry_price = entry_price
        self.exit_date = None
        self.exit_price = None

    def close(self, exit_date, exit_price):
        self.exit_date = exit_date
        self.exit_price = exit_price

    def is_open(self):
        return self.exit_date is None

    def profit(self):
        if self.exit_price is not None:
            return self.exit_price - self.entry_price
        return None

    def profit_pct(self):
        if self.exit_price is not None:
            return (self.exit_price - self.entry_price) / self.entry_price * 100
        return None
