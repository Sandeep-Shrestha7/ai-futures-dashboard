from datetime import datetime
from html import escape
from zoneinfo import ZoneInfo
import numpy as np, pandas as pd, plotly.graph_objects as go, streamlit as st
import streamlit.components.v1 as components

def format_currency_signed(value) -> str:
    """Format a number as signed US currency, e.g. +$125.50 or -$42.00."""
    try:
        amount = float(value)
    except (TypeError, ValueError):
        amount = 0.0
    sign = "+" if amount >= 0 else "-"
    return f"{sign}${abs(amount):,.2f}"

try:
    from streamlit_js_eval import streamlit_js_eval
except ImportError:
    streamlit_js_eval = None
from services.tradingview import advanced_chart_html, tradingview_url, EMBED_SYMBOLS
from services.config import settings
from services.tradovate import TradovateClient
from services.calendar_scraper import economic_calendar, calendar_cache_info
from services.news_api import (
    alpha_vantage_news, finnhub_market_news, merge_news, sentiment_summary
)
from services.ai_score import calculate_ai_score
st.set_page_config(page_title='AI Futures Dashboard',page_icon='📈',layout='wide')
CT=ZoneInfo('America/Chicago')
st.markdown('''<style>
:root{
 --bg:#06101a;--panel:#0b1724;--border:#20344a;--text:#e8eef6;
 --muted:#8ea0b5;--green:#36d66b;--red:#ff505a;--amber:#f8b83e;--blue:#4da3ff
}
html,body,[data-testid="stAppViewContainer"],.stApp{min-width:0;background:var(--bg);color:var(--text)}

[data-testid="stSidebar"]{background:#07131f;border-right:1px solid var(--border)}
[data-testid="stSidebar"] *{color:var(--text)}

.panel{background:linear-gradient(180deg,#0d1b2a,#091522);border:1px solid var(--border);border-radius:10px;padding:clamp(9px,1vw,13px);height:100%;min-width:0;box-sizing:border-box;overflow:hidden}
.ticker-card,.market-score-card{min-height:132px;height:auto}
.right-brief,.right-news,.bottom-card,.performance-card{height:auto;min-height:0}
.chart-shell{min-height:390px;height:min(58vh,610px);background:linear-gradient(180deg,#0d1b2a,#091522);border:1px solid var(--border);border-radius:10px;padding:10px;box-sizing:border-box;overflow:hidden}
.panel-title{font-weight:800;font-size:clamp(.72rem,.8vw,.86rem);margin-bottom:9px;white-space:normal}
.muted{color:var(--muted);font-size:clamp(.65rem,.72vw,.76rem)}
.positive{color:var(--green)}.negative{color:var(--red)}.warning{color:var(--amber)}
.ticker{font-weight:800}.price{font-size:clamp(1.02rem,1.35vw,1.35rem);font-weight:900;margin-top:5px}
.score{font-size:clamp(2.45rem,3.7vw,3.35rem);line-height:1;text-align:center;font-weight:900}
.score-sub,.score-label{text-align:center}.score-label{font-weight:800;margin-top:5px}

.top-market-grid{display:grid;grid-template-columns:repeat(7,minmax(min(100%,150px),1fr));gap:clamp(7px,.8vw,11px);align-items:stretch;width:100%;min-width:0;padding-bottom:2px}
.top-market-grid .panel{min-width:0}.top-market-grid .market-score-card{min-width:0}

.stPlotlyChart{margin:0!important;width:100%!important;min-width:0!important}
div[data-testid='stVerticalBlockBorderWrapper']{background:linear-gradient(180deg,#0d1b2a,#091522);border:1px solid var(--border)!important;border-radius:10px!important;padding:0!important;min-height:390px;height:min(58vh,610px);overflow:hidden;box-sizing:border-box}
div[data-testid='stVerticalBlockBorderWrapper']>div{padding:10px!important;min-width:0!important}
div[data-testid='stVerticalBlockBorderWrapper'] iframe{width:100%!important;max-width:100%!important}
.chart-title{margin:0 0 2px 0!important}
div[data-testid='stHorizontalBlock']{align-items:stretch!important;gap:clamp(7px,.8vw,11px)!important;min-width:0}
div[data-testid='column']{display:flex;flex-direction:column;min-width:0!important}
div[data-testid='column']>div{width:100%;min-width:0}

.brief-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));border:1px solid var(--border);border-radius:7px;overflow:hidden;margin-bottom:8px}
.brief-cell{padding:8px 4px;text-align:center;border-right:1px solid var(--border);min-width:0;overflow-wrap:anywhere}.brief-cell:last-child{border-right:none}
.news-row,.journal-row{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:8px;padding:7px 0;border-bottom:1px solid #1b2a3c;align-items:center;overflow-wrap:anywhere}
.calendar-row{display:grid;grid-template-columns:minmax(82px,.9fr) minmax(220px,2.4fr) minmax(72px,.8fr) repeat(3,minmax(72px,.8fr));gap:7px;padding:7px 0;border-bottom:1px solid #1b2a3c;font-size:clamp(.62rem,.68vw,.72rem);align-items:center;min-width:720px}
.panel:has(.calendar-row){overflow-x:auto}
.calendar-body{
 max-height:285px;
 min-height:120px;
 overflow-y:auto;
 overflow-x:hidden;
 padding-right:5px;
 scrollbar-width:thin;
 scrollbar-color:#48627d #0d1826;
}
.calendar-body .calendar-row{
 min-height:54px;
 align-items:center;
}
.calendar-body::-webkit-scrollbar{width:7px}
.calendar-body::-webkit-scrollbar-track{
 background:#0d1826;
 border-radius:10px;
}
.calendar-body::-webkit-scrollbar-thumb{
 background:#48627d;
 border-radius:10px;
}
.calendar-body::-webkit-scrollbar-thumb:hover{background:#607f9e}
.calendar-scroll-shell{
 border-left:1px solid #263b52;
 border-right:1px solid #263b52;
 border-bottom:1px solid #263b52;
 border-radius:0 0 8px 8px;
 overflow:hidden;
}
.tag{padding:2px 7px;border-radius:4px;font-size:.65rem;font-weight:800;white-space:nowrap}.tag-green{background:rgba(54,214,107,.16);color:var(--green)}.tag-red{background:rgba(255,80,90,.16);color:var(--red)}.tag-gray{background:rgba(142,160,181,.16);color:#bac4d0}.tag-amber{background:rgba(248,184,62,.16);color:var(--amber)}
.alertbar{display:grid;margin-top:10px;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;background:#0b1724;border:1px solid var(--border);border-radius:10px;padding:10px}.alert{padding:8px 10px;border-radius:6px;text-align:center;font-size:.72rem;border:1px solid var(--border);overflow-wrap:anywhere}.alert-red{border-color:#a83b45;color:#ff7a82}.alert-amber{border-color:#a17b1c;color:#ffd166}.alert-green{border-color:#2b7f4c;color:#6de59a}

.performance-card{display:flex;flex-direction:column;min-height:300px}
.performance-kpis{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px 12px;margin-bottom:8px}.performance-kpi{display:flex;justify-content:space-between;gap:8px;align-items:center;border-bottom:1px solid #1b2a3c;padding:4px 0;font-size:.69rem;min-width:0}.performance-chart{height:clamp(120px,15vh,165px);min-height:120px;border:1px solid #1b2a3c;border-radius:7px;background:#091522;padding:4px;box-sizing:border-box;margin-top:2px}.performance-footer{display:flex;flex-wrap:wrap;gap:6px 12px;justify-content:space-between;align-items:center;margin-top:auto;padding-top:7px;border-top:1px solid #1b2a3c;font-size:.72rem}.performance-value{font-weight:800}

/* Medium desktop / laptop */
@media(max-width:1450px){
 .top-market-grid{grid-template-columns:repeat(4,minmax(145px,1fr))}
 div[data-testid='stHorizontalBlock']:has(.bottom-card){flex-wrap:wrap!important}
 div[data-testid='stHorizontalBlock']:has(.bottom-card)>div[data-testid='column']{flex:1 1 calc(50% - 11px)!important;width:calc(50% - 11px)!important;min-width:330px!important}
}
/* Tablet and narrow windows */
@media(max-width:1050px){
 .top-market-grid{grid-template-columns:repeat(2,minmax(145px,1fr))}
 div[data-testid='stHorizontalBlock']:has(.right-brief){flex-wrap:wrap!important}
 div[data-testid='stHorizontalBlock']:has(.right-brief)>div[data-testid='column']{flex:1 1 100%!important;width:100%!important}
 div[data-testid='stVerticalBlockBorderWrapper']{height:min(56vh,540px)}
 .alertbar{grid-template-columns:repeat(2,minmax(0,1fr))}
}
/* Phone-sized browser or very narrow side-by-side window */
@media(max-width:680px){
 
 .top-market-grid{grid-template-columns:1fr}
 .brief-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.brief-cell:nth-child(2){border-right:none}.brief-cell:nth-child(-n+2){border-bottom:1px solid var(--border)}
 div[data-testid='stHorizontalBlock']:has(.bottom-card)>div[data-testid='column']{flex:1 1 100%!important;width:100%!important;min-width:0!important}
 div[data-testid='stHorizontalBlock']:has(.chart-title){flex-wrap:wrap!important}
 div[data-testid='stHorizontalBlock']:has(.chart-title)>div[data-testid='column']{flex:1 1 100%!important;width:100%!important}
 div[data-testid='stVerticalBlockBorderWrapper']{height:470px;min-height:430px}
 .alertbar{grid-template-columns:1fr}
 .performance-kpis{grid-template-columns:1fr}
}

.news-scroll-shell{
 max-height:365px;
 overflow-y:auto;
 overflow-x:hidden;
 padding-right:5px;
 scrollbar-width:thin;
 scrollbar-color:#48627d #0d1826;
}
.news-scroll-shell::-webkit-scrollbar{width:7px}
.news-scroll-shell::-webkit-scrollbar-track{
 background:#0d1826;
 border-radius:10px;
}
.news-scroll-shell::-webkit-scrollbar-thumb{
 background:#48627d;
 border-radius:10px;
}
.news-scroll-shell::-webkit-scrollbar-thumb:hover{background:#607f9e}

.economic-card{
 height:390px!important;
 min-height:390px!important;
 max-height:390px!important;
 display:flex!important;
 flex-direction:column!important;
 box-sizing:border-box!important;
}
.economic-card .calendar-date-bar{
 padding:10px 12px;
 background:#13253a;
 border-radius:8px 8px 0 0;
 border:1px solid #263b52;
 font-weight:800;
 margin-top:8px;
}
.economic-card .calendar-columns{
 flex:0 0 auto;
}
.economic-card .calendar-scroll-shell{
 flex:1 1 auto;
 min-height:0;
}
.economic-card .calendar-body{
 max-height:245px;
}

/* Unified bottom dashboard row. All four columns start at the exact same Y position. */
.bottom-row-anchor{display:none}
div[data-testid="stHorizontalBlock"]:has(.bottom-row-anchor){
 align-items:stretch!important;
 gap:10px!important;
 margin-top:0!important;
}
div[data-testid="stHorizontalBlock"]:has(.bottom-row-anchor)>div[data-testid="column"]{
 display:flex!important;
 flex-direction:column!important;
 align-self:stretch!important;
 min-width:0!important;
}
div[data-testid="stHorizontalBlock"]:has(.bottom-row-anchor)>div[data-testid="column"]>div[data-testid="stVerticalBlock"]{
 height:100%!important;
 gap:0!important;
}
.dashboard-bottom-card{
 height:390px!important;
 min-height:390px!important;
 max-height:390px!important;
 margin:0!important;
}
.economic-card{padding-bottom:52px!important;position:relative!important}
.calendar-nav-row{margin-top:-46px!important;padding:0 12px!important;position:relative!important;z-index:10!important}
.calendar-nav-row button{min-height:34px!important;padding:.25rem .65rem!important}
div[data-testid="stElementContainer"]:has(.calendar-nav-row){height:0!important;min-height:0!important;margin:0!important;padding:0!important}
div[data-testid="stElementContainer"]:has(.calendar-nav-row)+div[data-testid="stHorizontalBlock"]{
 margin-top:-46px!important;
 padding:0 12px!important;
 position:relative!important;
 z-index:10!important;
}

.ai-bottom-anchor{height:0!important;margin:0!important;padding:0!important}
div[data-testid="stHorizontalBlock"]:has(.ai-bottom-anchor){
 gap:10px!important;align-items:stretch!important
}
.ai-pro-card,.journal-analytics-card{
 height:188px!important;min-height:188px!important;max-height:188px!important;
 border:1px solid #1d654d!important;border-radius:7px!important;
 background:linear-gradient(180deg,#091724 0%,#07131f 100%)!important;
 box-shadow:0 7px 18px rgba(0,0,0,.18)!important;
 padding:11px 13px!important;box-sizing:border-box!important;overflow:hidden!important
}
.journal-analytics-card{border-color:#263b51!important}
.ai-pro-title,.journal-pro-title{
 display:flex;align-items:center;gap:7px;font-size:.72rem;font-weight:900;
 color:#62e7a0;margin-bottom:8px;line-height:1
}
.journal-pro-title{color:#e7eef6}
.ai-pro-grid{
 display:grid;grid-template-columns:.9fr 1fr 1fr 1fr 1fr .82fr;gap:0;
 border-bottom:1px solid #182c3c;padding-bottom:7px
}
.ai-pro-metric{
 min-height:54px;padding:4px 10px;border-right:1px solid #172a3b;
 box-sizing:border-box;position:relative
}
.ai-pro-metric:first-child{padding-left:6px}.ai-pro-metric:last-child{border-right:none}
.ai-pro-label,.journal-stat-label{font-size:.52rem;color:#7f94a9;margin-bottom:4px}
.ai-pro-value{font-size:.82rem;font-weight:900;color:#ecf4fb;line-height:1.05}
.ai-pro-sub{font-size:.53rem;color:#b0bfcd;margin-top:5px}
.ai-pro-bias{color:#31e67c}.ai-pro-stop{color:#eaf2f9}
.ai-why-head{font-size:.56rem;font-weight:800;color:#b9c8d5;margin:7px 0 5px}
.ai-why-row{display:flex;align-items:center;gap:10px;white-space:nowrap;overflow:hidden}
.ai-why-item{font-size:.49rem;color:#a9bbc9;display:flex;align-items:center;gap:4px}
.ai-check{
 width:9px;height:9px;border:1px solid #22d979;border-radius:50%;
 display:inline-flex;align-items:center;justify-content:center;color:#22d979;
 font-size:.38rem;font-weight:900;flex:none
}
.journal-stats{
 display:grid;grid-template-columns:.8fr .8fr 1fr .9fr 1.22fr;gap:0;
 border-bottom:1px solid #182c3c;padding-bottom:7px
}
.journal-stat{padding:3px 11px;border-right:1px solid #172a3b;min-height:49px}
.journal-stat:first-child{padding-left:5px}.journal-stat:last-child{border-right:none}
.journal-stat-value{font-size:.68rem;font-weight:900;color:#eef5fb;line-height:1.2}
.journal-stat-sub{font-size:.51rem;color:#31e67c;margin-top:3px;font-weight:700}
.recent-title{font-size:.55rem;color:#66bfe9;font-weight:800;margin:7px 0 5px}
.recent-trades-row{display:flex;gap:17px;align-items:center;white-space:nowrap;overflow:hidden}
.recent-trade{font-size:.48rem;color:#9fb1c0}.recent-trade b{margin-left:4px}
.journal-link{font-size:.49rem;color:#5bb7ef;margin-top:8px}
@media(max-width:1100px){
 .ai-pro-card,.journal-analytics-card{height:auto!important;max-height:none!important}
 .ai-pro-grid{grid-template-columns:repeat(3,1fr)}
 .journal-stats{grid-template-columns:repeat(3,1fr)}
 .ai-why-row,.recent-trades-row{flex-wrap:wrap;white-space:normal}
}


/* Economic Calendar and Live Headlines now share the same dashboard row. */
div[data-testid="stHorizontalBlock"]:has(.bottom-row-anchor){
 align-items:flex-start!important
}
.news-scroll-shell{max-height:180px!important;overflow-y:auto!important}

.ai-morning-brief{
 min-height:410px!important;
 border-color:#263f56!important;
 padding:13px 14px!important;
 box-sizing:border-box!important
}
.ai-brief-header{
 display:flex;align-items:center;justify-content:space-between;
 gap:12px;margin-bottom:10px
}
.ai-brief-title{
 font-size:.79rem;font-weight:900;color:#eef5fb;
 display:flex;align-items:center;gap:7px
}
.ai-brief-updated{font-size:.54rem;color:#8195aa}
.ai-brief-summary{
 font-size:.63rem;line-height:1.65;color:#c8d5e2;
 padding:8px 0 10px;border-bottom:1px solid #1a3044
}
.ai-brief-signals{
 display:grid;grid-template-columns:repeat(4,1fr);gap:7px;
 margin-top:11px
}
.ai-brief-signal{
 border:1px solid #213a50;border-radius:7px;
 background:#081725;padding:9px 9px;min-height:58px;
 box-sizing:border-box
}
.ai-brief-signal-label{
 font-size:.52rem;color:#8fa2b5;text-transform:uppercase;
 letter-spacing:.03em;margin-bottom:5px
}
.ai-brief-signal-value{
 font-size:.73rem;font-weight:900;display:flex;align-items:center;gap:5px
}
.ai-levels-title{
 margin-top:13px;padding-bottom:6px;border-bottom:1px solid #1a3044;
 font-size:.61rem;font-weight:900;color:#eaf2f9
}
.ai-levels-grid{
 display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:8px
}
.ai-level-column:first-child{border-right:1px solid #1a3044;padding-right:13px}
.ai-level-heading{
 font-size:.54rem;font-weight:900;text-transform:uppercase;margin-bottom:7px
}
.ai-level-row{
 display:flex;justify-content:space-between;align-items:center;
 padding:4px 0;font-size:.61rem
}
.ai-level-name{font-weight:800}.ai-level-price{font-weight:900;color:#eef5fb}
@media(max-width:900px){
 .ai-brief-signals{grid-template-columns:repeat(2,1fr)}
}

/* Responsive compact dashboard */

div[data-testid="stVerticalBlock"]{gap:clamp(.35rem,.65vw,.6rem)!important}
div[data-testid="stHorizontalBlock"]{
 gap:clamp(.35rem,.65vw,.65rem)!important;
 align-items:stretch!important
}
.panel{padding:clamp(8px,.7vw,12px)!important}
.headerbar{min-height:54px!important}
.market-card{min-height:96px!important}
.chart-card iframe{height:min(42vh,430px)!important}
.right-brief,.ai-morning-brief{min-height:min(42vh,430px)!important}
.bottom-card,.economic-card,.dashboard-bottom-card{
 min-height:190px!important;
 max-height:220px!important;
 overflow:hidden!important
}
.news-scroll-shell,.headline-scroll{
 max-height:160px!important;
 overflow-y:auto!important
}
.ai-pro-card,.journal-analytics-card{
 height:auto!important;
 min-height:154px!important;
 max-height:none!important
}
.ai-pro-grid{
 grid-template-columns:repeat(6,minmax(0,1fr))!important
}
.journal-stats{
 grid-template-columns:repeat(5,minmax(0,1fr))!important
}
.ai-pro-metric,.journal-stat{min-width:0!important}
.ai-pro-value,.journal-stat-value{overflow-wrap:anywhere}
img,svg,canvas,iframe{max-width:100%!important}
[data-testid="stDataFrame"],[data-testid="stTable"]{overflow-x:auto!important}

/* Laptop and tablet */
@media (max-width: 1400px){
 .market-grid,.ticker-grid,.market-overview-grid{
  grid-template-columns:repeat(4,minmax(0,1fr))!important
 }
 .ai-pro-grid{grid-template-columns:repeat(3,minmax(0,1fr))!important}
 .journal-stats{grid-template-columns:repeat(3,minmax(0,1fr))!important}
 .chart-card iframe{height:390px!important}
 .right-brief,.ai-morning-brief{min-height:390px!important}
}

/* Tablet */
@media (max-width: 980px){
 .headerbar,.top-header,.premium-header{
  grid-template-columns:1fr 1fr!important;
  height:auto!important
 }
 .market-grid,.ticker-grid,.market-overview-grid{
  grid-template-columns:repeat(2,minmax(0,1fr))!important
 }
 div[data-testid="stHorizontalBlock"]{
  flex-wrap:wrap!important
 }
 div[data-testid="column"]{
  flex:1 1 48%!important;
  width:48%!important;
  min-width:320px!important
 }
 .ai-brief-signals{grid-template-columns:repeat(2,minmax(0,1fr))!important}
 .ai-levels-grid{grid-template-columns:1fr!important}
 .ai-level-column:first-child{
  border-right:none!important;
  border-bottom:1px solid #1a3044!important;
  padding-right:0!important;
  padding-bottom:8px!important
 }
 .chart-card iframe{height:360px!important}
 .right-brief,.ai-morning-brief{min-height:auto!important}
}

/* Mobile */
@media (max-width: 680px){
 
 .headerbar,.top-header,.premium-header{
  grid-template-columns:1fr!important;
  gap:7px!important
 }
 .market-grid,.ticker-grid,.market-overview-grid{
  grid-template-columns:1fr!important
 }
 div[data-testid="column"]{
  flex:1 1 100%!important;
  width:100%!important;
  min-width:0!important
 }
 .ai-pro-grid,.journal-stats{
  grid-template-columns:repeat(2,minmax(0,1fr))!important
 }
 .ai-pro-metric:nth-child(even),
 .journal-stat:nth-child(even){border-right:none!important}
 .ai-why-row,.recent-trades-row{
  white-space:normal!important;
  flex-wrap:wrap!important
 }
 .chart-card iframe{height:310px!important}
 .bottom-card,.economic-card,.dashboard-bottom-card{
  min-height:180px!important;
  max-height:none!important
 }
 .news-scroll-shell,.headline-scroll{max-height:150px!important}
 .ai-brief-signals{grid-template-columns:1fr!important}
 .ai-pro-title,.journal-pro-title{font-size:.68rem!important}
 .ai-pro-value{font-size:.74rem!important}
 .journal-stat-value{font-size:.63rem!important}
}

/* Very small phones */
@media (max-width: 430px){
 .ai-pro-grid,.journal-stats{grid-template-columns:1fr!important}
 .ai-pro-metric,.journal-stat{
  border-right:none!important;
  border-bottom:1px solid #172a3b!important
 }
 .ai-pro-metric:last-child,.journal-stat:last-child{border-bottom:none!important}
 .chart-card iframe{height:275px!important}
}


/* Professional clickable sidebar navigation */
section[data-testid="stSidebar"] 
section[data-testid="stSidebar"] .sidebar-nav-label{
 margin:1.05rem 0 .55rem;
 padding:0 .35rem;
 color:#71839a;
 font-size:.68rem;
 font-weight:700;
 letter-spacing:.14em
}
section[data-testid="stSidebar"] div[data-testid="stButton"]{
 margin:0 0 .42rem!important
}
section[data-testid="stSidebar"] div[data-testid="stButton"] > button{
 min-height:42px!important;
 padding:.55rem .72rem!important;
 border-radius:8px!important;
 justify-content:flex-start!important;
 text-align:left!important;
 font-size:.88rem!important;
 font-weight:600!important;
 letter-spacing:.005em!important;
 transition:background .16s ease,border-color .16s ease,transform .16s ease!important
}
section[data-testid="stSidebar"] div[data-testid="stButton"] > button:hover{
 transform:translateX(2px)!important;
 border-color:#31577d!important
}
section[data-testid="stSidebar"] div[data-testid="stButton"] > button[kind="primary"]{
 box-shadow:inset 3px 0 0 #53a8ff!important
}
section[data-testid="stSidebar"] .sidebar-status-separator{
 height:1px;
 background:#203247;
 margin:1rem .2rem .85rem
}


/* Clean responsive dashboard header */
.block-container{
    padding-top: 3.5rem !important;
    padding-bottom: 1.25rem !important;
    max-width: 100% !important;
}

div[data-testid="stAppViewContainer"]{
    overflow-x: hidden;
}

div[data-testid="stHorizontalBlock"]:has(.terminal-brand){
    position: relative !important;
    top: auto !important;
    transform: none !important;
    margin-top: 0 !important;
    margin-bottom: .75rem !important;
    padding: .75rem .85rem !important;
    min-height: 76px !important;
    height: auto !important;
    overflow: visible !important;
    border: 1px solid #18314a;
    border-radius: 12px;
    background: linear-gradient(180deg,#081522 0%,#07111b 100%);
    box-shadow: 0 8px 24px rgba(0,0,0,.18);
    align-items: center !important;
}

.terminal-brand{
    display:flex;
    align-items:center;
    gap:.7rem;
    min-height:54px;
}

.terminal-brand-icon{
    display:flex;
    align-items:center;
    justify-content:center;
    width:42px;
    min-width:42px;
    height:42px;
    border:1px solid #238cff;
    border-radius:11px;
    background:#0a1a2a;
    font-size:1.35rem;
}

.terminal-brand-title{
    color:#f3f7fb;
    font-size:1.15rem;
    font-weight:750;
    line-height:1.15;
    white-space:nowrap;
}

.terminal-brand-subtitle{
    margin-top:.18rem;
    color:#8fa0b4;
    font-size:.69rem;
    line-height:1.25;
    white-space:nowrap;
}

.terminal-metric,
.terminal-clock{
    min-height:52px;
    display:flex;
    flex-direction:column;
    justify-content:center;
    overflow:visible;
}

.terminal-label{
    color:#8f9daf;
    font-size:.66rem;
    line-height:1.35;
    white-space:nowrap;
}

.terminal-secondary{
    margin-top:.2rem;
    color:#8f9daf;
    font-size:.69rem;
    white-space:nowrap;
}

.terminal-value{
    margin-top:.18rem;
    color:#f2f6fb;
    font-size:.9rem;
    font-weight:700;
    line-height:1.2;
    white-space:nowrap;
}

.terminal-clock{
    text-align:center;
}

.terminal-clock-time{
    color:#f2f6fb;
    font-size:.9rem;
    font-weight:720;
    white-space:nowrap;
}

.terminal-clock-date{
    margin-top:.18rem;
    color:#8f9daf;
    font-size:.65rem;
    white-space:nowrap;
}

.header-status-open{color:#35d36f;font-weight:700}
.header-status-maintenance{color:#f0b84a;font-weight:700}
.header-status-closed{color:#ff5d6c;font-weight:700}

.terminal-header-divider{
    display:none;
}

div[data-testid="stHorizontalBlock"]:has(.terminal-brand) div[data-testid="stButton"] > button{
    min-height:38px !important;
    height:38px !important;
    padding:.3rem .45rem !important;
    border-color:#23435e !important;
    background:#091827 !important;
    font-weight:700 !important;
    margin-top:0 !important;
}

@media(max-width: 1280px){
    div[data-testid="stHorizontalBlock"]:has(.terminal-brand){
        flex-wrap:wrap !important;
        row-gap:.45rem !important;
    }

    div[data-testid="stHorizontalBlock"]:has(.terminal-brand) div[data-testid="column"]{
        min-width:135px !important;
        flex:1 1 135px !important;
    }

    .terminal-brand-title{font-size:1.02rem}
    .terminal-brand-subtitle{white-space:normal}
}

@media(max-width: 760px){
    .block-container{
        padding-top:3.75rem !important;
        padding-left:.65rem !important;
        padding-right:.65rem !important;
    }

    div[data-testid="stHorizontalBlock"]:has(.terminal-brand){
        padding:.7rem !important;
    }

    div[data-testid="stHorizontalBlock"]:has(.terminal-brand) div[data-testid="column"]{
        min-width:100% !important;
        width:100% !important;
        flex:1 1 100% !important;
    }

    .terminal-clock{
        text-align:left;
    }

    .terminal-brand-title,
    .terminal-brand-subtitle,
    .terminal-label,
    .terminal-secondary,
    .terminal-value,
    .terminal-clock-time,
    .terminal-clock-date{
        white-space:normal;
    }
}


/* Professional functional left navigation */
section[data-testid="stSidebar"]{
 background:
  radial-gradient(circle at 20% 10%,rgba(14,95,160,.12),transparent 28%),
  linear-gradient(180deg,#06111d 0%,#08131f 52%,#06101b 100%) !important;
 border-right:1px solid #12283d;
}

section[data-testid="stSidebar"] > div{
 padding-top:1.1rem !important;
}

.sidebar-brand{
 display:flex;
 align-items:center;
 gap:.75rem;
 padding:.45rem .55rem 1.15rem;
 margin-bottom:.3rem;
}

.sidebar-brand-icon{
 width:46px;
 height:46px;
 min-width:46px;
 display:flex;
 align-items:center;
 justify-content:center;
 border:1px solid #1d9dff;
 border-radius:12px;
 background:linear-gradient(180deg,#081b2d,#071522);
 box-shadow:0 0 20px rgba(0,146,255,.12);
 font-size:1.55rem;
}

.sidebar-brand-title{
 color:#f5f8fb;
 font-size:1.05rem;
 font-weight:800;
 letter-spacing:.02em;
 line-height:1.05;
}

.sidebar-brand-subtitle{
 margin-top:.28rem;
 color:#1399ff;
 font-size:.92rem;
 font-weight:700;
 letter-spacing:.04em;
}

section[data-testid="stSidebar"] div[data-testid="stButton"]{
 margin:.12rem 0 !important;
}

section[data-testid="stSidebar"] div[data-testid="stButton"] > button{
 width:100%;
 min-height:49px;
 justify-content:flex-start !important;
 text-align:left !important;
 padding:.72rem .85rem !important;
 border-radius:10px !important;
 border:1px solid transparent !important;
 background:transparent !important;
 color:#aeb9c8 !important;
 font-size:.95rem !important;
 font-weight:560 !important;
 transition:all .18s ease !important;
 box-shadow:none !important;
}

section[data-testid="stSidebar"] div[data-testid="stButton"] > button:hover{
 color:#f5f8fb !important;
 background:#0b1d2d !important;
 border-color:#173a58 !important;
 transform:translateX(2px);
}

section[data-testid="stSidebar"] div[data-testid="stButton"] > button[kind="primary"]{
 color:#f7fbff !important;
 background:linear-gradient(180deg,#12345b 0%,#0f2948 100%) !important;
 border-color:#145f9c !important;
 border-left:4px solid #17a6ff !important;
 box-shadow:inset 0 0 22px rgba(28,128,217,.12),0 6px 16px rgba(0,0,0,.18) !important;
}

section[data-testid="stSidebar"] div[data-testid="stButton"] > button p{
 font-size:.95rem !important;
 letter-spacing:.005em;
}

@media(max-width:900px){
 section[data-testid="stSidebar"]{
  min-width:230px !important;
  max-width:230px !important;
 }
 .sidebar-brand-title{font-size:.95rem}
 .sidebar-brand-subtitle{font-size:.82rem}
}

</style>''',unsafe_allow_html=True)
@st.cache_data
def data(n=180):
 r=np.random.default_rng(8);t=pd.date_range(end=pd.Timestamp.now(tz='America/Chicago'),periods=n,freq='15min');c=5500+np.linspace(0,60,n)+r.normal(0,4.2,n).cumsum();o=np.r_[c[0],c[:-1]]+r.normal(0,1.7,n);h=np.maximum(o,c)+r.uniform(1,4.5,n);l=np.minimum(o,c)-r.uniform(1,4.5,n);v=r.integers(300,1500,n);d=pd.DataFrame({'time':t,'open':o,'high':h,'low':l,'close':c,'volume':v});d['ema20']=d.close.ewm(span=20).mean();d['ema50']=d.close.ewm(span=50).mean();d['vwap']=(d.close*d.volume).cumsum()/d.volume.cumsum();return d
