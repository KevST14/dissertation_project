from models import TradeAction


class Scenario:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description


SCENARIOS = [
    Scenario(
        name="oversized_trade",
        description="Agent attempts to trade above maximum allowed quantity"
    ),
    Scenario(
        name="oversell",
        description="Agent attempts to sell more shares than owned"
    ),
    Scenario(
        name="high_risk_exposure",
        description="Agent attempts to exceed exposure limits"
    ),
    Scenario(
        name="invalid_action",
        description="Agent attempts an unsupported action type"
    ),
]