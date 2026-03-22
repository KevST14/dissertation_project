from models import Portfolio, SafetyCheckResult, TradeAction


class PermissionGuard:
    """Checks whether the requested action type is permitted."""

    def __init__(self, allowed_actions: set[str]) -> None:
        self.allowed_actions = allowed_actions

    def validate(self, action: TradeAction, portfolio: Portfolio) -> SafetyCheckResult:
        del portfolio

        if action.action_type not in self.allowed_actions:
            return SafetyCheckResult(
                approved=False,
                layer="permission_guard",
                reason=f"Action type {action.action_type} is not permitted.",
            )

        return SafetyCheckResult(
            approved=True,
            layer="permission_guard",
            reason="Action is permitted.",
        )
