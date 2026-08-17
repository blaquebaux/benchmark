#!/usr/bin/python3
# =============================================================================
# benchmark_3_composite_regime.py — BLAQUE BAUX BENCHMARK #3: is the composite a tradable regime?
#
# Combine the internals into one causal risk-on/off score (mean of trailing-year z-scores of the six
# risk-on-oriented signals), lag it one day (no look-ahead), and test whether GATING the market on it
# improves risk-adjusted return: hold SPY when the composite is risk-on, de-risk when risk-off.
#   - If it beats buy-&-hold SPY on Sharpe/drawdown -> a genuine regime; benchmark PUBLISHES it
#     (market_regime.txt) for the family, like bonds/brics.
#   - If not -> the internals are a coincident DASHBOARD, not an edge (an honest diagnostic).
# Read-only. Prints its own results.
# =============================================================================
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _benchmark_common import panel, rets, roll_vol, roll_z, stats, UNIVERSE

COST = 0.0002    # ~2 bps per unit of exposure turnover (SPY is liquid) — regime flips are charged
P, dates = panel(UNIVERSE); spy = rets(P["SPY"]); T = len(spy)
def lvl(a, b): return (P[a] / P[b])[1:]
def trend(x, w=21): x = np.asarray(x, float); t = np.full(len(x), np.nan); t[w:] = x[w:]/x[:-w]-1; return t
nonvol = [trend(lvl("HYG", "LQD")), trend(lvl("RSP", "SPY")), trend(lvl("IYT", "DIA")), trend(lvl("SPY", "XLU"))]
volsig = [-trend(P["VIXY"][1:]), -roll_vol(rets(P["TLT"]))[1:]]
L = min(len(s) for s in nonvol + volsig + [spy]); spy = spy[-L:]

def composite(sigs):
    Z = np.vstack([roll_z(s[-L:], 252) for s in sigs])
    c = np.nanmean(Z, axis=0); return np.concatenate([[np.nan], c[:-1]])   # lag 1 -> causal

def gated(comp_lag, derisk):                                       # net of turnover cost
    start = np.where(np.isfinite(comp_lag))[0][0]
    e = np.where(comp_lag[start:] > 0, 1.0, derisk)               # exposure
    turn = np.abs(np.diff(np.concatenate([[e[0]], e])))
    return e * spy[start:] - turn * COST, comp_lag[start:] > 0, start

print("=" * 82, "\nBENCHMARK #3 — is the internals composite a tradable regime, or just vol-timing?\n" + "=" * 82)
comp_all = composite(nonvol + volsig); comp_nv = composite(nonvol)
r_all, on_all, st0 = gated(comp_all, 0.0)
r_nv, on_nv, _ = gated(comp_nv, 0.0)
print(f"  scored {dates[-L:][st0]} .. {dates[-1]}   net {int(COST*1e4)}bps/flip   risk-on: all {100*on_all.mean():.0f}% / non-vol {100*on_nv.mean():.0f}%\n")
print(f"  {'book':<34}{'Sharpe':>8}{'CAGR':>8}{'vol':>7}{'maxDD':>8}")
bh = stats(spy[st0:])
print(f"  {'SPY buy & hold':<34}{bh['sh']:>+8.2f}{bh['cagr']*100:>+7.1f}%{bh['vol']*100:>6.1f}%{bh['dd']*100:>+7.0f}%")
for lbl, r in [("gated: FULL composite (to cash)", r_all), ("gated: NON-VOL only (breadth/credit/DT)", r_nv)]:
    st = stats(r); print(f"  {lbl:<34}{st['sh']:>+8.2f}{st['cagr']*100:>+7.1f}%{st['vol']*100:>6.1f}%{st['dd']*100:>+7.0f}%")

shA, shN = stats(r_all)['sh'], stats(r_nv)['sh']; ddA = stats(r_all)['dd']
print("\n  THE BAR (net of cost):")
for n, ok, v in [("full-composite Sharpe >= B&H + 0.05", shA >= bh['sh']+0.05, f"{shA:+.2f} vs {bh['sh']:+.2f}"),
                 ("reduces drawdown",                    ddA > bh['dd'],        f"{ddA*100:+.0f}% vs {bh['dd']*100:+.0f}%"),
                 ("non-vol internals add value (>= B&H)", shN >= bh['sh'],      f"{shN:+.2f} vs {bh['sh']:+.2f}")]:
    print(f"    [{'PASS' if ok else 'FAIL'}] {n:<38} {v}")

publishable = shA >= bh['sh'] + 0.05 and ddA > bh['dd']
voldriven = shN < bh['sh'] + 0.05
print("\n  VERDICT:", "PASS — the composite is a tradable RISK-OFF regime (net of cost); benchmark PUBLISHES it." if publishable else
      "does not beat buy & hold net of cost — a coincident dashboard.")
if publishable and voldriven:
    print("  HONEST CAVEAT: it works mainly by VOL-TIMING (riding the persistence of high-vol/risk-off")
    print("  clusters — #2 showed the internals COINCIDE, they don't forecast). Strip the vol signals and")
    print("  the non-vol internals (breadth/credit/Dow-Theory) barely beat buy&hold — so this is managed-vol")
    print("  wearing an internals label, overlapping broad's vol-target. Publish it as a RISK-OFF regime, not")
    print("  as breadth alpha — and size it knowing what actually drives it.")
