"""Mock execution layer for the trading simulation.

The broker is responsible for turning an approved trade decision into changes
to cash and holdings. In a real system this would talk to an exchange or API.
"""

# Import the shared portfolio and trade models used by the broker methods.
from models import Portfolio, TradeAction


# `MockBroker` simulates fills locally without any external dependency.
class MockBroker:
    # `execute_trade` mutates the portfolio in place based on the trade type.
    def execute_trade(self, action: TradeAction, portfolio: Portfolio) -> None:
        # Handle buys by reducing cash and increasing the share count.
        if action.action_type == "BUY":
            # Deduct the total cost of the purchase from available cash.
            portfolio.cash -= action.price * action.quantity
            # Increase the owned position by the number of purchased shares.
            portfolio.update_position(action.symbol, action.quantity)
            # Return early because the buy path is complete.
            return

        # Handle sells by increasing cash and reducing the share count.
        if action.action_type == "SELL":
            # Add the sale proceeds back to cash.
            portfolio.cash += action.price * action.quantity
            # Reduce the position by the number of sold shares.
            portfolio.update_position(action.symbol, -action.quantity)
