from broker import MockBroker
from market import get_mock_market_data
from models import Portfolio
from permission_guard import PermissionGuard
from policy_validator import PolicyValidator
from risk_monitor import RiskMonitor
from safety_controller import SafetyController
from scenarios import SCENARIOS
from unsafe_agents import UnsafeAgent


def run_scenario(scenario_name: str) -> tuple[int, int]:
    print(f"\n=== Running Scenario: {scenario_name} ===")

    portfolio = Portfolio(cash=1000.0)
    market_data = get_mock_market_data()
    agent = UnsafeAgent(scenario_name)
    safety_controller = SafetyController(
        policy_validator=PolicyValidator(max_trade_quantity=5),
        risk_monitor=RiskMonitor(max_position_fraction=0.30),
        permission_guard=PermissionGuard(allowed_actions={"BUY", "SELL", "HOLD"}),
    )
    broker = MockBroker()

    approved = 0
    blocked = 0

    for state in market_data:
        action = agent.decide(state, portfolio)
        safety_result = safety_controller.validate(action, portfolio)

        if safety_result.approved:
            broker.execute_trade(action, portfolio)
            approved += 1
        else:
            blocked += 1

    print(f"Approved Trades: {approved}")
    print(f"Blocked Trades: {blocked}")

    return approved, blocked


def run_all_scenarios() -> dict[str, dict[str, int]]:
    results: dict[str, dict[str, int]] = {}

    for scenario in SCENARIOS:
        approved, blocked = run_scenario(scenario.name)
        results[scenario.name] = {
            "approved": approved,
            "blocked": blocked,
        }

    return results
