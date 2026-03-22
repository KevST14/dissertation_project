from models import Portfolio, SafetyCheckResult, TradeAction


class PolicyValidator:
    """Applies basic portfolio and order policy checks."""

    def __init__(self, max_trade_quantity: int) -> None:
        self.max_trade_quantity = max_trade_quantity

    def validate(self, action: TradeAction, portfolio: Portfolio) -> SafetyCheckResult:
        if action.quantity < 0:
            return SafetyCheckResult(
                approved=False,
                layer="policy_validator",
                reason="Trade quantity cannot be negative.",
            )

        if action.quantity > self.max_trade_quantity:
            return SafetyCheckResult(
                approved=False,
                layer="policy_validator",
                reason="Trade quantity exceeds the configured safety limit.",
            )

        if action.action_type == "HOLD":
            return SafetyCheckResult(
                approved=True,
                layer="policy_validator",
                reason="No trade requested.",
            )

        if action.quantity == 0:
            return SafetyCheckResult(
                approved=False,
                layer="policy_validator",
                reason="Trade quantity must be greater than zero.",
            )

        if action.action_type == "SELL" and portfolio.get_position(action.symbol) < action.quantity:
            return SafetyCheckResult(
                approved=False,
                layer="policy_validator",
                reason="Insufficient holdings for the requested sell order.",
            )

        if action.action_type == "BUY" and portfolio.cash < action.quantity * action.price:
            return SafetyCheckResult(
                approved=False,
                layer="policy_validator",
                reason="Insufficient cash for the requested buy order.",
            )

        return SafetyCheckResult(
            approved=True,
            layer="policy_validator",
            reason="Trade satisfies policy checks.",
        )
