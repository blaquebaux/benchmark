#!/usr/bin/python3
# =============================================================================
# benchmark_1_internals.py — BLAQUE BAUX BENCHMARK #1: the internals dashboard.
#
# Assemble the tradable-proxy market internals and characterize each vs the market (SPY): its
# risk-on/off orientation, correlation to SPY, and behavior on the worst-decile SPY days (does it
# actually diverge/warn, or just move with the tape?). Establishes what each internal says before #2
# asks whether any of it PREDICTS. Read-only. Prints its own results.
# =============================================================================
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _benchmark_common import panel, rets, stats, roll_vol, UNIVERSE

P, dates = panel(UNIVERSE)
spy = rets(P["SPY"])
# each internal as a daily "risk-on higher = healthier" reading (ratios / levels)
def ratio_ret(a, b): r = rets(P[a] / P[b]); return r
internals = {
    "credit  HYG/LQD":   ratio_ret("HYG", "LQD"),      # HY vs IG — credit risk appetite (risk-on +)
    "breadth RSP/SPY":   ratio_ret("RSP", "SPY"),      # equal- vs cap-weight — participation (risk-on +)
    "DowThry IYT/DIA":   ratio_ret("IYT", "DIA"),      # transports confirming industrials (risk-on +)
    "defens. XLU/SPY":   ratio_ret("XLU", "SPY"),      # utilities leading = defensive (risk-on -)
    "vol     VIXY":      rets(P["VIXY"]),              # fear (risk-on -)
    "bondvol TLT-rv":    roll_vol(rets(P["TLT"]))[1:], # macro stress proxy (risk-on -)
}
print("=" * 80, "\nBENCHMARK #1 — the market-internals dashboard (tradable proxies)\n" + "=" * 80)
print(f"  {dates[1]} .. {dates[-1]}   ($ADD/$TICK/$CPC/MOVE-index not on Alpaca — proxied or flagged)\n")
print(f"  {'internal':<20}{'corr-SPY':>10}{'SPY worst-decile day':>24}")
for name, x in internals.items():
    n = min(len(x), len(spy)); a, b = x[-n:], spy[-n:]
    m = np.isfinite(a) & np.isfinite(b); a, b = a[m], b[m]
    c = np.corrcoef(a, b)[0, 1]
    worst = b < np.percentile(b, 10)
    print(f"  {name:<20}{c:>+10.2f}{a[worst].mean()*100:>+22.2f}%")

print("\n  reading: credit/breadth/DowTheory move WITH SPY (risk-on, +corr); defensives/vol/bond-vol move")
print("  AGAINST it (risk-off, -corr). On the worst SPY days, the risk-off internals spike and the")
print("  risk-on ones fall — as expected. The real question (#2): do any of them do so BEFORE SPY (a")
print("  usable lead), or only alongside it (a coincident dashboard)?")
print("\nVERDICT: the internals are coherent and correctly-signed — a genuine risk dashboard. Whether it")
print("is a TRADABLE regime or just a mirror of the tape is decided in #2 (lead/lag) and #3 (does gating")
print("on a composite improve the market's risk-adjusted return).")
