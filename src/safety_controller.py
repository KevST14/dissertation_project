from models import Portfolio, SafetyDecision, TradeAction
from permission_guard import PermissionGuard
from policy_validator import PolicyValidator
from risk_monitor import RiskMonitor


class SafetyController:
    """
    Runs multiple safety layers in sequence and returns the first blocking decision.
    """

    def __init__(
        self,
        policy_validator: PolicyValidator,
        risk_monitor: RiskMonitor,
        permission_guard: PermissionGuard
    ) -> None:
        self.policy_validator = policy_validator
        self.risk_monitor = risk_monitor
        self.permission_guard = permission_guard

    def validate(self, action: TradeAction, portfolio: Portfolio) -> SafetyDecision:
        permission_result = self.permission_guard.check(action)
        if not permission_result.approved:
            return permission_result

        policy_result = self.policy_validator.validate(action, portfolio)
        if not policy_result.approved:
            return policy_result

        risk_result = self.risk_monitor.assess(action, portfolio)
        if not risk_result.approved:
            return risk_result

        return SafetyDecision(True, "All safety layers passed.", "SafetyController")

    def evaluate(self, action: TradeAction, portfolio: Portfolio) -> SafetyDecision:
        return self.validate(action, portfolio)
