from models import SafetyDecision, TradeAction


class PermissionGuard:
    """
    Restricts which action types are permitted at runtime.
    """

    def __init__(self, allowed_actions: set[str] | None = None) -> None:
        self.allowed_actions = allowed_actions or {"BUY", "SELL", "HOLD"}

    def check(self, action: TradeAction) -> SafetyDecision:
        if action.action_type not in self.allowed_actions:
            return SafetyDecision(
                False,
                f"Action type '{action.action_type}' is not permitted.",
                "PermissionGuard"
            )

        return SafetyDecision(True, "Permission check passed.", "PermissionGuard")