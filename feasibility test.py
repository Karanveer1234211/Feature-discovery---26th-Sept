#!/usr/bin/env python3
"""
feasibility_test.py - can this feature library make money at all, before the
lockbox is spent?

    python feasibility_test.py --root %CACHE_DAILY_ROOT%
    python feasibility_test.py --root %CACHE_DAILY_ROOT% --cost-bps 35

WHY THIS EXISTS
===============
The return-target atlas showed the TP-first label is misaligned with money:
96% of its signal does not carry over to realised trade return, and a third of
the shared signal flips sign. Before converting the research pipeline to a
return target and spending the lockbox, this asks the one question that
matters: in the RESEARCH period, out of sample, does a model trained on
realised return pick daily top-N trades that clear costs?

THE DESIGN IS FIXED BEFORE IT RUNS
----------------------------------
  * research sessions only - the lockbox is never read
  * walk-forward, expanding train, 5-session embargo (no label overlap)
  * EVERY panel feature, no selection -> no selection bias. Selecting
    features first can only do worse out of sample, so this is roughly the
    CEILING for this library with this model.
  * fixed model settings, no tuning
  * two models on identical folds, judged identically:
        A  trained on label_exit_ret        (proposed target)
        B  trained on label_tp_before_sl    (current design)
  * PRIMARY RULE: proceed only if model A's daily top-3 net-return 95%
    block-bootstrap interval is above zero. Top-1/5/10 and model B are
    descriptive.
  * v2 ADDS A SECOND, TIGHTER CONDITION: model A's top-3 must also beat
    BUYING EVERYTHING - the equal-weight average of every stock that day,
    same bracket, same cost - with a 95% interval above zero. v1 passed with
    +120 bp while fold 5 had NEGATIVE rank IC: a sign that much of the
    return was the market rising, not selection. A condition that can only
    block is safe to add after seeing a pass; loosening one is not.
  * Descriptive controls: "buy the most volatile" (top-N by ATR%) - with
    ATR-sized brackets in a rising market, high-volatility names earn the
    biggest % payoffs, so matching it means the skill is volatility
    exposure - and the ATR% / liquidity profile of the model's picks.

Net return per trade = label_exit_ret - cost. Intervals: circular block
bootstrap over trading days (research_common.topn_evidence).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import research_common as RC  # noqa: E402

CODE_VERSION = "feasibility_test v2"
CFG = {"n_splits": 5, "embargo": 5, "min_train_frac": 0.35, "fit_cap": 400_000,
       "top_n": (1, 3, 5, 10), "primary_top_n": 3, "seed": 7,
       "hgb": {"max_iter": 200, "learning_rate": 0.05, "max_leaf_nodes": 31,
               "min_samples_leaf": 200, "l2_regularization": 1.0}}


def _log(msg):
    print(f"{dt.datetime.now():%H:%M:%S}  {msg}", flush=True)


def splits(sessions: np.ndarray, n_splits: int, embargo: int, min_train_frac: float):
    """Expanding train; test blocks of equal length; last train row's label ends before test."""
    n = len(sessions)
    edges = np.linspace(int(n * min_train_frac), n, n_splits + 1).astype(int)
    out = []
    for k in range(n_splits):
        te0, te1 = edges[k], edges[k + 1]
        tr_end = te0 - embargo - 1
        out.append({"fold": k + 1, "train_end": sessions[tr_end],
                    "test_start": sessions[te0], "test_end": sessions[te1 - 1]})
    return out


def _med(x) -> float:
    x = np.asarray(x, dtype="float64")
    x = x[np.isfinite(x)]
    return float(np.median(x)) if len(x) else float("nan")


def rank_ic_by_date(ts, score, target) -> float:
    d = pd.DataFrame({"t": ts, "s": score, "y": target}).dropna()
    d["rs"] = d.groupby("t")["s"].rank()
    d["ry"] = d.groupby("t")["y"].rank()
    ic = d.groupby("t")[["rs", "ry"]].corr().xs("rs", level=1)["ry"]
    return float(ic.mean())


