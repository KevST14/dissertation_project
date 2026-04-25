from pathlib import Path
from collections import Counter
import csv
import math
from typing import Any

import matplotlib.pyplot as plt


def compute_max_drawdown(values: list[float]) -> float:
    """Return the maximum drawdown percentage."""
    if not values:
        return 0.0

    peak = values[0]
    max_drawdown = 0.0

    for value in values:
        peak = max(peak, value)
        if peak > 0:
            drawdown = (peak - value) / peak
            max_drawdown = max(max_drawdown, drawdown)

    return max_drawdown * 100


def compute_volatility(returns: list[float]) -> float:
    """Return volatility as the standard deviation of step returns."""
    if len(returns) < 2:
        return 0.0

    mean_return = sum(returns) / len(returns)
    variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
    return math.sqrt(variance) * 100


def compute_average_step_return(returns: list[float]) -> float:
    """Return average step return percentage."""
    if not returns:
        return 0.0
    return (sum(returns) / len(returns)) * 100


def compute_cumulative_returns(values: list[float]) -> list[float]:
    """Return cumulative return series from portfolio values."""
    if not values:
        return []

    initial_value = values[0]
    if initial_value == 0:
        return [0.0 for _ in values]

    return [((value - initial_value) / initial_value) * 100 for value in values]


def compute_drawdown_series(values: list[float]) -> list[float]:
    """Return drawdown series as percentages."""
    if not values:
        return []

    peak = values[0]
    drawdowns: list[float] = []

    for value in values:
        peak = max(peak, value)
        drawdown = ((peak - value) / peak) * 100 if peak > 0 else 0.0
        drawdowns.append(drawdown)

    return drawdowns


def count_profitable_and_losing_trades(
    transaction_history: list[dict[str, Any]]
) -> tuple[int, int]:
    """Estimate profitable and losing sell trades using average cost basis."""
    avg_cost: dict[str, float] = {}
    position_sizes: dict[str, int] = {}
    profitable = 0
    losing = 0

    for tx in transaction_history:
        action = tx.get("action_type") or tx.get("type")
        symbol = tx.get("symbol")
        quantity = int(tx.get("quantity", 0))
        price = float(tx.get("price", 0.0))

        if not symbol or quantity <= 0:
            continue

        if action == "BUY":
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

            if price > cost_basis:
                profitable += 1
            elif price < cost_basis:
                losing += 1

            position_sizes[symbol] = max(0, current_qty - quantity)
            if position_sizes[symbol] == 0:
                avg_cost.pop(symbol, None)

    return profitable, losing


def build_metrics_summary(
    *,
    label: str,
    values: list[float],
    returns: list[float],
    transaction_history: list[dict[str, Any]],
    action_counter: Counter[str] | None = None,
    safety_counter: Counter[str] | None = None,
) -> dict[str, Any]:
    """Build a summary metrics dictionary for one run."""
    if not values:
        return {"strategy": label}

    initial_value = values[0]
    final_value = values[-1]
    absolute_return = final_value - initial_value
    percentage_return = (absolute_return / initial_value) * 100 if initial_value != 0 else 0.0

    profitable_trades, losing_trades = count_profitable_and_losing_trades(transaction_history)
    total_sell_evaluations = profitable_trades + losing_trades
    win_rate = (
        (profitable_trades / total_sell_evaluations) * 100
        if total_sell_evaluations > 0
        else 0.0
    )

    approved_actions = safety_counter.get("APPROVED", 0) if safety_counter else 0
    blocked_actions = safety_counter.get("BLOCKED", 0) if safety_counter else 0
    total_safety_events = approved_actions + blocked_actions
    intervention_rate = (
        (blocked_actions / total_safety_events) * 100
        if total_safety_events > 0
        else 0.0
    )

    return {
        "strategy": label,
        "initial_portfolio_value": round(initial_value, 4),
        "final_portfolio_value": round(final_value, 4),
        "absolute_return": round(absolute_return, 4),
        "percentage_return_pct": round(percentage_return, 4),
        "max_portfolio_value": round(max(values), 4),
        "min_portfolio_value": round(min(values), 4),
        "max_drawdown_pct": round(compute_max_drawdown(values), 4),
        "step_return_volatility_pct": round(compute_volatility(returns), 4),
        "average_step_return_pct": round(compute_average_step_return(returns), 4),
        "transactions_recorded": len(transaction_history),
        "buy_decisions": action_counter.get("BUY", 0) if action_counter else 0,
        "sell_decisions": action_counter.get("SELL", 0) if action_counter else 0,
        "hold_decisions": action_counter.get("HOLD", 0) if action_counter else 0,
        "approved_actions": approved_actions,
        "blocked_actions": blocked_actions,
        "safety_intervention_rate_pct": round(intervention_rate, 4),
        "profitable_sell_trades": profitable_trades,
        "losing_sell_trades": losing_trades,
        "win_rate_pct": round(win_rate, 4),
    }


