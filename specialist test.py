#!/usr/bin/env python3
"""
specialist_test.py - one model per stock state, versus one model for all.

    python specialist_test.py --root %CACHE_DAILY_ROOT%

EXPLORATION ON RESEARCH DATA
============================
Idea under test: stocks behave differently in different states, so a
separate model per state - each stock scored by the specialist for the state
it is in that day - should rank better than one model for everything.

Everything except the routing is identical between the two contenders:

    M0          one HistGradientBoosting model, all panel features
    SPECIALIST  the same model class and settings, one per stock state;
                each stock is scored by its current state's model

  * research sessions only; the lockbox is never read
  * same walk-forward folds (expanding, 5-session embargo), same features,
    same target (label_tp_before_sl), same settings, same RAW-score ranking
  * states: the canonical 8-dimension stock state (research_common),
    Gaussian mixture fitted on each fold's TRAINING rows only; K chosen once
    by BIC on fold 1 and held fixed; each row goes to its most probable state
  * a state with fewer than min_state_rows training rows cannot support its
    own model - its stocks are scored by M0, and the share is reported

THE RULE, FIXED BEFORE IT RUNS
------------------------------
The specialist joins the forward paper test only if, day by day, its daily
top-3 net return MINUS M0's has a 95% block-bootstrap interval ABOVE zero.
Folds won are reported as support. Anything else - better on average but
not clearly - does not join.
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
import feasibility_test as FT  # noqa: E402

CODE_VERSION = "specialist_test v1"
CFG = {"n_splits": 5, "embargo": 5, "min_train_frac": 0.35, "fit_cap": 400_000,
       "min_state_rows": 30_000, "k_range": list(range(3, 11)),
       "gmm_select_rows": 60_000, "gmm_fit_rows": 200_000,
       "top_n": (1, 3, 5, 10), "primary_top_n": 3, "seed": 7, "hgb": None}


def _log(msg):
    print(f"{dt.datetime.now():%H:%M:%S}  {msg}", flush=True)


def _model(cfg):
    if cfg.get("hgb"):
        from sklearn.ensemble import HistGradientBoostingClassifier
        return HistGradientBoostingClassifier(random_state=cfg["seed"], **cfg["hgb"])
    import regime_research as RR          # the settings the forward candidates use
    return RR._hgb(cfg["seed"])


def _gain_importance(model, names, top: int = 10):
    """
    Share of the model's total split gain earned by each feature - which
    features the trees actually leaned on. Reads fitted trees (scikit-learn
    internals); descriptive only, never used for any decision. Returns [] if
    unavailable.
    """
    try:
        g = np.zeros(len(names))
        for it in model._predictors:
            nd = it[0].nodes
            sp = nd["is_leaf"] == 0
            np.add.at(g, nd["feature_idx"][sp], nd["gain"][sp])
        tot = g.sum()
        if tot <= 0:
            return []
        return [(names[i], float(g[i] / tot)) for i in np.argsort(-g)[:top]]
    except Exception:
        return []


def _profile(mean_vec, st_names, n: int = 3):
    """A state's most distinctive traits, from its centroid in rank units."""
    order = np.argsort(-np.abs(mean_vec))[:n]
    return [f"{'high' if mean_vec[i] > 0 else 'low'} {st_names[i][3:]}" for i in order]


