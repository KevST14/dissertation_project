"""Benchmark strategies used for comparison against the safety-enabled system."""

from collections import Counter
from typing import Any

from agent import SimpleTradingAgent
from broker import MockBroker
from market import get_mock_market_data
from models import Portfolio, TradeAction
from reporting import build_metrics_summary


def run_buy_and_hold_benchmark(initial_cash: float = 1000.0) -> dict[str, Any]:
    """Run a simple buy-and-hold benchmark."""
    market_data = get_mock_market_data()
    portfolio = Portfolio(cash=initial_cash)
    broker = MockBroker()
    values: list[float] = []
    returns: list[float] = []
    previous_total_value = initial_cash

    if not market_data:
        return build_metrics_summary(
            label="buy_and_hold",
            values=[],
            returns=[],
            transaction_history=[],
        )

    first_state = market_data[0]
    quantity = int(portfolio.cash // first_state.price)

    if quantity > 0:
        buy_action = TradeAction(
            action_type="BUY",
            symbol=first_state.symbol,
            quantity=quantity,
            price=first_state.price,
            reasoning="Buy-and-hold baseline purchase.",
        )
        broker.execute_trade(buy_action, portfolio)

    for state in market_data:
        current_prices = {state.symbol: state.price}
        total_value = portfolio.get_total_value(current_prices)
        values.append(total_value)

        step_return = (
            (total_value - previous_total_value) / previous_total_value
            if previous_total_value != 0
            else 0.0
        )
        returns.append(step_return)
        previous_total_value = total_value

    return build_metrics_summary(
        label="buy_and_hold",
        values=values,
        returns=returns,
        transaction_history=portfolio.transaction_history,
        action_counter=Counter({"BUY": 1, "SELL": 0, "HOLD": max(0, len(market_data) - 1)}),
        safety_counter=Counter(),
    )


def run_no_safety_benchmark(initial_cash: float = 1000.0) -> dict[str, Any]:
    """Run the agent without safety validation for comparison."""
    market_data = get_mock_market_data()
    portfolio = Portfolio(cash=initial_cash)
    agent = SimpleTradingAgent()
    broker = MockBroker()
    values: list[float] = []
    returns: list[float] = []
    actions: Counter[str] = Counter()
    previous_total_value = initial_cash

    for state in market_data:
        action = agent.decide(state, portfolio)
        actions[action.action_type] += 1

        if action.action_type in {"BUY", "SELL"} and action.quantity > 0:
            try:
                broker.execute_trade(action, portfolio)
            except Exception:
                pass

        current_prices = {state.symbol: state.price}
        total_value = portfolio.get_total_value(current_prices)
        values.append(total_value)

        step_return = (
            (total_value - previous_total_value) / previous_total_value
            if previous_total_value != 0
            else 0.0
        )
        returns.append(step_return)
        previous_total_value = total_value

    return build_metrics_summary(
        label="no_safety",
        values=values,
        returns=returns,
        transaction_history=portfolio.transaction_history,
        action_counter=actions,
        safety_counter=Counter({"APPROVED": sum(actions.values()), "BLOCKED": 0}),
    )
