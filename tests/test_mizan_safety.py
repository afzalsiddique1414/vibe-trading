from __future__ import annotations

import pytest

from src.mizan_safety import MizanSafetyConfig, evaluate_signal, status_payload


def test_approves_only_bounded_fresh_paper_signal():
    result = evaluate_signal(
        side="buy", confidence=0.75, notional_fraction=0.05, candle_age_seconds=30
    )
    assert result.allowed is True
    assert result.reason == "PAPER_SIGNAL_APPROVED"
    assert result.mode == "paper"


@pytest.mark.parametrize(
    ("kwargs", "reason"),
    [
        ({"side": "buy", "confidence": 0.55, "notional_fraction": 0.05, "candle_age_seconds": 1}, "CONFIDENCE_BELOW_THRESHOLD"),
        ({"side": "sell", "confidence": 0.9, "notional_fraction": 0.05, "candle_age_seconds": 151}, "STALE_MARKET_DATA"),
        ({"side": "buy", "confidence": 0.9, "notional_fraction": 0.30, "candle_age_seconds": 1}, "TRADE_SIZE_OUT_OF_BOUNDS"),
        ({"side": "hold", "confidence": 0.9, "notional_fraction": 0.05, "candle_age_seconds": 1}, "HOLD_SIGNAL"),
        ({"side": "wire", "confidence": 0.9, "notional_fraction": 0.05, "candle_age_seconds": 1}, "INVALID_SIDE"),
    ],
)
def test_fail_closed_signal_rejections(kwargs, reason):
    result = evaluate_signal(**kwargs)
    assert result.allowed is False
    assert result.reason == reason
    assert result.notional_fraction == 0.0


def test_live_mode_is_rejected():
    with pytest.raises(ValueError, match="MIZAN_PAPER_ONLY_REQUIRED"):
        MizanSafetyConfig(mode="live", paper_only=False).validate()


def test_status_never_enables_live_orders():
    payload = status_payload()
    assert payload["host"] == "Vibe-Trading"
    assert payload["mode"] == "paper"
    assert payload["paper_only"] is True
    assert payload["live_orders_enabled"] is False
