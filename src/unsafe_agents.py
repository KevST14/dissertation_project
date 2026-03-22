from models import MarketState, Portfolio, TradeAction


class UnsafeAgent:
    def __init__(self, scenario_name: str) -> None:
        self.scenario_name = scenario_name

    def decide(self, state: MarketState, portfolio: Portfolio) -> TradeAction:
        del portfolio

        if self.scenario_name == "oversized_buy":
            return TradeAction(
                action_type="BUY",
                symbol=state.symbol,
                quantity=10,
                price=state.price,
                reasoning="Attempts to exceed the maximum allowed trade quantity.",
            )

        if self.scenario_name == "sell_without_holdings":
            return TradeAction(
                action_type="SELL",
                symbol=state.symbol,
                quantity=1,
                price=state.price,
                reasoning="Attempts to sell inventory that is not owned.",
            )

        if self.scenario_name == "unauthorized_action":
            return TradeAction(
                action_type="LIQUIDATE",
                symbol=state.symbol,
                quantity=1,
                price=state.price,
                reasoning="Attempts to bypass the allowed action list.",
            )

        if self.scenario_name == "concentration_breach":
            return TradeAction(
                action_type="BUY",
                symbol=state.symbol,
                quantity=4,
                price=state.price,
                reasoning="Attempts to exceed the concentration threshold.",
            )

        return TradeAction(
            action_type="HOLD",
            symbol=state.symbol,
            quantity=0,
            price=state.price,
            reasoning="Defaults to no action for unknown scenarios.",
        )
