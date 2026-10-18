"""
Black-Scholes pricing, Greeks and implied volatility (SciPy root-finding).
European options on a non-dividend (or continuous-yield q) underlying.
"""
import numpy as np
from scipy.stats import norm
from scipy.optimize import brentq


def _d1_d2(S, K, T, r, sigma, q=0.0):
    d1 = (np.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    return d1, d1 - sigma * np.sqrt(T)


def bs_price(S, K, T, r, sigma, kind="call", q=0.0):
    d1, d2 = _d1_d2(S, K, T, r, sigma, q)
    if kind == "call":
        return S * np.exp(-q * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    return K * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp(-q * T) * norm.cdf(-d1)


def greeks(S, K, T, r, sigma, kind="call", q=0.0):
    d1, d2 = _d1_d2(S, K, T, r, sigma, q)
    pdf = norm.pdf(d1)
    delta = np.exp(-q * T) * (norm.cdf(d1) if kind == "call" else norm.cdf(d1) - 1)
    gamma = np.exp(-q * T) * pdf / (S * sigma * np.sqrt(T))
    vega = S * np.exp(-q * T) * pdf * np.sqrt(T) / 100          # per 1 vol point
    if kind == "call":
        theta = (-S * np.exp(-q * T) * pdf * sigma / (2 * np.sqrt(T))
                 - r * K * np.exp(-r * T) * norm.cdf(d2)
                 + q * S * np.exp(-q * T) * norm.cdf(d1)) / 365   # per day
    else:
        theta = (-S * np.exp(-q * T) * pdf * sigma / (2 * np.sqrt(T))
                 + r * K * np.exp(-r * T) * norm.cdf(-d2)
                 - q * S * np.exp(-q * T) * norm.cdf(-d1)) / 365
    return {"delta": delta, "gamma": gamma, "vega": vega, "theta": theta}


def implied_vol(price, S, K, T, r, kind="call", q=0.0, lo=1e-4, hi=5.0):
    """Solve for sigma with Brent's method. Returns nan if no solution exists."""
    intrinsic = max(0.0, (S * np.exp(-q * T) - K * np.exp(-r * T)) * (1 if kind == "call" else -1))
    if price <= intrinsic or T <= 0:
        return np.nan
    f = lambda sig: bs_price(S, K, T, r, sig, kind, q) - price
    try:
        return brentq(f, lo, hi, xtol=1e-8)
    except ValueError:
        return np.nan


if __name__ == "__main__":
    S, r, T = 22000, 0.07, 7 / 365
    print("Option chain demo (synthetic, true vol = 14%)")
    print(f"{'Strike':>8} {'Price':>10} {'IV %':>8} {'Delta':>8} {'Gamma':>10} {'Vega':>8} {'Theta':>8}")
    for K in range(21800, 22201, 100):
        p = bs_price(S, K, T, r, 0.14, "call")
        iv = implied_vol(p, S, K, T, r, "call")
        g = greeks(S, K, T, r, iv, "call")
        print(f"{K:>8} {p:>10.2f} {iv*100:>8.2f} {g['delta']:>8.3f} "
              f"{g['gamma']:>10.5f} {g['vega']:>8.2f} {g['theta']:>8.2f}")

    # sanity check: price -> IV -> price round trip
    p = bs_price(100, 105, 0.5, 0.05, 0.25, "put")
    iv = implied_vol(p, 100, 105, 0.5, 0.05, "put")
    assert abs(iv - 0.25) < 1e-6, iv
    print("\nRound-trip check passed: recovered IV =", round(iv, 6))
