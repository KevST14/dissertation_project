from typing import List
from models import MarketState


def get_mock_market_data() -> List[MarketState]:
    return [
        MarketState(symbol="AAPL", price=100.0, timestamp="2026-03-21 09:00:00"),
        MarketState(symbol="AAPL", price=97.0, timestamp="2026-03-21 10:00:00"),
        MarketState(symbol="AAPL", price=103.0, timestamp="2026-03-21 11:00:00"),
        MarketState(symbol="AAPL", price=108.0, timestamp="2026-03-21 12:00:00"),
        MarketState(symbol="AAPL", price=101.0, timestamp="2026-03-21 13:00:00"),
    ]