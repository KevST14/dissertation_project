from models import TradeAction, Portfolio, SafetyDecision


class SafetyValidator:
    """
    Validates whether a proposed trade action is allowed.
    """

    def __init__(self, max_trade_quantity: int = 5) -> None:
        self.max_trade_quantity = max_trade_quantity

    def validate(self, action: TradeAction, portfolio: Portfolio) -> SafetyDecision:
        if action.action_type == "HOLD":
            return SafetyDecision(True, "Hold action is always allowed.")

        if action.quantity <= 0:
            return SafetyDecision(False, "Trade quantity must be greater than zero.")

        if action.quantity > self.max_trade_quantity:
            return SafetyDecision(
                False,
                f"Trade quantity exceeds max allowed limit of {self.max_trade_quantity}."
            )

        if action.action_type == "BUY":
            total_cost = action.quantity * action.price
            if total_cost > portfolio.cash:
                return SafetyDecision(False, "Insufficient cash for buy order.")

        if action.action_type == "SELL":
            current_position = portfolio.get_position(action.symbol)
            if action.quantity > current_position:
                return SafetyDecision(False, "Cannot sell more shares than currently held.")

        return SafetyDecision(True, "Trade passed safety validation.")