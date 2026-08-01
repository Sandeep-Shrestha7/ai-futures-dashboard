from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
import json
import re

import pandas as pd
import requests
from bs4 import BeautifulSoup

CALENDAR_URL = "https://tradingeconomics.com/calendar"
CACHE_DIR = Path(__file__).resolve().parents[1] / "database"
CACHE_FILE = CACHE_DIR / "tradingeconomics_calendar_v3.json"
CACHE_TTL = timedelta(hours=24)

COUNTRY_CODES = {
    "United States": {"US", "United States"},
    "Canada": {"CA", "Canada"},
    "Euro Area": {"EA", "Euro Area"},
    "United Kingdom": {"GB", "United Kingdom"},
    "Japan": {"JP", "Japan"},
    "China": {"CN", "China"},
}


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def _importance(row, event_name: str = "") -> tuple[int, str]:
    """Return impact level and how it was determined.

    Trading Economics can encode impact in data attributes, numeric CSS
    classes, icons, titles, or aria labels. The public page markup is not
    always identical, so all known forms are checked before using a conservative
    event-name fallback.
    """
    # Explicit row/node attributes.
    nodes = [row, *row.select("[data-importance], [importance], [data-impact]")]
    for node in nodes:
        for attr in ("data-importance", "importance", "data-impact"):
            raw = _clean(node.get(attr))
            match = re.search(r"\b([1-3])\b", raw)
            if match:
                return int(match.group(1)), "Trading Economics markup"

    # Numeric importance embedded in CSS classes such as calendar-date-3,
    # importance-2, volatility-3, impact-2, or calendar-importance-3.
    for node in [row, *row.find_all(True)]:
        classes = " ".join(node.get("class", []))
        match = re.search(
            r"(?:calendar[-_ ]?(?:date|importance)|importance|impact|volatility)"
            r"[-_ ]?([1-3])(?:\b|$)",
            classes,
            re.I,
        )
        if match:
            return int(match.group(1)), "Trading Economics markup"

    # Accessible labels and hover titles often contain volatility wording.
    labels = " ".join(
        _clean(node.get(attr))
        for node in [row, *row.find_all(True)]
        for attr in ("title", "aria-label", "data-original-title")
        if node.get(attr)
    ).lower()

    combined = f"{labels} {_clean(row.get_text(' ', strip=True)).lower()}"
    if any(term in combined for term in (
        "high volatility", "high impact", "importance 3", "impact 3"
    )):
        return 3, "Trading Economics label"
    if any(term in combined for term in (
        "moderate volatility", "medium volatility", "medium impact",
        "importance 2", "impact 2"
    )):
        return 2, "Trading Economics label"
    if any(term in combined for term in (
        "low volatility", "low impact", "importance 1", "impact 1"
    )):
        return 1, "Trading Economics label"

    # Count only visible filled-star/importance icons.
    filled_icons = row.select(
        ".glyphicon-star:not(.glyphicon-star-empty), "
        ".fa-star:not(.fa-star-o), .fas.fa-star, "
        ".calendar-importance .active, .importance .active"
    )
    if filled_icons:
        return max(1, min(3, len(filled_icons))), "Trading Economics icons"

    # Conservative fallback for the U.S. futures calendar when the public HTML
    # omits importance metadata. This prevents every event from becoming Low.
    name = _clean(event_name).lower()

    high_patterns = (
        "fed interest rate decision", "fomc", "fed press conference",
        "non farm payroll", "nonfarm payroll", "unemployment rate",
        "inflation rate", "core inflation", "cpi", "pce price",
        "gdp growth", "retail sales", "ism manufacturing",
        "ism services", "initial jobless claims",
    )
    medium_patterns = (
        "adp employment", "jolts", "job openings", "consumer confidence",
        "consumer sentiment", "durable goods", "factory orders",
        "industrial production", "manufacturing pmi", "services pmi",
        "composite pmi", "trade balance", "pending home sales",
        "new home sales", "existing home sales", "housing starts",
        "building permits", "eia crude oil stocks", "eia gasoline stocks",
        "crude oil inventories", "business inventories",
    )

    if any(pattern in name for pattern in high_patterns):
        return 3, "event-name fallback"
    if any(pattern in name for pattern in medium_patterns):
        return 2, "event-name fallback"
    return 1, "default fallback"


def _parse_date_header(text: str) -> str | None:
    text = _clean(text)
    match = re.search(
        r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+"
        r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+"
        r"\d{1,2}\s+\d{4}",
        text,
        re.I,
    )
    if not match:
        return None
    try:
        return datetime.strptime(match.group(0), "%A %B %d %Y").date().isoformat()
    except ValueError:
        return None


def _cell_text(cell) -> str:
    return _clean(cell.get_text(" ", strip=True))


def _country_from_row(row, cells: list) -> str:
    node = row.select_one(
        ".calendar-country, td.country, [data-country], "
        "img[title], img[alt], span[title]"
    )
    if node:
        for attr in ("data-country", "title", "alt"):
            value = _clean(node.get(attr))
            if value:
                return value
        value = _cell_text(node)
        if value:
            return value

    known = {code for values in COUNTRY_CODES.values() for code in values}
    for cell in cells:
        value = _cell_text(cell)
        if value in known:
            return value
    return ""


