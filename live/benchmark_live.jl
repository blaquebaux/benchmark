#!/usr/bin/env julia
# ============================================================================
# benchmark_live.jl — BLAQUE BAUX BENCHMARK live driver (market-internals regime emitter).
#
# Runs on the Blaque Baux ENGINE (engine/ submodule) — same governed order path + Layer-3 safety gate
# as the spine.  data(9 internals) -> composite risk-on/off regime -> publish + gated-SPY book -> orders.
#
# THE PRODUCT IS THE REGIME READ. benchmark computes a composite of six risk-on-oriented internals
# (credit HYG/LQD, breadth RSP/SPY, Dow-Theory IYT/DIA, defensives SPY/XLU, -VIX via VIXY, -bond-vol
# via TLT realized vol), each causally z-scored and averaged, and PUBLISHES it to $BB_MARKET_REGIME_PATH
# (default ~/.config/blaquebaux/market_regime.txt) — the family's third regime signal after bonds'
# stock-bond and brics' dollar. It also trades the regime's own expression: hold SPY when risk-on, go
# to cash when risk-off (validated net of cost: Sharpe +0.87 -> +1.11, maxDD -34% -> -16%).
#
# HONEST LABEL: this regime is mostly VOL-TIMING / persistence, NOT breadth alpha — research #2 showed
# the internals COINCIDE (they don't lead), and #3 showed the benefit comes from the vol signals (strip
# them and breadth/credit/Dow-Theory barely beat buy&hold). It overlaps broad's vol-target and bonds'
# crash behavior. Consume the published regime as a RISK-OFF flag, sized knowing what drives it.
#
# MODES: dry-run by default via the wrapper (BB_DRYRUN=1 -> compute + publish, NO venue). Paper: unset
# BB_DRYRUN with paper keys. Real money requires BB_LIVE_CONFIRM=I_UNDERSTAND_THIS_IS_REAL_MONEY.
# Kill switch: ~/.config/blaquebaux/HALT.  Run:  julia --project=engine live/benchmark_live.jl
# ============================================================================
using Dates, Printf, Statistics

const REPO   = normpath(joinpath(@__DIR__, ".."))
const ENGINE = joinpath(REPO, "engine")
include(joinpath(ENGINE, "src/module_7_execution/module_7_execution.jl"))
include(joinpath(ENGINE, "src/module_10_feedback/module_10_feedback.jl"))
include(joinpath(ENGINE, "src/module_13_portfolio/module_13_portfolio.jl"))
include(joinpath(ENGINE, "src/module_1_data/equity_panel.jl"))
include(joinpath(ENGINE, "src/module_1_data/alpaca_panel.jl"))
include(joinpath(ENGINE, "src/module_8_governance/safety_gate.jl"))
using .ExecutionLayer, .FeedbackLayer, .PortfolioOptModule, .EquityPanel, .AlpacaPanel, .SafetyGate
include(joinpath(ENGINE, "scripts/live_execution.jl"))

const UNIVERSE = ["SPY", "RSP", "HYG", "LQD", "DIA", "IYT", "XLU", "VIXY", "TLT"]
const BOOK = "SPY"                                   # the regime's own expression: SPY when risk-on, cash when off
const LIVE_SENTINEL = "I_UNDERSTAND_THIS_IS_REAL_MONEY"
const ZWIN = 252                                     # trailing z-score window
const TW = 21                                        # trend window
const VW = 20                                        # bond-vol window
const RISK_ON_W = 0.80                               # SPY weight when risk-on (under the gate's 85% single-name cap; rest cash)

_readf(p) = isfile(p) ? (v = tryparse(Float64, strip(read(p, String))); v === nothing ? NaN : v) : NaN
_writef(p, x) = (mkpath(dirname(p)); write(p, string(x)))

_relpath(R, i) = cumprod(vcat(1.0, 1 .+ R[:, i]))    # relative price path from returns (length T+1)
function _trend(level, w)                            # w-day trend series (NaN for first w)
    t = fill(NaN, length(level)); for k in w+1:length(level); t[k] = level[k] / level[k-w] - 1; end; t
end
function _rvol(r, w)                                 # w-day realized vol series
    v = fill(NaN, length(r)); for k in w+1:length(r); v[k] = std(@view r[k-w:k-1]) * sqrt(252); end; v
end
function _zlast(x, zwin)                             # z-score of the last finite value vs trailing zwin
    v = x[.!isnan.(x)]; length(v) < zwin + 1 && return NaN
    h = @view v[end-zwin:end-1]; s = std(h); s > 0 ? (v[end] - mean(h)) / s : NaN
