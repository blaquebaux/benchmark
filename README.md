# Blaque Baux Benchmark

**Market internals as a risk-regime read — do the confirming/diverging signals predict, or just coincide?**

Benchmark is a member of the Blaque Baux family. The [core repo](https://github.com/blaquebaux/base)
is the **engine and blueprint** — a governed, systematic platform (Julia) with a venue-agnostic
execution controller and a Layer-3 live-money safety gate. Benchmark points that engine at the
market's own internals and inherits the governance wholesale.

> **Not investment advice.** Educational/research software. Nothing here is validated. See [LICENSE](LICENSE).

```bash
git clone --recursive https://github.com/blaquebaux/benchmark.git
julia --project=engine -e 'using Pkg; Pkg.instantiate()'   # one-time engine setup
```

## The thesis

Traders watch a wall of "internals" to judge whether a market move is healthy or hollow: **VIX** (fear),
the **advance-decline line / $TICK** (breadth), **HYG vs LQD** (credit risk appetite), the **MOVE index**
(bond vol), **SPY vs RSP** (cap- vs equal-weight participation), **Dow Theory** (DJIA confirmed by DJT,
with DJU as the defensive tell), and the **put/call ratio $CPC** (sentiment). The folk belief is that
divergences here *warn* — breadth rolling over, transports failing to confirm, credit widening — before
price does. Benchmark asks the honest question: **do these internals actually lead the market (a
tradable/sizing regime), or do they merely coincide with it (a dashboard)?** If they lead, benchmark
becomes the family's third **regime publisher** (after [bonds](https://github.com/blaquebaux/bonds)'
stock-bond regime and [brics](https://github.com/blaquebaux/brics)' dollar regime); if not, it's an
honest diagnostic.

**Data note:** several of these are index/breadth tickers a daily-bars vendor doesn't serve, so they're
proxied (or flagged) with tradable instruments:

| requested | proxy | |
|-----------|-------|--|
| VIX | `VIXY` | VIX-futures ETF |
| HYG vs LQD (credit) | `HYG` / `LQD` | direct |
| $ADD / $TICK (breadth) | `RSP` / `SPY` | equal- vs cap-weight ($ADD & intraday $TICK not on daily bars) |
| DJIA vs DJT (Dow Theory) | `DIA` vs `IYT` | industrials vs transports |
| DJU (defensive) | `XLU` | utilities |
| MOVE index (bond vol) | `TLT` realized vol | the MOVE index isn't on Alpaca |
| put/call `$CPC` | — | CBOE sentiment index not available (gap) |

## Research — first pass done

Full detail in [`research/README.md`](research/README.md). The scorecard (Alpaca SIP, 2016–2026):

| # | Question | Verdict |
|---|----------|---------|
| 1 | Are the internals a coherent dashboard? | ✅ correctly signed (VIXY corr −0.77, credit +0.47, defensives −0.43; risk-off internals spike on the worst SPY days) |
| 2 | Do they **lead** SPY or **coincide**? | ❌ **coincident** — fwd-20d spreads tiny/wrong-signed; peak cross-corr at k=0 (they mirror the tape) |
| 3 | Is the composite a **tradable regime**? | ⚠️ passes net of cost (gated SPY +0.87→+1.11 Sharpe, DD −34%→−16%) — but it's **vol-timing**: non-vol internals barely beat B&H (+0.89) |
| 4 | *Where* does it earn its keep? | ✅ on a **naive long book** (SPY B&H +0.87→+1.11) — value shrinks monotonically with the book's own risk management; **redundant** on managed sleeves (broad +0.84→+0.80) |

**The synthesis:** benchmark is a coherent risk **dashboard** that resolves into a genuine **risk-off
regime** — which, honestly, is **vol-timing, not the breadth/credit edge it looks like**. The internals
*coincide* with the market (they confirm, they don't forecast); the composite still gates profitably
because risk-off regimes *persist* (high-vol clusters), and that benefit comes almost entirely from the
VIX / bond-vol components — strip them and breadth/credit/Dow-Theory barely clear buy-and-hold. So it's
**managed-vol wearing an internals label**, overlapping [broad](https://github.com/blaquebaux/broad)'s
vol-target and [bonds](https://github.com/blaquebaux/bonds)' crash behavior. Publishable as a family
risk-off regime (`market_regime.txt`) *with that caveat* — a risk map to READ and size with, not novel
alpha. Same honest lesson as [Bubble](https://github.com/blaquebaux/bubble): diagnostics flag, they
don't time.

## Live driver — regime emitter (paper/dry-run)

The composite is now a governed driver on the engine ([`live/benchmark_live.jl`](live/benchmark_live.jl)).
Each run it:

1. **Publishes the market regime** to `~/.config/blaquebaux/market_regime.txt` (composite score + a
   `risk_on` flag) — the family's **third regime signal** after
   [bonds](https://github.com/blaquebaux/bonds)' stock-bond and [brics](https://github.com/blaquebaux/brics)'
   dollar. The file itself carries the honest label: *mostly vol-timing, not breadth forecasting.*
2. **Trades the regime's own expression** — hold **80% SPY** when risk-on (the 85% single-name safety-gate
   cap; the rest cash), **flat/cash** when risk-off — through the same Layer-3 gate, ledger, reconcile,
   kill switch and HWM as the spine.

```bash
BB_DRYRUN=1 bash live/run_benchmark_daily.sh          # compute + publish the regime, place nothing
```

**Validation of record is [`research/benchmark_3_composite_regime.py`](research/benchmark_3_composite_regime.py)**
— gated SPY beats buy-&-hold net of cost (Sharpe +0.87→+1.11, maxDD −34%→−16%), with the honest caveat
that the edge is vol-timing (strip the vol signals and the non-vol internals barely clear buy-&-hold).
Dry-run verified (today: **risk-on**, composite +0.20). Not a live-money endorsement; paper by default.

## About Blaque Baux

**Blaque Baux** is a quantitative research initiative and a subsidiary of **[Carter Warrens](https://carterwarrens.com)**.
[**BlaqueBaux.com**](https://blaquebaux.com) is the home for the work; the code lives here on GitHub — open to
study, test, and build bespoke strategies on top of.

Anyone can point an AI at a market. The edge is **understanding what the data actually says — and turning it
into something you can act on.** We test relentlessly and put most of it *on the record as rejected, with the
reason*; what survives is built, governed, and validated before it is ever called real. That combination —
honest research, reproducible evidence, and execution you can trust — is why Carter Warrens leads on
**strategy and implementation**, not merely uses the tools everyone now has.

## The Blaque Baux family
This repo is one sleeve of the **Blaque Baux** family — a single governed engine steered in
many directions. The [core repo](https://github.com/blaquebaux/base) is the
base/blueprint and holds the [full family roster](https://github.com/blaquebaux/base#the-blaquebaux-family).

## Layout
```
engine/     the Blaque Baux platform (git submodule -> blaquebaux/base)
research/   three sketches (internals dashboard, lead-vs-coincide, composite regime) + scorecard
live/       benchmark_live.jl (regime emitter + gated-SPY book) + run wrapper + plist
```

## License
[MIT](LICENSE). (c) 2026 Carter Warrens.
