from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import requests

FINNHUB_URL = "https://finnhub.io/api/v1/news"
ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"


def _iso_from_unix(value: Any) -> str:
    try:
        return datetime.fromtimestamp(int(value), tz=timezone.utc).isoformat()
    except (TypeError, ValueError, OSError):
        return ""


def finnhub_market_news(api_key: str, category: str = "general", limit: int = 20) -> list[dict]:
    """Fetch Finnhub general market headlines."""
    if not api_key:
        return []
    response = requests.get(
        FINNHUB_URL,
        params={"category": category, "token": api_key},
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list):
        raise RuntimeError("Finnhub returned an unexpected response.")
    return payload[:limit]


def alpha_vantage_news(api_key: str, limit: int = 20) -> list[dict]:
    """Fetch Alpha Vantage market news with provider-generated sentiment."""
    if not api_key:
        return []

    # Alpha Vantage NEWS_SENTIMENT accepts provider-supported page sizes.
    # Request 50 results, then trim locally to the number the dashboard needs.
    provider_limit = 50

    response = requests.get(
        ALPHA_VANTAGE_URL,
        params={
            "function": "NEWS_SENTIMENT",
            "topics": "financial_markets,economy_monetary,economy_macro",
            "sort": "LATEST",
            "limit": provider_limit,
            "apikey": api_key.strip(),
        },
        timeout=20,
    )
    response.raise_for_status()

    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError("Alpha Vantage returned a non-JSON response.") from exc

    error_message = (
        payload.get("Error Message")
        or payload.get("Note")
        or payload.get("Information")
    )
    if error_message:
        raise RuntimeError(str(error_message))

    feed = payload.get("feed")
    if not isinstance(feed, list):
        raise RuntimeError("Alpha Vantage returned no news feed.")

    return feed[:limit]


def normalize_finnhub(rows: list[dict]) -> list[dict]:
    return [
        {
            "title": row.get("headline", "").strip(),
            "summary": row.get("summary", "").strip(),
            "source": row.get("source", "Finnhub") or "Finnhub",
            "provider": "Finnhub",
            "url": row.get("url", ""),
            "published_at": _iso_from_unix(row.get("datetime")),
            "sentiment": "Neutral",
            "sentiment_score": 0.0,
        }
        for row in rows
        if row.get("headline")
    ]


def normalize_alpha_vantage(rows: list[dict]) -> list[dict]:
    normalized: list[dict] = []
    for row in rows:
        try:
            score = float(row.get("overall_sentiment_score") or 0)
        except (TypeError, ValueError):
            score = 0.0
        sentiment = "Bullish" if score >= 0.15 else "Bearish" if score <= -0.15 else "Neutral"
        normalized.append(
            {
                "title": row.get("title", "").strip(),
                "summary": row.get("summary", "").strip(),
                "source": row.get("source", "Alpha Vantage") or "Alpha Vantage",
                "provider": "Alpha Vantage",
                "url": row.get("url", ""),
                "published_at": row.get("time_published", ""),
                "sentiment": sentiment,
                "sentiment_score": score,
            }
        )
    return [row for row in normalized if row["title"]]


def merge_news(finnhub_rows: list[dict], alpha_rows: list[dict], limit: int = 20) -> list[dict]:
    rows = normalize_finnhub(finnhub_rows) + normalize_alpha_vantage(alpha_rows)
    seen: set[str] = set()
    unique: list[dict] = []
    for row in rows:
        key = " ".join(row["title"].lower().split())
        if key and key not in seen:
            seen.add(key)
            unique.append(row)
    return unique[:limit]


def sentiment_summary(rows: list[dict]) -> dict:
    counts = {"Bullish": 0, "Neutral": 0, "Bearish": 0}
    scores: list[float] = []
    for row in rows:
        sentiment = row.get("sentiment", "Neutral")
        counts[sentiment if sentiment in counts else "Neutral"] += 1
        if row.get("provider") == "Alpha Vantage":
            scores.append(float(row.get("sentiment_score") or 0))
    average = sum(scores) / len(scores) if scores else 0.0
    label = "Bullish" if average >= 0.15 else "Bearish" if average <= -0.15 else "Neutral"
    return {"counts": counts, "average_score": average, "label": label}