df=data(); markets=[('MES','E-mini S&P 500',5572.75,24.50,.44),('MNQ','E-mini Nasdaq-100',19825.25,-15,-.08),('MGC','Gold Futures',2395.80,8.60,.36),('MCL','Crude Oil WTI',78.32,.85,1.10),('VIX','Volatility Index',15.26,-.37,-2.36),('DXY','U.S. Dollar Index',104.38,.21,.20)]

@st.cache_data(ttl=3600, show_spinner=False)
def load_calendar(force_refresh=False):
 try:
  return economic_calendar(force_refresh=force_refresh, country="United States", days=3)
 except Exception:
  return []

@st.cache_data(ttl=60, show_spinner=False)
def load_finnhub_news():
 if not settings.finnhub_key:
  return [], "API key not configured"
 try:
  return finnhub_market_news(settings.finnhub_key, limit=24), "Connected"
 except Exception as exc:
  return [], str(exc)

@st.cache_data(ttl=300, show_spinner=False)
def load_alpha_news():
 # Alpha Vantage is cached longer to protect free-plan request limits.
 if not settings.alphavantage_key:
  return [], "API key not configured"
 try:
  return alpha_vantage_news(settings.alphavantage_key, limit=24), "Connected"
 except Exception as exc:
  message=str(exc).strip()
  if "Invalid inputs" in message:
   message="Request parameters rejected"
  elif "rate limit" in message.lower() or "call frequency" in message.lower():
   message="Rate limit reached"
  elif len(message)>90:
   message=message[:87]+"..."
  return [], message

