"""Read currency lists, exchange rates and history from Frankfurter v1."""

import json
import math
import re
from bisect import bisect_right
from datetime import date
from urllib.parse import urlencode

from api import get_url


BASE_URL = "https://api.frankfurter.app"
_CODE = re.compile(r"^[A-Z]{3}$")


def _valid_currency(code: str) -> bool:
    return isinstance(code, str) and bool(_CODE.fullmatch(code))


def _valid_amount(amount: float) -> bool:
    try:
        value = float(amount)
    except (TypeError, ValueError):
        return False
    return math.isfinite(value) and value >= 0


def _read_json(url: str) -> dict | None:
    status, text = get_url(url)
    if status != 200:
        return None
    try:
        data = json.loads(text)
    except (TypeError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _rate_from(data: dict, to_currency: str, same_currency: bool) -> float | None:
    if same_currency:
        return 1.0
    try:
        rate = float(data["rates"][to_currency])
    except (KeyError, TypeError, ValueError):
        return None
    return rate if math.isfinite(rate) and rate > 0 else None


def _query_url(path: str, from_currency: str, to_currency: str) -> str:
    params = {"base": from_currency}
    if from_currency != to_currency:
        params["symbols"] = to_currency
    return f"{BASE_URL}/{path}?{urlencode(params)}"


def get_currencies_list() -> list[str] | None:
    """Return sorted Frankfurter currency codes, or None on an API error."""
    data = _read_json(f"{BASE_URL}/currencies")
    if not data:
        return None
    currencies = [code for code in data if _valid_currency(code)]
    return sorted(currencies) if currencies else None


def get_latest_rates(
    from_currency: str, to_currency: str, amount: float
) -> tuple[str | None, float | None]:
    """Return the latest published rate date and one-unit conversion rate."""
    if not (_valid_currency(from_currency) and _valid_currency(to_currency)):
        return None, None
    if not _valid_amount(amount):
        return None, None
    data = _read_json(_query_url("latest", from_currency, to_currency))
    if data is None or not isinstance(data.get("date"), str):
        return None, None
    rate = _rate_from(data, to_currency, from_currency == to_currency)
    return (data["date"], rate) if rate is not None else (None, None)


def get_historical_quote(
    from_currency: str, to_currency: str, from_date: str | date, amount: float
) -> tuple[str | None, float | None]:
    """Return the effective published date and rate for a requested date.

    Frankfurter may use the preceding working day for weekends or holidays.
    Its response date is returned so the app can label the result accurately.
    """
    if not (_valid_currency(from_currency) and _valid_currency(to_currency)):
        return None, None
    if not _valid_amount(amount):
        return None, None
    try:
        requested = date.fromisoformat(str(from_date))
    except ValueError:
        return None, None
    if requested > date.today():
        return None, None
    data = _read_json(_query_url(requested.isoformat(), from_currency, to_currency))
    if data is None or not isinstance(data.get("date"), str):
        return None, None
    rate = _rate_from(data, to_currency, from_currency == to_currency)
    return (data["date"], rate) if rate is not None else (None, None)


def get_historical_rate(
    from_currency: str, to_currency: str, from_date: str | date, amount: float
) -> float | None:
    """Return the rate for a requested historical date, or None on error."""
    _, rate = get_historical_quote(from_currency, to_currency, from_date, amount)
    return rate


def _add_months(day: date, months: int) -> date:
    year, month = divmod(day.month - 1 + months, 12)
    target_year, target_month = day.year + year, month + 1
    # The 28th exists in every month; quarter sampling does not need month end.
    return date(target_year, target_month, min(day.day, 28))


def get_rate_trend(from_currency: str, to_currency: str, years: int) -> dict[str, float]:
    """Return approximately quarterly observations over the last N years.

    A single time-series request is used. For non-trading dates, each sample
    takes the most recent published rate on or before its target date.
    """
    if not (_valid_currency(from_currency) and _valid_currency(to_currency)):
        return {}
    if not isinstance(years, int) or isinstance(years, bool) or years < 1 or years > 10:
        return {}
    today = date.today()
    try:
        start = today.replace(year=today.year - years)
    except ValueError:  # 29 February in a non-leap year
        start = today.replace(year=today.year - years, day=28)
    data = _read_json(
        _query_url(f"{start.isoformat()}..{today.isoformat()}", from_currency, to_currency)
    )
    if data is None or not isinstance(data.get("rates"), dict):
        return {}
    observations = {}
    for day, rates in data["rates"].items():
        if not isinstance(day, str) or not isinstance(rates, dict):
            continue
        rate = _rate_from({"rates": rates}, to_currency, from_currency == to_currency)
        if rate is not None:
            observations[day] = rate
    if not observations:
        return {}
    available_days = sorted(observations)
    sampled = {}
    for offset in range(0, years * 12 + 1, 3):
        target = min(_add_months(start, offset), today).isoformat()
        index = bisect_right(available_days, target) - 1
        if index >= 0:
            day = available_days[index]
            sampled[day] = observations[day]
    latest_day = available_days[-1]
    sampled[latest_day] = observations[latest_day]
    return dict(sorted(sampled.items()))
