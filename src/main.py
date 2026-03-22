"""Entry point for the trading simulation.

This file combines the market feed, agent, safety layer, broker, experiment
runner, and evaluation utilities into one executable script.

It provides:
- step-by-step terminal tracing
- portfolio performance metrics
- CSV exports for analysis
- dissertation-friendly plots
- adversarial scenario evaluation
"""

# Import utilities for file paths
from pathlib import Path
# Import Counter for counting occurrences (e.g., actions, safety results)
from collections import Counter
# CSV handling
import csv
# Math utilities (e.g., sqrt)
import math
# Type hints
from typing import Any

# Plotting library for visualisations
import matplotlib.pyplot as plt

# Import project modules
from models import Portfolio
from market import get_mock_market_data
from agent import SimpleTradingAgent
from broker import MockBroker
from policy_validator import PolicyValidator
from risk_monitor import RiskMonitor
from permission_guard import PermissionGuard
from safety_controller import SafetyController
from experiments import run_all_scenarios


# Global tracking containers used for reporting and plotting.
portfolio_values: list[float] = []          # Stores portfolio value over time
portfolio_timestamps: list[str] = []        # Stores timestamps for each step
step_returns: list[float] = []              # Stores returns per step
action_counts: Counter[str] = Counter()     # Tracks BUY/SELL/HOLD decisions
safety_counts: Counter[str] = Counter()     # Tracks APPROVED/BLOCKED outcomes
blocked_by_layer_counts: Counter[str] = Counter()  # Tracks which safety layer blocked actions
simulation_log: list[dict[str, Any]] = []   # Stores detailed step-by-step logs


def print_portfolio(portfolio: Portfolio) -> None:
    """Print the current portfolio state in a consistent format."""
    print(f"Cash: {portfolio.cash:.2f}")           # Display available cash
    print(f"Holdings: {portfolio.holdings}")       # Display asset holdings


def compute_max_drawdown(values: list[float]) -> float:
    """Return the maximum drawdown as a percentage."""
    if not values:
        return 0.0  # No data → no drawdown

    peak = values[0]           # Highest value seen so far
    max_drawdown = 0.0         # Track worst drawdown

    for value in values:
        peak = max(peak, value)  # Update peak if new high
        if peak > 0:
            drawdown = (peak - value) / peak  # Compute drawdown
            max_drawdown = max(max_drawdown, drawdown)

    return max_drawdown * 100  # Convert to percentage


def compute_volatility(returns: list[float]) -> float:
    """Return the standard deviation of step returns as a percentage."""
    if len(returns) < 2:
        return 0.0  # Not enough data

    mean_return = sum(returns) / len(returns)  # Average return
    variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
    return math.sqrt(variance) * 100  # Standard deviation → percentage


def compute_average_step_return(returns: list[float]) -> float:
    """Return the mean step return as a percentage."""
    if not returns:
        return 0.0
    return (sum(returns) / len(returns)) * 100  # Convert to percentage


def compute_cumulative_returns(values: list[float]) -> list[float]:
    """Compute cumulative return series from portfolio values."""
    if not values:
        return []

    initial_value = values[0]  # Starting portfolio value
    if initial_value == 0:
        return [0.0 for _ in values]

    # Return % change from initial value
    return [((value - initial_value) / initial_value) * 100 for value in values]


def compute_drawdown_series(values: list[float]) -> list[float]:
    """Compute drawdown at each step as a percentage."""
    if not values:
        return []

    peak = values[0]     # Track highest value seen so far
    drawdowns = []       # Store drawdown values

    for value in values:
        peak = max(peak, value)
        drawdown = ((peak - value) / peak) * 100 if peak > 0 else 0.0
        drawdowns.append(drawdown)

    return drawdowns


def count_profitable_and_losing_trades(transaction_history: list[dict[str, Any]]) -> tuple[int, int]:
    """Estimate profitable and losing sell trades using average cost basis."""
    avg_cost: dict[str, float] = {}      # Average cost per symbol
    position_sizes: dict[str, int] = {}  # Current position sizes
    profitable = 0                       # Count of profitable trades
    losing = 0                           # Count of losing trades

    for tx in transaction_history:
        action = tx.get("action_type")
        symbol = tx.get("symbol")
        quantity = int(tx.get("quantity", 0))
        price = float(tx.get("price", 0.0))

        if not symbol or quantity <= 0:
            continue  # Skip invalid trades

        if action == "BUY":
            # Update average cost basis
            current_qty = position_sizes.get(symbol, 0)
            current_cost = avg_cost.get(symbol, 0.0) * current_qty
            new_total_qty = current_qty + quantity
            if new_total_qty > 0:
                avg_cost[symbol] = (current_cost + price * quantity) / new_total_qty
            position_sizes[symbol] = new_total_qty

        elif action == "SELL":
            current_qty = position_sizes.get(symbol, 0)
            if current_qty <= 0:
                continue

            cost_basis = avg_cost.get(symbol, 0.0)

            # Determine profit/loss
            if price > cost_basis:
                profitable += 1
            elif price < cost_basis:
                losing += 1

            # Reduce position
            position_sizes[symbol] = max(0, current_qty - quantity)

            # Remove if position closed
            if position_sizes[symbol] == 0:
                avg_cost.pop(symbol, None)

    return profitable, losing


