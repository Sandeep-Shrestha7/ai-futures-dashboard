
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd

@dataclass(frozen=True)
class AIScore:
    score: int
    label: str
    confidence: int
    components: dict[str, float]

def calculate_ai_score(df: pd.DataFrame, news: list[dict], calendar: list[dict]) -> AIScore:
    close=df["close"].astype(float)
    ema20=close.ewm(span=20).mean()
    ema50=close.ewm(span=50).mean()
    trend=np.clip(50 + (ema20.iloc[-1]-ema50.iloc[-1]) / max(abs(close.iloc[-1])*.002,1)*20,0,100)
    momentum=np.clip(50 + close.pct_change(12).iloc[-1]*1500,0,100)
    returns=close.pct_change().dropna()
    volatility=np.clip(85-returns.tail(30).std()*10000,15,95)
    sentiment_values={"Bullish":1,"Neutral":0,"Bearish":-1}
    sent=np.mean([sentiment_values.get(n.get("sentiment","Neutral"),0) for n in news]) if news else 0
    sentiment=np.clip(50+sent*30,0,100)
    high_events=sum(1 for e in calendar if int(e.get("Importance") or e.get("importance") or 0)>=3)
    event_risk=np.clip(80-high_events*12,20,90)
    components={"trend":float(trend),"momentum":float(momentum),"volatility":float(volatility),"sentiment":float(sentiment),"event_risk":float(event_risk)}
    score=round(trend*.30+momentum*.22+volatility*.16+sentiment*.17+event_risk*.15)
    label="Strong Bullish" if score>=80 else "Bullish" if score>=65 else "Neutral" if score>=45 else "Bearish" if score>=25 else "High Risk"
    confidence=round(min(95,55+abs(score-50)*.8+min(len(news),8)*1.5))
    return AIScore(int(score),label,int(confidence),components)