end

"Composite market-internals risk-on score at the latest bar (mean of causal z-scored, risk-on-oriented signals)."
function market_regime(panel)
    syms = panel.symbols; R = panel.returns
    i(s) = findfirst(==(s), syms); rp(s) = _relpath(R, i(s))
    sigs = Dict(
        "credit"  => _trend(rp("HYG") ./ rp("LQD"), TW),
        "breadth" => _trend(rp("RSP") ./ rp("SPY"), TW),
        "dow"     => _trend(rp("IYT") ./ rp("DIA"), TW),
        "defens"  => _trend(rp("SPY") ./ rp("XLU"), TW),
        "vol"     => -_trend(rp("VIXY"), TW),
        "bondvol" => -_rvol(R[:, i("TLT")], VW),
    )
    zs = Dict(k => _zlast(v, ZWIN) for (k, v) in sigs)
    good = [z for z in values(zs) if isfinite(z)]
    comp = isempty(good) ? NaN : mean(good)
    (; composite = comp, risk_on = isfinite(comp) && comp > 0, zs = zs, n = length(good))
end

function benchmark_target(panel, cap, risk_on)       # gated SPY: 80% when risk-on (gate cap), cash when off
    px = panel.prices[findfirst(==(BOOK), panel.symbols)]
    w = risk_on ? RISK_ON_W : 0.0
    (targets = Dict(BOOK => round(Float64, w * cap / px)), prices = Dict(BOOK => px), net = Dict(BOOK => w))
end

function emit_regime(path, reg, asof)
    mkpath(dirname(path))
    open(path, "w") do io
        println(io, "# Blaque Baux — market-internals risk regime (published by benchmark; composite of 6 internals)")
        println(io, "# NOTE: mostly vol-timing/persistence, not breadth forecasting — internals coincide (research #2).")
        println(io, "asof=", asof)
        if isfinite(reg.composite)
            @printf(io, "composite=%.3f\n", reg.composite)
            println(io, "regime=", reg.risk_on ? "risk-on" : "risk-off")
            println(io, "risk_on=", reg.risk_on ? 1 : 0)    # 1 = hold risk; 0 = de-risk
        else
            println(io, "regime=unknown"); println(io, "risk_on=1")
        end
    end
end

