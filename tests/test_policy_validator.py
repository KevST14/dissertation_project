from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from models import Portfolio, TradeAction
from policy_validator import PolicyValidator


def test_policy_validator_blocks_oversized_trades() -> None:
    validator = PolicyValidator(max_trade_quantity=5)
    portfolio = Portfolio(cash=5000.0)
    action = TradeAction(
        action_type="BUY",
        symbol="AAPL",
        quantity=6,
        price=100.0,
        reasoning="Attempt an oversized order.",
    )

    result = validator.validate(action, portfolio)

    assert result.approved is False
    assert result.layer == "PolicyValidator"
    assert "maximum allowed limit" in result.reason