def run(panel_path: Path, cost_bps: float = 35.0, verbose: bool = True) -> dict:
    import pyarrow.parquet as pq
    import panel_build as PB
    from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
    t0 = time.perf_counter()
    cfg = dict(CFG)

    schema = pq.ParquetFile(panel_path).schema_arrow.names
    feats = PB.panel_feature_columns(pd.DataFrame(columns=schema))
    feats = [c for c in feats if c not in ("open", "high", "low", "close", "volume")]
    RC.assert_no_label_leak(feats, "feasibility_test")
    for need in ("label_exit_ret", "label_tp_before_sl"):
        if need not in schema:
            raise SystemExit(f"{need} missing - rebuild the panel")

    ts_all = pd.to_datetime(pd.read_parquet(panel_path, columns=["timestamp"])["timestamp"])
    if getattr(ts_all.dt, "tz", None) is not None:
        ts_all = ts_all.dt.tz_localize(None)
    sessions_all = np.sort(ts_all.unique())
    research_end, lockbox_start = RC.lockbox_bounds(sessions_all, RC.DEFAULT_LOCKBOX_FRACTION,
                                                    PB.LABEL_HORIZON)
    keep = (ts_all <= pd.Timestamp(research_end)).to_numpy()
    del ts_all

    _log(f"loading {len(feats)} features, research rows only (through "
         f"{pd.Timestamp(research_end).date()}; lockbox from "
         f"{pd.Timestamp(lockbox_start).date()} is never read)")
    prof = [c for c in ("X_turnover_med",) if c in schema and c not in feats]
    p = pd.read_parquet(panel_path, columns=["timestamp", "symbol", "label_exit_ret",
                                             "label_tp_before_sl"] + feats + prof)
    p = p[keep].reset_index(drop=True)
    p["timestamp"] = pd.to_datetime(p["timestamp"])
    if getattr(p["timestamp"].dt, "tz", None) is not None:
        p["timestamp"] = p["timestamp"].dt.tz_localize(None)
    p = p.sort_values(["timestamp", "symbol"]).reset_index(drop=True)
    er = pd.to_numeric(p["label_exit_ret"], errors="coerce").to_numpy("float64")
    tp = pd.to_numeric(p["label_tp_before_sl"], errors="coerce").to_numpy("float64")
    ok = np.isfinite(er) & np.isfinite(tp)
    ts = p["timestamp"].to_numpy()
    sessions = np.sort(np.unique(ts))
    X = p[feats]
    atr = (pd.to_numeric(p["D_atr_pct"], errors="coerce").to_numpy("float64")
           if "D_atr_pct" in p.columns else np.full(len(p), np.nan))
    tov = (pd.to_numeric(p["X_turnover_med"], errors="coerce").to_numpy("float64")
           if "X_turnover_med" in p.columns else np.full(len(p), np.nan))
    _log(f"{int(ok.sum()):,} labelled research rows | {p['symbol'].nunique():,} symbols | "
         f"{len(sessions):,} sessions")

    sp = splits(sessions, cfg["n_splits"], cfg["embargo"], cfg["min_train_frac"])
    rng = np.random.default_rng(cfg["seed"])
    preds = {"A_return": [], "B_tp_first": [], "C_most_volatile": []}
    fold_rows = []
    for s in sp:
        tr = np.where(ok & (ts <= s["train_end"]))[0]
        te = np.where(ok & (ts >= s["test_start"]) & (ts <= s["test_end"]))[0]
        if len(tr) > cfg["fit_cap"]:
            tr = np.sort(rng.choice(tr, cfg["fit_cap"], replace=False))
        Xtr = X.iloc[tr].to_numpy("float32")
        Xte = X.iloc[te].to_numpy("float32")
        mA = HistGradientBoostingRegressor(random_state=cfg["seed"], **cfg["hgb"]).fit(Xtr, er[tr])
        mB = HistGradientBoostingClassifier(random_state=cfg["seed"], **cfg["hgb"]).fit(
            Xtr, tp[tr].astype(int))
        sA = mA.predict(Xte)
        sB = mB.predict_proba(Xte)[:, 1]
        del Xtr, Xte
        row = {"fold": s["fold"], "test": f"{pd.Timestamp(s['test_start']).date()}.."
                                          f"{pd.Timestamp(s['test_end']).date()}",
               "train_rows": int(len(tr)), "test_rows": int(len(te))}
        for nm, sc in (("A_return", sA), ("B_tp_first", sB), ("C_most_volatile", atr[te])):
            d = pd.DataFrame({"timestamp": ts[te], "p_cal": sc, "exit_ret": er[te],
                              "y": (er[te] - cost_bps / 1e4 > 0).astype(float),
                              "atr": atr[te], "tov": tov[te]})
            preds[nm].append(d)
            row[f"{nm}_ic"] = rank_ic_by_date(ts[te], sc, er[te])
            e3 = RC.topn_evidence(d, cfg["primary_top_n"], cost_bps=cost_bps, B=500,
                                  seed=cfg["seed"])
            row[f"{nm}_top3_net"] = e3["net"]["mean"]
        fold_rows.append(row)
        uni = (pd.DataFrame({"t": ts[te], "n": er[te] - cost_bps / 1e4})
               .groupby("t")["n"].mean().mean())
        row["universe_net"] = float(uni)
        _log(f"fold {s['fold']} buy-everything net {uni*1e4:+.0f}bp")
        _log(f"fold {s['fold']} {row['test']}: IC A {row['A_return_ic']:+.4f} / "
             f"B {row['B_tp_first_ic']:+.4f} | top-3 net A "
             f"{row['A_return_top3_net']*1e4:+.0f}bp / B {row['B_tp_first_top3_net']*1e4:+.0f}bp")

    res = {"code": CODE_VERSION, "built_at": dt.datetime.now().isoformat(),
           "cost_bps": cost_bps, "research_end": str(pd.Timestamp(research_end).date()),
           "lockbox_start": str(pd.Timestamp(lockbox_start).date()),
           "n_features": len(feats), "config": {k: v for k, v in cfg.items()},
           "folds": fold_rows, "pooled": {}}
    for nm, parts in preds.items():
        d = pd.concat(parts, ignore_index=True)
        res["pooled"][nm] = {
            "rank_ic": rank_ic_by_date(d["timestamp"], d["p_cal"], d["exit_ret"]),
            "topn": {int(n): RC.topn_evidence(d, n, cost_bps=cost_bps, seed=cfg["seed"])
                     for n in cfg["top_n"]}}
    allA = pd.concat(preds["A_return"], ignore_index=True)
    uni_day = (allA.assign(n=allA["exit_ret"] - cost_bps / 1e4)
               .groupby("timestamp")["n"].mean().sort_index())
    res["universe"] = RC.block_bootstrap_mean(uni_day.to_numpy(), seed=cfg["seed"])
    res["excess"], res["profile"] = {}, {}
    for nm, parts in preds.items():
        d = pd.concat(parts, ignore_index=True)
        d["net"] = d["exit_ret"] - cost_bps / 1e4
        res["excess"][nm], res["profile"][nm] = {}, {}
        for n in cfg["top_n"]:
            top = RC.daily_topn_values(d, n, "net")
            ex = (top - uni_day.reindex(top.index)).dropna()
            res["excess"][nm][int(n)] = RC.block_bootstrap_mean(ex.to_numpy(), seed=cfg["seed"])
        d["_rk"] = d.groupby("timestamp")["p_cal"].rank(ascending=False, method="first")
        pk = d[d["_rk"] <= cfg["primary_top_n"]]
        res["profile"][nm] = {
            "pick_atr_median": _med(pk["atr"]),
            "universe_atr_median": _med(d["atr"]),
            "pick_turnover_median": _med(pk["tov"]),
            "universe_turnover_median": _med(d["tov"]),
            "pick_share_losing": float((pk["net"] < 0).mean())}
    dA = pd.concat(preds["A_return"], ignore_index=True)
    dC = pd.concat(preds["C_most_volatile"], ignore_index=True)
    for d_ in (dA, dC):
        d_["net"] = d_["exit_ret"] - cost_bps / 1e4
    tA = RC.daily_topn_values(dA, cfg["primary_top_n"], "net")
    tC = RC.daily_topn_values(dC, cfg["primary_top_n"], "net")
    res["A_minus_most_volatile"] = RC.block_bootstrap_mean(
        (tA - tC.reindex(tA.index)).dropna().to_numpy(), seed=cfg["seed"])
    pA = res["pooled"]["A_return"]["topn"][cfg["primary_top_n"]]
    xA = res["excess"]["A_return"][cfg["primary_top_n"]]
    res["beats_buy_everything"] = bool(np.isfinite(xA["lo"]) and xA["lo"] > 0)
    res["primary_rule"] = (f"model A daily top-{cfg['primary_top_n']} net-return 95% "
                           f"interval above zero")
    res["passes"] = bool(pA.get("clears")) and res["beats_buy_everything"]
    res["minutes"] = round((time.perf_counter() - t0) / 60, 1)

    out = panel_path.parent / "feasibility"
    out.mkdir(parents=True, exist_ok=True)
    (out / "feasibility.json").write_text(json.dumps(res, indent=2, default=str),
                                          encoding="utf-8")
    RC.ledger_append(panel_path, {"kind": "feasibility", "tool": CODE_VERSION,
                                  "passes": res["passes"], "cost_bps": cost_bps,
                                  "research_end": res["research_end"]})
    if verbose:
        _print(res)
    return res