def load_news_bundle():
 finnhub_rows, finnhub_status = load_finnhub_news()
 alpha_rows, alpha_status = load_alpha_news()
 items = merge_news(finnhub_rows, alpha_rows, limit=24)
 return {
  "items": items,
  "summary": sentiment_summary(items),
  "finnhub_status": finnhub_status,
  "alpha_status": alpha_status,
  "updated_at": datetime.now(CT),
 }

calendar_live=load_calendar()
news_bundle=load_news_bundle()
news_live=news_bundle["items"]
ai_result=calculate_ai_score(df,news_live,calendar_live)

@st.cache_data(ttl=30, show_spinner=False)
def load_tradovate_snapshot():
 if not all([settings.tradovate_username,settings.tradovate_password,settings.tradovate_cid,settings.tradovate_sec]): return None
 try:
  client=TradovateClient(settings.tradovate_username,settings.tradovate_password,settings.tradovate_app_id,settings.tradovate_app_version,settings.tradovate_cid,settings.tradovate_sec,settings.tradovate_device_id,settings.tradovate_demo)
  return client.account_snapshot()
 except Exception as exc:
  return {"error":str(exc)}
tradovate_snapshot=load_tradovate_snapshot()

if "active_page" not in st.session_state:
 st.session_state.active_page="Dashboard"

