from collections import Counter

from models import Portfolio
from market import get_mock_market_data
from broker import MockBroker
from policy_validator import PolicyValidator
from risk_monitor import RiskMonitor
from permission_guard import PermissionGuard
from safety_controller import SafetyController
from unsafe_agents import UnsafeAgent
from scenarios import SCENARIOS


def run_scenario(scenario_name: str) -> dict[str, object]:
    """Run one adversarial scenario and return structured results."""
    print(f"\n=== Running Scenario: {scenario_name} ===")

    portfolio = Portfolio(cash=1000.0)
    market_data = get_mock_market_data()
    agent = UnsafeAgent(scenario_name)

    safety_controller = SafetyController(
        policy_validator=PolicyValidator(),
        risk_monitor=RiskMonitor(),
        permission_guard=PermissionGuard()
    )

    broker = MockBroker()

    blocked = 0
    approved = 0
    blocked_layers: Counter[str] = Counter()

    for state in market_data:
        action = agent.decide(state, portfolio)
        safety_result = safety_controller.evaluate(action, portfolio)

        if safety_result.approved:
            broker.execute_trade(action, portfolio)
            approved += 1
        else:
            blocked += 1
            blocked_layers[safety_result.layer] += 1

    print(f"Approved Trades: {approved}")
    print(f"Blocked Trades: {blocked}")
    print(f"Blocked by Layer: {dict(blocked_layers)}")

    return {
        "approved": approved,
        "blocked": blocked,
        "blocked_by_layer": dict(blocked_layers),
    }


def run_all_scenarios() -> dict[str, dict[str, object]]:
    """Run all configured adversarial scenarios."""
    results: dict[str, dict[str, object]] = {}

    for scenario in SCENARIOS:
        results[scenario.name] = run_scenario(scenario.name)

    return results
