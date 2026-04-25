from collections import Counter
from typing import Any


def build_scenario_summary(scenario_results: dict[str, Any]) -> list[dict[str, Any]]:
    """Build a flat summary table for adversarial scenario results."""
    rows: list[dict[str, Any]] = []

    for scenario_name, data in scenario_results.items():
        approved = int(data.get("approved", 0))
        blocked = int(data.get("blocked", 0))
        total = approved + blocked

        block_rate = (blocked / total) * 100 if total > 0 else 0.0
        approval_rate = (approved / total) * 100 if total > 0 else 0.0

        rows.append(
            {
                "scenario": scenario_name,
                "approved_actions": approved,
                "blocked_actions": blocked,
                "total_actions": total,
                "block_rate_pct": round(block_rate, 4),
                "approval_rate_pct": round(approval_rate, 4),
            }
        )

    return rows


def summarise_blocked_layers(blocked_layers: Counter[str]) -> list[dict[str, Any]]:
    """Build a flat summary table for blocked counts per safety layer."""
    rows: list[dict[str, Any]] = []

    for layer, count in blocked_layers.items():
        rows.append(
            {
                "layer": layer,
                "blocked_count": count,
            }
        )

    return rows