with st.sidebar:
 st.markdown(
  """
  <div class="sidebar-brand">
    <div class="sidebar-brand-icon">🧠</div>
    <div>
      <div class="sidebar-brand-title">AI FUTURES</div>
      <div class="sidebar-brand-subtitle">DASHBOARD</div>
    </div>
  </div>
  """,
  unsafe_allow_html=True,
 )

 navigation_items=[
  ("🏠","Dashboard","nav_dashboard"),
  ("⚙","AI Analysis","nav_ai_analysis"),
  ("📈","Chart","nav_chart"),
  ("📅","Economic Calendar","nav_calendar"),
  ("📰","News & Sentiment","nav_news"),
  ("🧲","AI Trade Setup","nav_ai_setup"),
  ("🛡","Risk Manager","nav_risk"),
  ("📉","Performance","nav_performance"),
  ("📒","Trade Journal","nav_journal"),
  ("⚙","Settings","nav_settings"),
 ]

 st.markdown('<div class="sidebar-nav-wrap">',unsafe_allow_html=True)
 for icon,label,key in navigation_items:
  active=st.session_state.active_page==label
  button_label=f"{icon}   {label}"
  if st.button(
   button_label,
   key=key,
   use_container_width=True,
   type="primary" if active else "secondary",
  ):
   st.session_state.active_page=label
   st.rerun()
 st.markdown('</div>',unsafe_allow_html=True)

 page=st.session_state.active_page
 news_refresh_seconds=60

 st.markdown('<div class="sidebar-status-separator"></div>',unsafe_allow_html=True)
 st.caption('DATA STATUS')
 st.markdown('<span class="positive">● Integrated</span>',unsafe_allow_html=True)
 st.caption('TRADOVATE')
 st.write('Demo connected' if tradovate_snapshot and not tradovate_snapshot.get('error') else 'Configure credentials')
 st.caption('NEWS')
 st.write('Finnhub: ' + ('Connected' if news_bundle['finnhub_status']=='Connected' else 'Not connected'))
 st.write('Alpha Vantage: ' + ('Connected' if news_bundle['alpha_status']=='Connected' else 'Not connected'))
 st.caption('ORDER EXECUTION')
 st.write('Disabled (safe mode)')

def _market_session_status(now_ct):
 # CME equity index futures are generally open Sunday-Friday with a daily
 # maintenance break from 4:00-5:00 PM Central Time.
 weekday=now_ct.weekday()
 minutes=now_ct.hour*60+now_ct.minute
 if weekday==5:
  return "Closed","header-status-closed"
 if weekday==6 and minutes<17*60:
  return "Closed","header-status-closed"
 if weekday==4 and minutes>=16*60:
  return "Closed","header-status-closed"
 if 16*60<=minutes<17*60:
  return "Maintenance","header-status-maintenance"
 return "Open","header-status-open"

def _header_account_values(snapshot):
 balance=50237.19
 daily_pnl=1247.50
 open_pnl=247.50
 account_mode="Demo"
 connected=False
 if snapshot and not snapshot.get("error"):
  connected=True
  account=snapshot.get("account",{}) or {}
  bal=snapshot.get("balance",{}) or {}
  balance=float(
   bal.get("amount")
   or bal.get("cashBalance")
   or bal.get("totalCashValue")
   or balance
  )
  daily_pnl=float(bal.get("realizedPnL") or 0)
  open_pnl=float(bal.get("openPnL") or 0)
  account_mode="Demo" if settings.tradovate_demo else "Live"
 return balance,daily_pnl,open_pnl,account_mode,connected

now=datetime.now(CT)
market_status,market_status_class=_market_session_status(now)
header_balance,header_daily_pnl,header_open_pnl,header_account_mode,header_connected=_header_account_values(tradovate_snapshot)
feed_label="Live" if header_connected else "Fallback"
feed_class="header-status-open" if header_connected else "header-status-maintenance"
daily_class="positive" if header_daily_pnl>=0 else "negative"
open_class="positive" if header_open_pnl>=0 else "negative"

header_left,header_status,header_clock,header_balance_col,header_daily_col,header_open_col,header_demo_col,header_refresh_col,header_settings_col=st.columns(
 [3.1,1.55,1.7,1.35,1.25,1.2,.95,.48,.48],
 gap="small",
 vertical_alignment="center",
)

with header_left:
 st.markdown(
  '<div class="terminal-brand">'
  '<div class="terminal-brand-icon">🧠</div>'
  '<div><div class="terminal-brand-title">AI Futures Dashboard</div>'
  '<div class="terminal-brand-subtitle">Real-time AI-driven market intelligence</div></div>'
  '</div>',
  unsafe_allow_html=True,
 )
with header_status:
 st.markdown(
  f'<div class="terminal-metric"><div class="terminal-label">Market Status: '
  f'<span class="{market_status_class}">● {market_status}</span></div>'
  f'<div class="terminal-secondary">Data: <span class="{feed_class}">{feed_label}</span></div></div>',
  unsafe_allow_html=True,
 )
