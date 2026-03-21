"""Mock market data provider used by the simulation.

The project does not connect to a real exchange, so this file supplies a short
hard-coded sequence of prices that is predictable and easy to inspect.
"""

# Import the shared market data type so every market tick has the same shape.
from models import MarketState


# `get_mock_market_data` returns a deterministic timeline of prices.
# Returning a list keeps the main loop simple for a teaching/demo project.
def get_mock_market_data() -> list[MarketState]:
    # Each `MarketState` entry acts like one observation from the market feed.
    return [
        # The first price is below the buy threshold, so the agent should buy.
        MarketState(timestamp="2026-03-21T09:00:00Z", symbol="AAPL", price=98.50),
        # The second price sits between the thresholds, so the agent should hold.
        MarketState(timestamp="2026-03-21T10:00:00Z", symbol="AAPL", price=101.25),
        # The third price is high enough to trigger a sell when shares are owned.
        MarketState(timestamp="2026-03-21T11:00:00Z", symbol="AAPL", price=106.75),
        # The last price returns to the neutral zone for another hold decision.
        MarketState(timestamp="2026-03-21T12:00:00Z", symbol="AAPL", price=103.10),
    ]
