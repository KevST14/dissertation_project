from models import Portfolio, SafetyDecision, TradeAction


class RiskMonitor:
    """
    Evaluates whether a proposed trade would create excessive portfolio exposure.
    """

    def __init__(self, max_position_fraction: float = 0.30) -> None:
        self.max_position_fraction = max_position_fraction

    def assess(self, action: TradeAction, portfolio: Portfolio) -> SafetyDecision:
        if action.action_type in {"HOLD", "SELL"}:
            return SafetyDecision(True, "Risk check passed.", "RiskMonitor")

        proposed_position = portfolio.get_position(action.symbol) + action.quantity
        proposed_position_value = proposed_position * action.price

        current_prices = {action.symbol: action.price}
        total_portfolio_value = portfolio.get_total_value(current_prices)

        if total_portfolio_value <= 0:
            return SafetyDecision(
                False,
                "Portfolio value is non-positive, cannot assess exposure safely.",
                "RiskMonitor"
            )

        exposure_fraction = proposed_position_value / total_portfolio_value

        if exposure_fraction > self.max_position_fraction:
            return SafetyDecision(
                False,
                (
                    f"Proposed trade would create exposure of "
                    f"{exposure_fraction:.2%}, exceeding limit of "
                    f"{self.max_position_fraction:.2%}."
                ),
                "RiskMonitor"
            )

        return SafetyDecision(True, "Risk check passed.", "RiskMonitor")