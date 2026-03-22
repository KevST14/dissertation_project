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
# Import the mock broker that applies approved trades to the portfolio.
from broker import MockBroker

# Safety system components
from policy_validator import PolicyValidator
from risk_monitor import RiskMonitor
from permission_guard import PermissionGuard
from safety_controller import SafetyController

# Experiment runner
from experiments import run_all_scenarios

portfolio_values = []


# `print_portfolio` centralizes portfolio formatting so the output stays consistent.
def print_portfolio(portfolio: Portfolio) -> None:
    print(f"Cash: {portfolio.cash:.2f}")
    print(f"Holdings: {portfolio.holdings}")


# `main` performs one full simulation run from setup through completion.
def main() -> None:
    portfolio = Portfolio(cash=1000.0)
    market_data = get_mock_market_data()
    agent = SimpleTradingAgent()

    # Safety system setup
    policy_validator = PolicyValidator(max_trade_quantity=5)
    risk_monitor = RiskMonitor(max_position_fraction=0.30)
    permission_guard = PermissionGuard(allowed_actions={"BUY", "SELL", "HOLD"})
    safety_controller = SafetyController(
        policy_validator=policy_validator,
        risk_monitor=risk_monitor,
        permission_guard=permission_guard
    )

    broker = MockBroker()

    portfolio_values.clear()

    print("=== Starting Simulation ===")
    print_portfolio(portfolio)
    print()

    for state in market_data:
        print(f"Timestamp: {state.timestamp}")
        print(f"Market: {state.symbol} @ {state.price:.2f}")

        proposed_action = agent.decide(state, portfolio)

        print(
            f"Agent Decision: {proposed_action.action_type} "
            f"{proposed_action.quantity} {proposed_action.symbol}"
        )
        print(f"Action Price: {proposed_action.price:.2f}")
        print(f"Reasoning: {proposed_action.reasoning}")

        safety_result = safety_controller.validate(proposed_action, portfolio)

        print(f"Safety Check: {'APPROVED' if safety_result.approved else 'BLOCKED'}")
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

        print(
            f"Debug: market price={state.price:.2f}, "
            f"action price={proposed_action.price:.2f}, "
            f"cash={portfolio.cash:.2f}"
        )

        print("Updated Portfolio:")
        print_portfolio(portfolio)
        print(f"Total Portfolio Value: {total_value:.2f}")
        print("-" * 50)

    print("=== Simulation Complete ===")

    print("\nPortfolio Value Over Time:")
    for i, value in enumerate(portfolio_values):
        print(f"Step {i}: {value:.2f}")

    # ✅ Adversarial testing section (CORRECT placement)
    print("\n=== Running Adversarial Tests ===")
    results = run_all_scenarios()

    print("\nScenario Results:")
    for scenario, data in results.items():
        print(f"{scenario}: {data}")


# Standard Python entry-point guard so the script only auto-runs when executed.
if __name__ == "__main__":
    main()