def _fmt(e):
    return f"{e['mean']*1e4:+5.0f} [{e['lo']*1e4:+4.0f},{e['hi']*1e4:+4.0f}]"


def _print(res):
    cost = res["cost_bps"]
    labs = (("A_return", "A: return"), ("B_tp_first", "B: TP-first"),
            ("C_most_volatile", "C: most volatile"))
    print("\n" + "=" * 78)
    print(f"  FEASIBILITY - research period only, net of {cost:.0f} bp, "
          f"{res['n_features']} features, no selection")
    print("=" * 78)
    u = res["universe"]
    print(f"  BUY EVERYTHING (equal weight, same bracket, same cost): {_fmt(u)} bp per trade")
    print("\n  NET RETURN PER TRADE, bp [95%]")
    print(f"  {'':<18}{'rank IC':>8}" + "".join(f"{'top-'+str(n):>20}" for n in (1, 3, 5, 10)))
    for nm, lab in labs:
        r = res["pooled"][nm]
        cells = [_fmt(r["topn"][n]["net"]) + ("*" if r["topn"][n]["clears"] else " ")
                 for n in (1, 3, 5, 10)]
        print(f"  {lab:<18}{r['rank_ic']:>+8.4f}" + "".join(f"{c:>20}" for c in cells))
    print("\n  EXCESS OVER BUY-EVERYTHING, bp [95%]  <- the model's actual contribution")
    for nm, lab in labs:
        x = res["excess"][nm]
        cells = [_fmt(x[n]) + ("*" if np.isfinite(x[n]["lo"]) and x[n]["lo"] > 0 else " ")
                 for n in (1, 3, 5, 10)]
        print(f"  {lab:<18}{'':>8}" + "".join(f"{c:>20}" for c in cells))
    print("  * = lower end of the interval above zero")
    print("\n  WHAT THE TOP-3 BUYS (median)")
    for nm, lab in labs:
        pr = res["profile"][nm]
        print(f"  {lab:<18} ATR% {pr['pick_atr_median']:.2f} vs universe "
              f"{pr['universe_atr_median']:.2f} | turnover "
              f"{pr['pick_turnover_median']/1e7:.1f} cr vs {pr['universe_turnover_median']/1e7:.1f} cr"
              f" | losing trades {pr['pick_share_losing']:.0%}")
    print("\n  per fold (top-3 net bp, and buy-everything):  " + " | ".join(
        f"F{f['fold']} A {f['A_return_top3_net']*1e4:+.0f} / all {f['universe_net']*1e4:+.0f}"
        for f in res["folds"]))
    pA = res["pooled"]["A_return"]["topn"][3]["clears"]
    av = res["A_minus_most_volatile"]
    print(f"\n  model A top-3 minus most-volatile top-3: {_fmt(av)} bp"
          + ("   <- A adds nothing beyond buying volatility"
             if not (np.isfinite(av['lo']) and av['lo'] > 0) else ""))
    print("\n" + "-" * 78)
    print(f"  1. model A top-3 net return above zero:        {'yes' if pA else 'NO'}")
    print(f"  2. model A top-3 beats buying everything:      "
          f"{'yes' if res['beats_buy_everything'] else 'NO'}")
    print(f"  RESULT: " + ("PASS - the model adds return beyond the market; convert "
                           "regime_research" if res["passes"] else
                           "FAIL - do not spend the lockbox"))
    print("-" * 78)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=None)
    ap.add_argument("--cost-bps", type=float, default=35.0)
    a = ap.parse_args()
    root = a.root or os.environ.get("CACHE_DAILY_ROOT")
    if not root:
        raise SystemExit("CACHE_DAILY_ROOT not set and --root not given")
    run(Path(root) / "panel" / "panel.parquet", cost_bps=a.cost_bps)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