def _parse_html(html: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "lxml")
    events: list[dict[str, Any]] = []
    current_date: str | None = None

    rows = soup.select("table tr, #calendar tr, tr[data-url], tr.calendar-item")
    seen_rows: set[int] = set()

    for row in rows:
        if id(row) in seen_rows:
            continue
        seen_rows.add(id(row))

        row_text = _clean(row.get_text(" ", strip=True))
        date_header = _parse_date_header(row_text)
        cells = row.select("td")
        if date_header and len(cells) <= 2:
            current_date = date_header
            continue
        if len(cells) < 3:
            continue

        values = [_cell_text(c) for c in cells]

        # Find the time cell instead of assuming a fixed position. Trading
        # Economics sometimes inserts a hidden date/flag column before it.
        time_idx = next(
            (
                i for i, value in enumerate(values)
                if re.fullmatch(r"\d{1,2}:\d{2}\s*(?:AM|PM)?", value, re.I)
            ),
            0,
        )
        time_text = values[time_idx]

        country_text = _country_from_row(row, cells)
        country_idx = next(
            (i for i, value in enumerate(values) if value == country_text and value),
            time_idx + 1,
        )

        event_node = row.select_one(
            ".calendar-event, td.event, td.calendar-event, a[href*='/calendar/']"
        )
        if event_node:
            event_text = _cell_text(event_node)
            event_idx = next(
                (i for i, value in enumerate(values) if value == event_text),
                country_idx + 1,
            )
        else:
            event_idx = min(country_idx + 1, len(values) - 1)
            event_text = values[event_idx]

        if not event_text or event_text.lower() in {
            "event", "actual", "previous", "consensus", "forecast"
        }:
            continue

        # Values after the event are consistently Actual, Previous,
        # Consensus and Forecast, even when leading utility columns change.
        trailing = values[event_idx + 1 :]
        actual = trailing[0] if len(trailing) > 0 else ""
        previous = trailing[1] if len(trailing) > 1 else ""
        consensus = trailing[2] if len(trailing) > 2 else ""
        forecast = trailing[3] if len(trailing) > 3 else ""

        date_value = current_date or datetime.now().date().isoformat()
        dt = pd.to_datetime(f"{date_value} {time_text}", errors="coerce")
        date_iso = dt.isoformat() if pd.notna(dt) else date_value

        events.append(
            {
                "Date": date_iso,
                "Country": country_text,
                "Event": event_text,
                "Category": event_text,
                "Importance": _importance(row, event_text)[0],
                "ImportanceSource": _importance(row, event_text)[1],
                "Actual": actual,
                "Previous": previous,
                "Consensus": consensus,
                "Forecast": forecast,
                "Source": "Trading Economics webpage",
            }
        )

    return events


def _download() -> list[dict[str, Any]]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://tradingeconomics.com/",
    }
    response = requests.get(CALENDAR_URL, headers=headers, timeout=25)
    response.raise_for_status()
    events = _parse_html(response.text)
    if not events:
        raise RuntimeError("Trading Economics calendar rows could not be parsed.")
    return events


def _read_cache() -> dict[str, Any] | None:
    try:
        payload = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        if isinstance(payload, dict) and isinstance(payload.get("events"), list):
            return payload
    except (OSError, ValueError, TypeError):
        pass
    return None


def _write_cache(events: list[dict[str, Any]]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": CALENDAR_URL,
        "events": events,
    }
    CACHE_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _cache_is_fresh(payload: dict[str, Any]) -> bool:
    try:
        fetched = datetime.fromisoformat(payload["fetched_at"].replace("Z", "+00:00"))
        return datetime.now(timezone.utc) - fetched <= CACHE_TTL
    except (KeyError, TypeError, ValueError):
        return False


def _filter(
    events: list[dict[str, Any]],
    country: str,
    days: int,
    past_days: int = 0,
) -> list[dict[str, Any]]:
    accepted = COUNTRY_CODES.get(country, {country})
    today = datetime.now().date()
    start = today - timedelta(days=max(0, past_days))
    end = today + timedelta(days=max(1, days))
    result: list[dict[str, Any]] = []

    for event in events:
        event_country = _clean(event.get("Country"))
        if event_country not in accepted:
            continue
        dt = pd.to_datetime(event.get("Date"), errors="coerce")
        if pd.isna(dt):
            continue
        event_date = dt.date()
        if start <= event_date <= end:
            result.append(event)

    result.sort(key=lambda x: pd.to_datetime(x.get("Date"), errors="coerce"))
    return result


def economic_calendar(
    force_refresh: bool = False,
    country: str = "United States",
    days: int = 14,
    past_days: int = 7,
) -> list[dict[str, Any]]:
    """Read the public Trading Economics calendar once per day, with fallback cache.

    This does not use the Trading Economics API and requires no API key. It only
    refreshes while the Streamlit app is running or when the app is opened.
    """
    cached = _read_cache()

    if not force_refresh and cached and _cache_is_fresh(cached):
        return _filter(cached["events"], country, days, past_days)

    try:
        events = _download()
        _write_cache(events)
        return _filter(events, country, days, past_days)
    except Exception:
        if cached:
            return _filter(cached["events"], country, days, past_days)
        raise


def calendar_cache_info() -> dict[str, str]:
    cached = _read_cache()
    return {
        "source": CALENDAR_URL,
        "fetched_at": cached.get("fetched_at", "Never") if cached else "Never",
        "cache_file": str(CACHE_FILE),
    }
