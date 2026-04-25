"""Entry point for the trading simulation and evaluation framework.

This file runs the main trading simulation, evaluates portfolio performance,
exports CSV results, saves plots, and compares the full system against
benchmarks such as buy-and-hold and a no-safety execution mode.
"""

from pathlib import Path

from evaluation_runner import run_full_evaluation


def main() -> None:
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    run_full_evaluation(output_dir)


if __name__ == "__main__":
    main()