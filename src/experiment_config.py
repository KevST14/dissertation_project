from dataclasses import dataclass, field


@dataclass
class ExperimentConfig:
    """Central configuration for evaluation runs."""
    initial_cash: float = 1000.0
    max_trade_quantity: int = 5
    max_position_fraction: float = 0.30
    allowed_actions: set[str] = field(default_factory=lambda: {"BUY", "SELL", "HOLD"})
    run_benchmarks: bool = True
    run_adversarial_tests: bool = True
    repeat_runs: int = 1