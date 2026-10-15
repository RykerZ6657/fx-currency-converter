"""Currency calculations and the assignment's required result sentence."""

import math


def round_rate(rate: float) -> float:
    """Round a finite exchange rate to four decimal places."""
    value = float(rate)
    if not math.isfinite(value):
        raise ValueError("The exchange rate must be finite.")
    return round(value, 4)


def reverse_rate(rate: float) -> float:
    """Return the reciprocal rate to four decimals, or zero for a zero rate."""
    value = float(rate)
    if not math.isfinite(value):
        raise ValueError("The exchange rate must be finite.")
    return round_rate(1 / value) if value != 0 else 0.0


def format_output(
    date: str, from_currency: str, to_currency: str, rate: float, amount: float
) -> str:
    """Format the rate, converted amount and inverse rate for the app."""
    amount_value = float(amount)
    rate_value = float(rate)
    if not math.isfinite(amount_value) or not math.isfinite(rate_value):
        raise ValueError("The amount and exchange rate must be finite.")
    converted = round(amount_value * rate_value, 2)
    return (
        f"The conversion rate on {date} from {from_currency} to {to_currency} "
        f"was {rate_value}. So {amount_value} in {from_currency} "
        f"correspond to {converted} in {to_currency}. "
        f"The inverse rate was {reverse_rate(rate_value)}."
    )
