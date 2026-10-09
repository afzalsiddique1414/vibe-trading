# Mizan V2 inside Vibe-Trading

This branch makes **Vibe-Trading the host** and adds a small Mizan safety
package to its existing Python application. It does not replace Vibe's agent,
strategy-generation, or backtesting systems.

## Included in this first integration slice

- `src/mizan_safety.py`: fail-closed paper-signal policy with a 10% default
  notional cap, confidence floor, stale-candle rejection, and a hard paper-only
  configuration check.
- `src/api/mizan_routes.py`: read-only `GET /api/mizan/status` endpoint
  served by Vibe's existing FastAPI app.
- Tests for accepted paper signals and safety rejections.

## Safety boundary

This package has no exchange connector, broker adapter, or order-submission
function. The status endpoint only reports configuration. Passing a signal
through `evaluate_signal` is not an executed or simulated fill; Vibe's existing
research/backtest workflow remains responsible for generating and evaluating
strategies. Do not interpret this initial slice as full Mizan learning-worker,
paper-ledger, or frontend-dashboard integration.

## Verification

Run the repository's existing test command plus:

```bash
pytest -q tests/test_mizan_safety.py
```

No production service is changed by this branch.