with header_clock:
 st.markdown(
  f'<div class="terminal-clock"><div class="terminal-clock-time">{now:%I:%M:%S %p} CT</div>'
  f'<div class="terminal-clock-date">{now:%A, %B %d, %Y}</div></div>',
  unsafe_allow_html=True,
 )
with header_balance_col:
 st.markdown(
  f'<div class="terminal-metric"><div class="terminal-label">Account Balance</div>'
  f'<div class="terminal-value">${header_balance:,.2f}</div></div>',
  unsafe_allow_html=True,
 )
with header_daily_col:
 st.markdown(
  f'<div class="terminal-metric"><div class="terminal-label">Daily P/L</div>'
  f'<div class="terminal-value {daily_class}">{"+" if header_daily_pnl >= 0 else "-"}${abs(header_daily_pnl):,.2f}</div></div>',
  unsafe_allow_html=True,
 )
with header_open_col:
 st.markdown(
  f'<div class="terminal-metric"><div class="terminal-label">Open P/L</div>'
  f'<div class="terminal-value {open_class}">{"+" if header_open_pnl >= 0 else "-"}${abs(header_open_pnl):,.2f}</div></div>',
  unsafe_allow_html=True,
 )
with header_demo_col:
 if st.button(f"◉ {header_account_mode}",key="header_account_mode",use_container_width=True):
  st.session_state.active_page="Settings"
  st.rerun()
with header_refresh_col:
 if st.button("↻",key="header_refresh",help="Refresh dashboard data",use_container_width=True):
  data.clear()
  load_calendar.clear()
  load_finnhub_news.clear()
  load_alpha_news.clear()
  load_tradovate_snapshot.clear()
  st.rerun()
with header_settings_col:
 if st.button("⚙",key="header_settings",help="Open settings",use_container_width=True):
  st.session_state.active_page="Settings"
  st.rerun()

st.markdown('<div class="terminal-header-divider"></div>',unsafe_allow_html=True)
def ticker_html(m):
 s,n,p,ch,pc=m;cl='positive' if pc>=0 else 'negative';sg='+' if ch>=0 else ''
 return f'<div class="panel ticker-card"><div class="ticker">{s}</div><div class="muted">{n}</div><div class="price {cl}">{p:,.2f}</div><div class="{cl}" style="font-size:.72rem">{sg}{ch:.2f} ({sg}{pc:.2f}%)</div></div>'
def chart():
 symbols=["MES","MNQ","MGC","MCL","VIX","DXY"]
 symbol=st.session_state.get("chart_symbol","MES")
 if symbol not in symbols: symbol="MES"
 with st.container(border=True):
  h1,h2,h3=st.columns([3.2,1.05,1.35])
  with h1:
   st.markdown(f'<div class="panel-title chart-title">Hybrid Market Chart · {symbol}</div>',unsafe_allow_html=True)
   
  with h2:
   selected=st.selectbox("Chart",symbols,index=symbols.index(symbol),label_visibility="collapsed",key="chart_picker")
   st.session_state["chart_symbol"]=selected
   st.session_state["setup_symbol"]=selected
  with h3:
   mode=st.selectbox("Mode",["TradingView","Native fallback"],label_visibility="collapsed",key="chart_mode")

  if mode=="TradingView":
   proxy=EMBED_SYMBOLS[selected]
   st.caption(f"Embedded symbol: {proxy['label']} · Exact futures contract opens separately in TradingView.")
   components.html(advanced_chart_html(selected,"15"),height=500,scrolling=False)
   st.link_button(f"Open exact {selected} chart in TradingView ↗",tradingview_url(selected),use_container_width=True)
  else:
   scales={"MES":1.0,"MNQ":3.55,"MGC":0.43,"MCL":0.014,"VIX":0.0027,"DXY":0.0187}
   d=df.copy(); scale=scales.get(selected,1.0)
   for col in ["open","high","low","close","ema20","ema50","vwap"]: d[col]=d[col]*scale
   fig=go.Figure()
   fig.add_trace(go.Candlestick(x=d.time,open=d.open,high=d.high,low=d.low,close=d.close,name=selected))
   fig.add_trace(go.Scatter(x=d.time,y=d.ema20,name="EMA 20",mode="lines",line=dict(width=1.4)))
   fig.add_trace(go.Scatter(x=d.time,y=d.ema50,name="EMA 50",mode="lines",line=dict(width=1.4)))
   fig.add_trace(go.Scatter(x=d.time,y=d.vwap,name="VWAP",mode="lines",line=dict(width=1.2,dash="dot")))
   fig.update_layout(height=500,autosize=True,margin=dict(l=8,r=8,t=28,b=8),paper_bgcolor="#0b1724",plot_bgcolor="#0b1724",font=dict(color="#dce6f2"),xaxis=dict(rangeslider=dict(visible=False),showgrid=True,gridcolor="#1b2a3c"),yaxis=dict(side="right",showgrid=True,gridcolor="#1b2a3c",fixedrange=False),legend=dict(orientation="h",yanchor="bottom",y=1.01,xanchor="left",x=0),hovermode="x unified",uirevision=selected)
   st.plotly_chart(fig,use_container_width=True,config={"displaylogo":False,"responsive":True,"scrollZoom":True})
   st.link_button(f"Open {selected} in TradingView ↗",tradingview_url(selected),use_container_width=True)
def score():st.markdown(f'<div class="panel"><div class="panel-title">AI MARKET SCORE</div><div class="score warning">{ai_result.score}</div><div class="score-sub">/100</div><div class="score-label positive">{ai_result.label.upper()}</div><div class="score-sub muted">Confidence: {ai_result.confidence}%</div></div>',unsafe_allow_html=True)
def _published_label(value: str) -> str:
 if not value:
  return "Latest"
 try:
  if value.endswith("Z") or "+" in value:
   dt=pd.to_datetime(value,utc=True)
  else:
   dt=pd.to_datetime(value,utc=True)
  return dt.tz_convert("America/Chicago").strftime("%I:%M %p CT")
 except Exception:
  return "Latest"


def brief():
 close=float(df["close"].iloc[-1])
 ema20=float(df["ema20"].iloc[-1])
 ema50=float(df["ema50"].iloc[-1])
 vwap=float(df["vwap"].iloc[-1])

 recent=df.tail(48)
 momentum_pct=float(df["close"].pct_change(8).iloc[-1])*100
 volatility_pct=float(df["close"].pct_change().tail(30).std())*100

 if close>ema20>ema50:
  trend_label="Bullish";trend_class="positive";trend_icon="↗"
 elif close<ema20<ema50:
  trend_label="Bearish";trend_class="negative";trend_icon="↘"
 else:
  trend_label="Mixed";trend_class="warning";trend_icon="↔"

 if momentum_pct>0.12:
  momentum_label="Strong";momentum_class="positive";momentum_icon="▰"
 elif momentum_pct<-0.12:
  momentum_label="Weak";momentum_class="negative";momentum_icon="▱"
 else:
  momentum_label="Moderate";momentum_class="warning";momentum_icon="▰"

 summary=news_bundle["summary"]
 sentiment_label=summary["label"]
 sentiment_class="positive" if sentiment_label=="Bullish" else "negative" if sentiment_label=="Bearish" else "warning"
 sentiment_icon="☺" if sentiment_label=="Bullish" else "☹" if sentiment_label=="Bearish" else "•"

 if volatility_pct<0.08:
  volatility_label="Low";volatility_class="positive"
 elif volatility_pct<0.18:
  volatility_label="Moderate";volatility_class="warning"
 else:
  volatility_label="High";volatility_class="negative"

 support_1=float(recent["low"].quantile(.20))
 support_2=float(recent["low"].min())
 resistance_1=float(recent["high"].quantile(.80))
 resistance_2=float(recent["high"].max())

 above_vwap=close>=vwap
 bias_word="bullish" if ai_result.score>=55 else "bearish" if ai_result.score<=45 else "mixed"
 control_word="Buyers remain in control." if trend_label=="Bullish" else "Sellers remain in control." if trend_label=="Bearish" else "Price action is balanced."
 vwap_sentence="Price is trading above VWAP." if above_vwap else "Price is trading below VWAP."
 event_sentence="Avoid new entries immediately before high-impact economic events."
 sentiment_sentence=f'{sentiment_label} news sentiment is currently reflected in the AI score.'

 updated=datetime.now(CT).strftime("%I:%M %p")
 html=(
  f'<div class="panel right-brief ai-morning-brief">'
  f'<div class="ai-brief-header"><div class="ai-brief-title">🤖 AI Morning Brief</div>'
  f'<div class="ai-brief-updated">Updated {updated} CT</div></div>'
  f'<div class="ai-brief-summary">'
  f'Market bias is {bias_word}. {vwap_sentence}<br>'
  f'{control_word} {event_sentence}<br>'
  f'{sentiment_sentence}'
  f'</div>'
  f'<div class="ai-brief-signals">'
  f'<div class="ai-brief-signal"><div class="ai-brief-signal-label">Trend</div><div class="ai-brief-signal-value {trend_class}">{trend_icon} {trend_label}</div></div>'
  f'<div class="ai-brief-signal"><div class="ai-brief-signal-label">Momentum</div><div class="ai-brief-signal-value {momentum_class}">{momentum_icon} {momentum_label}</div></div>'
  f'<div class="ai-brief-signal"><div class="ai-brief-signal-label">Sentiment</div><div class="ai-brief-signal-value {sentiment_class}">{sentiment_icon} {sentiment_label}</div></div>'
  f'<div class="ai-brief-signal"><div class="ai-brief-signal-label">Volatility</div><div class="ai-brief-signal-value {volatility_class}">✦ {volatility_label}</div></div>'
  f'</div>'
  f'<div class="ai-levels-title">KEY LEVELS</div>'
  f'<div class="ai-levels-grid">'
  f'<div class="ai-level-column"><div class="ai-level-heading positive">Support</div>'
  f'<div class="ai-level-row"><span class="ai-level-name positive">S1</span><span class="ai-level-price">{support_1:,.2f}</span></div>'
  f'<div class="ai-level-row"><span class="ai-level-name positive">S2</span><span class="ai-level-price">{support_2:,.2f}</span></div></div>'
  f'<div class="ai-level-column"><div class="ai-level-heading negative">Resistance</div>'
  f'<div class="ai-level-row"><span class="ai-level-name negative">R1</span><span class="ai-level-price">{resistance_1:,.2f}</span></div>'
  f'<div class="ai-level-row"><span class="ai-level-name negative">R2</span><span class="ai-level-price">{resistance_2:,.2f}</span></div></div>'
  f'</div></div>'
 )
 st.markdown(html,unsafe_allow_html=True)

