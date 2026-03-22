from pathlib import Path
import sys

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from broker import MockBroker
from models import Portfolio, TradeAction


def test_broker_updates_cash_and_holdings_for_buy() -> None:
    broker = MockBroker()
    portfolio = Portfolio(cash=1000.0)
    action = TradeAction(
        action_type="BUY",
        symbol="AAPL",
        quantity=2,
        price=100.0,
        reasoning="Buy two shares.",
    )

    broker.execute_trade(action, portfolio)

    assert portfolio.cash == pytest.approx(800.0)
    assert portfolio.holdings == {"AAPL": 2}


def test_broker_updates_cash_and_holdings_for_sell() -> None:
    broker = MockBroker()
    portfolio = Portfolio(cash=800.0, holdings={"AAPL": 2})
    action = TradeAction(
        action_type="SELL",
        symbol="AAPL",
        quantity=1,
        price=110.0,
        reasoning="Sell one share.",
    )

    broker.execute_trade(action, portfolio)

    assert portfolio.cash == pytest.approx(910.0)
    assert portfolio.holdings == {"AAPL": 1}
