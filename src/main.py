"""Thin entry point for the dissertation evaluation pipeline."""

from pathlib import Path

from evaluation_runner import run_full_evaluation


def main() -> None:
    """Create the output directory and run the full evaluation."""
    output_dir = Path(__file__).resolve().parent.parent / "outputs"
    output_dir.mkdir(exist_ok=True)
    run_full_evaluation(output_dir)


if __name__ == "__main__":
    main()
