# Black-Scholes Pricing, Greeks and Implied Volatility

Prices European options, computes delta/gamma/vega/theta, and solves for
implied volatility with SciPy's Brent root-finder.

**Run:** `python options.py`

**Notes**
- Vega is per 1 volatility point; theta is per calendar day.
- `implied_vol` returns NaN for prices below intrinsic value or with no solution.
- Includes a price -> IV -> price round-trip check.
- Synthetic inputs. Educational example, not trading advice.
