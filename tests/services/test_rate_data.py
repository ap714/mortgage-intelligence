"""Tests for rate_data service — uses httpx MockTransport to avoid live API calls."""

from datetime import date

import httpx
import pytest

from backend.services.rate_data import (
    SERIES_BOC_OVERNIGHT,
    SERIES_GOC_5YR,
    _parse_observations,
    fetch_boc_overnight_rate,
    fetch_boc_overnight_rate_history,
)


def _make_valet_response(series: str, observations: list[dict]) -> dict:
    """Build a minimal Valet API JSON response."""
    return {
        "seriesDetail": {series: {"label": series}},
        "observations": [
            {"d": obs["date"], series: {"v": str(obs["value"])}}
            for obs in observations
        ],
    }


# --- _parse_observations unit tests ---


def test_parse_observations_converts_to_decimal() -> None:
    data = _make_valet_response(
        SERIES_BOC_OVERNIGHT,
        [{"date": "2024-01-15", "value": 5.0}],
    )
    result = _parse_observations(data, SERIES_BOC_OVERNIGHT)
    assert result == [{"date": "2024-01-15", "rate": 0.05}]


def test_parse_observations_skips_null_values() -> None:
    data = {
        "observations": [
            {"d": "2024-01-15", SERIES_BOC_OVERNIGHT: {"v": None}},
            {"d": "2024-01-16", SERIES_BOC_OVERNIGHT: {"v": "5.0"}},
        ]
    }
    result = _parse_observations(data, SERIES_BOC_OVERNIGHT)
    assert len(result) == 1
    assert result[0]["date"] == "2024-01-16"


def test_parse_observations_empty() -> None:
    assert _parse_observations({"observations": []}, SERIES_BOC_OVERNIGHT) == []


# --- fetch_boc_overnight_rate integration tests (mocked) ---


def _fake_response(url: str, payload: dict) -> httpx.Response:
    """Build an httpx.Response with a request attached (required for raise_for_status)."""
    return httpx.Response(
        200,
        json=payload,
        request=httpx.Request("GET", url),
    )


def _make_fake_client(payload: dict):
    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            pass

        async def get(self, url: str, **kwargs) -> httpx.Response:
            return _fake_response(url, payload)

    return FakeClient


@pytest.mark.asyncio
async def test_fetch_boc_overnight_rate_returns_decimal(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = _make_valet_response(
        SERIES_BOC_OVERNIGHT, [{"date": "2024-01-15", "value": 5.0}]
    )
    monkeypatch.setattr(
        "backend.services.rate_data.httpx.AsyncClient", _make_fake_client(payload)
    )
    rate = await fetch_boc_overnight_rate()
    assert rate == pytest.approx(0.05)


@pytest.mark.asyncio
async def test_fetch_boc_overnight_rate_history_date_range(monkeypatch: pytest.MonkeyPatch) -> None:
    observations = [
        {"date": "2023-01-25", "value": 4.25},
        {"date": "2023-03-08", "value": 4.5},
        {"date": "2023-04-12", "value": 4.5},
    ]
    payload = _make_valet_response(SERIES_BOC_OVERNIGHT, observations)
    monkeypatch.setattr(
        "backend.services.rate_data.httpx.AsyncClient", _make_fake_client(payload)
    )
    result = await fetch_boc_overnight_rate_history(
        start_date=date(2023, 1, 1), end_date=date(2023, 12, 31)
    )
    assert len(result) == 3
    assert result[0] == {"date": "2023-01-25", "rate": pytest.approx(0.0425)}
    assert result[-1] == {"date": "2023-04-12", "rate": pytest.approx(0.045)}
