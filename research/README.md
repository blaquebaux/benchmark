# Blaque Baux Benchmark — research

A **market-internals / risk-regime** study: the confirming-vs-diverging signals that gauge market
health — VIX, credit (HYG vs LQD), breadth (equal- vs cap-weight), Dow Theory (industrials vs
transports), defensives (utilities), bond vol — asked one honest question: do they **predict** forward
returns (a tradable regime) or merely **coincide** (a dashboard)? All sketches read Alpaca SIP daily
bars, are read-only, and print their own results. 2016–2026.

> **Data honesty.** Several requested feeds are index/breadth tickers Alpaca does not serve; proxied
> where possible, flagged where not: VIX→**VIXY**, HYG/LQD→**direct**, breadth ($ADD/$TICK)→**RSP/SPY**
> (equal- vs cap-weight; intraday $TICK & $ADD unavailable), DJIA/DJT→**DIA/IYT**, DJU→**XLU**, MOVE
> index→**TLT realized vol** (the MOVE index isn't on Alpaca), put/call **$CPC → no proxy (gap)**.

```bash
export $(grep -v '^#' ~/.config/blaquebaux/alpaca.env | xargs)   # or source it
python research/benchmark_1_internals.py            # the dashboard — each internal vs SPY
python research/benchmark_2_predict_or_coincide.py  # do they LEAD or COINCIDE?  (the crux)
python research/benchmark_3_composite_regime.py     # is the composite a tradable regime, or vol-timing?
python research/benchmark_4_naive_long.py       # WHERE it earns its keep (naive long vs managed)
```

## Scorecard

| # | Question | Result | Verdict |
|---|----------|--------|---------|
| 1 | Are the internals a coherent dashboard? | correctly signed — VIXY corr **−0.77**, credit +0.47, defensives −0.43; risk-off internals spike on the worst SPY days (VIXY +8%, bond-vol +16%) | ✅ a genuine risk dashboard |
| 2 | Do the internals **lead** SPY or **coincide**? | fwd-20d risk-on−off spreads tiny/wrong-signed; **peak cross-corr at k=0** for nearly all | ❌ **coincident** — they mirror the tape, don't forecast |
| 3 | Is the composite a **tradable regime**? | gated SPY **+0.87→+1.11** Sharpe, maxDD **−34%→−16%** (net of cost) — PASSES; but **non-vol** internals barely beat B&H (+0.89) | ⚠️ passes, but it's **vol-timing**, not breadth alpha |
| 4 | *Where* does it earn its keep? | naive SPY B&H **+0.87→+1.11**; plain vol-target +1.00→+1.12; broad (trend+vol-target) +0.84→**+0.80** | ✅ value shrinks monotonically with a book's own risk management — decisive on a **naive long book**, redundant on a managed one |

## The synthesis

**A coherent risk dashboard that resolves into a real risk-off regime — which turns out to be
vol-timing, not the breadth/credit edge it looks like.** The four sketches decompose cleanly:

1. **The dashboard is real and correctly built.** Every internal is signed as expected — VIX and
   bond-vol spike on the worst SPY days, defensives (utilities) outperform, credit and breadth fall.
   As a *read* of market stress it works.
2. **But the internals COINCIDE, they don't lead.** The forward-20-day return spread between risk-on
   and risk-off readings is tiny and often wrong-signed, and the cross-correlation peaks at **k=0** —
   the internals move *with* the tape, not before it. Breadth, Dow Theory, and credit are classic
   mirrors; this confirms it on our data.
3. **The composite still gates profitably — because risk-off regimes persist, not because internals
   forecast.** Gating SPY to cash when the composite is risk-off lifts Sharpe +0.87→+1.11 and halves
   the drawdown (−34%→−16%), *net of cost*. But that benefit is **vol-timing**: strip the VIXY /
   bond-vol signals and the non-vol internals (breadth/credit/Dow-Theory — the ones this sleeve is
   named for) barely clear buy-and-hold (+0.89 vs +0.87). So the regime works by *riding the
   persistence of high-vol clusters*, which is **managed-vol wearing an internals label** — the same
   effect [broad](https://github.com/blaquebaux/broad)'s vol-target already captures and that overlaps
   [bonds](https://github.com/blaquebaux/bonds)' crash-day behavior.
4. **So *where* does it earn its keep? On a naive long book, and only there.** Its marginal value
   shrinks monotonically with how much a book already manages its own risk: decisive on a plain
   buy-&-hold SPY (+0.87→+1.11, drawdown halved), smaller on a plain vol-target (+1.00→+1.12), and
   redundant-to-negative once a book has *trend + vol-target* together (broad: +0.84→+0.80, which is
   why broad correctly declined it). Much of each increment is simply "more de-risking helps in a
   crash-heavy sample," not new information. Its right home in this family is exactly **benchmark's own
   gated-SPY book** (a naive long book gated on the regime) — the managed sleeves already do the job.

**Net:** benchmark is a legitimate **risk-off regime** (publishable as `market_regime.txt`, a third
family signal after bonds' stock-bond and brics' dollar) — but it must be labeled for what it is:
*mostly vol-timing/persistence, not a forecasting edge from breadth or credit.* The internals **confirm,
they don't predict** — the same honest lesson as [Bubble](https://github.com/blaquebaux/bubble) ("you
cannot fade the prop / diagnostics flag but don't time"). A risk map to READ and a de-risking regime to
SIZE with, not novel alpha. ($TICK, $CPC, $ADD, and the MOVE *index* couldn't be tested on daily bars.)

## Status
**Research: first pass complete.** A coherent market-internals dashboard that yields a tradable
risk-off regime (net of cost) — but it is **vol-timing, not breadth alpha** (the internals coincide;
the vol signals do the work). Now published via a live emitter
(`live/benchmark_live.jl` → `market_regime.txt`), labeled as vol-timing. Nothing validated to the spine's bar.
