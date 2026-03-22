from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from models import Portfolio, TradeAction
from permission_guard import PermissionGuard
from policy_validator import PolicyValidator
from risk_monitor import RiskMonitor
from safety_controller import SafetyController


def test_safety_controller_blocks_invalid_action_type_via_permission_guard() -> None:
    controller = SafetyController(
        policy_validator=PolicyValidator(max_trade_quantity=5),
        risk_monitor=RiskMonitor(max_position_fraction=0.30),
        permission_guard=PermissionGuard(allowed_actions={"BUY", "SELL", "HOLD"}),
    )
    portfolio = Portfolio(cash=1000.0)
    action = TradeAction(
        action_type="SHORT",
        symbol="AAPL",
        quantity=1,
        price=100.0,
        reasoning="Use a disallowed action type.",
    )

    result = controller.validate(action, portfolio)

    assert result.approved is False
    assert result.layer == "PermissionGuard"
    assert "not permitted" in result.reason