def print_summary_metrics(metrics: dict[str, Any]) -> None:
    """Print metrics in a clean terminal format."""
    if not metrics or "final_portfolio_value" not in metrics:
        print("\nNo metrics available.")
        return

    print(f"\n=== Performance Summary: {metrics['strategy']} ===")
    print(f"Initial Portfolio Value: {metrics['initial_portfolio_value']:.2f}")
    print(f"Final Portfolio Value: {metrics['final_portfolio_value']:.2f}")
    print(f"Absolute Return: {metrics['absolute_return']:.2f}")
    print(f"Percentage Return: {metrics['percentage_return_pct']:.2f}%")
    print(f"Maximum Portfolio Value: {metrics['max_portfolio_value']:.2f}")
    print(f"Minimum Portfolio Value: {metrics['min_portfolio_value']:.2f}")
    print(f"Max Drawdown: {metrics['max_drawdown_pct']:.2f}%")
    print(f"Step Return Volatility: {metrics['step_return_volatility_pct']:.2f}%")
    print(f"Average Step Return: {metrics['average_step_return_pct']:.2f}%")
    print(f"Transactions Recorded: {metrics['transactions_recorded']}")

    print("\n=== Trade Outcome Summary ===")
    print(f"Profitable Sell Trades: {metrics['profitable_sell_trades']}")
    print(f"Losing Sell Trades: {metrics['losing_sell_trades']}")
    print(f"Win Rate: {metrics['win_rate_pct']:.2f}%")

    print("\n=== Action Summary ===")
    print(f"BUY decisions: {metrics['buy_decisions']}")
    print(f"SELL decisions: {metrics['sell_decisions']}")
    print(f"HOLD decisions: {metrics['hold_decisions']}")

    print("\n=== Safety Summary ===")
    print(f"Approved actions: {metrics['approved_actions']}")
    print(f"Blocked actions: {metrics['blocked_actions']}")
    print(f"Safety intervention rate: {metrics['safety_intervention_rate_pct']:.2f}%")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write a list of dictionaries to CSV."""
    if not rows:
        return

    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def save_portfolio_value_plot(
    output_dir: Path,
    timestamps: list[str],
    values: list[float],
) -> None:
    """Save portfolio value over time plot."""
    if not values:
        return

    plt.figure(figsize=(11, 5))
    plt.plot(timestamps, values, marker="o")
    plt.title("Portfolio Value Over Time")
    plt.xlabel("Timestamp")
    plt.ylabel("Portfolio Value")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_dir / "portfolio_value.png")
    plt.close()


def save_cumulative_return_plot(
    output_dir: Path,
    timestamps: list[str],
    values: list[float],
) -> None:
    """Save cumulative return plot."""
    cumulative_returns = compute_cumulative_returns(values)
    if not cumulative_returns:
        return

    plt.figure(figsize=(11, 5))
    plt.plot(timestamps, cumulative_returns, marker="o")
    plt.title("Cumulative Return Over Time")
    plt.xlabel("Timestamp")
    plt.ylabel("Cumulative Return (%)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_dir / "cumulative_return.png")
    plt.close()


def save_drawdown_plot(
    output_dir: Path,
    timestamps: list[str],
    values: list[float],
) -> None:
    """Save drawdown plot."""
    drawdowns = compute_drawdown_series(values)
    if not drawdowns:
        return

    plt.figure(figsize=(11, 5))
    plt.plot(timestamps, drawdowns, marker="o")
    plt.title("Drawdown Over Time")
    plt.xlabel("Timestamp")
    plt.ylabel("Drawdown (%)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_dir / "drawdown.png")
    plt.close()


def save_step_returns_plot(
    output_dir: Path,
    returns: list[float],
) -> None:
    """Save step returns plot."""
    if not returns:
        return

    step_labels = list(range(1, len(returns) + 1))

    plt.figure(figsize=(11, 5))
    plt.plot(step_labels, [r * 100 for r in returns], marker="o")
    plt.title("Step Returns Over Time")
    plt.xlabel("Step")
    plt.ylabel("Return (%)")
    plt.tight_layout()
    plt.savefig(output_dir / "step_returns.png")
    plt.close()


def save_action_distribution_plot(
    output_dir: Path,
    action_counts: Counter[str],
) -> None:
    """Save action distribution plot."""
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


def save_safety_outcomes_plot(
    output_dir: Path,
    safety_counts: Counter[str],
) -> None:
    """Save safety outcomes plot."""
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


def save_blocked_by_layer_plot(
    output_dir: Path,
    blocked_by_layer_counts: Counter[str],
) -> None:
    """Save blocked-by-layer plot."""
    if not blocked_by_layer_counts:
        return

    labels = list(blocked_by_layer_counts.keys())
    values = list(blocked_by_layer_counts.values())

    plt.figure(figsize=(10, 5))
    plt.bar(labels, values)
    plt.title("Blocked Trades by Safety Layer")
    plt.xlabel("Safety Layer")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.savefig(output_dir / "blocked_by_layer.png")
    plt.close()


def save_strategy_comparison_plot(
    comparison_rows: list[dict[str, Any]],
    output_dir: Path,
) -> None:
    """Save a bar chart comparing final portfolio values across strategies."""
    if not comparison_rows:
        return

    labels = [row["strategy"] for row in comparison_rows]
    values = [row.get("final_portfolio_value", 0.0) for row in comparison_rows]

    plt.figure(figsize=(10, 5))
    plt.bar(labels, values)
    plt.title("Final Portfolio Value by Strategy")
    plt.xlabel("Strategy")
    plt.ylabel("Final Portfolio Value")
    plt.tight_layout()
    plt.savefig(output_dir / "strategy_comparison.png")
    plt.close()


def save_return_comparison_plot(
    comparison_rows: list[dict[str, Any]],
    output_dir: Path,
) -> None:
    """Save a bar chart comparing percentage returns across strategies."""
    if not comparison_rows:
        return

    labels = [row["strategy"] for row in comparison_rows]
    values = [row.get("percentage_return_pct", 0.0) for row in comparison_rows]

    plt.figure(figsize=(10, 5))
    plt.bar(labels, values)
    plt.title("Percentage Return by Strategy")
    plt.xlabel("Strategy")
    plt.ylabel("Percentage Return (%)")
    plt.tight_layout()
    plt.savefig(output_dir / "return_comparison.png")
    plt.close()


def save_scenario_block_rate_plot(
    scenario_summary_rows: list[dict[str, Any]],
    output_dir: Path,
) -> None:
    """Save blocked action rate by adversarial scenario."""
    if not scenario_summary_rows:
        return

    labels = [row["scenario"] for row in scenario_summary_rows]
    values = [row["block_rate_pct"] for row in scenario_summary_rows]

    plt.figure(figsize=(10, 5))
    plt.bar(labels, values)
    plt.title("Blocked Action Rate by Adversarial Scenario")
    plt.xlabel("Scenario")
    plt.ylabel("Blocked Actions (%)")
    plt.tight_layout()
    plt.savefig(output_dir / "scenario_block_rate.png")
    plt.close()


def export_main_outputs(
    *,
    output_dir: Path,
    metrics: dict[str, Any],
    scenario_results: dict[str, Any],
    comparison_rows: list[dict[str, Any]],
    dissertation_rows: list[dict[str, Any]],
    scenario_summary_rows: list[dict[str, Any]],
    blocked_layer_rows: list[dict[str, Any]],
    portfolio_transaction_history: list[dict[str, Any]],
    simulation_log: list[dict[str, Any]],
) -> None:
    """Export CSV files for the main simulation and evaluations."""
    if simulation_log:
        write_csv(output_dir / "simulation_log.csv", simulation_log)

    if portfolio_transaction_history:
        write_csv(output_dir / "transactions.csv", portfolio_transaction_history)

    if metrics:
        write_csv(output_dir / "metrics_summary.csv", [metrics])

    if comparison_rows:
        write_csv(output_dir / "strategy_comparison.csv", comparison_rows)

    if dissertation_rows:
        write_csv(output_dir / "dissertation_results_table.csv", dissertation_rows)

    if scenario_summary_rows:
        write_csv(output_dir / "scenario_summary.csv", scenario_summary_rows)

    if blocked_layer_rows:
        write_csv(output_dir / "blocked_layer_summary.csv", blocked_layer_rows)

    scenario_rows: list[dict[str, Any]] = []
    for scenario_name, data in scenario_results.items():
        row = {"scenario": scenario_name}
        if isinstance(data, dict):
            row.update(data)
        else:
            row["result"] = data
        scenario_rows.append(row)

    if scenario_rows:
        write_csv(output_dir / "scenario_results.csv", scenario_rows)


def print_output_manifest(output_dir: Path) -> None:
    """Print key output file locations."""
    print("\n=== Saved Outputs ===")
    print(output_dir / "simulation_log.csv")
    print(output_dir / "transactions.csv")
    print(output_dir / "metrics_summary.csv")
    print(output_dir / "strategy_comparison.csv")
    print(output_dir / "dissertation_results_table.csv")
    print(output_dir / "scenario_results.csv")
    print(output_dir / "scenario_summary.csv")
    print(output_dir / "blocked_layer_summary.csv")
    print(output_dir / "portfolio_value.png")
    print(output_dir / "cumulative_return.png")
    print(output_dir / "drawdown.png")
    print(output_dir / "step_returns.png")
    print(output_dir / "action_distribution.png")
    print(output_dir / "safety_outcomes.png")
    print(output_dir / "blocked_by_layer.png")
    print(output_dir / "strategy_comparison.png")
    print(output_dir / "return_comparison.png")
    print(output_dir / "scenario_block_rate.png")