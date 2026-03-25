"""Rate data service — Bank of Canada Valet API for overnight rate and yield curves.

Series used:
  V39079           — Target for the overnight rate (BoC policy rate)
  BD.CDN.5YR.DQ.YLD — Government of Canada 5-year benchmark bond yield
  AVG.INTWO        — Canadian Overnight Repo Rate Average (CORRA)

All rates returned as decimals (0.045 = 4.5%).
Dates in ISO 8601 format (YYYY-MM-DD).
"""

from datetime import date, timedelta

import httpx

BOC_VALET_BASE = "https://www.bankofcanada.ca/valet"

# Bank of Canada series identifiers
SERIES_BOC_OVERNIGHT = "V39079"
SERIES_GOC_5YR = "BD.CDN.5YR.DQ.YLD"
SERIES_CORRA = "AVG.INTWO"


def _observations_url(series: str) -> str:
    return f"{BOC_VALET_BASE}/observations/{series}/json"


def _parse_observations(data: dict, series: str) -> list[dict[str, float | str]]:
    """Parse Valet JSON response into a list of {date, rate} dicts.

    Args:
        data: Parsed JSON response from the Valet API.
        series: The series identifier key inside each observation object.

    Returns:
        List of dicts with keys "date" (str, ISO 8601) and "rate" (float, decimal).
        Observations where the value is missing or null are skipped.
    """
    results: list[dict[str, float | str]] = []
    for obs in data.get("observations", []):
        raw = obs.get(series, {}).get("v")
        if raw is None:
            continue
        results.append({"date": obs["d"], "rate": float(raw) / 100})
    return results


async def fetch_boc_overnight_rate() -> float:
    """Fetch the current Bank of Canada target overnight rate.

    Returns:
        Current overnight rate as a decimal (e.g. 0.045 for 4.5%).

    Raises:
        httpx.HTTPStatusError: On non-2xx responses.
        ValueError: If no observations are returned.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            _observations_url(SERIES_BOC_OVERNIGHT),
            params={"recent": 1},
        )
        resp.raise_for_status()
    observations = _parse_observations(resp.json(), SERIES_BOC_OVERNIGHT)
    if not observations:
        raise ValueError("No observations returned for BoC overnight rate.")
    return observations[-1]["rate"]  # type: ignore[return-value]


async def fetch_boc_overnight_rate_history(
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict[str, float | str]]:
    """Fetch Bank of Canada target overnight rate history.

    Defaults to the last 10 years if no date range is provided.

    Args:
        start_date: Start of date range (inclusive). Defaults to 10 years ago.
        end_date: End of date range (inclusive). Defaults to today.

    Returns:
        List of {"date": "YYYY-MM-DD", "rate": float} dicts in ascending order.

    Raises:
        httpx.HTTPStatusError: On non-2xx responses.
    """
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date - timedelta(days=365 * 10)

    params = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(_observations_url(SERIES_BOC_OVERNIGHT), params=params)
        resp.raise_for_status()
    return _parse_observations(resp.json(), SERIES_BOC_OVERNIGHT)


async def fetch_goc_5yr_bond_yield() -> float:
    """Fetch the most recent Government of Canada 5-year benchmark bond yield.

    Used as a proxy for fixed mortgage rates.

    Returns:
        Current 5-year GoC yield as a decimal.

    Raises:
        httpx.HTTPStatusError: On non-2xx responses.
        ValueError: If no observations are returned.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            _observations_url(SERIES_GOC_5YR),
            params={"recent": 1},
        )
        resp.raise_for_status()
    observations = _parse_observations(resp.json(), SERIES_GOC_5YR)
    if not observations:
        raise ValueError("No observations returned for GoC 5-year yield.")
    return observations[-1]["rate"]  # type: ignore[return-value]


async def fetch_goc_5yr_bond_yield_history(
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict[str, float | str]]:
    """Fetch Government of Canada 5-year bond yield history.

    Args:
        start_date: Start of date range (inclusive). Defaults to 10 years ago.
        end_date: End of date range (inclusive). Defaults to today.

    Returns:
        List of {"date": "YYYY-MM-DD", "rate": float} dicts in ascending order.
    """
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date - timedelta(days=365 * 10)

    params = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(_observations_url(SERIES_GOC_5YR), params=params)
        resp.raise_for_status()
    return _parse_observations(resp.json(), SERIES_GOC_5YR)


async def fetch_corra() -> float:
    """Fetch the most recent Canadian Overnight Repo Rate Average (CORRA).

    Returns:
        Current CORRA as a decimal.

    Raises:
        httpx.HTTPStatusError: On non-2xx responses.
        ValueError: If no observations are returned.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            _observations_url(SERIES_CORRA),
            params={"recent": 1},
        )
        resp.raise_for_status()
    observations = _parse_observations(resp.json(), SERIES_CORRA)
    if not observations:
        raise ValueError("No observations returned for CORRA.")
    return observations[-1]["rate"]  # type: ignore[return-value]
