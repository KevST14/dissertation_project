"""Entry point for the trading simulation.

This file combines the market feed, agent, safety layer, broker, and
evaluation utilities into one executable script.

It prints state transitions to the terminal so the simulation is easy to
inspect, then outputs performance metrics and dissertation-friendly plots.
"""

from pathlib import Path
from collections import Counter
import math

import matplotlib.pyplot as plt

# Import the portfolio model used to hold account state.
from models import Portfolio
# Import the mock market data generator that feeds the simulation loop.
from market import get_mock_market_data
# Import the simple rule-based trading agent.
from agent import SimpleTradingAgent
# Import the mock broker that applies approved trades to the portfolio.
from broker import MockBroker

# Safety system components.
from policy_validator import PolicyValidator
from risk_monitor import RiskMonitor
from permission_guard import PermissionGuard
from safety_controller import SafetyController

# Experiment runner.
from experiments import run_all_scenarios


# Global tracking containers used for reporting and plotting.
portfolio_values = []
portfolio_timestamps = []
step_returns = []
action_counts = Counter()
safety_counts = Counter()
blocked_by_layer_counts = Counter()


# `print_portfolio` centralizes portfolio formatting so the output stays consistent.
def print_portfolio(portfolio: Portfolio) -> None:
    print(f"Cash: {portfolio.cash:.2f}")
    print(f"Holdings: {portfolio.holdings}")


# `compute_max_drawdown` measures the worst peak-to-trough decline.
def compute_max_drawdown(values: list[float]) -> float:
    if not values:
        return 0.0

    peak = values[0]
    max_drawdown = 0.0

    for value in values:
        if value > peak:
            peak = value

        if peak > 0:
            drawdown = (peak - value) / peak
            max_drawdown = max(max_drawdown, drawdown)

    return max_drawdown * 100


# `compute_volatility` estimates the variability of step returns.
def compute_volatility(returns: list[float]) -> float:
    if len(returns) < 2:
        return 0.0

    mean_return = sum(returns) / len(returns)
    variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
    return math.sqrt(variance) * 100


# `print_summary_metrics` reports final performance indicators.
def print_summary_metrics(portfolio: Portfolio) -> None:
    if not portfolio_values:
        print("\nNo portfolio values were recorded.")
        return

    initial_value = portfolio_values[0]
    final_value = portfolio_values[-1]
    max_value = max(portfolio_values)
    min_value = min(portfolio_values)
    absolute_return = final_value - initial_value
    percentage_return = (
        (absolute_return / initial_value) * 100 if initial_value != 0 else 0.0
    )
    max_drawdown = compute_max_drawdown(portfolio_values)
    volatility = compute_volatility(step_returns)

    print("\n=== Performance Summary ===")
    print(f"Initial Portfolio Value: {initial_value:.2f}")
    print(f"Final Portfolio Value: {final_value:.2f}")
    print(f"Absolute Return: {absolute_return:.2f}")
    print(f"Percentage Return: {percentage_return:.2f}%")
    print(f"Maximum Portfolio Value: {max_value:.2f}")
    print(f"Minimum Portfolio Value: {min_value:.2f}")
    print(f"Max Drawdown: {max_drawdown:.2f}%")
    print(f"Step Return Volatility: {volatility:.2f}%")
    print(f"Transactions Recorded: {len(portfolio.transaction_history)}")

    print("\n=== Action Summary ===")
    print(f"BUY decisions: {action_counts.get('BUY', 0)}")
    print(f"SELL decisions: {action_counts.get('SELL', 0)}")
    print(f"HOLD decisions: {action_counts.get('HOLD', 0)}")

    print("\n=== Safety Summary ===")
    print(f"Approved actions: {safety_counts.get('APPROVED', 0)}")
    print(f"Blocked actions: {safety_counts.get('BLOCKED', 0)}")

    if blocked_by_layer_counts:
        print("Blocked by layer:")
        for layer, count in blocked_by_layer_counts.items():
            print(f"  {layer}: {count}")


# `save_portfolio_value_plot` creates a line chart of portfolio value over time.
def save_portfolio_value_plot(output_dir: Path) -> None:
    if not portfolio_values:
        return

    plt.figure(figsize=(10, 5))
    plt.plot(portfolio_timestamps, portfolio_values, marker="o")
    plt.title("Portfolio Value Over Time")
    plt.xlabel("Timestamp")
    plt.ylabel("Portfolio Value")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_dir / "portfolio_value.png")
    plt.close()


# `save_step_returns_plot` creates a line chart of per-step returns.
def save_step_returns_plot(output_dir: Path) -> None:
    if not step_returns:
        return

    step_labels = list(range(1, len(step_returns) + 1))

    plt.figure(figsize=(10, 5))
    plt.plot(step_labels, step_returns, marker="o")
    plt.title("Step Returns Over Time")
    plt.xlabel("Step")
    plt.ylabel("Return")
    plt.tight_layout()
    plt.savefig(output_dir / "step_returns.png")
    plt.close()


