"""Core data structures shared across the trading simulation.

This module defines the common data models used across the system so all
components (agent, broker, safety layer, etc.) operate on consistent structures.
"""

# `dataclass` reduces boilerplate for data containers.
# `field` is used for safe defaults on mutable types like dict and list.
from dataclasses import dataclass, field
# Typing improves clarity and helps with static analysis.
from typing import Dict, List, Optional


# `MarketState` represents a single market observation at a point in time.
@dataclass
class MarketState:
    # `symbol` identifies the asset (e.g., AAPL, BTC).
    symbol: str
    # `price` is the observed market price for this tick.
    price: float
    # `timestamp` indicates when this data point occurred.
    timestamp: str


# `Portfolio` represents the evolving account state during the simulation.
@dataclass
class Portfolio:
    # `cash` is the available balance not currently invested.
    cash: float
    # `holdings` maps symbols to share quantities.
    holdings: Dict[str, int] = field(default_factory=dict)
    # `transaction_history` logs executed trades for traceability.
    transaction_history: List[dict] = field(default_factory=list)

    # Returns the number of shares held for a given symbol.
    def get_position(self, symbol: str) -> int:
        return self.holdings.get(symbol, 0)

    # Updates the position after a trade is executed.
    def update_position(self, symbol: str, quantity_change: int) -> None:
        current = self.get_position(symbol)
        new_quantity = current + quantity_change

        # Prevent invalid negative holdings.
        if new_quantity < 0:
            raise ValueError(f"Cannot have negative holdings for {symbol}.")

        # Remove symbol if position becomes zero to keep data clean.
        if new_quantity == 0:
            self.holdings.pop(symbol, None)
        else:
            self.holdings[symbol] = new_quantity

    # Records a transaction for audit/debug purposes.
    def record_transaction(self, transaction: dict) -> None:
        self.transaction_history.append(transaction)

    # Computes total portfolio value (cash + value of holdings).
    def get_total_value(self, current_prices: Dict[str, float]) -> float:
        holdings_value = sum(
            quantity * current_prices.get(symbol, 0.0)
            for symbol, quantity in self.holdings.items()
        )
        return self.cash + holdings_value


# `TradeAction` represents a decision made by the agent.
@dataclass
class TradeAction:
    # `action_type` should be BUY, SELL, or HOLD.
    action_type: str
    # `symbol` is the asset being traded.
    symbol: str
    # `quantity` is the number of shares involved.
    quantity: int
    # `price` is the execution or intended trade price.
    price: float
    # `reasoning` is an optional explanation from the agent.
    reasoning: Optional[str] = None


# `SafetyDecision` captures the result of safety validation.
@dataclass
class SafetyDecision:
    # `approved` indicates whether the trade can proceed.
    approved: bool
    # `reason` explains why the decision was made.
    reason: str
    # `layer` identifies which safety rule or component made the decision.
    layer: str