def build_metrics_summary(portfolio: Portfolio) -> dict[str, Any]:
    """Assemble a metrics dictionary for terminal display and CSV export."""
    if not portfolio_values:
        return {}

    # Basic return calculations
    initial_value = portfolio_values[0]
    final_value = portfolio_values[-1]
    absolute_return = final_value - initial_value
    percentage_return = (absolute_return / initial_value) * 100 if initial_value != 0 else 0.0

    # Risk and performance metrics
    max_drawdown = compute_max_drawdown(portfolio_values)
    volatility = compute_volatility(step_returns)
    average_step_return = compute_average_step_return(step_returns)

    # Trade performance stats
    profitable_trades, losing_trades = count_profitable_and_losing_trades(
        portfolio.transaction_history
    )
    total_sell_evaluations = profitable_trades + losing_trades
    win_rate = (
        (profitable_trades / total_sell_evaluations) * 100
        if total_sell_evaluations > 0
        else 0.0
    )

    # Compile all metrics into dictionary
    metrics = {
        "initial_portfolio_value": round(initial_value, 4),
        "final_portfolio_value": round(final_value, 4),
        "absolute_return": round(absolute_return, 4),
        "percentage_return": round(percentage_return, 4),
        "max_portfolio_value": round(max(portfolio_values), 4),
        "min_portfolio_value": round(min(portfolio_values), 4),
        "max_drawdown_pct": round(max_drawdown, 4),
        "step_return_volatility_pct": round(volatility, 4),
        "average_step_return_pct": round(average_step_return, 4),
        "transactions_recorded": len(portfolio.transaction_history),
        "buy_decisions": action_counts.get("BUY", 0),
        "sell_decisions": action_counts.get("SELL", 0),
        "hold_decisions": action_counts.get("HOLD", 0),
        "approved_actions": safety_counts.get("APPROVED", 0),
        "blocked_actions": safety_counts.get("BLOCKED", 0),
        "profitable_sell_trades": profitable_trades,
        "losing_sell_trades": losing_trades,
        "win_rate_pct": round(win_rate, 4),
    }

    return metrics


# NOTE: Remaining functions follow the same pattern:
# - write_csv → writes dictionaries to CSV
# - export_* → saves outputs
# - save_*_plot → generates charts using matplotlib
# - main() → orchestrates the full simulation loop

def main() -> None:
    """Run one full simulation, then export results and scenario evaluations."""

    # Initialise portfolio with starting cash
    portfolio = Portfolio(cash=1000.0)

    # Load mock market data
    market_data = get_mock_market_data()

    # Initialise trading agent
    agent = SimpleTradingAgent()

    # Setup safety system components
    policy_validator = PolicyValidator(max_trade_quantity=5)
    risk_monitor = RiskMonitor(max_position_fraction=0.30)
    permission_guard = PermissionGuard(allowed_actions={"BUY", "SELL", "HOLD"})

    # Combine safety layers into one controller
    safety_controller = SafetyController(
        policy_validator=policy_validator,
        risk_monitor=risk_monitor,
        permission_guard=permission_guard,
    )

    # Broker executes trades
    broker = MockBroker()

    # Reset global tracking variables
    portfolio_values.clear()
    portfolio_timestamps.clear()
    step_returns.clear()
    action_counts.clear()
    safety_counts.clear()
    blocked_by_layer_counts.clear()
    simulation_log.clear()

    # Create output directory
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    print("=== Starting Simulation ===")

    previous_total_value = portfolio.cash  # Track previous value for returns

    # Main simulation loop
    for step, state in enumerate(market_data, start=1):

        # Agent decides action
        proposed_action = agent.decide(state, portfolio)
        action_counts[proposed_action.action_type] += 1

        # Safety validation
        safety_result = safety_controller.validate(proposed_action, portfolio)

        # Execute trade only if approved
        if safety_result.approved:
            broker.execute_trade(proposed_action, portfolio)

        # Compute total portfolio value
        current_prices = {state.symbol: state.price}
        total_value = portfolio.get_total_value(current_prices)

        # Store tracking data
        portfolio_values.append(total_value)
        portfolio_timestamps.append(state.timestamp)

        # Compute step return
        step_return = (
            (total_value - previous_total_value) / previous_total_value
            if previous_total_value != 0
            else 0.0
        )
        step_returns.append(step_return)

        previous_total_value = total_value

    print("=== Simulation Complete ===")

    # Generate metrics and outputs
    metrics = build_metrics_summary(portfolio)
    print_summary_metrics(metrics)

    # Run adversarial scenarios
    scenario_results = run_all_scenarios()

    # Export results
    export_simulation_log(output_dir)
    export_transactions(portfolio, output_dir)
    export_metrics_summary(metrics, output_dir)
    export_scenario_results(scenario_results, output_dir)

    # Generate plots
    save_all_plots(output_dir)

    # Show saved file list
    print_output_manifest(output_dir)


# Run script if executed directly
if __name__ == "__main__":
    main()