"""Whole-lot matched-notional sizing."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MatchedLots:
    """Whole-lot size and notional mismatch for the two held contracts."""

    left_lots: int
    right_lots: int
    left_notional: float
    right_notional: float


def matched_whole_lots(
    left_price_per_gram: float,
    right_price_per_gram: float,
    left_lot_grams: float,
    right_lot_grams: float,
    target_notional: float,
) -> MatchedLots:
    """Choose whole-lot legs below ``target_notional`` with the closest notionals."""
    if min(left_price_per_gram, right_price_per_gram, left_lot_grams, right_lot_grams, target_notional) <= 0:
        raise ValueError("prices, lot sizes, and target_notional must be positive")
    left_value = left_price_per_gram * left_lot_grams
    right_value = right_price_per_gram * right_lot_grams
    max_left = int(target_notional // left_value)
    max_right = int(target_notional // right_value)
    if max_left == 0 or max_right == 0:
        return MatchedLots(0, 0, 0.0, 0.0)

    candidates = []
    for left_lots in range(1, max_left + 1):
        exact_right_lots = left_lots * left_value / right_value
        for right_lots in {int(exact_right_lots), int(exact_right_lots) + 1}:
            if 1 <= right_lots <= max_right:
                candidates.append((left_lots, right_lots))
    left_lots, right_lots = min(
        candidates,
        key=lambda counts: (
            abs(counts[0] * left_value - counts[1] * right_value),
            -(counts[0] * left_value + counts[1] * right_value),
        ),
    )
    return MatchedLots(
        left_lots,
        right_lots,
        left_lots * left_value,
        right_lots * right_value,
    )
