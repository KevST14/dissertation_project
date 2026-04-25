from models import Portfolio, SafetyDecision, TradeAction


class PolicyValidator:
    """
    Enforces hard trading rules and execution constraints.
    """

    def __init__(self, max_trade_quantity: int = 5) -> None:
        self.max_trade_quantity = max_trade_quantity

    def validate(self, action: TradeAction, portfolio: Portfolio) -> SafetyDecision:
        if action.action_type == "HOLD":
            return SafetyDecision(True, "Hold action is allowed.", "PolicyValidator")

        if action.quantity <= 0:
            return SafetyDecision(
                False,
                "Trade quantity must be greater than zero.",
                "PolicyValidator"
            )

        if action.quantity > self.max_trade_quantity:
            return SafetyDecision(
                False,
                f"Trade quantity exceeds the maximum allowed limit of {self.max_trade_quantity}.",
                "PolicyValidator"
            )

        if action.action_type == "BUY":
            total_cost = action.quantity * action.price
            if total_cost > portfolio.cash:
                return SafetyDecision(
                    False,
                    "Insufficient cash for proposed buy order.",
                    "PolicyValidator"
                )

        if action.action_type == "SELL":
            current_position = portfolio.get_position(action.symbol)
            if action.quantity > current_position:
                return SafetyDecision(
                    False,
                    "Cannot sell more shares than currently held.",
                    "PolicyValidator"
                )

        return SafetyDecision(True, "Policy checks passed.", "PolicyValidator")