"""Simulation and evaluation orchestration for the dissertation project."""

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agent import SimpleTradingAgent
from benchmarks import run_buy_and_hold_benchmark, run_no_safety_benchmark
from broker import MockBroker
from experiments import run_all_scenarios
from market import get_mock_market_data
from models import Portfolio
from permission_guard import PermissionGuard
from policy_validator import PolicyValidator
from reporting import (
    build_metrics_summary,
    export_main_outputs,
    print_output_manifest,
    print_portfolio,
    print_summary_metrics,
    save_action_distribution_plot,
    save_blocked_by_layer_plot,
    save_cumulative_return_plot,
    save_drawdown_plot,
    save_portfolio_value_plot,
    save_return_comparison_plot,
    save_safety_outcomes_plot,
    save_step_returns_plot,
    save_strategy_comparison_plot,
)
from risk_monitor import RiskMonitor
from safety_controller import SafetyController


@dataclass
class SimulationTrace:
    """In-memory records collected during one simulation run."""

    portfolio_values: list[float] = field(default_factory=list)
    portfolio_timestamps: list[str] = field(default_factory=list)
    step_returns: list[float] = field(default_factory=list)
    action_counts: Counter[str] = field(default_factory=Counter)
    safety_counts: Counter[str] = field(default_factory=Counter)
    blocked_by_layer_counts: Counter[str] = field(default_factory=Counter)
    simulation_log: list[dict[str, Any]] = field(default_factory=list)


def run_main_simulation(initial_cash: float = 1000.0) -> tuple[Portfolio, SimulationTrace]:
    """Run the main safety-enabled simulation."""
    portfolio = Portfolio(cash=initial_cash)
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
    trace = SimulationTrace()

    print("=== Starting Simulation ===")
    print_portfolio(portfolio)
    print()

    previous_total_value = portfolio.cash

    for step, state in enumerate(market_data, start=1):
        print(f"Step: {step}")
        print(f"Timestamp: {state.timestamp}")
        print(f"Market: {state.symbol} @ {state.price:.2f}")

        proposed_action = agent.decide(state, portfolio)
        trace.action_counts[proposed_action.action_type] += 1

        print(
            f"Agent Decision: {proposed_action.action_type} "
            f"{proposed_action.quantity} {proposed_action.symbol}"
        )
        print(f"Action Price: {proposed_action.price:.2f}")
        print(f"Reasoning: {proposed_action.reasoning}")

        safety_result = safety_controller.validate(proposed_action, portfolio)
        safety_label = "APPROVED" if safety_result.approved else "BLOCKED"
        trace.safety_counts[safety_label] += 1

        if not safety_result.approved:
            trace.blocked_by_layer_counts[safety_result.layer] += 1

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
        trace.portfolio_values.append(total_value)
        trace.portfolio_timestamps.append(state.timestamp)

        step_return = (
            (total_value - previous_total_value) / previous_total_value
            if previous_total_value != 0
            else 0.0
        )
        trace.step_returns.append(step_return)

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

        trace.simulation_log.append(
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
    return portfolio, trace


def run_full_evaluation(output_dir: Path) -> None:
    """Run the full evaluation pipeline and generate outputs."""
    portfolio, trace = run_main_simulation()

    metrics = build_metrics_summary(
        label="full_safety_system",
        values=trace.portfolio_values,
        returns=trace.step_returns,
        transaction_history=portfolio.transaction_history,
        action_counter=trace.action_counts,
        safety_counter=trace.safety_counts,
    )
    print_summary_metrics(metrics)

    save_portfolio_value_plot(
        output_dir=output_dir,
        timestamps=trace.portfolio_timestamps,
        values=trace.portfolio_values,
    )
    save_cumulative_return_plot(
        output_dir=output_dir,
        timestamps=trace.portfolio_timestamps,
        values=trace.portfolio_values,
    )
    save_drawdown_plot(
        output_dir=output_dir,
        timestamps=trace.portfolio_timestamps,
        values=trace.portfolio_values,
    )
    save_step_returns_plot(output_dir=output_dir, returns=trace.step_returns)
    save_action_distribution_plot(
        output_dir=output_dir,
        action_counts=trace.action_counts,
    )
    save_safety_outcomes_plot(
        output_dir=output_dir,
        safety_counts=trace.safety_counts,
    )
    save_blocked_by_layer_plot(
        output_dir=output_dir,
        blocked_by_layer_counts=trace.blocked_by_layer_counts,
    )

    print("\n=== Running Benchmark Comparisons ===")
    buy_hold_metrics = run_buy_and_hold_benchmark()
    no_safety_metrics = run_no_safety_benchmark()
    comparison_rows = [metrics, buy_hold_metrics, no_safety_metrics]
    save_strategy_comparison_plot(
        comparison_rows=comparison_rows,
        output_dir=output_dir,
    )
    save_return_comparison_plot(
        comparison_rows=comparison_rows,
        output_dir=output_dir,
    )
    print_summary_metrics(buy_hold_metrics)
    print_summary_metrics(no_safety_metrics)

    print("\n=== Running Adversarial Tests ===")
    scenario_results = run_all_scenarios()

    print("\nScenario Results:")
    for scenario, data in scenario_results.items():
        print(f"{scenario}: {data}")

    export_main_outputs(
        output_dir=output_dir,
        metrics=metrics,
        scenario_results=scenario_results,
        comparison_rows=comparison_rows,
        portfolio=portfolio,
        simulation_log=trace.simulation_log,
    )
    print_output_manifest(output_dir)
