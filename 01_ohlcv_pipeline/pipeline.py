"""
OHLCV pipeline: 1-minute candles -> 5-minute candles -> indicators.

Uses synthetic data so the project runs anywhere. To use real data,
replace make_synthetic_1m() with pd.read_csv(...) that returns a
DataFrame indexed by timestamp with open/high/low/close/volume columns.
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def make_synthetic_1m(days=5, seed=42, start_price=100.0):
    """Random-walk 1-minute candles for an Indian market session (09:15-15:29)."""
    rng = np.random.default_rng(seed)
    stamps = []
    for d in pd.bdate_range("2024-01-01", periods=days):
        stamps.extend(pd.date_range(d + pd.Timedelta(hours=9, minutes=15),
                                    d + pd.Timedelta(hours=15, minutes=29), freq="1min"))
    idx = pd.DatetimeIndex(stamps)
    n = len(idx)
    close = start_price * np.exp(np.cumsum(rng.normal(0, 0.0004, n)))
    open_ = np.r_[start_price, close[:-1]]
    high = np.maximum(open_, close) * (1 + np.abs(rng.normal(0, 0.0002, n)))
    low = np.minimum(open_, close) * (1 - np.abs(rng.normal(0, 0.0002, n)))
    volume = rng.integers(100, 1000, n)
    return pd.DataFrame({"open": open_, "high": high, "low": low,
                         "close": close, "volume": volume}, index=idx)


def resample_ohlcv(df, rule="5min"):
    """Aggregate candles correctly: first open, max high, min low, last close, sum volume."""
    out = df.resample(rule).agg({"open": "first", "high": "max", "low": "min",
                                 "close": "last", "volume": "sum"})
    return out.dropna(subset=["close"])  # drops overnight empty bins


def ema(s, span):
    return s.ewm(span=span, adjust=False).mean()


def rsi(close, n=14):
    """Wilder's RSI."""
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    rs = gain / loss
    return 100 - 100 / (1 + rs)


def atr(df, n=14):
    """Average True Range (Wilder smoothing)."""
    prev_close = df["close"].shift()
    tr = pd.concat([df["high"] - df["low"],
                    (df["high"] - prev_close).abs(),
                    (df["low"] - prev_close).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


def vwap(df):
    """Session VWAP, reset each trading day."""
    typical = (df["high"] + df["low"] + df["close"]) / 3
    pv = typical * df["volume"]
    day = df.index.date
    return pv.groupby(day).cumsum() / df["volume"].groupby(day).cumsum()


def add_indicators(df):
    df = df.copy()
    df["ema_9"] = ema(df["close"], 9)
    df["ema_21"] = ema(df["close"], 21)
    df["rsi_14"] = rsi(df["close"], 14)
    df["atr_14"] = atr(df, 14)
    df["vwap"] = vwap(df)
    df["ret"] = df["close"].pct_change()
    return df


if __name__ == "__main__":
    m1 = make_synthetic_1m()
    m5 = add_indicators(resample_ohlcv(m1, "5min"))
    print(f"1m rows: {len(m1)} -> 5m rows: {len(m5)}")
    print(m5.tail())
    m5.to_csv("output_5m_with_indicators.csv")

    last_day = m5[m5.index.date == m5.index.date[-1]]
    fig, ax = plt.subplots(2, 1, figsize=(10, 6), sharex=True,
                           gridspec_kw={"height_ratios": [3, 1]})
    ax[0].plot(last_day.index, last_day["close"], label="Close")
    ax[0].plot(last_day.index, last_day["ema_9"], label="EMA 9")
    ax[0].plot(last_day.index, last_day["ema_21"], label="EMA 21")
    ax[0].plot(last_day.index, last_day["vwap"], label="VWAP", linestyle="--")
    ax[0].legend(); ax[0].set_title("5-minute candles with indicators (synthetic data)")
    ax[1].plot(last_day.index, last_day["rsi_14"], color="purple"); ax[1].set_ylabel("RSI 14")
    ax[1].axhline(70, color="gray", lw=0.5); ax[1].axhline(30, color="gray", lw=0.5)
    plt.tight_layout(); plt.savefig("chart.png", dpi=120)
