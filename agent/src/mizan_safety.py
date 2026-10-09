"""Mizan paper-only safety layer embedded in the Vibe-Trading host.

This module deliberately contains no broker client and no order-submission path.
Vibe remains responsible for research and backtesting; this module only gates
whether a proposed signal is eligible for a simulated paper decision.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from math import isfinite
from typing import Any


@dataclass(frozen=True)
class MizanSafetyConfig:
    mode: str = "paper"
    paper_only: bool = True
    max_trade_fraction: float = 0.10
    min_signal_probability: float = 0.60
    stale_after_seconds: int = 150

    def validate(self) -> None:
        if self.mode != "paper" or not self.paper_only:
            raise ValueError("MIZAN_PAPER_ONLY_REQUIRED")
        if not isfinite(self.max_trade_fraction) or not 0 < self.max_trade_fraction <= 0.25:
            raise ValueError("UNSAFE_TRADE_FRACTION")
        if not isfinite(self.min_signal_probability) or not 0.5 <= self.min_signal_probability <= 1:
            raise ValueError("INVALID_SIGNAL_PROBABILITY")
        if self.stale_after_seconds < 1:
            raise ValueError("INVALID_STALE_THRESHOLD")


@dataclass(frozen=True)
class SafetyDecision:
    allowed: bool
    reason: str
    side: str
    confidence: float
    notional_fraction: float
    mode: str = "paper"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_signal(
    *,
    side: str,
    confidence: float,
    notional_fraction: float,
    candle_age_seconds: int,
    config: MizanSafetyConfig | None = None,
) -> SafetyDecision:
    """Fail-closed eligibility check for a paper signal; never places an order."""
    cfg = config or MizanSafetyConfig()
    cfg.validate()
    normalized_side = str(side).strip().lower()
    if normalized_side not in {"buy", "sell", "hold"}:
        return SafetyDecision(False, "INVALID_SIDE", "hold", 0.0, 0.0)
    if normalized_side == "hold":
        return SafetyDecision(False, "HOLD_SIGNAL", "hold", 0.0, 0.0)
    if not isfinite(confidence) or not 0 <= confidence <= 1:
        return SafetyDecision(False, "INVALID_CONFIDENCE", normalized_side, 0.0, 0.0)
    if confidence < cfg.min_signal_probability:
        return SafetyDecision(False, "CONFIDENCE_BELOW_THRESHOLD", normalized_side, confidence, 0.0)
    if not isinstance(candle_age_seconds, int) or candle_age_seconds < 0:
        return SafetyDecision(False, "INVALID_CANDLE_AGE", normalized_side, confidence, 0.0)
    if candle_age_seconds > cfg.stale_after_seconds:
        return SafetyDecision(False, "STALE_MARKET_DATA", normalized_side, confidence, 0.0)
    if not isfinite(notional_fraction) or not 0 < notional_fraction <= cfg.max_trade_fraction:
        return SafetyDecision(False, "TRADE_SIZE_OUT_OF_BOUNDS", normalized_side, confidence, 0.0)
    return SafetyDecision(True, "PAPER_SIGNAL_APPROVED", normalized_side, confidence, notional_fraction)


def status_payload() -> dict[str, Any]:
    cfg = MizanSafetyConfig()
    cfg.validate()
    return {
        "component": "Mizan V2 safety layer",
        "host": "Vibe-Trading",
        "mode": cfg.mode,
        "paper_only": cfg.paper_only,
        "live_orders_enabled": False,
        "max_trade_fraction": cfg.max_trade_fraction,
        "min_signal_probability": cfg.min_signal_probability,
        "stale_after_seconds": cfg.stale_after_seconds,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "execution": "disabled; this endpoint only reports safety configuration",
    }
