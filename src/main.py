"""Entry point for the trading simulation.

This file combines the market feed, agent, safety layer, broker, and
evaluation utilities into one executable script.

It prints state transitions to the terminal so the simulation is easy to
inspect, then outputs summary statistics and a simple portfolio value chart
for analysis.
"""

# Standard library import used for safe directory creation when saving plots.
from pathlib import Path

# Third-party plotting library for dissertation-friendly visual output.
import matplotlib.pyplot as plt

# Import the portfolio model used to hold account state.
from models import Portfolio
# Import the mock market data generator that feeds the simulation loop.
from market import get_mock_market_data
# Import the simple rule-based trading agent.
from agent import SimpleTradingAgent
# Import the mock broker that applies approved trades to the portfolio.
from broker import MockBroker

# Import safety system components.
from policy_validator import PolicyValidator
from risk_monitor import RiskMonitor
from permission_guard import PermissionGuard
from safety_controller import SafetyController

# Import experiment runner for adversarial testing.
from experiments import run_all_scenarios

# Stores total portfolio value at each step for later reporting and plotting.
portfolio_values = []
# Stores timestamps so the value series can be labelled clearly.
portfolio_timestamps = []


# `print_portfolio` centralizes portfolio formatting so the output stays consistent.
def print_portfolio(portfolio: Portfolio) -> None:
    # Show cash with two decimal places to resemble a currency amount.
    print(f"Cash: {portfolio.cash:.2f}")
    # Print the holdings dictionary so we can see owned symbols and share counts.
    print(f"Holdings: {portfolio.holdings}")


# `print_summary_metrics` reports final performance indicators.
def print_summary_metrics(portfolio: Portfolio) -> None:
    # If no values were recorded, there is nothing meaningful to summarise.
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

    print("\n=== Performance Summary ===")
    print(f"Initial Portfolio Value: {initial_value:.2f}")
    print(f"Final Portfolio Value: {final_value:.2f}")
    print(f"Absolute Return: {absolute_return:.2f}")
    print(f"Percentage Return: {percentage_return:.2f}%")
    print(f"Maximum Portfolio Value: {max_value:.2f}")
    print(f"Minimum Portfolio Value: {min_value:.2f}")
    print(f"Transactions Recorded: {len(portfolio.transaction_history)}")


# `plot_portfolio_value` creates a simple line chart of portfolio value over time.
def plot_portfolio_value() -> None:
    # Skip plotting if no values are available.
    if not portfolio_values:
        print("No portfolio values available to plot.")
        return

    # Create output directory if it does not already exist.
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    plt.figure(figsize=(10, 5))
    plt.plot(portfolio_timestamps, portfolio_values, marker="o")
    plt.title("Portfolio Value Over Time")
    plt.xlabel("Timestamp")
    plt.ylabel("Portfolio Value")
    plt.xticks(rotation=45)
    plt.tight_layout()

    output_path = output_dir / "portfolio_value.png"
    plt.savefig(output_path)
    plt.close()

    print(f"\nPortfolio value chart saved to: {output_path}")


# `main` performs one full simulation run from setup through completion.
def main() -> None:
    # Start with a portfolio that has cash but no positions.
    portfolio = Portfolio(cash=1000.0)
    # Load the mock market timeline that the loop will iterate over.
    market_data = get_mock_market_data()
    # Create the agent that will propose trades for each market state.
    agent = SimpleTradingAgent()

    # Configure the safety architecture.
    policy_validator = PolicyValidator(max_trade_quantity=5)
    risk_monitor = RiskMonitor(max_position_fraction=0.30)
    permission_guard = PermissionGuard(allowed_actions={"BUY", "SELL", "HOLD"})
    safety_controller = SafetyController(
        policy_validator=policy_validator,
        risk_monitor=risk_monitor,
        permission_guard=permission_guard,
    )

    # Create the broker that will execute any approved trades.
    broker = MockBroker()

    # Clear any previous run values.
    portfolio_values.clear()
    portfolio_timestamps.clear()

    # Announce the start of the run so terminal output has a clear boundary.
    print("=== Starting Simulation ===")
    # Print the initial account state before any trades occur.
    print_portfolio(portfolio)
    # Add a blank line to separate setup output from the first market tick.
    print()

    # Process each market observation in chronological order.
    for step, state in enumerate(market_data, start=1):
        # Show which step and market event is currently being evaluated.
        print(f"Step: {step}")
        print(f"Timestamp: {state.timestamp}")
        # Show the asset and price the agent is about to react to.
        print(f"Market: {state.symbol} @ {state.price:.2f}")

        # Ask the agent to produce a proposed action for this market state.
        proposed_action = agent.decide(state, portfolio)

        # Print the core trade decision in a compact single-line format.
        print(
            f"Agent Decision: {proposed_action.action_type} "
            f"{proposed_action.quantity} {proposed_action.symbol}"
        )
        # Print the price attached to the action so it can be compared to the market tick.
        print(f"Action Price: {proposed_action.price:.2f}")
        # Print the human-readable explanation returned by the agent.
        print(f"Reasoning: {proposed_action.reasoning}")

        # Run the proposed trade through the safety guardrails.
        safety_result = safety_controller.validate(proposed_action, portfolio)

        # Show whether the safety layer approved or blocked the action.
        print(f"Safety Check: {'APPROVED' if safety_result.approved else 'BLOCKED'}")
        # Print the layer responsible for the safety decision.
        print(f"Safety Layer: {safety_result.layer}")
        # Print the explanation for the safety outcome.
        print(f"Safety Reason: {safety_result.reason}")

        # Only execute the trade when the safety layer approves it.
        if safety_result.approved:
            broker.execute_trade(proposed_action, portfolio)
            print("Execution: Trade processed.")
        else:
            print("Execution: Trade blocked.")

        # Track the portfolio value after this step using the latest market price.
        current_prices = {state.symbol: state.price}
        total_value = portfolio.get_total_value(current_prices)
        portfolio_values.append(total_value)
        portfolio_timestamps.append(state.timestamp)

        # Print the traced prices and resulting cash to verify execution correctness.
        print(
            f"Debug: market price={state.price:.2f}, "
            f"action price={proposed_action.price:.2f}, "
            f"cash={portfolio.cash:.2f}"
        )

        # Print a label before showing the mutated account state.
        print("Updated Portfolio:")
        print_portfolio(portfolio)
        print(f"Total Portfolio Value: {total_value:.2f}")
        print("-" * 50)

    # Announce that the simulation finished all market ticks.
    print("=== Simulation Complete ===")

    print("\nPortfolio Value Over Time:")
    for i, value in enumerate(portfolio_values):
        print(f"Step {i + 1}: {value:.2f}")

    # Print summary performance metrics for analysis.
    print_summary_metrics(portfolio)

    # Save a chart showing how the portfolio value evolved.
    plot_portfolio_value()

    # Run adversarial scenario testing after the main simulation.
    print("\n=== Running Adversarial Tests ===")
    results = run_all_scenarios()

    print("\nScenario Results:")
    for scenario, data in results.items():
        print(f"{scenario}: {data}")


# Standard Python entry-point guard so the script only auto-runs when executed.
if __name__ == "__main__":
    main()