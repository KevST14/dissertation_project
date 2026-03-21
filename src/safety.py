"""Safety checks that gate whether an agent decision may be executed.

This layer sits between the trading agent and the broker so obviously invalid
orders can be blocked before they mutate the portfolio.
"""

# Import the portfolio, trade request, and safety result types used below.
from models import Portfolio, SafetyCheckResult, TradeAction


# `SafetyValidator` holds configurable rules that all trades must satisfy.
class SafetyValidator:
    # Store the maximum trade size once when the validator is created.
    def __init__(self, max_trade_quantity: int) -> None:
        # This limit protects the simulation from oversized orders.
        self.max_trade_quantity = max_trade_quantity

    # `validate` checks one proposed action against static and portfolio-based rules.
    def validate(self, action: TradeAction, portfolio: Portfolio) -> SafetyCheckResult:
        # Negative quantities are nonsensical in this simplified trade model.
        if action.quantity < 0:
            return SafetyCheckResult(
                approved=False,
                reason="Trade quantity cannot be negative.",
            )

        # Block any order that exceeds the configured size limit.
        if action.quantity > self.max_trade_quantity:
            return SafetyCheckResult(
                approved=False,
                reason="Trade quantity exceeds the configured safety limit.",
            )

        # `HOLD` is always safe because it does not change the portfolio.
        if action.action_type == "HOLD":
            return SafetyCheckResult(
                approved=True,
                reason="No trade requested.",
            )

        # Real trades must request at least one share.
        if action.quantity == 0:
            return SafetyCheckResult(
                approved=False,
                reason="Trade quantity must be greater than zero.",
            )

        # Selling requires enough existing inventory to cover the order.
        if action.action_type == "SELL":
            # Read the current position for the symbol being sold.
            available = portfolio.get_position(action.symbol)
            # Reject the order if it asks to sell more than is owned.
            if available < action.quantity:
                return SafetyCheckResult(
                    approved=False,
                    reason="Insufficient holdings for the requested sell order.",
                )

        # If none of the blocking rules fired, the trade is safe to execute.
        return SafetyCheckResult(
            approved=True,
            reason="Trade satisfies safety checks.",
        )