function main(; capital = nothing, pool = "us", limits::SafetyLimits = SafetyLimits(),
              db_path     = get(ENV, "BB_LEDGER_PATH", joinpath(REPO, "alpaca_ledger_benchmark.sqlite")),
              audit_path  = get(ENV, "BB_AUDIT_PATH",  joinpath(REPO, "alpaca_audit_benchmark.jsonl")),
              hwm_path    = get(ENV, "BB_HWM_PATH",    joinpath(homedir(), ".config", "blaquebaux", "equity_hwm_benchmark.txt")),
              equity_path = get(ENV, "BB_EQUITY_PATH", joinpath(homedir(), ".config", "blaquebaux", "equity_last_benchmark.txt")),
              regime_path = get(ENV, "BB_MARKET_REGIME_PATH", joinpath(homedir(), ".config", "blaquebaux", "market_regime.txt")))
    (get(ENV, "ALPACA_KEY_ID", "") == "" || get(ENV, "ALPACA_SECRET_KEY", "") == "") &&
        error("Set ALPACA_KEY_ID and ALPACA_SECRET_KEY (read-only bars are needed even in dry-run).")
    dryrun = get(ENV, "BB_DRYRUN", "") in ("1", "true", "yes")

    if dryrun
        panel = panel_at(AlpacaPanelProvider(UNIVERSE; lookback = 400))
        reg = market_regime(panel); emit_regime(regime_path, reg, panel.asof)
        bk = benchmark_target(panel, capital === nothing ? 100_000.0 : capital, reg.risk_on)
        @info "BENCHMARK dry run" asof=panel.asof composite=round(reg.composite, digits=2) regime=(reg.risk_on ? "risk-on" : "risk-off") signals=reg.n
        println("\n  market regime -> ", reg.risk_on ? "RISK-ON (hold SPY)" : "RISK-OFF (to cash)",
                "   composite ", @sprintf("%+.2f", reg.composite), "   (published to ", regime_path, ")")
        for (k, z) in sort(collect(reg.zs)); @printf("    %-8s z=%+.2f\n", k, z); end
        println("  gated book: SPY ", @sprintf("%.0f%%", 100 * get(bk.net, BOOK, 0.0)),
                " -> ", Int(get(bk.targets, BOOK, 0.0)), " sh @ \$", @sprintf("%.2f", get(bk.prices, BOOK, NaN)))
        ok, reasons = preflight(; account_status = "ACTIVE", equity = 100_000.0, hwm = 100_000.0,
            last_equity = 100_000.0, buying_power = 100_000.0, data_fresh = (Dates.today() - panel.asof) <= Day(5),
            targets = bk.targets, prices = bk.prices, limits = limits)
        println("\n  DRY RUN — no venue, no orders. Gate: ", ok ? "PASS" : "ABORT: " * join(reasons, "; "))
        return ok ? :dryrun_ok : :dryrun_gate_abort
    end

    live = get(ENV, "BB_LIVE_CONFIRM", "") == LIVE_SENTINEL; paper = !live
    mode = live ? "*** LIVE REAL MONEY ***" : "paper"
    @info "benchmark_live starting" mode
    live && alert("BENCHMARK LIVE REAL-MONEY mode engaged"; level = :critical)
    venue = AlpacaVenue(AlpacaConfig(; paper = paper))
    built = build_live_controller(; venue = venue, ledger_config = LedgerConfig(; db_path = db_path), audit_path = audit_path)
    ctrl, ledger = built.ctrl, built.ledger
    try
        connect!(venue) || (alert("ABORT [$mode]: Alpaca connect failed (benchmark)"; level = :critical); return :connect_failed)
        acct = account_info(venue)
        acct === nothing && (alert("ABORT [$mode]: could not read account (benchmark)"; level = :critical); return :no_account)
        cap = capital === nothing ? acct.equity : capital
        hwm = max(load_hwm(hwm_path), acct.equity); last_eq = _readf(equity_path)
        panel = panel_at(AlpacaPanelProvider(UNIVERSE; lookback = 400)); fresh = (Dates.today() - panel.asof) <= Day(5)
        reg = market_regime(panel); emit_regime(regime_path, reg, panel.asof)   # publish even if the gate halts trading
        @info "market regime" composite=round(reg.composite, digits=2) regime=(reg.risk_on ? "risk-on" : "risk-off")
        bk = benchmark_target(panel, cap, reg.risk_on)
        ok, reasons = preflight(; account_status = acct.status, trading_blocked = acct.trading_blocked,
            account_blocked = acct.account_blocked, equity = acct.equity, hwm = hwm, last_equity = last_eq,
            buying_power = acct.buying_power, data_fresh = fresh, targets = bk.targets, prices = bk.prices, limits = limits)
        save_hwm(hwm, hwm_path); _writef(equity_path, acct.equity)
        if !ok
            msg = "SAFETY ABORT [$mode] (benchmark): " * join(reasons, "; "); @error msg
            halt!(ctrl, "safety gate"); alert(msg; level = :critical); return :aborted
        end
        reset_daily!(ctrl)
        set_pool_budget!(ctrl, pool, limits.max_gross_leverage * acct.equity)
        set_pool_loss_limit!(ctrl, pool, limits.max_daily_loss)
        set_pool_staleness!(ctrl, pool, Day(5)); feed_staleness!(ctrl, pool; stale = !fresh)
        isfinite(last_eq) && update_pnl!(ctrl, pool, acct.equity - last_eq)
        ncanc = cancel_all_open!(venue); ncanc > 0 && sleep(2)
        for (sym, qty) in positions(venue, ctrl.account); apply_fill!(ctrl, sym, qty); end
        res = execute_rebalance!(ctrl, ledger; targets = bk.targets, prices = bk.prices,
            signal_id = "benchmark", regime = (reg.risk_on ? "risk-on" : "risk-off"),
            solve_id = Dates.format(panel.asof, "yyyymmdd"), pool_id = pool, settle_secs = 20)
        !res.reconciled && (alert("RECONCILE FAILED [$mode] (benchmark) — halting"; level = :critical); halt!(ctrl, "reconcile mismatch"))
        summary = "[$mode] benchmark $(reg.risk_on ? "risk-on/SPY" : "risk-off/cash"); orders=$(length(res.acks)) fills=$(length(res.fills)) reconciled=$(res.reconciled) equity=$(round(Int, acct.equity))"
        @info "benchmark_live complete" summary; alert(summary; level = :info)
        return res.reconciled ? :ok : :reconcile_failed
    finally
        disconnect!(venue); close_ledger(ledger)
    end
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
