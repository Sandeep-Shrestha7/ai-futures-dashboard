from __future__ import annotations
import json
from urllib.parse import quote

# Exact symbols open on TradingView.com. A user's TradingView Premium and exchange
# subscriptions apply there, not inside third-party embedded widgets.
EXACT_SYMBOLS = {
    "MES": "CME_MINI:MES1!",
    "MNQ": "CME_MINI:MNQ1!",
    "MGC": "COMEX:MGC1!",
    "MCL": "NYMEX:MCL1!",
    "VIX": "CBOE:VIX",
    "DXY": "TVC:DXY",
}

# Embeddable proxies avoid the “only available on TradingView” futures restriction.
# They are context charts, not contract-identical replacements.
EMBED_SYMBOLS = {
    "MES": {"symbol": "AMEX:SPY", "label": "SPY (S&P 500 proxy)"},
    "MNQ": {"symbol": "NASDAQ:QQQ", "label": "QQQ (Nasdaq-100 proxy)"},
    "MGC": {"symbol": "AMEX:GLD", "label": "GLD (gold proxy)"},
    "MCL": {"symbol": "AMEX:USO", "label": "USO (crude-oil proxy)"},
    "VIX": {"symbol": "CBOE:VIX", "label": "VIX index"},
    "DXY": {"symbol": "TVC:DXY", "label": "U.S. Dollar Index"},
}

def tradingview_url(symbol: str) -> str:
    exact = EXACT_SYMBOLS.get(symbol, EXACT_SYMBOLS["MES"])
    return f"https://www.tradingview.com/chart/?symbol={quote(exact, safe='')}"

def advanced_chart_html(symbol: str = "MES", interval: str = "15") -> str:
    tv_symbol = EMBED_SYMBOLS.get(symbol, EMBED_SYMBOLS["MES"])["symbol"]
    config = {
        "autosize": True,
        "symbol": tv_symbol,
        "interval": interval,
        "timezone": "America/Chicago",
        "theme": "dark",
        "style": "1",
        "locale": "en",
        "backgroundColor": "rgba(11, 23, 36, 1)",
        "gridColor": "rgba(32, 52, 74, 0.45)",
        "withdateranges": True,
        "hide_side_toolbar": False,
        "allow_symbol_change": False,
        "save_image": False,
        "calendar": False,
        "details": False,
        "hotlist": False,
        "studies": ["STD;EMA", "STD;VWAP"],
        "support_host": "https://www.tradingview.com",
    }
    return f'''<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>
html,body,.tradingview-widget-container,.tradingview-widget-container__widget{{height:100%;width:100%;margin:0;background:#0b1724;overflow:hidden}}
</style></head><body><div class="tradingview-widget-container"><div class="tradingview-widget-container__widget"></div>
<script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async>{json.dumps(config)}</script>
</div></body></html>'''