def run(panel_path: Path, cost_bps: float = 35.0, overrides: dict | None = None,
        verbose: bool = True) -> dict:
    import pyarrow.parquet as pq
    import panel_build as PB
    t0 = time.perf_counter()
    cfg = {**CFG, **(overrides or {})}

    schema = pq.ParquetFile(panel_path).schema_arrow.names
    feats = [c for c in PB.panel_feature_columns(pd.DataFrame(columns=schema))
             if c not in ("open", "high", "low", "close", "volume")]
    RC.assert_no_label_leak(feats, "specialist_test")

    ts_all = pd.to_datetime(pd.read_parquet(panel_path, columns=["timestamp"])["timestamp"])
    if getattr(ts_all.dt, "tz", None) is not None:
        ts_all = ts_all.dt.tz_localize(None)
    research_end, lockbox_start = RC.lockbox_bounds(np.sort(ts_all.unique()),
                                                    RC.DEFAULT_LOCKBOX_FRACTION,
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
    date_code = np.searchsorted(sessions, ts)
    X = p[feats]

    Xst, st_names, st_missing = RC.stock_state(
        lambda c: pd.to_numeric(p[c], errors="coerce").to_numpy() if c in p.columns else None,
        date_code)
    _log(f"{int(ok.sum()):,} labelled research rows | stock state: {len(st_names)} dims"
         + (f" (missing {st_missing})" if st_missing else ""))

    sp = FT.splits(sessions, cfg["n_splits"], cfg["embargo"], cfg["min_train_frac"])
    rng = np.random.default_rng(cfg["seed"])
    tr0 = np.where(ok & (ts <= sp[0]["train_end"]))[0]
    sel = rng.choice(tr0, min(cfg["gmm_select_rows"], len(tr0)), replace=False)
    K, bic = RC.choose_k_bic(Xst, cfg["k_range"], sel, cfg["seed"])
    _log(f"stock states: K={K} by BIC on fold-1 training rows (held fixed)")

    preds = {"M0": [], "SPECIALIST": []}
    folds, routing = [], []
    for s in sp:
        tf = time.perf_counter()
        tr_all = np.where(ok & (ts <= s["train_end"]))[0]
        te = np.where(ok & (ts >= s["test_start"]) & (ts <= s["test_end"]))[0]
        # --- M0
        tr = tr_all if len(tr_all) <= cfg["fit_cap"] else np.sort(
            rng.choice(tr_all, cfg["fit_cap"], replace=False))
        m0 = _model(cfg).fit(X.iloc[tr].to_numpy("float32"), tp[tr].astype(int))
        s_m0 = m0.predict_proba(X.iloc[te].to_numpy("float32"))[:, 1]
        # --- states from THIS fold's training rows only
        gsel = rng.choice(tr_all, min(cfg["gmm_fit_rows"], len(tr_all)), replace=False)
        gm = RC.fit_state_gmm(Xst, K, gsel, cfg["seed"])
        st_tr = RC.gmm_proba(gm, Xst[tr_all]).argmax(axis=1)
        st_te = RC.gmm_proba(gm, Xst[te]).argmax(axis=1)
        s_sp = s_m0.copy()                    # thin states keep the M0 score
        last = s["fold"] == sp[-1]["fold"]
        if last:
            state_report = {"fold": s["fold"], "test": f"{pd.Timestamp(s['test_start']).date()}.."
                                                      f"{pd.Timestamp(s['test_end']).date()}",
                            "m0_top": _gain_importance(m0, feats), "states": []}
        own, fell_back = 0, 0
        for k in range(K):
            rows_k = tr_all[st_tr == k]
            te_k = np.where(st_te == k)[0]
            if len(te_k) == 0:
                continue
            if len(rows_k) < cfg["min_state_rows"] or len(np.unique(tp[rows_k])) < 2:
                fell_back += len(te_k)
                if last:
                    state_report["states"].append({
                        "state": k, "share_of_stocks": len(te_k) / len(te),
                        "profile": _profile(gm.means_[k], st_names), "own_model": False,
                        "top_features": [], "overlap_with_m0_top10": None})
                continue
            if len(rows_k) > cfg["fit_cap"]:
                rows_k = np.sort(rng.choice(rows_k, cfg["fit_cap"], replace=False))
            mk = _model(cfg).fit(X.iloc[rows_k].to_numpy("float32"), tp[rows_k].astype(int))
            s_sp[te_k] = mk.predict_proba(X.iloc[te[te_k]].to_numpy("float32"))[:, 1]
            own += len(te_k)
            if last:
                imp = _gain_importance(mk, feats)
                m0set = {f for f, _ in state_report["m0_top"]}
                state_report["states"].append({
                    "state": k, "share_of_stocks": len(te_k) / len(te),
                    "profile": _profile(gm.means_[k], st_names), "own_model": True,
                    "top_features": imp,
                    "overlap_with_m0_top10": (len({f for f, _ in imp} & m0set) / 10
                                              if imp and m0set else None)})
        routing.append({"fold": s["fold"], "own_model_share": own / max(len(te), 1),
                        "fallback_share": fell_back / max(len(te), 1)})
        row = {"fold": s["fold"], "test": f"{pd.Timestamp(s['test_start']).date()}.."
                                          f"{pd.Timestamp(s['test_end']).date()}"}
        for nm, sc in (("M0", s_m0), ("SPECIALIST", s_sp)):
            d = pd.DataFrame({"timestamp": ts[te], "p_raw": sc, "exit_ret": er[te],
                              "y": (er[te] - cost_bps / 1e4 > 0).astype(float)})
            preds[nm].append(d)
            e3 = RC.topn_evidence(d, cfg["primary_top_n"], cost_bps=cost_bps, B=300,
                                  seed=cfg["seed"], score_col="p_raw")
            row[f"{nm}_top3_net"] = e3["net"]["mean"]
            row[f"{nm}_ic"] = FT.rank_ic_by_date(ts[te], sc, er[te])
        folds.append(row)
        _log(f"fold {s['fold']} {row['test']}: top-3 net M0 {row['M0_top3_net']*1e4:+.0f}bp / "
             f"specialist {row['SPECIALIST_top3_net']*1e4:+.0f}bp | own-state models scored "
             f"{routing[-1]['own_model_share']:.0%} of stocks ({time.perf_counter()-tf:.0f}s)")

    res = {"code": CODE_VERSION, "built_at": dt.datetime.now().isoformat(),
           "cost_bps": cost_bps, "research_end": str(pd.Timestamp(research_end).date()),
           "K": int(K), "bic": bic, "folds": folds, "routing": routing}
    res.update(evaluate(preds, folds, cost_bps, cfg))
    res["state_report"] = state_report
    res["minutes"] = round((time.perf_counter() - t0) / 60, 1)

    out = panel_path.parent / "specialist"
    out.mkdir(parents=True, exist_ok=True)
    (out / "specialist.json").write_text(json.dumps(res, indent=2, default=str), encoding="utf-8")
    RC.ledger_append(panel_path, {"kind": "exploration", "tool": CODE_VERSION,
                                  "joins_forward_test": res["joins_forward_test"],
                                  "research_end": res["research_end"]})
    if verbose:
        _print(res)
    return res


def evaluate(preds: dict, folds: list, cost_bps: float, cfg: dict) -> dict:
    """Pooled evidence and THE RULE. Separate so the decision can be tested directly."""
    res = {"pooled": {}}
    net_day, uni = {}, None
    for nm, parts in preds.items():
        d = pd.concat(parts, ignore_index=True)
        d["net"] = d["exit_ret"] - cost_bps / 1e4
        if uni is None:
            uni = d.groupby("timestamp")["net"].mean().sort_index()
            res["universe"] = RC.block_bootstrap_mean(uni.to_numpy(), seed=cfg["seed"])
        ev = {int(n): RC.topn_evidence(d, n, cost_bps=cost_bps, seed=cfg["seed"],
                                       score_col="p_raw") for n in cfg["top_n"]}
        ex = {}
        for n in cfg["top_n"]:
            top = RC.daily_topn_values(d, n, "net", "p_raw")
            ex[int(n)] = RC.block_bootstrap_mean((top - uni.reindex(top.index)).dropna().to_numpy(),
                                                 seed=cfg["seed"])
        net_day[nm] = RC.daily_topn_values(d, cfg["primary_top_n"], "net", "p_raw")
        res["pooled"][nm] = {"rank_ic": FT.rank_ic_by_date(d["timestamp"], d["p_raw"],
                                                           d["exit_ret"]),
                             "topn": ev, "excess": ex}
    diff = (net_day["SPECIALIST"] - net_day["M0"].reindex(net_day["SPECIALIST"].index)).dropna()
    res["specialist_minus_m0"] = RC.block_bootstrap_mean(diff.to_numpy(), seed=cfg["seed"])
    res["folds_won"] = int(sum(f["SPECIALIST_top3_net"] > f["M0_top3_net"] for f in folds))
    dm = res["specialist_minus_m0"]
    res["joins_forward_test"] = bool(np.isfinite(dm["lo"]) and dm["lo"] > 0)
    return res


def _f(e):
    return f"{e['mean']*1e4:+5.0f} [{e['lo']*1e4:+4.0f},{e['hi']*1e4:+4.0f}]"


def _print(res):
    print("\n" + "=" * 78)
    print(f"  ONE MODEL PER STATE vs ONE MODEL FOR ALL - research only, net of "
          f"{res['cost_bps']:.0f} bp, K={res['K']} states")
    print("=" * 78)
    print(f"  buy everything: {_f(res['universe'])} bp per trade")
    print(f"\n  {'':<12}{'rank IC':>9}" + "".join(f"{'top-'+str(n)+' net':>20}" for n in (1, 3, 5, 10)))
    for nm in ("M0", "SPECIALIST"):
        r = res["pooled"][nm]
        print(f"  {nm:<12}{r['rank_ic']:>+9.4f}" + "".join(
            f"{_f(r['topn'][n]['net']):>20}" for n in (1, 3, 5, 10)))
    print(f"\n  excess over buy-everything, top-3:  M0 {_f(res['pooled']['M0']['excess'][3])} | "
          f"specialist {_f(res['pooled']['SPECIALIST']['excess'][3])}")
    sh = np.mean([r["own_model_share"] for r in res["routing"]])
    print(f"  stocks scored by their own state's model: {sh:.0%} (the rest fell back to M0)")
    print("  per fold, top-3 net bp:  " + " | ".join(
        f"F{f['fold']} M0 {f['M0_top3_net']*1e4:+.0f} / S {f['SPECIALIST_top3_net']*1e4:+.0f}"
        for f in res["folds"]))
    sr = res.get("state_report")
    if sr and sr["m0_top"]:
        print(f"\n  WHAT EACH MODEL LEANS ON - fold {sr['fold']} ({sr['test']}), share of split gain")
        print("  (descriptive only; it does not affect the result)")
        print("  M0 (all stocks): " + ", ".join(f"{f} {w:.0%}" for f, w in sr["m0_top"][:5]))
        for st in sorted(sr["states"], key=lambda x: -x["share_of_stocks"]):
            head = (f"  S{st['state']} ({st['share_of_stocks']:.0%} of stocks; "
                    f"{', '.join(st['profile'])})")
            if not st["own_model"]:
                print(head + ": too thin - scored by M0")
                continue
            ov = st["overlap_with_m0_top10"]
            print(head + (f" | top-10 shared with M0: {ov:.0%}" if ov is not None else ""))
            print("      " + ", ".join(f"{f} {w:.0%}" for f, w in st["top_features"][:5]))
    print("\n" + "-" * 78)
    print(f"  RULE: specialist top-3 minus M0 top-3, day by day, 95% interval above zero")
    print(f"  specialist minus M0: {_f(res['specialist_minus_m0'])} bp | folds won "
          f"{res['folds_won']}/{len(res['folds'])}")
    print("  RESULT: " + ("JOINS the forward paper test" if res["joins_forward_test"] else
                          "does NOT join - not clearly better than one model for all"))
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
