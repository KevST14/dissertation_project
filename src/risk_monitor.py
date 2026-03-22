from models import Portfolio, SafetyCheckResult, TradeAction


class RiskMonitor:
    """Checks whether a trade would breach a simple position concentration limit."""

    def __init__(self, max_position_fraction: float) -> None:
        self.max_position_fraction = max_position_fraction

    def validate(self, action: TradeAction, portfolio: Portfolio) -> SafetyCheckResult:
        if action.action_type in {"HOLD", "SELL"}:
            return SafetyCheckResult(
                approved=True,
                layer="risk_monitor",
                reason="Trade does not increase concentration risk.",
            )

        current_total_value = portfolio.get_total_value({action.symbol: action.price})
        if current_total_value <= 0:
            return SafetyCheckResult(
                approved=False,
                layer="risk_monitor",
                reason="Portfolio value must be positive to evaluate risk.",
            )

        projected_quantity = portfolio.get_position(action.symbol) + action.quantity
        projected_position_value = projected_quantity * action.price
        projected_fraction = projected_position_value / current_total_value

        if projected_fraction > self.max_position_fraction:
            return SafetyCheckResult(
                approved=False,
                layer="risk_monitor",
                reason="Trade exceeds the configured position concentration limit.",
            )

        return SafetyCheckResult(
            approved=True,
            layer="risk_monitor",
            reason="Trade satisfies concentration risk checks.",
        )
