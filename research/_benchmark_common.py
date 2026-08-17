#!/usr/bin/python3
# =============================================================================
# _benchmark_common.py — shared helpers for the Blaque Baux Benchmark (market-internals) study.
# Alpaca SIP daily bars; reads ALPACA_KEY_ID / ALPACA_SECRET_KEY from env. Read-only.
#
# WHAT THIS SLEEVE IS: a market-INTERNALS / risk-regime read — the confirming-vs-diverging signals
# that gauge market health. The honest question is whether these internals PREDICT forward returns
# (a tradable/sizing regime) or merely COINCIDE (a dashboard). If they predict, benchmark becomes the
# family's third regime publisher (after bonds' stock-bond and brics' dollar); if not, it's a diagnostic.
#
# DATA HONESTY — several requested feeds are index/breadth tickers Alpaca does NOT serve; proxied where
# possible, flagged where not:
#   VIX (fear)              -> VIXY            (VIX-futures ETF)              [proxy]
#   HYG vs LQD (credit)     -> HYG / LQD        (high-yield vs inv-grade)     [direct]
#   SPY, RSP (breadth)      -> RSP / SPY        (equal- vs cap-weight)        [direct]
#   DJIA vs DJT (Dow Theory)-> DIA vs IYT       (industrials vs transports)   [proxy]
#   DJU (defensive)         -> XLU              (utilities)                   [proxy]
#   MOVE index (bond vol)   -> TLT realized vol (the MOVE index is not on Alpaca) [proxy]
#   $ADD / $TICK (breadth)  -> RSP/SPY          ($ADD & intraday $TICK not on daily bars) [gap]
#   $CPC (put/call)         -> (none)           (CBOE sentiment index not on Alpaca)     [gap]
# =============================================================================
import os, json, urllib.request, math
import numpy as np

H = {"APCA-API-KEY-ID": os.environ["ALPACA_KEY_ID"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]}
START, END = "2016-01-01", "2026-08-01"
_cache = {}
UNIVERSE = ["SPY", "RSP", "HYG", "LQD", "DIA", "IYT", "XLU", "VIXY", "TLT"]

def bars(s):
    if s in _cache: return _cache[s]
    u = (f"https://data.alpaca.markets/v2/stocks/bars?symbols={s}&timeframe=1Day"
         f"&start={START}&end={END}&adjustment=all&feed=sip&limit=10000")
    try:
        d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=40))
        _cache[s] = {b["t"][:10]: b for b in d.get("bars", {}).get(s, [])}
    except Exception:
        _cache[s] = {}
    return _cache[s]

def panel(syms):
    D = {s: bars(s) for s in syms}; D = {s: v for s, v in D.items() if len(v) > 250}
    u = list(D); dates = sorted(set.intersection(*[set(D[s]) for s in u]))
    M = np.array([[D[s][d]["c"] for s in u] for d in dates], float)
    return {s: M[:, i] for i, s in enumerate(u)}, dates          # {sym: price[T]}, dates[T]

def stats(r):
    r = np.asarray(r, float); r = r[np.isfinite(r)]
    if len(r) < 30 or r.std() == 0: return dict(sh=float('nan'), cagr=float('nan'), dd=float('nan'), vol=float('nan'))
    cum = np.cumprod(1 + r)
    return dict(sh=r.mean() / r.std() * math.sqrt(252), cagr=cum[-1] ** (252 / len(r)) - 1,
                dd=(cum / np.maximum.accumulate(cum) - 1).min(), vol=r.std() * math.sqrt(252))

def rets(px): return px[1:] / px[:-1] - 1
def roll_z(x, w=252):                                            # causal rolling z-score
    x = np.asarray(x, float); z = np.full(len(x), np.nan)
    for i in range(w, len(x)):
        h = x[i-w:i]; s = h.std()
        if s > 0: z[i] = (x[i] - h.mean()) / s
    return z
def roll_vol(r, w=20):
    r = np.asarray(r, float); v = np.full(len(r), np.nan)
    for i in range(w, len(r)): v[i] = r[i-w:i].std() * math.sqrt(252)
    return v
