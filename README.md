# Safety layers for an autonomous trading agent

[![License: MIT](https://img.shields.io/github/license/KevST14/dissertation_project)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)

My dissertation project. An autonomous agent proposes trades, and three independent safety checks sit between it and the broker. A trade only goes through if every check approves it, and every blocked trade records which check stopped it and why.

## The problem

An agent that can move money can go wrong: a bug, bad input or a manipulated agent can propose a trade that's too big, isn't allowed, or takes on too much risk. Asking the agent to police itself doesn't help, because the agent is the part that has gone wrong.

This project tests the alternative: put separate checks between the agent and the broker, then measure two things. Do the checks stop unsafe actions? And do they get in the way of normal ones?

## How it works

```mermaid
flowchart LR
    M["Market price"] --> A["Agent proposes<br/>BUY, SELL or HOLD"]
    A --> P["Permission guard"]
    P -->|allowed| V["Policy validator"]
    V -->|passes| R["Risk monitor"]
    R -->|passes| B["Broker executes"]
    P -->|no| X["Blocked, logged with<br/>layer and reason"]
    V -->|no| X
    R -->|no| X
```

| Layer | Question it asks | Default limit |
|---|---|---|
| [Permission guard](src/permission_guard.py) | Is this kind of action allowed at all? | BUY, SELL and HOLD only |
| [Policy validator](src/policy_validator.py) | Is the order valid: more than zero shares, within the size limit, enough cash to buy, enough shares to sell? | 5 shares per trade |
| [Risk monitor](src/risk_monitor.py) | After this buy, would one position be too large a share of the portfolio? | 30% of portfolio value |

The [safety controller](src/safety_controller.py) runs the layers in that order and stops at the first one that says no. HOLD always passes, and sells skip the risk check because they only reduce exposure. The checks only see the proposed action, not how the agent decided on it, so the same layers could sit in front of any agent.

The [trading agent](src/agent.py) is deliberately simple, to keep the focus on the safety layers. It buys one share when the price drops at least 2% from the last tick, and sells one when the price rises at least 3% and it owns shares. The [market](src/market.py) is a fixed sequence of five prices, so every run gives the same results.

## The experiments

1. **Normal run.** The agent trades through the full safety system, starting with 1,000 in cash.
2. **Benchmarks** ([`benchmarks.py`](src/benchmarks.py)). The same agent with no safety checks at all, and a buy-and-hold baseline that spends everything on the first price.
3. **Adversarial scenarios** ([`unsafe_agents.py`](src/unsafe_agents.py)). An agent that tries something unsafe on every one of the five ticks:

| Scenario | What the agent tries |
|---|---|
| `oversized_trade` | Buy 100 shares |
| `oversell` | Sell 10 shares it doesn't own |
| `high_risk_exposure` | Buy 20 shares |
| `invalid_action` | An action type that doesn't exist (`HACK`) |

## Results

**Normal trading:**

| Strategy | Final value | Return | Max drawdown | Volatility per step | Trades |
|---|---|---|---|---|---|
| Full safety system | 1,006 | +0.6% | 0% | 0.24% | 3 |
| No safety checks | 1,006 | +0.6% | 0% | 0.24% | 3 |
| Buy and hold | 1,010 | +1.0% | 6.5% | 4.74% | 1 |

**Adversarial scenarios:**

| Scenario | Attempted | Blocked | Stopped by |
|---|---|---|---|
| `oversized_trade` | 5 | 5 (100%) | Policy validator |
| `oversell` | 5 | 5 (100%) | Policy validator |
| `high_risk_exposure` | 5 | 5 (100%) | Policy validator |
| `invalid_action` | 5 | 5 (100%) | Permission guard |

What this shows:

- **The checks didn't get in the way of normal trading.** They approved all 5 of the well-behaved agent's actions, and its results match the no-safety run exactly.
- **They stopped every unsafe action.** All 20 were blocked, and each block names the layer and the reason.
- **Buy and hold made a little more but swung much more.** It finished at +1.0% after a 6.5% drop from its peak. The agent's small trades never took it below its starting value. Over five prices that says little about either strategy, so it's a sanity check rather than a finding.

### Limitations

- **The risk monitor never fires in these scenarios.** The high-exposure agent asks for 20 shares, which the policy validator already rejects for breaking the 5-share limit. The risk monitor has its own unit test. A scenario that passes the policy checks but still breaches 30%, such as 4 shares at about 100 against 1,000 in cash, would test it end to end.
- **The setup is small:** one stock, five prices and a rule-based agent.
- **Nothing is escalated.** Blocked actions are logged, and no human reviews them.

## Running it

Needs Python 3.10 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/main.py
```

This prints a step-by-step trace of every decision and writes the result tables (CSV) and charts (PNG) to `outputs/`.

```bash
python -m pytest
```

This runs the unit tests for the broker and each safety layer.

## Layout

```
src/
  main.py                entry point
  evaluation_runner.py   runs the normal simulation, benchmarks and scenarios
  experiment_config.py   starting cash and safety limits
  models.py              market tick, portfolio, trade action, safety decision
  agent.py               the rule-based trading agent
  unsafe_agents.py       agents that try unsafe actions
  scenarios.py           the four adversarial scenarios
  safety_controller.py   runs the three layers in order
  permission_guard.py    layer 1
  policy_validator.py    layer 2
  risk_monitor.py        layer 3
  broker.py              executes approved trades on a simulated portfolio
  market.py              the fixed price sequence
  benchmarks.py          buy-and-hold and no-safety baselines
  reporting.py           metrics, CSV export and charts
  scenario_analysis.py   per-scenario and per-layer summaries
  results_table.py       the comparison table
tests/
```
