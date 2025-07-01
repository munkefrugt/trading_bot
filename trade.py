class Trade:
    def __init__(self, entry_date, entry_price, entry_equity, quantity=1, stoploss=None ):
        self.entry_date = entry_date
        self.entry_price = entry_price
        self.entry_equity = entry_equity
        self.exit_date = None
        self.exit_price = None

        self.quantity = quantity
        self.stoploss = stoploss
        self.status = 'open'

    def close(self, exit_date, exit_price):
        self.exit_date = exit_date
        self.exit_price = exit_price
        self.status = 'closed'

    def profit(self):
        if self.exit_price is not None:
            return (self.exit_price - self.entry_price) * self.quantity
        return 0

    def is_stopped_out(self, current_price):
        return self.stoploss is not None and current_price <= self.stoploss

    def is_open(self):
        return self.status == 'open'

    def profit_pct(self):
        if self.exit_price is not None:
            return ((self.exit_price - self.entry_price) / self.entry_price) * 100
        return 0
