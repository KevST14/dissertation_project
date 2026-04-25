from typing import Optional
from models import MarketState, Portfolio, TradeAction


class SimpleTradingAgent:
    """
    A basic rule-based trading agent for baseline testing.
    """
    def __init__(self) -> None:
        self.last_price: Optional[float] = None

    def decide(self, market_state: MarketState, portfolio: Portfolio) -> TradeAction:
        symbol = market_state.symbol
        price = market_state.price

        if self.last_price is None:
            self.last_price = price
            return TradeAction(
                action_type="HOLD",
                symbol=symbol,
                quantity=0,
                price=price,
                reasoning="No previous price available, so hold."
            )

        if price <= self.last_price * 0.98:
            action = TradeAction(
                action_type="BUY",
                symbol=symbol,
                quantity=1,
                price=price,
                reasoning="Price dropped by at least 2%, buying 1 share."
            )
        elif price >= self.last_price * 1.03 and portfolio.get_position(symbol) > 0:
            action = TradeAction(
                action_type="SELL",
                symbol=symbol,
                quantity=1,
                price=price,
                reasoning="Price rose by at least 3%, selling 1 share."
            )
        else:
            action = TradeAction(
                action_type="HOLD",
                symbol=symbol,
                quantity=0,
                price=price,
                reasoning="No trading condition met, so hold."
            )

        self.last_price = price
        return action