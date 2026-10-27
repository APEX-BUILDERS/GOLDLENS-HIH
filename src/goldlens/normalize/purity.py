"""Purity adjustments for gold price comparisons."""


def adjust_for_purity(price_per_gram: float, contract_purity: float, target_purity: float) -> float:
    """Express a per-gram price at ``target_purity``.

    Both purity values are expressed in parts per thousand (for example, 995
    and 999).  The function contains no time-series logic and therefore cannot
    introduce look-ahead bias.
    """
    if contract_purity <= 0 or target_purity <= 0:
        raise ValueError("purity values must be positive")
    return price_per_gram * target_purity / contract_purity
