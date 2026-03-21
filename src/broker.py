from models import TradeAction, Portfolio


class MockBroker:
    """
    Executes approved trades against a simulated portfolio.
    """

    def execute_trade(self, action: TradeAction, portfolio: Portfolio) -> None:
        if action.action_type == "HOLD":
            return

        if action.action_type == "BUY":
            total_cost = action.quantity * action.price
            portfolio.cash -= total_cost
            portfolio.update_position(action.symbol, action.quantity)
            
            portfolio.record_transaction({
                "type": "BUY",
                "symbol": action.symbol,
                "quantity": action.quantity,
                "price": action.price,
                "value": total_cost
            })

        elif action.action_type == "SELL":
            total_value = action.quantity * action.price
            portfolio.cash += total_value
            portfolio.update_position(action.symbol, -action.quantity)
            
            portfolio.record_transaction({
                "type": "SELL",
                "symbol": action.symbol,
                "quantity": action.quantity,
                "price": action.price,
                "value": total_value
            })

        else:
            raise ValueError(f"Unsupported action type: {action.action_type}")