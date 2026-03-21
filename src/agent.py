"""Simple trading policy used in the simulation.

The logic here is intentionally basic: buy below one threshold, sell above
another threshold, otherwise hold. That makes the decision path easy to follow.
"""

# Import the shared types used in the decision method signature and return value.
from models import MarketState, Portfolio, TradeAction


# `SimpleTradingAgent` groups the trading rules behind a single interface.
class SimpleTradingAgent:
    # `decide` consumes the latest market tick plus the current portfolio state.
    # It returns a `TradeAction` describing what the agent wants to do next.
    def decide(self, state: MarketState, portfolio: Portfolio) -> TradeAction:
        # Read the current share count for this symbol so sell decisions are safe.
        holdings = portfolio.get_position(state.symbol)

        # Buy when the price is cheap enough and the account can afford one share.
        if state.price < 100 and portfolio.cash >= state.price:
            return TradeAction(
                # `BUY` tells downstream components this action increases exposure.
                action_type="BUY",
                # Reuse the symbol from the incoming market tick.
                symbol=state.symbol,
                # Trade a single share to keep the simulation easy to reason about.
                quantity=1,
                # Preserve the current market price so execution uses the same value.
                price=state.price,
                # Include a readable explanation for the console log.
                reasoning="Price is below the buy threshold and cash is available.",
            )

        # Sell when the price is high enough and we actually own the asset.
        if state.price > 105 and holdings > 0:
            return TradeAction(
                # `SELL` tells the broker to reduce the current position.
                action_type="SELL",
                # Sell the same symbol we just evaluated.
                symbol=state.symbol,
                # Again use one share so state transitions stay obvious.
                quantity=1,
                # Preserve the current market price so execution uses the same value.
                price=state.price,
                # Explain why the sell branch fired.
                reasoning="Price is above the sell threshold and inventory is available.",
            )

        # If neither threshold fires, the agent explicitly does nothing.
        return TradeAction(
            # `HOLD` makes the no-op decision explicit for safety and logging.
            action_type="HOLD",
            # Keep the same symbol for consistent reporting.
            symbol=state.symbol,
            # Zero quantity reflects that no order should be sent.
            quantity=0,
            # Keep the current market price attached for debugging and traceability.
            price=state.price,
            # State plainly that no rule produced a trade signal.
            reasoning="No trade signal met the current thresholds.",
        )