# `save_action_distribution_plot` visualizes the frequency of agent actions.
def save_action_distribution_plot(output_dir: Path) -> None:
    if not action_counts:
        return

    labels = list(action_counts.keys())
    values = list(action_counts.values())

    plt.figure(figsize=(8, 5))
    plt.bar(labels, values)
    plt.title("Agent Action Distribution")
    plt.xlabel("Action Type")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.savefig(output_dir / "action_distribution.png")
    plt.close()


# `save_safety_outcomes_plot` visualizes approved vs blocked actions.
def save_safety_outcomes_plot(output_dir: Path) -> None:
    if not safety_counts:
        return

    labels = list(safety_counts.keys())
    values = list(safety_counts.values())

    plt.figure(figsize=(8, 5))
    plt.bar(labels, values)
    plt.title("Safety Outcomes")
    plt.xlabel("Outcome")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.savefig(output_dir / "safety_outcomes.png")
    plt.close()


# `save_all_plots` writes all available visual outputs to the outputs folder.
def save_all_plots() -> None:
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    save_portfolio_value_plot(output_dir)
    save_step_returns_plot(output_dir)
    save_action_distribution_plot(output_dir)
    save_safety_outcomes_plot(output_dir)

    print("\nSaved plots:")
    print(f"- {output_dir / 'portfolio_value.png'}")
    print(f"- {output_dir / 'step_returns.png'}")
    print(f"- {output_dir / 'action_distribution.png'}")
    print(f"- {output_dir / 'safety_outcomes.png'}")


# `main` performs one full simulation run from setup through completion.
def main() -> None:
    portfolio = Portfolio(cash=1000.0)
    market_data = get_mock_market_data()
    agent = SimpleTradingAgent()

    policy_validator = PolicyValidator(max_trade_quantity=5)
    risk_monitor = RiskMonitor(max_position_fraction=0.30)
    permission_guard = PermissionGuard(allowed_actions={"BUY", "SELL", "HOLD"})
    safety_controller = SafetyController(
        policy_validator=policy_validator,
        risk_monitor=risk_monitor,
        permission_guard=permission_guard,
    )

    broker = MockBroker()

    portfolio_values.clear()
    portfolio_timestamps.clear()
    step_returns.clear()
    action_counts.clear()
    safety_counts.clear()
    blocked_by_layer_counts.clear()

    print("=== Starting Simulation ===")
    print_portfolio(portfolio)
    print()

    previous_total_value = portfolio.cash

    for step, state in enumerate(market_data, start=1):
        print(f"Step: {step}")
        print(f"Timestamp: {state.timestamp}")
        print(f"Market: {state.symbol} @ {state.price:.2f}")

        proposed_action = agent.decide(state, portfolio)
        action_counts[proposed_action.action_type] += 1

        print(
            f"Agent Decision: {proposed_action.action_type} "
            f"{proposed_action.quantity} {proposed_action.symbol}"
        )
        print(f"Action Price: {proposed_action.price:.2f}")
        print(f"Reasoning: {proposed_action.reasoning}")

        safety_result = safety_controller.validate(proposed_action, portfolio)

        safety_label = "APPROVED" if safety_result.approved else "BLOCKED"
        safety_counts[safety_label] += 1

        if not safety_result.approved:
            blocked_by_layer_counts[safety_result.layer] += 1

        print(f"Safety Check: {safety_label}")
        print(f"Safety Layer: {safety_result.layer}")
        print(f"Safety Reason: {safety_result.reason}")

        if safety_result.approved:
            broker.execute_trade(proposed_action, portfolio)
            print("Execution: Trade processed.")
        else:
            print("Execution: Trade blocked.")

        current_prices = {state.symbol: state.price}
        total_value = portfolio.get_total_value(current_prices)
        portfolio_values.append(total_value)
        portfolio_timestamps.append(state.timestamp)

        step_return = (
            (total_value - previous_total_value) / previous_total_value
            if previous_total_value != 0
            else 0.0
        )
        step_returns.append(step_return)

        print(
            f"Debug: market price={state.price:.2f}, "
            f"action price={proposed_action.price:.2f}, "
            f"cash={portfolio.cash:.2f}"
        )

        print("Updated Portfolio:")
        print_portfolio(portfolio)
        print(f"Total Portfolio Value: {total_value:.2f}")
        print(f"Step Return: {step_return * 100:.2f}%")
        print("-" * 50)

        previous_total_value = total_value

    print("=== Simulation Complete ===")

    print("\nPortfolio Value Over Time:")
    for i, value in enumerate(portfolio_values, start=1):
        print(f"Step {i}: {value:.2f}")

    print_summary_metrics(portfolio)
    save_all_plots()

    print("\n=== Running Adversarial Tests ===")
    results = run_all_scenarios()

    print("\nScenario Results:")
    for scenario, data in results.items():
        print(f"{scenario}: {data}")


if __name__ == "__main__":
    main()