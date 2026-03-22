from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from models import Portfolio, TradeAction
from risk_monitor import RiskMonitor


def test_risk_monitor_blocks_excessive_exposure() -> None:
    monitor = RiskMonitor(max_position_fraction=0.30)
    portfolio = Portfolio(cash=1000.0)
    action = TradeAction(
        action_type="BUY",
        symbol="AAPL",
        quantity=4,
        price=100.0,
        reasoning="Create excessive concentration.",
    )

    result = monitor.assess(action, portfolio)

    assert result.approved is False
    assert result.layer == "RiskMonitor"
    assert "exceeding limit" in result.reason
