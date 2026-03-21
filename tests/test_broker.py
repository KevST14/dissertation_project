from pathlib import Path
import sys

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from broker import MockBroker
from models import Portfolio, TradeAction


def test_execute_trade_updates_cash_for_buy_using_action_price() -> None:
    broker = MockBroker()
    portfolio = Portfolio(cash=1000.0)
    action = TradeAction(
        action_type="BUY",
        symbol="AAPL",
        quantity=1,
        price=98.50,
        reasoning="Buy one share at the current market price.",
    )

    broker.execute_trade(action, portfolio)

    assert portfolio.cash == pytest.approx(901.50)
    assert portfolio.holdings == {"AAPL": 1}


def test_execute_trade_updates_cash_for_sell_using_action_price() -> None:
    broker = MockBroker()
    portfolio = Portfolio(cash=901.50, holdings={"AAPL": 1})
    action = TradeAction(
        action_type="SELL",
        symbol="AAPL",
        quantity=1,
        price=106.75,
        reasoning="Sell one share at the current market price.",
    )

    broker.execute_trade(action, portfolio)

    assert portfolio.cash == pytest.approx(1008.25)
    assert portfolio.holdings == {}
