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

CODE_VERSION = "feasibility_test v1"
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
    p = pd.read_parquet(panel_path, columns=["timestamp", "symbol", "label_exit_ret",
                                             "label_tp_before_sl"] + feats)
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
    _log(f"{int(ok.sum()):,} labelled research rows | {p['symbol'].nunique():,} symbols | "
         f"{len(sessions):,} sessions")

    sp = splits(sessions, cfg["n_splits"], cfg["embargo"], cfg["min_train_frac"])
    rng = np.random.default_rng(cfg["seed"])
    preds = {"A_return": [], "B_tp_first": []}
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
        for nm, sc in (("A_return", sA), ("B_tp_first", sB)):
            d = pd.DataFrame({"timestamp": ts[te], "p_cal": sc, "exit_ret": er[te],
                              "y": (er[te] - cost_bps / 1e4 > 0).astype(float)})
            preds[nm].append(d)
            row[f"{nm}_ic"] = rank_ic_by_date(ts[te], sc, er[te])
            e3 = RC.topn_evidence(d, cfg["primary_top_n"], cost_bps=cost_bps, B=500,
                                  seed=cfg["seed"])
            row[f"{nm}_top3_net"] = e3["net"]["mean"]
        fold_rows.append(row)
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
    pA = res["pooled"]["A_return"]["topn"][cfg["primary_top_n"]]
    res["primary_rule"] = (f"model A daily top-{cfg['primary_top_n']} net-return 95% "
                           f"interval above zero")
    res["passes"] = bool(pA.get("clears"))
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


def _print(res):
    cost = res["cost_bps"]
    print("\n" + "=" * 72)
    print(f"  FEASIBILITY - research period only, net of {cost:.0f} bp, "
          f"{res['n_features']} features, no selection")
    print("=" * 72)
    print(f"  {'':<14}{'rank IC':>9}   " + "  ".join(f"{'top-'+str(n)+' net bp [95%]':>22}"
                                                  for n in (1, 3, 5, 10)))
    for nm, lab in (("A_return", "A: return"), ("B_tp_first", "B: TP-first")):
        r = res["pooled"][nm]
        cells = []
        for n in (1, 3, 5, 10):
            t = r["topn"][n]["net"]
            mark = "*" if r["topn"][n]["clears"] else " "
            cells.append(f"{t['mean']*1e4:+5.0f} [{t['lo']*1e4:+4.0f},{t['hi']*1e4:+4.0f}]{mark}")
        print(f"  {lab:<14}{r['rank_ic']:>+9.4f}   " + "  ".join(f"{c:>22}" for c in cells))
    print("  * = lower end of the net-return interval above zero")
    print("\n  per fold, top-3 net bp:  " + " | ".join(
        f"F{f['fold']} A {f['A_return_top3_net']*1e4:+.0f} / B {f['B_tp_first_top3_net']*1e4:+.0f}"
        for f in res["folds"]))
    print("\n" + "-" * 72)
    print(f"  PRIMARY RULE: {res['primary_rule']}")
    print(f"  RESULT: {'PASS - worth converting regime_research to the return target' if res['passes'] else 'FAIL - do not spend the lockbox; this library shows no tradable edge at this cost'}")
    print("-" * 72)


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
