# AI Futures Dashboard — Integrated Edition

## Integrations

- Responsive native Plotly candlestick chart
- Tradovate REST authentication, accounts, balances, positions and orders (read-only)
- Trading Economics economic calendar
- Finnhub market news
- Alpha Vantage News & Sentiment
- Custom AI Market Score

## Safety

Order execution is deliberately disabled in `services/tradovate.py`. This build reads account data but cannot place a trade. Validate everything in the Tradovate demo environment before adding order code.

## Setup

```cmd
py -m pip install -r requirements.txt
copy .env.example .env
py -m streamlit run app.py
```

Fill in `.env` with your own API credentials. The dashboard runs with fallback/demo content when keys are missing.

## Chart data note

The dashboard no longer embeds TradingView. It uses a responsive native Plotly chart, preventing TradingView-only symbol errors. Demo candles remain visible until a supported live market-data feed is connected.

## Tradovate credentials

Create API credentials from your Tradovate account and use the demo environment first. Depending on your account permissions and market-data subscriptions, some endpoints may not return data.


## Responsive layout

This edition automatically adapts to large monitors, laptops, tablets, and narrow browser windows. Market cards, the chart/news area, bottom analytics panels, and alert cards reflow at 1450 px, 1050 px, and 680 px breakpoints.

## Hybrid TradingView mode

The dashboard uses embeddable market proxies in the TradingView widget for futures whose exact CME/COMEX/NYMEX contracts are restricted in third-party embeds. Use **Open exact chart in TradingView** to view MES, MNQ, MGC, or MCL in your logged-in TradingView Premium account. The dashboard is view-only and contains no order-routing controls.

## Live headlines

Add one or both keys to `.env`:

```env
FINNHUB_API_KEY=your_finnhub_key
ALPHAVANTAGE_API_KEY=your_alpha_vantage_key
```

Finnhub supplies the fast general-market headline stream. Alpha Vantage supplies news sentiment. The dashboard refreshes Finnhub data every 60 seconds and caches Alpha Vantage for five minutes to reduce rate-limit usage. The sidebar also provides a manual refresh button and refresh-interval selector.

## API-key troubleshooting
Place `.env` beside `app.py` (recommended). This build also checks the folder immediately above the project folder, which helps when the ZIP is extracted with an extra nested directory.

Use exact variable names:

```env
FINNHUB_API_KEY=your_finnhub_key
ALPHAVANTAGE_API_KEY=your_alpha_vantage_key
```

After saving `.env`, completely stop Streamlit with `Ctrl+C`, then restart it.


## Economic calendar without an API key

The app reads the public Trading Economics calendar webpage directly and stores a local JSON cache for 24 hours. No `TRADINGECONOMICS_KEY` is needed.

- Source: `https://tradingeconomics.com/calendar`
- Default filter: United States
- Range: today through the next 3 days
- Automatic refresh: once after the cache becomes older than 24 hours
- Manual refresh: sidebar button
- Offline fallback: last successful local cache

The scan only occurs while the app is running or when it is opened. Website HTML changes or access restrictions can require parser maintenance. Review the website terms before automated use.


## Date-wise calendar

The Economic Calendar can now be filtered by date, groups events under date headers, shows Medium and High impact by default, and retains pagination.


## Calendar impact and timezone fix

- Reads impact from multiple Trading Economics HTML markers.
- Uses a conservative event-name fallback only when the public markup omits impact.
- Treats scraped webpage times as UTC/GMT and converts them to America/Chicago.
- Central Time automatically switches between CST and CDT.
- Uses a new v3 cache so old Low-impact and incorrectly timed rows are discarded.


## Simplified calendar interface

- Removed impact, date, events-per-page, and All Dates controls.
- Displays Medium and High impact events automatically.
- Detects the browser's IANA timezone and converts event times locally.
- Keeps each calendar date together and displays up to three dates per page.
- Uses numbered pagination at the bottom.


## Current-day calendar pagination

- Removed the local-timezone sentence from the interface.
- Shows only one calendar date per page.
- Page 1 shows today when today has events; otherwise the next available date.
- Other dates appear as numbered pagination buttons at the bottom.
- Medium and High impact events remain enabled automatically.


## Economic Calendar card navigation

- Economic Calendar title is now inside the card.
- Numbered pagination was removed.
- Compact Back and Next buttons are inside the card footer.
- One local calendar date is displayed at a time.
- Event times continue to use the viewer's browser timezone.


## Economic Calendar scrolling

- The event rows now scroll independently inside the calendar card.
- The date header, column headings, and Back/Next buttons remain visible.
- The event area has a fixed maximum height of 330 px.
- A compact styled scrollbar was added.


## Live Headlines scrolling

- Displays five news items in LIVE HEADLINES & SENTIMENT.
- Adds an independent vertical scrollbar to the headline list.
- Keeps the title and update/status line visible.


## Economic Calendar five-row scroll

- Displays approximately five economic events at a time.
- Additional events remain available through the vertical scrollbar.
- The date header, column headings, and Back/Next controls stay visible.


## Economic Calendar alignment

- Aligns the calendar card with Risk Manager, Performance Overview, and Trade Journal.
- Removes the chart-specific 390 px minimum height from the calendar only.
- Preserves the five-event scrolling area and Back/Next controls.


## Bottom card alignment

- Economic Calendar, Risk Manager, Performance Overview, and Trade Journal now share one top line.
- All four cards use the same 390 px height.
- The invisible browser-timezone component no longer creates space above the calendar.
- Existing calendar scrolling and Back/Next navigation are preserved.


## Economic Calendar HTML card rebuild

- Replaced Streamlit bordered container with the same HTML card system used by the other bottom cards.
- Calendar now aligns at the same top edge as Risk Manager, Performance Overview, and Trade Journal.
- Preserved five-row scrolling, local timezone conversion, and Back/Next navigation.
