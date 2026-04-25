from typing import Any


def build_dissertation_results_table(
    strategy_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Create a compact dissertation-friendly comparison table."""
    table_rows: list[dict[str, Any]] = []

    for row in strategy_rows:
        table_rows.append(
            {
                "strategy": row.get("strategy"),
                "final_value": row.get("final_portfolio_value"),
                "return_pct": row.get("percentage_return_pct"),
                "max_drawdown_pct": row.get("max_drawdown_pct"),
                "volatility_pct": row.get("step_return_volatility_pct"),
                "transactions": row.get("transactions_recorded"),
                "approved_actions": row.get("approved_actions", 0),
                "blocked_actions": row.get("blocked_actions", 0),
                "safety_intervention_rate_pct": row.get("safety_intervention_rate_pct", 0.0),
            }
        )

    return table_rows