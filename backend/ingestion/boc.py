"""Ingestion script — fetches Bank of Canada rate history and persists to data/raw/.

Usage:
    python -m backend.ingestion.boc

Output files (JSON, newline-delimited):
    data/raw/boc_overnight_rate.json
    data/raw/goc_5yr_yield.json
"""

import asyncio
import json
import logging
from datetime import date
from pathlib import Path

from backend.services.rate_data import (
    fetch_boc_overnight_rate_history,
    fetch_goc_5yr_bond_yield_history,
)

logger = logging.getLogger(__name__)

RAW_DIR = Path(__file__).resolve().parents[3] / "data" / "raw"


async def ingest_boc_overnight_rate(
    start_date: date | None = None,
    end_date: date | None = None,
) -> Path:
    """Fetch BoC overnight rate history and write to data/raw/boc_overnight_rate.json.

    Args:
        start_date: Start of date range. Defaults to 10 years ago.
        end_date: End of date range. Defaults to today.

    Returns:
        Path to the written file.
    """
    logger.info("Fetching BoC overnight rate history...")
    records = await fetch_boc_overnight_rate_history(start_date, end_date)
    out = RAW_DIR / "boc_overnight_rate.json"
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    with out.open("w") as f:
        json.dump(
            {
                "series": "V39079",
                "description": "Target for the overnight rate",
                "fetched_at": date.today().isoformat(),
                "observations": records,
            },
            f,
            indent=2,
        )
    logger.info("Wrote %d observations to %s", len(records), out)
    return out


async def ingest_goc_5yr_yield(
    start_date: date | None = None,
    end_date: date | None = None,
) -> Path:
    """Fetch GoC 5-year bond yield history and write to data/raw/goc_5yr_yield.json.

    Args:
        start_date: Start of date range. Defaults to 10 years ago.
        end_date: End of date range. Defaults to today.

    Returns:
        Path to the written file.
    """
    logger.info("Fetching GoC 5-year bond yield history...")
    records = await fetch_goc_5yr_bond_yield_history(start_date, end_date)
    out = RAW_DIR / "goc_5yr_yield.json"
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    with out.open("w") as f:
        json.dump(
            {
                "series": "BD.CDN.5YR.DQ.YLD",
                "description": "Government of Canada benchmark bond yields - 5 year",
                "fetched_at": date.today().isoformat(),
                "observations": records,
            },
            f,
            indent=2,
        )
    logger.info("Wrote %d observations to %s", len(records), out)
    return out


async def run_all() -> None:
    """Ingest all rate series."""
    await asyncio.gather(
        ingest_boc_overnight_rate(),
        ingest_goc_5yr_yield(),
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    asyncio.run(run_all())
