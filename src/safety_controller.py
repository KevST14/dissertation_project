from models import Portfolio, SafetyCheckResult, TradeAction
from permission_guard import PermissionGuard
from policy_validator import PolicyValidator
from risk_monitor import RiskMonitor


class SafetyController:
    """Runs the safety layers in order and stops at the first rejection."""

    def __init__(
        self,
        policy_validator: PolicyValidator,
        risk_monitor: RiskMonitor,
        permission_guard: PermissionGuard,
    ) -> None:
        self.policy_validator = policy_validator
        self.risk_monitor = risk_monitor
        self.permission_guard = permission_guard

    def validate(self, action: TradeAction, portfolio: Portfolio) -> SafetyCheckResult:
        for validator in (
            self.permission_guard,
            self.policy_validator,
            self.risk_monitor,
        ):
            result = validator.validate(action, portfolio)
            if not result.approved:
                return result

        return SafetyCheckResult(
            approved=True,
            layer="safety_controller",
            reason="Trade passed all safety layers.",
        )