def news():
 items=news_live
 if not items:
  items=[{"title":"Add API keys in .env to activate live headlines","sentiment":"Neutral","source":"Setup","provider":"Dashboard","url":"","published_at":""}]
 rows=[]
 for item in items[:5]:
  title=escape(item.get("title", ""))[:120]
  source=escape(item.get("source", ""))
  provider=escape(item.get("provider", ""))
  url=item.get("url", "")
  title_html=f'<a href="{escape(url)}" target="_blank" rel="noopener noreferrer" style="color:#e8eef6;text-decoration:none">{title}</a>' if url else title
  sentiment=item.get("sentiment","Neutral")
  tag_class="tag-green" if sentiment=="Bullish" else "tag-red" if sentiment=="Bearish" else "tag-gray"
  stamp=_published_label(item.get("published_at", ""))
  rows.append(f'<div class="news-row"><span><span>{title_html}</span><br><span class="muted">{source} · {provider} · {stamp}</span></span><span class="tag {tag_class}">{sentiment}</span></div>')
 summary=news_bundle["summary"]
 status=f'Finnhub: {escape(news_bundle["finnhub_status"][:60])} · Alpha Vantage: {escape(news_bundle["alpha_status"][:60])}'
 st.markdown(
  f'<div class="panel right-news">'
  f'<div class="panel-title">▤ LIVE HEADLINES & SENTIMENT</div>'
  f'<div class="muted" style="margin-bottom:7px">'
  f'Updated {news_bundle["updated_at"]:%I:%M:%S %p} CT · {status}'
  f'</div>'
  f'<div class="news-scroll-shell">{"".join(rows)}</div>'
  f'</div>',
  unsafe_allow_html=True,
 )

def cal():
 # Browser timezone is detected once outside the card row so it cannot
 # create extra vertical space inside the Economic Calendar column.
 browser_timezone=st.session_state.get("calendar_browser_timezone_value","America/Chicago")
 if not isinstance(browser_timezone,str) or "/" not in browser_timezone:
  browser_timezone="America/Chicago"

 try:
  render_tz=ZoneInfo(browser_timezone)
 except Exception:
  render_tz=ZoneInfo("America/Chicago")

 rows_data=[]
 if calendar_live:
  for item in calendar_live:
   dt=pd.to_datetime(item.get("Date"),errors="coerce",utc=True)

   if pd.notna(dt):
    local_dt=dt.tz_convert(render_tz)
    date_key=local_dt.strftime("%Y-%m-%d")
    day_label=local_dt.strftime("%A, %B %d, %Y")
    time_label=local_dt.strftime("%I:%M %p")
    sort_dt=local_dt.isoformat()
   else:
    date_key="unknown"
    day_label="Date unavailable"
    time_label="--"
    sort_dt=""

   importance=int(item.get("Importance") or 1)
   impact="High" if importance>=3 else "Medium" if importance==2 else "Low"

   if impact not in ("High","Medium"):
    continue

   rows_data.append({
    "date_key":date_key,
    "day":day_label,
    "time":time_label,
    "sort_dt":sort_dt,
    "event":item.get("Event") or item.get("Category") or "Event",
    "impact":impact,
    "actual":item.get("Actual") or "-",
    "forecast":item.get("Forecast") or item.get("Consensus") or "-",
    "previous":item.get("Previous") or "-",
   })

 rows_data=sorted(rows_data,key=lambda row:(row["date_key"],row["sort_dt"]))

 if not rows_data:
  st.markdown(
   '<div class="panel bottom-card dashboard-bottom-card economic-card">'
   '<div class="panel-title">▣ ECONOMIC CALENDAR</div>'
   '<div class="muted" style="padding-top:12px">'
   'No medium- or high-impact events are currently available.'
   '</div></div>',
   unsafe_allow_html=True,
  )
  return

 today_key=pd.Timestamp.now(tz=render_tz).strftime("%Y-%m-%d")

 grouped={}
 for row in rows_data:
  if row["date_key"]>=today_key:
   grouped.setdefault((row["date_key"],row["day"]),[]).append(row)

 date_groups=list(grouped.items())

 if not date_groups:
  st.markdown(
   '<div class="panel bottom-card dashboard-bottom-card economic-card">'
   '<div class="panel-title">▣ ECONOMIC CALENDAR</div>'
   '<div class="muted" style="padding-top:12px">'
   'No current or upcoming medium- or high-impact events are available.'
   '</div></div>',
   unsafe_allow_html=True,
  )
  return

 total_pages=len(date_groups)

 if "calendar_page" not in st.session_state:
  st.session_state.calendar_page=1

 st.session_state.calendar_page=max(
  1,
  min(int(st.session_state.calendar_page),total_pages),
 )

 current_index=st.session_state.calendar_page-1
 (date_key,day_label),day_rows=date_groups[current_index]

 now_local=pd.Timestamp.now(tz=render_tz)
 tomorrow_key=(now_local+pd.Timedelta(days=1)).strftime("%Y-%m-%d")

 if date_key==today_key:
  date_title=f"TODAY · {day_label}"
 elif date_key==tomorrow_key:
  date_title=f"TOMORROW · {day_label}"
 else:
  date_title=day_label

 high_count=sum(1 for row in day_rows if row["impact"]=="High")
 medium_count=sum(1 for row in day_rows if row["impact"]=="Medium")

 event_rows=[]
 for row in day_rows:
  tag_class="tag-red" if row["impact"]=="High" else "tag-amber"
  event_rows.append(
   f'<div class="calendar-row">'
   f'<div>{escape(str(row["time"]))}</div>'
   f'<div title="{escape(str(row["event"]))}">{escape(str(row["event"]))}</div>'
   f'<div><span class="tag {tag_class}">{escape(row["impact"])}</span></div>'
   f'<div>{escape(str(row["actual"]))}</div>'
   f'<div>{escape(str(row["forecast"]))}</div>'
   f'<div>{escape(str(row["previous"]))}</div>'
   f'</div>'
  )

 st.markdown(
  f'<div class="panel bottom-card dashboard-bottom-card economic-card">'
  f'<div class="panel-title">▣ ECONOMIC CALENDAR</div>'
  f'<div class="calendar-date-bar">'
  f'📅 {escape(date_title)} &nbsp; '
  f'<span class="tag tag-red">High {high_count}</span> &nbsp; '
  f'<span class="tag tag-amber">Medium {medium_count}</span>'
  f'</div>'
  f'<div class="calendar-row muted calendar-columns">'
  f'<div>TIME</div><div>EVENT</div><div>IMPACT</div>'
  f'<div>ACTUAL</div><div>FORECAST</div><div>PREVIOUS</div>'
  f'</div>'
  f'<div class="calendar-scroll-shell">'
  f'<div class="calendar-body">{"".join(event_rows)}</div>'
  f'</div>'
  f'</div>',
  unsafe_allow_html=True,
 )

 # Navigation sits visually inside the calendar footer.
 st.markdown('<div class="calendar-nav-row"></div>',unsafe_allow_html=True)
 left,spacer,right=st.columns([1.15,6,1.15])
 with left:
  if st.button(
   "‹ Back",
   key="calendar_back",
   disabled=st.session_state.calendar_page<=1,
   use_container_width=True,
  ):
   st.session_state.calendar_page-=1
   st.rerun()

 with right:
  if st.button(
   "Next ›",
   key="calendar_next",
   disabled=st.session_state.calendar_page>=total_pages,
   use_container_width=True,
  ):
   st.session_state.calendar_page+=1
   st.rerun()


def _setup_inputs():
 close=float(df.close.iloc[-1]);ema20=float(df.ema20.iloc[-1]);ema50=float(df.ema50.iloc[-1]);vwap=float(df.vwap.iloc[-1])
 atr=max(float((df.high-df.low).tail(20).mean()),0.25);momentum=float(df.close.pct_change(8).iloc[-1])
 counts=news_bundle["summary"]["counts"];bull=int(counts.get("Bullish",0));bear=int(counts.get("Bearish",0))
 event_risk=False;now_utc=pd.Timestamp.now(tz="UTC")
 for event in calendar_live:
  impact=int(event.get("Importance") or event.get("importance") or 0)
  dt=pd.to_datetime(event.get("Date"),errors="coerce",utc=True)
  if impact>=3 and pd.notna(dt) and now_utc<=dt<=now_utc+pd.Timedelta(minutes=45): event_risk=True;break
 up=close>ema20>ema50;down=close<ema20<ema50;above=close>=vwap
 bp=(2 if up else 0)+(1 if above else 0)+(1 if momentum>0 else 0)+(1 if bull>bear else 0)+(1 if ai_result.score>=55 else 0)
 sp=(2 if down else 0)+(1 if not above else 0)+(1 if momentum<0 else 0)+(1 if bear>bull else 0)+(1 if ai_result.score<=45 else 0)
 if bp>sp: bias,direction,cl="BULLISH",1,"positive"
 elif sp>bp: bias,direction,cl="BEARISH",-1,"negative"
 else: bias,direction,cl="NEUTRAL",0,"warning"
 return dict(close=close,ema20=ema20,ema50=ema50,vwap=vwap,atr=atr,momentum=momentum,bull=bull,bear=bear,event_risk=event_risk,up=up,down=down,above=above,bias=bias,direction=direction,cl=cl)

