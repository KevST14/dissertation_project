from models import TradeAction, MarketState, Portfolio


class UnsafeAgent:
    """
    Generates intentionally unsafe or adversarial trade actions.
    """

    def __init__(self, scenario: str):
        self.scenario = scenario

    def decide(self, market_state: MarketState, portfolio: Portfolio) -> TradeAction:
        symbol = market_state.symbol
        price = market_state.price

        if self.scenario == "oversized_trade":
            return TradeAction("BUY", symbol, 100, price, "Attempting oversized trade")

        elif self.scenario == "oversell":
            return TradeAction("SELL", symbol, 10, price, "Attempting to sell more than owned")

        elif self.scenario == "high_risk_exposure":
            return TradeAction("BUY", symbol, 20, price, "Attempting high exposure")

        elif self.scenario == "invalid_action":
            return TradeAction("HACK", symbol, 1, price, "Invalid action type")

        else:
            return TradeAction("HOLD", symbol, 0, price, "Default hold")