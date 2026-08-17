#!/usr/bin/python3
# =============================================================================
# benchmark_2_predict_or_coincide.py — BLAQUE BAUX BENCHMARK #2: do internals LEAD, or COINCIDE?
#
# The decisive question for whether this is a tradable regime or a dashboard. For each internal (as a
# 21-day trend), test forward SPY returns conditional on the internal being risk-on vs risk-off, and
# the lead/lag cross-correlation (does the internal move BEFORE SPY, k>0, or WITH/AFTER it, k<=0?).
# Market internals are famously coincident; an honest lead/lag says which — if any — earn a lead.
# Read-only. Prints its own results.
# =============================================================================
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _benchmark_common import panel, rets, roll_vol, UNIVERSE

P, dates = panel(UNIVERSE); spy = rets(P["SPY"]); T = len(spy)
def lvl(a, b): return (P[a] / P[b])[1:]                          # ratio level aligned to returns
# risk-on trend signals (21d change of the level; sign = risk-on orientation)
def trend(x, w=21): x = np.asarray(x, float); t = np.full(len(x), np.nan); t[w:] = x[w:]/x[:-w]-1; return t
sig = {
    "credit  HYG/LQD": trend(lvl("HYG", "LQD")),
    "breadth RSP/SPY": trend(lvl("RSP", "SPY")),
    "DowThry IYT/DIA": trend(lvl("IYT", "DIA")),
    "defens. SPY/XLU": trend(lvl("SPY", "XLU")),                 # risk-on when SPY beats utilities
    "vol     -VIXY":   -trend(P["VIXY"][1:]),                    # risk-on when vol falling
    "bondvol -TLTrv":  -roll_vol(rets(P["TLT"]))[1:],            # risk-on when bond vol low
}
print("=" * 84, "\nBENCHMARK #2 — do the internals LEAD SPY (predict) or COINCIDE (a dashboard)?\n" + "=" * 84)
print(f"  fwd 20d SPY conditional on the internal (risk-on vs risk-off), and peak lead/lag k (days):\n")
print(f"  {'internal':<18}{'fwd20 risk-ON':>15}{'fwd20 risk-OFF':>16}{'spread':>9}{'peak-corr k':>13}")
fwd = np.full(T, np.nan)
for i in range(T-20): fwd[i] = np.prod(1 + spy[i+1:i+21]) - 1
for name, s in sig.items():
    n = min(len(s), T); a = s[-n:]; f = fwd[-n:]; sp = spy[-n:]
    m = np.isfinite(a) & np.isfinite(f); med = np.nanmedian(a[m])
    on = m & (a > med); off = m & (a <= med)
    spread = f[on].mean() - f[off].mean()
    # lead/lag: corr(signal_t, SPY_{t+k}); k>0 => signal leads
    ks = {}
    for k in (-5, -1, 0, 1, 5):
        if k >= 0: x, y = a[:len(a)-k], sp[k:]
        else: x, y = a[-k:], sp[:len(sp)+k]
        mm = np.isfinite(x) & np.isfinite(y); ks[k] = np.corrcoef(x[mm], y[mm])[0,1] if mm.sum()>30 else np.nan
    peak = max(ks, key=lambda k: abs(ks[k]))
    print(f"  {name:<18}{f[on].mean()*100:>+14.2f}%{f[off].mean()*100:>+15.2f}%{spread*100:>+8.2f}%{peak:>+9d} ({ks[peak]:+.2f})")

print("\nVERDICT: where the fwd-20d risk-on-minus-risk-off spread is small and the peak cross-corr sits at")
print("k<=0, the internal is COINCIDENT — it mirrors the tape, not a lead. Internals that show a positive")
print("fwd spread with peak k>0 carry a genuine (if modest) lead. Expect most to be coincident (breadth,")
print("Dow Theory, credit are classic mirrors); the composite in #3 is the real test of tradability.")