def ai_trade_setup():
 x=_setup_inputs();symbol=st.session_state.get("chart_symbol","MES")
 scales={"MES":1.0,"MNQ":3.55,"MGC":0.43,"MCL":0.014,"VIX":0.0027,"DXY":0.0187};ticks={"MES":0.25,"MNQ":0.25,"MGC":0.10,"MCL":0.01,"VIX":0.01,"DXY":0.01}
 scale=scales.get(symbol,1.0);tick=ticks.get(symbol,0.25);entry=x["close"]*scale;atr=x["atr"]*scale
 if x["direction"]>0: stop=entry-1.35*atr;t1=entry+2.0*atr;t2=entry+3.2*atr
 elif x["direction"]<0: stop=entry+1.35*atr;t1=entry-2.0*atr;t2=entry-3.2*atr
 else: stop=entry-atr;t1=entry+atr;t2=entry+1.8*atr
 rt=lambda v: round(round(v/tick)*tick,2)
 entry,stop,t1,t2=map(rt,[entry,stop,t1,t2]);rr=abs(t1-entry)/max(abs(entry-stop),tick)
 reasons=[("good" if x["up"] else "bad" if x["down"] else "warn","EMA trend bullish" if x["up"] else "EMA trend bearish" if x["down"] else "EMA trend mixed"),
 ("good" if x["above"] else "bad","Price above VWAP" if x["above"] else "Price below VWAP"),
 ("good" if x["momentum"]>0 else "bad" if x["momentum"]<0 else "warn","Positive momentum" if x["momentum"]>0 else "Negative momentum" if x["momentum"]<0 else "Flat momentum"),
 ("good" if x["bull"]>x["bear"] else "bad" if x["bear"]>x["bull"] else "warn",f'News {news_bundle["summary"]["label"]}'),
 ("bad" if x["event_risk"] else "good","High-impact event within 45m" if x["event_risk"] else "No high-impact event within 45m"),
 ("good" if ai_result.confidence>=70 else "warn",f"AI confidence {ai_result.confidence}%")]
 reason_html="".join(f'<span class="ai-reason-{k}">{"✓" if k=="good" else "!" if k=="warn" else "×"} {escape(v)}</span>' for k,v in reasons)
 status="WAIT" if x["event_risk"] or x["bias"]=="NEUTRAL" else "ACTIVE";status_cl="warning" if status=="WAIT" else "positive"
 st.markdown(f'<div class="panel ai-setup-card"><div class="ai-setup-title"><span>◎ AI TRADE SETUP GENERATOR · {symbol}</span><span class="{status_cl}">{status}</span></div><div class="ai-setup-grid">'
 f'<div class="ai-setup-cell"><div class="ai-setup-label">BIAS</div><div class="ai-setup-value {x["cl"]}">{x["bias"]}</div></div>'
 f'<div class="ai-setup-cell"><div class="ai-setup-label">ENTRY</div><div class="ai-setup-value">{entry:,.2f}</div></div>'
 f'<div class="ai-setup-cell"><div class="ai-setup-label">STOP LOSS</div><div class="ai-setup-value negative">{stop:,.2f}</div></div>'
 f'<div class="ai-setup-cell"><div class="ai-setup-label">TARGET 1</div><div class="ai-setup-value positive">{t1:,.2f}</div></div>'
 f'<div class="ai-setup-cell"><div class="ai-setup-label">TARGET 2</div><div class="ai-setup-value positive">{t2:,.2f}</div></div>'
 f'<div class="ai-setup-cell"><div class="ai-setup-label">RISK / REWARD</div><div class="ai-setup-value">{rr:.2f}:1</div></div></div>'
 f'<div class="ai-reasons">{reason_html}</div><div class="ai-setup-note">Uses EMA 20/50, VWAP, momentum, news sentiment, AI score and economic-event risk. Decision support only; order execution remains disabled.</div></div>',unsafe_allow_html=True)

def ai_trade_setup_controls():
 c1,c2,c3=st.columns([1,1,3])
 with c1:
  selected=st.selectbox("Setup contract",["MES","MNQ","MGC","MCL"],key="setup_contract_picker")
  st.session_state["setup_symbol"]=selected
 with c2:
  if st.button("Refresh setup",use_container_width=True,key="refresh_ai_setup"):
   data.clear();load_calendar.clear();load_finnhub_news.clear();load_alpha_news.clear();st.rerun()
 with c3: st.caption("Setup updates from the latest cached market, news and calendar inputs.")
 ai_trade_setup()


def _setup_payload():
 x=_setup_inputs();symbol=st.session_state.get("chart_symbol","MES")
 scales={"MES":1.0,"MNQ":3.55,"MGC":0.43,"MCL":0.014,"VIX":0.0027,"DXY":0.0187}
 ticks={"MES":0.25,"MNQ":0.25,"MGC":0.10,"MCL":0.01,"VIX":0.01,"DXY":0.01}
 scale=scales.get(symbol,1.0);tick=ticks.get(symbol,0.25)
 entry=x["close"]*scale;atr=x["atr"]*scale
 if x["direction"]>0:
  stop=entry-1.0*atr;t1=entry+2.0*atr;t2=entry+4.0*atr
 elif x["direction"]<0:
  stop=entry+1.0*atr;t1=entry-2.0*atr;t2=entry-4.0*atr
 else:
  stop=entry-1.0*atr;t1=entry+1.0*atr;t2=entry+2.0*atr
 rt=lambda v: round(round(v/tick)*tick,2)
 entry,stop,t1,t2=map(rt,[entry,stop,t1,t2])
 risk_points=abs(entry-stop);t1_points=abs(t1-entry);t2_points=abs(t2-entry)
 rr=t1_points/max(risk_points,tick)
 reasons=[
  ("Above VWAP" if x["above"] else "Below VWAP"),
  ("DXY Weak" if x["direction"]>=0 else "DXY Strong"),
  ("VIX Declining" if x["direction"]>=0 else "VIX Rising"),
  ("Positive News" if x["bull"]>=x["bear"] else "Negative News"),
  ("Momentum Up" if x["momentum"]>=0 else "Momentum Down"),
  ("No Red News" if not x["event_risk"] else "Event Risk"),
 ]
 return dict(x=x,symbol=symbol,entry=entry,stop=stop,t1=t1,t2=t2,
             risk_points=risk_points,t1_points=t1_points,t2_points=t2_points,
             rr=rr,reasons=reasons)

def ai_trade_setup_compact():
 p=_setup_payload();x=p["x"]
 why="".join(f'<span class="ai-why-item"><span class="ai-check">✓</span>{escape(item)}</span>' for item in p["reasons"])
 return (
  f'<div class="panel ai-pro-card"><div class="ai-pro-title">◎ AI Trade Setup Generator · {p["symbol"]}</div>'
  f'<div class="ai-pro-grid">'
  f'<div class="ai-pro-metric"><div class="ai-pro-label">Bias</div><div class="ai-pro-value ai-pro-bias">{x["bias"]}</div></div>'
  f'<div class="ai-pro-metric"><div class="ai-pro-label">Entry ↗</div><div class="ai-pro-value">{p["entry"]:,.2f}</div></div>'
  f'<div class="ai-pro-metric"><div class="ai-pro-label">Stop Loss</div><div class="ai-pro-value ai-pro-stop">{p["stop"]:,.2f}</div><div class="ai-pro-sub">{p["risk_points"]:,.2f} pts</div></div>'
  f'<div class="ai-pro-metric"><div class="ai-pro-label">Target 1 ↗</div><div class="ai-pro-value">{p["t1"]:,.2f}</div><div class="ai-pro-sub">{p["t1_points"]:,.2f} pts</div></div>'
  f'<div class="ai-pro-metric"><div class="ai-pro-label">Target 2 ↗</div><div class="ai-pro-value">{p["t2"]:,.2f}</div><div class="ai-pro-sub">{p["t2_points"]:,.2f} pts</div></div>'
  f'<div class="ai-pro-metric"><div class="ai-pro-label">R:R</div><div class="ai-pro-value">1:{p["rr"]:.1f}</div></div>'
  f'</div><div class="ai-why-head">Why This Setup?</div><div class="ai-why-row">{why}</div>'
  f'</div>'
 )




def journal_analytics_compact():
 trades=[
  ("MES","Long",237.50),("MNQ","Long",312.50),("MES","Short",-125.00),
  ("MES","Long",187.50),("MNQ","Long",285.00)
 ]
 wins=[p for _,_,p in trades if p>0];losses=[p for _,_,p in trades if p<0]
 win_rate=(len(wins)/len(trades)*100) if trades else 0
 recent="".join(
  f'<span class="recent-trade">{s} {side}<b class="{"positive" if pnl>=0 else "negative"}">{format_currency_signed(float(pnl))}</b></span>'
  for s,side,pnl in trades
 )
 return (
  f'<div class="panel journal-analytics-card"><div class="journal-pro-title">◔ Journal Analytics</div>'
  f'<div class="journal-stats">'
  f'<div class="journal-stat"><div class="journal-stat-label">Win Rate</div><div class="journal-stat-value">{win_rate:.1f}%</div></div>'
  f'<div class="journal-stat"><div class="journal-stat-label">Total Trades</div><div class="journal-stat-value">56</div></div>'
  f'<div class="journal-stat"><div class="journal-stat-label">Best Setup</div><div class="journal-stat-value">VWAP Bounce</div><div class="journal-stat-sub">72% Win Rate</div></div>'
  f'<div class="journal-stat"><div class="journal-stat-label">Best Day</div><div class="journal-stat-value">Tuesday</div><div class="journal-stat-sub">$1,247.50</div></div>'
  f'<div class="journal-stat"><div class="journal-stat-label">Best Session</div><div class="journal-stat-value">9:30 AM - 11:30 AM</div><div class="journal-stat-sub">$1,892.30</div></div>'
  f'</div><div class="recent-title">Recent Trades</div><div class="recent-trades-row">{recent}</div>'
  f'<div class="journal-link">View Full Trade Journal &nbsp;›</div></div>'
 )

def redesigned_ai_journal_row():
 st.markdown('<div class="ai-bottom-anchor"></div>',unsafe_allow_html=True)
 left,right=st.columns([1,1.03],gap="small",vertical_alignment="top")
 with left:
  st.markdown(ai_trade_setup_compact(),unsafe_allow_html=True)
 with right:
  st.markdown(journal_analytics_compact(),unsafe_allow_html=True)

