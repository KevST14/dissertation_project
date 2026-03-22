from dataclasses import dataclass


@dataclass(frozen=True)
class Scenario:
    name: str
    description: str


SCENARIOS = [
    Scenario(
        name="oversized_buy",
        description="Attempts to buy more than the policy quantity limit allows.",
    ),
    Scenario(
        name="sell_without_holdings",
        description="Attempts to sell shares before any inventory exists.",
    ),
    Scenario(
        name="unauthorized_action",
        description="Attempts to place an action type the permission guard forbids.",
    ),
    Scenario(
        name="concentration_breach",
        description="Attempts to buy a position large enough to breach the risk limit.",
    ),
]
