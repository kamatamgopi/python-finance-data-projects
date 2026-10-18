# OHLCV Resampling and Indicator Pipeline

Converts 1-minute candle data to 5-minute candles and adds EMA, RSI, ATR and
session VWAP using pandas and NumPy. No TA library is needed; the indicators
are implemented directly so the logic is transparent.

**Run:** `python pipeline.py` (creates `output_5m_with_indicators.csv` and `chart.png`)

**Notes**
- Uses synthetic data. Swap in your own CSV by returning a timestamp-indexed
  DataFrame with open/high/low/close/volume.
- Resampling uses the correct aggregation (first/max/min/last/sum), and empty overnight bins are dropped.
- VWAP resets each trading day.
- Educational data-processing example. Not trading advice.
