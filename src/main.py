"""Entry point for the trading simulation.

This file combine the market feed, agent, safety layer, and broker, then
prints the state transitions to make sure that the flow is easy to inspect from the terminal.
"""

# Import the portfolio model used to hold account state.
from models import Portfolio
# Import the mock market data generator that feeds the simulation loop.
from market import get_mock_market_data
# Import the simple rule-based trading agent.
from agent import SimpleTradingAgent
# Import the component that blocks unsafe trade requests.
from safety import SafetyValidator
# Import the mock broker that applies approved trades to the portfolio.
from broker import MockBroker

portfolio_values = []


# `print_portfolio` centralizes portfolio formatting so the output stays consistent.
def print_portfolio(portfolio: Portfolio) -> None:
    # Show cash with two decimal places to resemble a currency amount.
    print(f"Cash: {portfolio.cash:.2f}")
    # Print the holdings dictionary so we can see owned symbols and share counts.
    print(f"Holdings: {portfolio.holdings}")


# `main` performs one full simulation run from setup through completion.
def main() -> None:
    # Start with a portfolio that has cash but no positions.
    portfolio = Portfolio(cash=1000.0)
    # Load the mock market timeline that the loop will iterate over.
    market_data = get_mock_market_data()
    # Create the agent that will propose trades for each market state.
    agent = SimpleTradingAgent()
    # Configure the safety layer with a maximum allowed trade size.
    safety_validator = SafetyValidator(max_trade_quantity=5)
    # Create the broker that will execute any approved trades.
    broker = MockBroker()

    # Clear any previous run values.
    portfolio_values.clear()

    # Announce the start of the run so terminal output has a clear boundary.
    print("=== Starting Simulation ===")
    # Print the initial account state before any trades occur.
    print_portfolio(portfolio)
    # Add a blank line to separate setup output from the first market tick.
    print()

    # Process each market observation in chronological order.
    for state in market_data:
        # Show which market event is currently being evaluated.
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
        safety_result = safety_validator.validate(proposed_action, portfolio)
        # Show whether the safety layer approved or blocked the action.
        print(f"Safety Check: {'APPROVED' if safety_result.approved else 'BLOCKED'}")
        # Print the explanation for the safety outcome.
        print(f"Safety Reason: {safety_result.reason}")

        # Only execute the trade when the safety layer approves it.
        if safety_result.approved:
            # Apply the trade to the portfolio through the broker abstraction.
            broker.execute_trade(proposed_action, portfolio)
            # Confirm that the approved action was processed.
            print("Execution: Trade processed.")
        else:
            # Make it explicit when the broker was not allowed to run.
            print("Execution: Trade blocked.")

        # Track the portfolio value after this step using the latest market price.
        current_prices = {state.symbol: state.price}
        total_value = portfolio.get_total_value(current_prices)
        portfolio_values.append(total_value)

        # Print the traced prices and resulting cash to verify execution correctness.
        print(
            f"Debug: market price={state.price:.2f}, "
            f"action price={proposed_action.price:.2f}, "
            f"cash={portfolio.cash:.2f}"
        )

        # Print a label before showing the mutated account state.
        print("Updated Portfolio:")
        # Show the portfolio after the current market step has finished.
        print_portfolio(portfolio)
        print(f"Total Portfolio Value: {total_value:.2f}")
        # Print a divider so each loop iteration is visually separated.
        print("-" * 50)

    # Announce that the simulation finished all market ticks.
    print("=== Simulation Complete ===")
    print("\nPortfolio Value Over Time:")
    for i, value in enumerate(portfolio_values):
        print(f"Step {i}: {value:.2f}")


# Standard Python entry-point guard so the script only auto-runs when executed.
if __name__ == "__main__":
    # Start the simulation.
    main()