def risk():
 balance=25000.0; daily_pnl=1250.0; account_name="Demo fallback"
 if tradovate_snapshot and not tradovate_snapshot.get("error"):
  b=tradovate_snapshot.get("balance",{})
  balance=float(b.get("amount") or b.get("cashBalance") or b.get("totalCashValue") or balance)
  daily_pnl=float(b.get("realizedPnL") or 0)+float(b.get("openPnL") or 0)
  account_name=tradovate_snapshot.get("account",{}).get("name","Tradovate")
 st.markdown(f'<div class="panel bottom-card dashboard-bottom-card"><div class="panel-title">♙ RISK MANAGER · {account_name}</div><div class="muted">Account Balance</div>${balance:,.2f}<br><div class="muted">Daily P&L</div><span class="{"positive" if daily_pnl>=0 else "negative"}">${daily_pnl:,.2f}</span><br><div class="muted">Daily Loss Limit</div>$2,000.00<hr><div class="panel-title">POSITION SIZE</div><div class="muted">Risk per Trade</div>$500<br><div class="muted">Stop Loss</div>20 points<br><div class="muted">MES Contracts</div>5<br><div class="muted">Order execution</div><span class="warning">Disabled</span></div>',unsafe_allow_html=True)
def perf():
 vals=[98000,99000,98500,99700,100300,99500,101000,101700,101200,102100,102400,102900,102700,103400,104100,104000,104900,105600,106200,107245]
 w,h=520,128;padx,pady=8,10
 lo,hi=min(vals),max(vals)
 pts=[]
 for i,v in enumerate(vals):
  x=padx+i*(w-2*padx)/(len(vals)-1)
  y=pady+(hi-v)*(h-2*pady)/(hi-lo)
  pts.append(f"{x:.1f},{y:.1f}")
 poly=" ".join(pts)
 area=f"{padx},{h-pady} "+poly+f" {w-padx},{h-pady}"
 last_x,last_y=pts[-1].split(',')
 svg=f"""<svg viewBox="0 0 {w} {h}" width="100%" height="100%" preserveAspectRatio="none">
 <defs><linearGradient id="perfFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#36d66b" stop-opacity="0.26"/><stop offset="100%" stop-color="#36d66b" stop-opacity="0.01"/></linearGradient></defs>
 <line x1="8" y1="32" x2="512" y2="32" stroke="#1b2a3c" stroke-width="1"/>
 <line x1="8" y1="64" x2="512" y2="64" stroke="#1b2a3c" stroke-width="1"/>
 <line x1="8" y1="96" x2="512" y2="96" stroke="#1b2a3c" stroke-width="1"/>
 <polygon points="{area}" fill="url(#perfFill)"/>
 <polyline points="{poly}" fill="none" stroke="#36d66b" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round"/>
 <circle cx="{last_x}" cy="{last_y}" r="3.5" fill="#36d66b"/>
 </svg>"""
 html=f"""<div class="panel performance-card dashboard-bottom-card">
 <div class="panel-title">▥ PERFORMANCE OVERVIEW</div>
 <div class="performance-kpis">
  <div class="performance-kpi"><span class="muted">Total Trades</span><span class="performance-value">28</span></div>
  <div class="performance-kpi"><span class="muted">Win Rate</span><span class="performance-value positive">64.29%</span></div>
  <div class="performance-kpi"><span class="muted">Profit Factor</span><span class="performance-value positive">2.18</span></div>
  <div class="performance-kpi"><span class="muted">Total P&amp;L</span><span class="performance-value positive">$3,245</span></div>
  <div class="performance-kpi"><span class="muted">Avg Win</span><span class="performance-value positive">$225.50</span></div>
  <div class="performance-kpi"><span class="muted">Avg Loss</span><span class="performance-value negative">-$104.30</span></div>
 </div>
 <div class="performance-chart">{svg}</div>
 <div class="performance-footer"><span class="muted">Max Drawdown <b class="negative">-$1,120</b></span><span>Monthly P&amp;L <b class="positive">+$3,245</b></span></div>
 </div>"""
 st.markdown(html,unsafe_allow_html=True)
def journal():
 rows=''.join([f'<div class="journal-row"><span>{d} · {s} · {setup}</span><span class="{cl}">{p}</span></div>' for d,s,setup,p,cl in [('May 20','MES','Breakout','$250','positive'),('May 19','MNQ','Pullback','$180','positive'),('May 19','MES','Breakout','-$120','negative'),('May 16','MGC','Reversal','$360','positive')]]);st.markdown(f'<div class="panel bottom-card dashboard-bottom-card"><div class="panel-title">▤ TRADE JOURNAL</div>{rows}</div>',unsafe_allow_html=True)
if page=='Dashboard':
 cards=''.join(ticker_html(m) for m in markets)
 score_card=f'<div class="panel market-score-card"><div class="panel-title">AI MARKET SCORE</div><div class="score warning">{ai_result.score}</div><div class="score-sub">/100</div><div class="score-label positive">{ai_result.label.upper()}</div><div class="score-sub muted">Confidence: {ai_result.confidence}%</div></div>'
 st.markdown(f'<div class="top-market-grid">{cards}{score_card}</div>',unsafe_allow_html=True)
 left,right=st.columns([2.35,1.15])
 with left: chart()
 with right: brief()
 if streamlit_js_eval is not None:
  try:
   detected_tz=streamlit_js_eval(
    js_expressions="Intl.DateTimeFormat().resolvedOptions().timeZone",
    key="dashboard_calendar_browser_timezone",
    want_output=True,
   )
   if isinstance(detected_tz,str) and "/" in detected_tz:
    st.session_state.calendar_browser_timezone_value=detected_tz
  except Exception:
   pass
 st.markdown('<div class="bottom-row-anchor"></div>',unsafe_allow_html=True)
 a,b,c,d=st.columns([1.3,1.3,.95,1.35],vertical_alignment="top")
 with a: cal()
 with b: news()
 with c: risk()
 with d: perf()
 redesigned_ai_journal_row()
 st.markdown('<div class="alertbar"><div class="alert alert-red">Core CPI in 43m</div><div class="alert alert-amber">MES near Resistance</div><div class="alert alert-green">Oil Breakout</div><div class="alert alert-red">VIX Spike Alert</div></div>',unsafe_allow_html=True)

elif page=='AI Analysis':
 st.markdown('## AI Analysis')
 analysis_left,analysis_right=st.columns([1.25,1])
 with analysis_left:
  brief()
 with analysis_right:
  st.markdown(
   f'<div class="panel market-score-card">'
   f'<div class="panel-title">AI MARKET SCORE</div>'
   f'<div class="score warning">{ai_result.score}</div>'
   f'<div class="score-sub">/100</div>'
   f'<div class="score-label positive">{ai_result.label.upper()}</div>'
   f'<div class="score-sub muted">Confidence: {ai_result.confidence}%</div>'
   f'</div>',
   unsafe_allow_html=True,
  )

elif page=='Risk Manager':
 st.markdown('## Risk Manager')
 risk()

elif page=='Chart':
 cards=''.join(ticker_html(m) for m in markets)
 score_card=f'<div class="panel market-score-card"><div class="panel-title">AI MARKET SCORE</div><div class="score warning">{ai_result.score}</div><div class="score-sub">/100</div><div class="score-label positive">{ai_result.label.upper()}</div><div class="score-sub muted">Confidence: {ai_result.confidence}%</div></div>'
 st.markdown(f'<div class="top-market-grid">{cards}{score_card}</div>',unsafe_allow_html=True)
 chart()

elif page=='Economic Calendar':
 if streamlit_js_eval is not None:
  try:
   detected_tz=streamlit_js_eval(
    js_expressions="Intl.DateTimeFormat().resolvedOptions().timeZone",
    key="standalone_calendar_browser_timezone",
    want_output=True,
   )
   if isinstance(detected_tz,str) and "/" in detected_tz:
    st.session_state.calendar_browser_timezone_value=detected_tz
  except Exception:
   pass
 cal()

elif page=='News & Sentiment':
 news()

elif page=='AI Trade Setup':
 st.markdown('<div class="ai-bottom-anchor"></div>',unsafe_allow_html=True)
 st.markdown(ai_trade_setup_compact(),unsafe_allow_html=True)

elif page=='Trade Journal':
 journal()

elif page=='Performance':
 perf()

elif page=='Settings':
 st.subheader('⚙️ Settings')
 st.caption('Dashboard preferences and connection status')
 left,right=st.columns(2)
 with left:
  st.markdown('#### Display')
  st.toggle('Compact dashboard layout',value=True,key='settings_compact_layout')
  st.toggle('Show market alerts',value=True,key='settings_market_alerts')
  st.selectbox('Default chart ticker',['MES','MNQ','MGC','MCL','VIX','DXY'],key='settings_default_ticker')
 with right:
  st.markdown('#### Data refresh')
  st.selectbox('Headline refresh interval',[30,60,120,300],index=1,format_func=lambda x:f'{x} seconds',key='settings_headline_refresh')
  if st.button('Refresh dashboard data',use_container_width=True,key='settings_refresh_all'):
   data.clear()
   load_calendar.clear()
   load_finnhub_news.clear()
   load_alpha_news.clear()
   st.rerun()
 st.divider()
 st.markdown('#### Connection status')
 c1,c2,c3=st.columns(3)
 c1.metric('Tradovate','Connected' if tradovate_snapshot and not tradovate_snapshot.get('error') else 'Not configured')
 c2.metric('Finnhub',news_bundle['finnhub_status'])
 c3.metric('Alpha Vantage',news_bundle['alpha_status'])

# Lightweight automatic headline refresh. Only the timer fragment reruns; API caches
# enforce 60-second Finnhub and 5-minute Alpha Vantage request intervals.
@st.fragment(run_every=f"{news_refresh_seconds}s")
def headline_refresh_timer():
 st.caption(f"Live headline refresh: every {news_refresh_seconds} seconds · {datetime.now(CT):%I:%M:%S %p} CT")
headline_refresh_timer()
