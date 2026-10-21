from pathlib import Path
from collections import Counter
from typing import Any

from models import Portfolio
from market import get_mock_market_data
from agent import SimpleTradingAgent
from broker import MockBroker
from policy_validator import PolicyValidator
from risk_monitor import RiskMonitor
from permission_guard import PermissionGuard
from safety_controller import SafetyController
from experiments import run_all_scenarios
from benchmarks import run_buy_and_hold_benchmark, run_no_safety_benchmark
from experiment_config import ExperimentConfig
from scenario_analysis import build_scenario_summary, summarise_blocked_layers
from results_table import build_dissertation_results_table
from reporting import (
    build_metrics_summary,
    print_summary_metrics,
    save_portfolio_value_plot,
    save_cumulative_return_plot,
    save_drawdown_plot,
    save_step_returns_plot,
    save_action_distribution_plot,
    save_safety_outcomes_plot,
    save_blocked_by_layer_plot,
    save_strategy_comparison_plot,
    save_return_comparison_plot,
    save_scenario_block_rate_plot,
    export_main_outputs,
    print_output_manifest,
)


def print_portfolio(portfolio: Portfolio) -> None:
    """Print portfolio state in a consistent terminal format."""
    print(f"Cash: {portfolio.cash:.2f}")
    print(f"Holdings: {portfolio.holdings}")


def run_full_evaluation(
    output_dir: Path,
    config: ExperimentConfig | None = None,
) -> None:
    """Run the full safety-enabled evaluation pipeline."""
    config = config or ExperimentConfig()

    portfolio = Portfolio(cash=config.initial_cash)
    market_data = get_mock_market_data()
    agent = SimpleTradingAgent()

    policy_validator = PolicyValidator(max_trade_quantity=config.max_trade_quantity)
    risk_monitor = RiskMonitor(max_position_fraction=config.max_position_fraction)
    permission_guard = PermissionGuard(allowed_actions=config.allowed_actions)

    safety_controller = SafetyController(
        policy_validator=policy_validator,
        risk_monitor=risk_monitor,
        permission_guard=permission_guard,
    )

    broker = MockBroker()

    portfolio_values: list[float] = []
    portfolio_timestamps: list[str] = []
    step_returns: list[float] = []
    action_counts: Counter[str] = Counter()
    safety_counts: Counter[str] = Counter()
    blocked_by_layer_counts: Counter[str] = Counter()
    simulation_log: list[dict[str, Any]] = []

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

        safety_result = safety_controller.evaluate(proposed_action, portfolio)
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
        print("-" * 60)

        simulation_log.append(
            {
                "step": step,
                "timestamp": state.timestamp,
                "symbol": state.symbol,
                "market_price": round(state.price, 4),
                "action_type": proposed_action.action_type,
                "action_quantity": proposed_action.quantity,
                "action_price": round(proposed_action.price, 4),
                "reasoning": proposed_action.reasoning,
                "safety_outcome": safety_label,
                "safety_layer": safety_result.layer,
                "safety_reason": safety_result.reason,
                "cash": round(portfolio.cash, 4),
                "holdings": str(portfolio.holdings),
                "portfolio_value": round(total_value, 4),
                "step_return_pct": round(step_return * 100, 4),
            }
        )

        previous_total_value = total_value

    print("=== Simulation Complete ===")

    metrics = build_metrics_summary(
        label="full_safety_system",
        values=portfolio_values,
        returns=step_returns,
        transaction_history=portfolio.transaction_history,
        action_counter=action_counts,
        safety_counter=safety_counts,
    )
    print_summary_metrics(metrics)

    save_portfolio_value_plot(output_dir, portfolio_timestamps, portfolio_values)
    save_cumulative_return_plot(output_dir, portfolio_timestamps, portfolio_values)
    save_drawdown_plot(output_dir, portfolio_timestamps, portfolio_values)
    save_step_returns_plot(output_dir, step_returns)
    save_action_distribution_plot(output_dir, action_counts)
    save_safety_outcomes_plot(output_dir, safety_counts)
    save_blocked_by_layer_plot(output_dir, blocked_by_layer_counts)

    comparison_rows: list[dict[str, Any]] = [metrics]

    if config.run_benchmarks:
        print("\n=== Running Benchmark Comparisons ===")
        buy_hold_metrics = run_buy_and_hold_benchmark(initial_cash=config.initial_cash)
        no_safety_metrics = run_no_safety_benchmark(initial_cash=config.initial_cash)

        comparison_rows.extend([buy_hold_metrics, no_safety_metrics])

        print_summary_metrics(buy_hold_metrics)
        print_summary_metrics(no_safety_metrics)

        save_strategy_comparison_plot(comparison_rows, output_dir)
        save_return_comparison_plot(comparison_rows, output_dir)

    scenario_results: dict[str, Any] = {}
    scenario_summary_rows: list[dict[str, Any]] = []
    blocked_layer_rows: list[dict[str, Any]] = []

    if config.run_adversarial_tests:
        print("\n=== Running Adversarial Tests ===")
        scenario_results = run_all_scenarios()

        print("\nScenario Results:")
        for scenario, data in scenario_results.items():
            print(f"{scenario}: {data}")

        scenario_summary_rows = build_scenario_summary(scenario_results)

        combined_blocked_layers: Counter[str] = Counter()
        for scenario_data in scenario_results.values():
            for layer, count in scenario_data.get("blocked_by_layer", {}).items():
                combined_blocked_layers[layer] += count

        blocked_layer_rows = summarise_blocked_layers(combined_blocked_layers)

        save_scenario_block_rate_plot(scenario_summary_rows, output_dir)

    dissertation_rows = build_dissertation_results_table(comparison_rows)

    export_main_outputs(
        output_dir=output_dir,
        metrics=metrics,
        scenario_results=scenario_results,
        comparison_rows=comparison_rows,
        dissertation_rows=dissertation_rows,
        scenario_summary_rows=scenario_summary_rows,
        blocked_layer_rows=blocked_layer_rows,
        portfolio_transaction_history=portfolio.transaction_history,
        simulation_log=simulation_log,
    )

    print_output_manifest(output_dir)