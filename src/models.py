"""Core data structures shared across the trading simulation.

This module keeps the data model in one place so the other files can agree on
what a market tick, a portfolio snapshot, a proposed trade, and a safety
decision look like.
"""

# `dataclass` reduces boilerplate for classes that mostly store data.
# `field` is used to give mutable attributes a safe default factory.
from dataclasses import dataclass, field


# `MarketState` represents one point-in-time view of the market.
# The agent consumes these records one by one during the simulation loop.
@dataclass(frozen=True)
class MarketState:
    # `timestamp` tells us when this market observation happened.
    timestamp: str
    # `symbol` identifies which asset the price belongs to.
    symbol: str
    # `price` is the observed market price for this tick.
    price: float


# `Portfolio` tracks the account state that changes as trades are executed.
@dataclass
class Portfolio:
    # `cash` is the uninvested balance available for future buys.
    cash: float
    # `holdings` maps each symbol to the number of shares currently owned.
    # `default_factory=dict` avoids sharing the same dictionary across instances.
    holdings: dict[str, int] = field(default_factory=dict)
    # `transactions` stores a simple audit trail of executed trades.
    transactions: list[dict[str, str | int | float]] = field(default_factory=list)

    # `get_position` centralizes how the rest of the code reads a holding.
    # Returning `0` for missing symbols keeps callers simple.
    def get_position(self, symbol: str) -> int:
        # `dict.get(..., 0)` means "return the share count if present, else 0."
        return self.holdings.get(symbol, 0)

    # `update_position` applies a share delta after a buy or sell.
    # Keeping the rule here prevents each caller from duplicating portfolio logic.
    def update_position(self, symbol: str, quantity_change: int) -> None:
        # Read the current position first so we can calculate the new total.
        current_quantity = self.get_position(symbol)
        # Add the requested change to the existing number of shares.
        new_quantity = current_quantity + quantity_change

        # Negative positions are not allowed in this simple simulation.
        if new_quantity < 0:
            raise ValueError(f"Cannot have negative holdings for {symbol}.")

        # Removing zero-share positions keeps the holdings dictionary clean.
        if new_quantity == 0:
            self.holdings.pop(symbol, None)
        else:
            # Any positive result is stored back into the holdings map.
            self.holdings[symbol] = new_quantity

    # `record_transaction` appends one executed trade to the audit log.
    def record_transaction(self, transaction: dict[str, str | int | float]) -> None:
        # Store a shallow copy so later callers do not mutate the saved record.
        self.transactions.append(dict(transaction))

    # `get_total_value` combines cash with the marked-to-market value of holdings.
    def get_total_value(self, current_prices: dict[str, float]) -> float:
        # Start with the cash balance because it already contributes to total value.
        total_value = self.cash

        # Add each position valued at the latest provided market price.
        for symbol, quantity in self.holdings.items():
            total_value += quantity * current_prices.get(symbol, 0.0)

        # Return the combined portfolio valuation.
        return total_value


# `TradeAction` is the agent's proposed next step.
@dataclass(frozen=True)
class TradeAction:
    # `action_type` is expected to be `BUY`, `SELL`, or `HOLD`.
    action_type: str
    # `symbol` identifies which asset the action targets.
    symbol: str
    # `quantity` is the number of shares to trade.
    quantity: int
    # `price` is the execution price proposed by the agent from the market tick.
    price: float
    # `reasoning` stores a human-readable explanation for logging.
    reasoning: str


# `SafetyCheckResult` captures whether a trade passed the guardrails.
@dataclass(frozen=True)
class SafetyCheckResult:
    # `approved` is `True` when the broker is allowed to execute the trade.
    approved: bool
    # `reason` explains why the action was approved or blocked.
    reason: str
