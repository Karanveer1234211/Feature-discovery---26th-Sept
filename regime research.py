#!/usr/bin/env python3
"""
regime_research.py - regime + feature discovery, resumable and versioned.

    python regime_research.py run    --root <cache_root>
    python regime_research.py run    --root <cache_root> --resume RUN_20260923_001
    python regime_research.py report --root <cache_root> --run RUN_20260923_001
    python regime_research.py list   --root <cache_root>

WHAT THIS ANSWERS
=================
Does knowing the STATE of a stock and the market make it more predictable -
and if so, is that because regimes carry signal, because features behave
differently per regime, or because some regimes are simply tradeable and
others are not?

Four nested models, identical folds, identical seed:

    M1  base features
    M2  M1 + regime probabilities + state scores + market state
    M3  M2 + surviving feature families
    M4  M3 + explicit regime x feature interactions

Each is judged on the same economic test as base_model: does the DAILY TOP-N
- what you would actually trade - clear breakeven net of costs? AUC is
reported, but it is not the verdict.

DESIGN DECISIONS THAT DEPART FROM THE BRIEF, AND WHY
====================================================
1. No per-regime feature SETS. Selecting features separately inside each of
   eight regimes cuts every selection's sample by ~8x and multiplies the
   number of tests by 8x - the most reliable way there is to manufacture
   regime-specific "findings" from noise. A gradient-boosted tree given
   regime probabilities learns regime-conditional behaviour itself, from all
   the data. The feature-by-regime matrix is still produced, as DESCRIPTION.

2. Regimes are tested as a TRADE FILTER, not only as features. If the model
   clears breakeven in R4 and R6 and nowhere else, "trade only there" is an
   edge even with zero AUC improvement.

3. Families, not features. Permutation importance has a known flaw: two
   features carrying the same information both look unimportant, because the
   model falls back on the other. That is what collapsed the audit's KEEP
   set - D_atr_ratio_14_30 and X_rank_D_realvol_ratio_20_60 split the credit.
   Features are clustered into families per fold and each family is permuted
   JOINTLY, so shared information is credited once.

4. One fit per fold, not greedy refits. Greedy took 44 minutes for 15
   candidates; at 255 it would take days. Grouped permutation importance on
   an inner validation split costs predictions, not fits.

5. K is chosen by BIC inside each fold. Choosing the number of regimes is
   model selection, and model selection on test data is leakage.

WHAT IT PRESERVES FROM THE BRIEF
--------------------------------
Every stock-day gets a regime with a probability vector; regimes use only
information at T and never the target; K is an output; persistence is
measured, never imposed; market context is tested rather than assumed; every
phase checkpoints and resumes; runs are versioned and never overwritten; a
run refuses to resume against a panel whose build signature has changed.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sys
import time
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
warnings.filterwarnings("ignore", category=RuntimeWarning)

CODE_VERSION = "regime_research v8"

import research_common as RC

DEFAULTS = {
    "target": "label_tp_before_sl",
    "n_splits": 5,
    "k_range": [3, 4, 5, 6, 7, 8, 9, 10],
    "gmm_fit_rows": 150_000,
    "gmm_select_rows": 40_000,
    "fit_cap": 400_000,
    "val_fraction": 0.20,
    "val_rows": 60_000,
    # 50 sentinels x 5 repeats: the null's tail is estimated from its own
    # spread, and 12 draws cannot pin a 3-sigma tail. Costs compute, not
    # correctness. "Beats null" remains a SCREEN, not a significance test.
    "perm_repeats": 5,
    "family_corr": 0.70,
    "n_sentinels": 50,
    "null_sigmas": 3.0,
    "min_fold_survival": 0.8,   # family must beat the null in >=80% of folds
    "calib_fraction": 0.25,
    "embargo": 5,
    # No breakeven constant: with ATR-scaled barriers each trade's payoff is
    # set by its own stock's volatility, so no single probability is right.
    # Evidence is net return per trade = label_exit_ret - cost.
    "cost_bps": 35.0,
    "boot_B": 2000,
    "min_regime_dates": 150,
    "top_n": [1, 3, 5, 10],
    "max_family_reps": 25,
    "seed": 0,
    "horizon": 5,
    "lockbox_fraction": RC.DEFAULT_LOCKBOX_FRACTION,
}

# Inputs to the stock-state vector. Ranked WITHIN EACH DATE, so the state is
# "where this stock sits among its peers today" - point-in-time by
# construction, and comparable across a smallcap and a large cap.
# Canonical state lives in research_common; this alias is read-only.
STATE_INPUTS = {nm: col for nm, (_, col, _) in zip(RC.STOCK_STATE_NAMES,
                                                   RC.STOCK_STATE_SPEC)}

DEFAULT_BASE = ["D_rsi14", "D_atr_pct", "D_ema20_angle_deg",
                "D_dvol_z20", "D_pos_in_52w_range"]


# ======================================================================
# RUN MANAGEMENT - checkpointing, versioning, provenance
# ======================================================================
class RunConflict(RuntimeError):
    pass


def _sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str)
                          .encode()).hexdigest()[:16]


class Run:
    """
    A research run: one directory, one config, one data fingerprint.

    A checkpoint is valid only for the exact (config, panel) it was produced
    under. Resuming against a rebuilt panel or a changed config is refused
    rather than silently mixing results from two different experiments.
    """

    def __init__(self, base: Path, run_id: str, config: dict, fingerprint: dict):
        self.dir = Path(base) / run_id
        self.dir.mkdir(parents=True, exist_ok=True)
        self.run_id = run_id
        self.config = config
        self.fingerprint = fingerprint
        self.hash = _sha({"config": config, "data": fingerprint,
                          "code": CODE_VERSION})
        cfg = self.dir / "config.json"
        if cfg.exists():
            old = json.loads(cfg.read_text(encoding="utf-8"))
            if old.get("hash") != self.hash:
                diffs = [k for k in set(config) | set(old.get("config", {}))
                         if config.get(k) != old.get("config", {}).get(k)]
                data_changed = old.get("fingerprint") != fingerprint
                raise RunConflict(
                    f"{run_id} was created under a different "
                    f"{'panel' if data_changed else 'config'}"
                    + (f" (changed: {diffs})" if diffs else "") +
                    ". Refusing to resume - results from two experiments "
                    "would mix. Start a new run instead.")
        else:
            cfg.write_text(json.dumps({
                "run_id": run_id, "hash": self.hash, "code": CODE_VERSION,
                "created": dt.datetime.now().isoformat(),
                "config": config, "fingerprint": fingerprint,
            }, indent=2, default=str), encoding="utf-8")

    def path(self, *parts) -> Path:
        p = self.dir.joinpath(*parts)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def done(self, key: str) -> bool:
        m = self.dir / "checkpoints" / f"{key}.done"
        if not m.exists():
            return False
        try:
            return json.loads(m.read_text(encoding="utf-8")).get("hash") == self.hash
        except Exception:
            return False

    def mark(self, key: str, **meta) -> None:
        self.path("checkpoints", f"{key}.done").write_text(json.dumps(
            {"hash": self.hash, "at": dt.datetime.now().isoformat(), **meta},
            indent=2, default=str), encoding="utf-8")

    def log(self, msg: str) -> None:
        line = f"{dt.datetime.now():%H:%M:%S}  {msg}"
        print(line, flush=True)
        with open(self.dir / "run.log", "a", encoding="utf-8") as f:
            f.write(line + "\n")


def new_run_id(base: Path) -> str:
    base.mkdir(parents=True, exist_ok=True)
    day = dt.date.today().strftime("%Y%m%d")
    n = 1 + max([int(p.name.rsplit("_", 1)[-1]) for p in base.glob(f"RUN_{day}_*")
                 if p.name.rsplit("_", 1)[-1].isdigit()] or [0])
    return f"RUN_{day}_{n:03d}"


def fingerprint(panel_path: Path) -> dict:
    """What the results depend on. A rebuilt panel invalidates every phase."""
    meta_p = panel_path.parent / "panel_meta.json"
    meta = json.loads(meta_p.read_text(encoding="utf-8")) if meta_p.exists() else {}
    st = panel_path.stat()
    return {"panel": str(panel_path), "size": st.st_size,
            "build_signature": meta.get("build_signature"),
            "rows": meta.get("rows"), "last_session": meta.get("last_session")}


# ======================================================================
# PHASE 1 - STATE SCORES (per date, point-in-time)
# ======================================================================
def _codes(p: pd.DataFrame):
    ts = pd.to_datetime(p["timestamp"]).to_numpy()
    sessions = np.unique(ts)
    date_code = np.searchsorted(sessions, ts)
    sym_code = pd.factorize(p["symbol"])[0]
    return sessions, date_code, RC.session_segments(date_code, sym_code)


def state_scores(p: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """Canonical stock state (research_common.stock_state)."""
    _, date_code, _ = _codes(p)
    X, names, missing = RC.stock_state(
        lambda c: pd.to_numeric(p[c], errors="coerce").to_numpy() if c in p.columns else None,
        date_code)
    if missing:
        print(f"    WARNING: stock-state inputs missing {missing}; "
              f"{len(names)} of {len(RC.STOCK_STATE_SPEC)} dimensions used", flush=True)
    return pd.DataFrame(X, columns=names, index=p.index), names


def market_state(p: pd.DataFrame) -> pd.DataFrame:
    """Canonical market state (research_common.market_state), one row per date."""
    sessions, date_code, seg = _codes(p)
    mk = RC.market_state(pd.to_numeric(p["close"], errors="coerce").to_numpy(),
                         date_code, seg, len(sessions))
    out = pd.DataFrame({k: v.astype("float32") for k, v in mk.items()})
    out.insert(0, "timestamp", sessions)
    return out


# ======================================================================
# PHASE 2 - REGIME ENGINE (fold-local; reusable by downstream models)
# ======================================================================
def fit_regime_engine(X: np.ndarray, k_range: Sequence[int], *, select_rows: int,
                      fit_rows: int, seed: int = 0,
                      k_fixed: Optional[int] = None) -> dict:
    """
    Fit a Gaussian mixture on TRAIN state vectors, choosing K by BIC.

    This is the public entry point for any later model that wants regime
    features: fit on its own training window, apply to its own test window.
    Never fit on data the downstream model will be scored on.
    """
    from sklearn.mixture import GaussianMixture
    # BIC answers "which mixture DESCRIBES this state distribution best" -
    # a clustering criterion, not evidence of predictive use (that is M2 vs
    # M1). K is chosen once on fold 1 and held fixed so IDs can be aligned.
    rng = np.random.default_rng(seed)
    ok = np.where(np.isfinite(X).all(axis=1))[0]
    if len(ok) < 1000:
        raise RuntimeError(f"only {len(ok)} complete state vectors to fit on")
    sel = rng.choice(ok, min(select_rows, len(ok)), replace=False)
    best_k, bics = RC.choose_k_bic(X, [k_fixed] if k_fixed else k_range, sel, seed)
    fit = rng.choice(ok, min(fit_rows, len(ok)), replace=False)
    gm = RC.fit_state_gmm(X, best_k, fit, seed)
    return {"gmm": gm, "k": best_k, "bic": bics}


def apply_regime_engine(engine: dict, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Every row gets a regime, and a row with missing inputs is scored on the
    inputs it HAS (research_common.gmm_proba) - never imputed. v1 replaced
    missing values with 0, which claimed "average" where the truth is
    "unknown"; on a test case that produced 82% confidence in an arbitrary
    regime. A row missing everything now gets the prior weights.

    `perm` (from alignment) reorders columns so column k is reference regime
    k in every fold.
    """
    proba = RC.gmm_proba(engine["gmm"], X)
    if engine.get("perm") is not None:
        proba = RC.permute_proba(proba, engine["perm"])
    proba = proba.astype("float32")
    hard = proba.argmax(axis=1).astype("int16")
    conf = proba.max(axis=1).astype("float32")
    return proba, hard, conf


# ======================================================================
# FOLD HELPERS
# ======================================================================
def _split_train(ts: pd.Series, sessions: np.ndarray, train_end: pd.Timestamp,
                 frac: float, embargo: int) -> Tuple[np.ndarray, np.ndarray]:
    """Split a train window into (earlier part, held-out tail) with an embargo."""
    tr_sess = sessions[sessions <= np.datetime64(train_end)]
    cut = max(1, int(len(tr_sess) * (1 - frac)))
    a_end = pd.Timestamp(tr_sess[cut - 1])
    b_start = pd.Timestamp(tr_sess[min(cut - 1 + embargo, len(tr_sess) - 1)])
    a = (ts <= a_end).to_numpy()
    b = ((ts >= b_start) & (ts <= train_end)).to_numpy()
    return a, b


def _gather(p: pd.DataFrame, ex: dict, cols: Sequence[str], idx) -> np.ndarray:
    """
    Build a float32 (len(idx) x len(cols)) matrix one column at a time.

    THIS IS THE 9 GB FIX. The previous code did `p.iloc[idx][cols]`, which
    copies EVERY column of the panel for those rows before selecting, and
    widened the full 1.95M-row frame through repeated concat/merge until
    pandas consolidated ~600 columns into one float64 block (~9.4 GB).
    Here each column is read as a view, indexed, and written into a
    preallocated float32 array; nothing wider than one column exists.
    Extra columns (state, market, regime) live in `ex` as numpy arrays and
    are never attached to the panel at all.
    """
    idx = np.asarray(idx)
    out = np.empty((len(idx), len(cols)), dtype="float32")
    for j, c in enumerate(cols):
        src = ex[c] if c in ex else p[c].to_numpy()
        out[:, j] = src[idx]
    return out


def _hgb(seed: int = 0):
    from sklearn.ensemble import HistGradientBoostingClassifier
    return HistGradientBoostingClassifier(
        max_iter=300, max_depth=5, learning_rate=0.06, min_samples_leaf=200,
        l2_regularization=1.0, early_stopping=False, random_state=seed)


def _families(Xfit: pd.DataFrame, cols: List[str], thresh: float,
              rows: int, seed: int) -> Dict[str, int]:
    """
    Group features whose |Spearman| >= thresh on THIS fold's fit data.

    Spearman rather than Pearson, so a raw feature and its rank transform -
    monotone but not linear - land in the same family. That is precisely the
    pair that split credit in the feature audit.
    """
    samp = Xfit[cols]
    if len(samp) > rows:
        samp = samp.sample(rows, random_state=seed)
    corr = samp.rank().corr().abs().fillna(0.0).to_numpy()
    fam = {}
    fid = 0
    unassigned = list(range(len(cols)))
    while unassigned:
        i = unassigned.pop(0)
        members = [i] + [j for j in unassigned if corr[i, j] >= thresh]
        unassigned = [j for j in unassigned if j not in members]
        for m in members:
            fam[cols[m]] = fid
        fid += 1
    return fam


def _grouped_perm_importance_slow(model, Xv: np.ndarray, yv: np.ndarray,
                                  groups: Dict[int, List[int]], repeats: int,
                                  rng) -> Tuple[float, Dict[int, float]]:
    """Reference implementation: AUC drop when a whole family is shuffled together."""
    from sklearn.metrics import roc_auc_score
    base = float(roc_auc_score(yv, model.predict_proba(Xv)[:, 1]))
    out = {}
    X = Xv.copy()
    for gid, idx in groups.items():
        orig = X[:, idx].copy()
        drops = []
        for _ in range(repeats):
            perm = rng.permutation(len(X))
            X[:, idx] = orig[perm]
            drops.append(base - float(roc_auc_score(
                yv, model.predict_proba(X)[:, 1])))
        X[:, idx] = orig
        out[gid] = float(np.mean(drops))
    return base, out


SCREEN_PATH = {"fast": 0, "reference": 0}


class _TreeCache:
    """
    Per-tree contributions of a fitted HistGradientBoostingClassifier.

    Shuffling one family of columns can only change the trees that SPLIT on
    those columns; every other tree returns exactly what it returned before.
    So each tree's contribution is computed once, and a shuffle recomputes
    only the affected trees, then re-adds all contributions in scikit-learn's
    own order (baseline, then tree 1, 2, 3, ...). Same float64 operations in
    the same order -> bit-identical probabilities.

    Uses scikit-learn internals, so it proves itself before use: the full
    reconstruction must equal predict_proba EXACTLY on the unshuffled data,
    or the caller falls back to the reference implementation.
    """

    def __init__(self, model, X64: np.ndarray):
        from sklearn.utils._openmp_helpers import _openmp_effective_n_threads
        if getattr(model, "n_trees_per_iteration_", 1) != 1:
            raise ValueError("binary models only")
        self.m, self.nt = model, _openmp_effective_n_threads()
        self.trees = [it[0] for it in model._predictors]
        self.uses = [set(np.unique(t.nodes["feature_idx"][t.nodes["is_leaf"] == 0]).tolist())
                     for t in self.trees]
        self.base_contrib = np.stack([self._one(t, X64) for t in self.trees])
        self.baseline = model._baseline_prediction

    def _one(self, tree, X64):
        buf = np.zeros((X64.shape[0], 1), dtype=self.m._baseline_prediction.dtype, order="F")
        self.m._predict_iterations(X64, [[tree]], buf, False, self.nt)
        return buf[:, 0].copy()

    def proba(self, X64: np.ndarray, changed: Optional[set] = None) -> np.ndarray:
        raw = np.zeros((X64.shape[0], 1), dtype=self.baseline.dtype, order="F")
        raw += self.baseline
        for t, tree in enumerate(self.trees):
            if changed is not None and self.uses[t] & changed:
                raw[:, 0] += self._one(tree, X64)
            else:
                raw[:, 0] += self.base_contrib[t]
        return self.m._loss.predict_proba(raw)[:, 1]


def _grouped_perm_importance(model, Xv: np.ndarray, yv: np.ndarray,
                             groups: Dict[int, List[int]], repeats: int,
                             rng) -> Tuple[float, Dict[int, float]]:
    """
    AUC drop when a whole family is shuffled together - FAST PATH.

    Identical results to _grouped_perm_importance_slow: same permutations
    drawn in the same order, bit-identical probabilities (see _TreeCache).
    Verified twice before trusting it; any mismatch or error -> slow path,
    with the RNG untouched so the draws stay the same.
    """
    from sklearn.metrics import roc_auc_score
    X64 = np.ascontiguousarray(Xv, dtype=np.float64)
    try:
        cache = _TreeCache(model, X64)
        ref = model.predict_proba(Xv)[:, 1]
        if not np.array_equal(cache.proba(X64), ref):
            raise ValueError("reconstruction differs from predict_proba")
        # second proof, on a real shuffle, using a COPY of the RNG so the
        # draws the screen actually uses are unaffected
        gid0 = next(iter(groups))
        probe_rng = np.random.default_rng()
        probe_rng.bit_generator.state = rng.bit_generator.state
        Xp = X64.copy()
        Xp[:, groups[gid0]] = X64[probe_rng.permutation(len(Xp))][:, groups[gid0]]
        if not np.array_equal(cache.proba(Xp, set(groups[gid0])),
                              model.predict_proba(Xp)[:, 1]):
            raise ValueError("shuffled reconstruction differs")
        del Xp
    except Exception:
        SCREEN_PATH["reference"] += 1
        return _grouped_perm_importance_slow(model, Xv, yv, groups, repeats, rng)
    SCREEN_PATH["fast"] += 1

    base = float(roc_auc_score(yv, ref))
    out = {}
    X = X64.copy()
    for gid, idx in groups.items():
        orig = X[:, idx].copy()
        changed = set(idx)
        drops = []
        for _ in range(repeats):
            perm = rng.permutation(len(X))
            X[:, idx] = orig[perm]
            drops.append(base - float(roc_auc_score(yv, cache.proba(X, changed))))
        X[:, idx] = orig
        out[gid] = float(np.mean(drops))
    return base, out


# ======================================================================
# THE PIPELINE
# ======================================================================
def run(panel_path, *, run_id: Optional[str] = None, resume: Optional[str] = None,
        overrides: Optional[dict] = None, verbose: bool = True) -> Path:
    import panel_build as PB
    import feature_audit as FA
    import base_model as BM

    panel_path = Path(panel_path)
    cfg = {**DEFAULTS, **(overrides or {})}
    base_dir = panel_path.parent / "research"
    rid = resume or run_id or new_run_id(base_dir)
    R = Run(base_dir, rid, cfg, fingerprint(panel_path))
    R.log(f"=== {rid} ({'resume' if resume else 'new'}) ===")
    rng = np.random.default_rng(cfg["seed"])
    t_all = time.perf_counter()

    # ---------------------------------------------------------- PHASE 0
    R.log("[0] load + validate")
    p = pd.read_parquet(panel_path)
    p["timestamp"] = pd.to_datetime(p["timestamp"]).dt.tz_localize(None)
    # build_panel already writes (timestamp, symbol) order. Sorting anyway
    # copies the ENTIRE panel - at 1.95M x 200 that is another ~1.6 GB - so
    # check first and only pay for it when the file is genuinely unsorted.
    order = np.lexsort((p["symbol"].astype(str).to_numpy(),
                        p["timestamp"].to_numpy()))
    if not np.array_equal(order, np.arange(len(p))):
        p = p.take(order).reset_index(drop=True)
    del order
    tgt = cfg["target"]
    if tgt not in p.columns:
        raise SystemExit(f"target {tgt} not in panel")
    y = pd.to_numeric(p[tgt], errors="coerce")
    ts = p["timestamp"]
    sessions = np.sort(ts.unique())
    H = cfg["horizon"]

    # LOCKBOX - the final period no research step may touch. Shared with the
    # feature atlas through research_common so one tool's lockbox is never
    # another tool's research data.
    research_end, lb_start = RC.lockbox_bounds(sessions, cfg["lockbox_fraction"], H)
    research = (ts <= pd.Timestamp(research_end)).to_numpy()
    lockbox = ((ts >= pd.Timestamp(lb_start)).to_numpy() if lb_start is not None
               else np.zeros(len(p), bool))
    R.log(f"    research <= {pd.Timestamp(research_end).date()} | lockbox "
          + (f">= {pd.Timestamp(lb_start).date()} ({lockbox.mean():.1%} of rows) "
             f"- untouched until the hypothesis is locked"
             if lb_start is not None else "DISABLED"))
    # TIMING CONTRACT - checked against the data. Refuses to run if the
    # target turns out to include session T.
    sym_code = pd.factorize(p["symbol"])[0]
    if "close" in p.columns:
        fwd = (pd.to_numeric(p["label_fwd_ret_5d"], errors="coerce").to_numpy()
               if "label_fwd_ret_5d" in p.columns
               else RC.forward_return_for_check(p["close"].to_numpy(), sym_code, H))
        # research rows only: even a pass/fail check should not read the lockbox
        timing = RC.assert_timing_contract(p["close"].to_numpy()[research],
                                           sym_code[research], fwd[research])
        R.log(f"    timing contract OK: corr(fwd, same day) "
              f"{timing['corr_fwd_vs_same_day']:+.3f}, corr(fwd, next day) "
              f"{timing['corr_fwd_vs_next_day']:+.3f}")
    else:
        timing = {"skipped": "no close column"}
        R.log("    WARNING: no close column - timing contract NOT checked")

    if not R.done("p0"):
        R.mark("p0", rows=len(p), symbols=int(p["symbol"].nunique()),
               first=str(ts.min().date()), last=str(ts.max().date()),
               base_rate=float(y[research].mean()), timing=timing,
               research_end=str(research_end), lockbox_start=str(lb_start))

    # ---------------------------------------------------------- PHASE 1
    ss_p = R.path("p1_state.parquet")
    if R.done("p1"):
        R.log("[1] state scores: checkpoint found, loading")
        ss = pd.read_parquet(ss_p)
        st_cols = [c for c in ss.columns if c.startswith("st_")]
        mk = pd.read_parquet(R.path("p1_market.parquet"))
    else:
        R.log("[1] state scores + market state")
        ss, st_cols = state_scores(p)
        mk = market_state(p)
        ss.to_parquet(ss_p, index=False)
        mk.to_parquet(R.path("p1_market.parquet"), index=False)
        R.mark("p1", state_cols=st_cols, market_cols=list(mk.columns),
               state_engine=RC.STATE_ENGINE_VERSION)
    # Extras live in a dict of float32 arrays, NOT as new panel columns:
    # every concat/merge onto a 1.95M-row frame is a full copy, and pandas
    # later consolidates same-dtype blocks - the route to a 9 GB allocation.
    ex: Dict[str, np.ndarray] = {c: ss[c].to_numpy(dtype="float32") for c in st_cols}
    del ss
    mk_cols = [c for c in mk.columns if c.startswith("mk_")]
    if mk_cols:
        pos = pd.Index(pd.to_datetime(mk["timestamp"])).get_indexer(p["timestamp"])
        for c in mk_cols:
            v = mk[c].to_numpy(dtype="float32")
            ex[c] = np.where(pos >= 0, v[np.clip(pos, 0, None)], np.nan).astype("float32")

    # candidate universe (reuses the audited hygiene + dedup)
    base_feats = [c for c in DEFAULT_BASE if c in p.columns]
    af = panel_path.parent / "audit" / "approved_features.json"
    if af.exists():
        b = json.loads(af.read_text(encoding="utf-8")).get("base")
        if b:
            base_feats = [c for c in b if c in p.columns]
    der, der_names = FA.derive(p, verbose=False)
    for c in der_names:
        ex[c] = der[c].to_numpy(dtype="float32")
    del der
    if not R.done("p1b"):
        cand = [c for c in PB.panel_feature_columns(p)
                if pd.api.types.is_numeric_dtype(p[c])
                and not c.startswith(("st_", "mk_"))] + der_names
        cand = list(dict.fromkeys(cand))
        # Hygiene and duplicate detection on a DATE SUBSAMPLE. find_duplicates
        # ran .apply(pd.to_numeric) over the full panel before sampling - a
        # ~3 GB float64 copy on its own. Whole dates are kept so nothing
        # cross-sectional is distorted.
        # Hygiene needs coverage and constancy, not a big sample: cap at
        # ~200k rows of whole dates. 400 dates x 1,500 stocks x 260 cols
        # would otherwise be another ~600 MB for a check that 150 dates
        # answers just as well.
        # RESEARCH DATES ONLY. v2 sampled from every date, so hygiene and
        # duplicate removal - which decide the CANDIDATE SET - partly read the
        # lockbox. Which features the lockbox model may use was being chosen
        # with lockbox data.
        dts = sessions[sessions <= np.datetime64(research_end)]
        per_date = max(1, int(research.sum()) // max(len(dts), 1))
        n_dates = max(20, min(400, 200_000 // per_date))
        keep_d = dts[:: max(1, len(dts) // n_dates)]
        sidx = np.where(p["timestamp"].isin(keep_d).to_numpy())[0]
        sub = pd.DataFrame(_gather(p, ex, cand, sidx), columns=cand)
        sub["timestamp"] = p["timestamp"].to_numpy()[sidx]
        hy = FA.hygiene(sub, cand, verbose=False)
        cand = hy.loc[hy["hygiene_fail"].isna(), "feature"].tolist()
        dup = FA.find_duplicates(sub, cand, verbose=False)
        del sub
        cand = [c for c in cand if c not in dup and c not in base_feats]
        R.path("p1_candidates.json").write_text(json.dumps(
            {"base": base_feats, "candidates": cand, "derived": der_names,
             "hygiene_rejected": int(hy["hygiene_fail"].notna().sum()),
             "duplicates": len(dup)}, indent=2), encoding="utf-8")
        R.mark("p1b", n_candidates=len(cand))
    cj = json.loads(R.path("p1_candidates.json").read_text(encoding="utf-8"))
    cand = cj["candidates"]
    R.log(f"    base {len(base_feats)} | candidates {len(cand)} | "
          f"state {len(st_cols)} | market {len(mk_cols)}")

    # Walk-forward folds live INSIDE the research period only.
    splits = PB.walk_forward_splits(
        pd.DataFrame({"timestamp": ts[research].to_numpy()}), n_splits=cfg["n_splits"])
    have = y.notna().to_numpy()
    Xst = np.column_stack([ex[c] for c in st_cols]).astype("float32")
    state_obs = (~np.isnan(Xst)).sum(axis=1).astype("int8")
    if "label_exit_ret" in p.columns:
        exit_ret = pd.to_numeric(p["label_exit_ret"], errors="coerce").to_numpy("float64")
        econ = "exact (label_exit_ret)"
    else:
        exit_ret = np.full(len(p), np.nan)
        econ = "UNAVAILABLE - rebuild the panel to get label_exit_ret"
        R.log("    WARNING: panel has no label_exit_ret; net-return evidence disabled. "
              "Rebuild the panel (panel_build --full) to enable it.")

    # ------------------------------------------ PHASE 2 + 4, per fold
    for fi, sp in enumerate(splits, 1):
        key = f"p2p4_fold{fi}"
        if R.done(key):
            R.log(f"[2/4] fold {fi}: checkpoint found, skipping")
            continue
        t0 = time.perf_counter()
        tr_end = pd.Timestamp(sp["train_end"])
        tr_m = (ts <= tr_end).to_numpy()
        te_m = ((ts >= pd.Timestamp(sp["test_start"])) &
                (ts <= pd.Timestamp(sp["test_end"]))).to_numpy()

        # --- PHASE 2: regime engine on TRAIN only, K fixed from fold 1,
        #     aligned to fold 1's centroids so an ID means the same state
        ref_p = R.path("p2_regimes", "fold1_engine.json")
        if fi == 1:
            eng = fit_regime_engine(Xst[tr_m], cfg["k_range"],
                                    select_rows=cfg["gmm_select_rows"],
                                    fit_rows=cfg["gmm_fit_rows"], seed=cfg["seed"])
            eng["perm"], drift = None, 0.0
        else:
            ref = json.loads(ref_p.read_text(encoding="utf-8"))
            eng = fit_regime_engine(Xst[tr_m], cfg["k_range"],
                                    select_rows=cfg["gmm_select_rows"],
                                    fit_rows=cfg["gmm_fit_rows"], seed=cfg["seed"],
                                    k_fixed=int(ref["k"]))
            ref_means = np.array([ref["centroids_raw"][str(k)]
                                  for k in range(int(ref["k"]))])
            eng["perm"], drift = RC.align_components(ref_means, eng["gmm"].means_)
        idx = np.where(tr_m | te_m)[0]
        proba, hard, conf = apply_regime_engine(eng, Xst[idx])
        miss = RC.missing_report(Xst[idx], proba)
        rg = pd.DataFrame({"row": idx, "regime": hard, "confidence": conf})
        for k in range(proba.shape[1]):
            rg[f"rp_{k}"] = proba[:, k]
        rg.to_parquet(R.path("p2_regimes", f"fold{fi}.parquet"), index=False)
        means = eng["gmm"].means_
        if eng.get("perm") is not None:          # store centroids in ALIGNED order
            aligned = np.empty_like(means)
            aligned[eng["perm"]] = means
            means = aligned
        (R.path("p2_regimes", f"fold{fi}_engine.json")).write_text(json.dumps({
            "k": eng["k"], "bic": eng["bic"], "drift": drift, "missing": miss,
            "centroids": {int(k): dict(zip(st_cols, map(float, means[k])))
                          for k in range(eng["k"])},
            "centroids_raw": {str(k): list(map(float, means[k]))
                              for k in range(eng["k"])},
            "train_end": sp["train_end"]}, indent=2), encoding="utf-8")

        # --- PHASE 4: grouped permutation screening on TRAIN only
        a_m, b_m = _split_train(ts, sessions, tr_end, cfg["val_fraction"],
                                cfg["embargo"])
        fit_i = np.where(a_m & have)[0]
        val_i = np.where(b_m & have)[0]
        if len(fit_i) > cfg["fit_cap"]:
            fit_i = np.sort(rng.choice(fit_i, cfg["fit_cap"], replace=False))
        if len(val_i) > cfg["val_rows"]:
            val_i = np.sort(rng.choice(val_i, cfg["val_rows"], replace=False))

        cols = base_feats + [c for c in cand if c not in base_feats]
        RC.assert_no_label_leak(cols, f"regime_research phase 4 fold {fi}")
        # fold-local permutation sentinels: shuffled within fit and within val
        sen_src = list(rng.choice(cand, size=min(cfg["n_sentinels"], len(cand)),
                                  replace=False))
        # Sentinels are built as ONE block and appended ONCE. Calling
        # column_stack per sentinel copies the whole matrix every time - at
        # 400k x 260 float32 that is ~400 MB per call, twelve times over,
        # which is the same class of bug as the panel's ArrayMemoryError.
        Xf0 = _gather(p, ex, cols, fit_i)
        Xv0 = _gather(p, ex, cols, val_i)
        js = [cols.index(c) for c in sen_src]
        sf = np.empty((len(Xf0), len(js)), dtype="float32")
        sv = np.empty((len(Xv0), len(js)), dtype="float32")
        for i, j in enumerate(js):
            sf[:, i] = rng.permutation(Xf0[:, j])
            sv[:, i] = rng.permutation(Xv0[:, j])
        Xf = np.hstack([Xf0, sf]); del Xf0, sf
        Xv = np.hstack([Xv0, sv]); del Xv0, sv
        sen_names = [f"__perm{i}" for i in range(len(js))]
        all_cols = cols + sen_names

        # Subsample the ROWS before building a frame: wrapping the full
        # 400k-row fit matrix first, then sampling, copies all of it.
        fr = np.sort(rng.choice(len(Xf), min(60_000, len(Xf)), replace=False))
        fam = _families(pd.DataFrame(Xf[fr, :len(cols)], columns=cols),
                        cols, cfg["family_corr"], 60_000, cfg["seed"])
        del fr
        nf = max(fam.values()) + 1
        for i, s in enumerate(sen_names):      # each sentinel its own family
            fam[s] = nf + i
        groups: Dict[int, List[int]] = {}
        for c, g in fam.items():
            groups.setdefault(g, []).append(all_cols.index(c))

        m = _hgb(cfg["seed"])
        m.fit(Xf, y.iloc[fit_i].astype(int).to_numpy())
        v_auc, imp = _grouped_perm_importance(
            m, Xv, y.iloc[val_i].astype(int).to_numpy(), groups,
            cfg["perm_repeats"], rng)

        sen_gid = {fam[s] for s in sen_names}
        null = np.array([imp[g] for g in sen_gid])
        cut = float(null.mean() + cfg["null_sigmas"] * null.std(ddof=1)) \
            if len(null) > 1 else 0.0
        rows = []
        for c in cols:
            g = fam[c]
            rows.append({"fold": fi, "feature": c, "family": g,
                         "family_size": len(groups[g]),
                         "family_importance": imp[g],
                         "beats_null": bool(imp[g] > cut and imp[g] > 0),
                         "is_base": c in base_feats})
        scr = pd.DataFrame(rows)
        scr.to_parquet(R.path("p4_screen", f"fold{fi}.parquet"), index=False)
        R.mark(key, k=eng["k"], val_auc=v_auc, null_cut=cut,
               null_mean=float(null.mean()), null_sd=float(null.std(ddof=1)),
               families=int(nf), survived=int(scr.loc[scr.beats_null, "family"].nunique()),
               secs=round(time.perf_counter() - t0, 1))
        R.log(f"[2/4] fold {fi}: K={eng['k']} | {nf} families | null cut "
              f"{cut:+.5f} | {scr.loc[scr.beats_null,'family'].nunique()} "
              f"families beat it ({time.perf_counter()-t0:.0f}s, "
              f"{'fast' if SCREEN_PATH['fast'] and not SCREEN_PATH['reference'] else 'reference' if not SCREEN_PATH['fast'] else 'mixed'} screen)")

    # ---------------------------------------------------------- PHASE 5
    # FOLD-LOCAL SELECTION. v1 aggregated survival over ALL folds and fed the
    # result to every fold. Folds expand, so fold 3's TRAIN window contains
    # fold 1's TEST window - fold 1's test labels shaped fold 3's screen,
    # which then chose fold 1's features. The model fit was out of sample;
    # the decision about what to fit was not.
    #
    # Now fold k uses screens from folds 1..k only. Every one of those was
    # computed on a train window that ends before fold k's test begins.
    # The all-folds set is still built - it is exactly right for the
    # LOCKBOX model, because by then every screen predates the lockbox.
    R.log("[5] fold-local family selection (folds 1..k for fold k)")
    screens = {i: pd.read_parquet(R.path("p4_screen", f"fold{i}.parquet"))
               for i in range(1, len(splits) + 1)}

    def _select(upto: int, row_mask: np.ndarray):
        sc = pd.concat([screens[i] for i in range(1, upto + 1)], ignore_index=True)
        sv = (sc.groupby("feature")
              .agg(folds_survived=("beats_null", "sum"), folds=("fold", "nunique"),
                   mean_family_imp=("family_importance", "mean")).reset_index())
        sv["survival"] = sv["folds_survived"] / sv["folds"]
        st = sv[(sv["survival"] >= cfg["min_fold_survival"])
                & ~sv["feature"].isin(base_feats)]
        if not len(st):
            return [], sv, st
        sf = st["feature"].tolist()
        hi = np.where(have & row_mask)[0]           # families from PAST rows only
        hi = np.sort(rng.choice(hi, min(60_000, len(hi)), replace=False))
        fam = _families(pd.DataFrame(_gather(p, ex, sf, hi), columns=sf),
                        sf, cfg["family_corr"], 60_000, cfg["seed"])
        st = st.assign(final_family=st["feature"].map(fam))
        reps = (st.sort_values(["survival", "mean_family_imp"], ascending=False)
                .groupby("final_family").head(1).head(cfg["max_family_reps"]))
        return reps["feature"].tolist(), sv, st

    reps_by_fold: Dict[int, List[str]] = {}
    for fi, sp in enumerate(splits, 1):
        m_ = (ts <= pd.Timestamp(sp["train_end"])).to_numpy()
        reps_by_fold[fi], _, _ = _select(fi, m_)
        R.log(f"    fold {fi}: {len(reps_by_fold[fi])} representatives "
              f"(from screens of folds 1..{fi})")
    final_reps, surv, stable = _select(len(splits), research)
    rep_feats = final_reps
    surv.to_csv(R.path("p5_feature_survival.csv"), index=False)
    R.path("p5_families.json").write_text(json.dumps(
        {"representatives": final_reps,
         "representatives_by_fold": {str(k): v for k, v in reps_by_fold.items()},
         "n_stable_features": int(len(stable)),
         "min_fold_survival": cfg["min_fold_survival"],
         "note": "representatives_by_fold drive the historical folds; "
                 "representatives (all research folds) drive ONLY the lockbox."},
        indent=2), encoding="utf-8")
    R.log(f"    final set (all research folds, lockbox only): {len(final_reps)}")

    # ---------------------------------------------------------- PHASE 6
    # M0: EVERY panel feature, no regimes - the model the feasibility test
    # passed with (+130 bp excess over buying everything, research period).
    # v5 compared only M1-M4 (5 base features plus a few selected families),
    # so the lockbox would never have tested the model with evidence behind
    # it. Choosing among five candidates is optimism the lockbox corrects.
    import panel_build as _PB
    all_feats = [c for c in _PB.panel_feature_columns(p)
                 if c not in ("open", "high", "low", "close", "volume")]
    RC.assert_no_label_leak(all_feats, "regime_research M0")

    def model_specs(reps: List[str]) -> dict:
        return {
            "M0_all_features": {"regime": False, "feats": all_feats, "ix": False, "reps": []},
            "M1_base": {"regime": False, "feats": base_feats, "ix": False, "reps": []},
            "M2_regime": {"regime": True, "feats": base_feats, "ix": False, "reps": []},
            "M3_families": {"regime": True, "feats": base_feats + reps, "ix": False,
                            "reps": reps},
            "M4_interactions": {"regime": True, "feats": base_feats + reps, "ix": True,
                                "reps": reps},
        }
    models = model_specs([])          # names, for the report
    from sklearn.isotonic import IsotonicRegression
    for fi, sp in enumerate(splits, 1):
        rgf = pd.read_parquet(R.path("p2_regimes", f"fold{fi}.parquet"))
        rp_cols = [c for c in rgf.columns if c.startswith("rp_")]
        # Regime columns as full-length float32 arrays in the extras dict.
        # The old version built an empty DataFrame and .loc-assigned into it,
        # which creates object/float64 columns across all 1.95M rows.
        rows_ = rgf["row"].to_numpy()
        rex: Dict[str, np.ndarray] = {}
        for c in rp_cols + ["confidence"]:
            a = np.full(len(p), np.nan, dtype="float32")
            a[rows_] = rgf[c].to_numpy(dtype="float32")
            rex[c] = a
        reg_lab = np.full(len(p), -1, dtype="int16")
        reg_lab[rows_] = rgf["regime"].to_numpy()
        tr_end = pd.Timestamp(sp["train_end"])
        te_m = ((ts >= pd.Timestamp(sp["test_start"])) &
                (ts <= pd.Timestamp(sp["test_end"]))).to_numpy()
        a_m, b_m = _split_train(ts, sessions, tr_end, cfg["calib_fraction"],
                                cfg["embargo"])
        fit_i = np.where(a_m & have)[0]
        cal_i = np.where(b_m & have)[0]
        te_i = np.where(te_m & have)[0]
        if len(fit_i) > cfg["fit_cap"]:
            fit_i = np.sort(rng.choice(fit_i, cfg["fit_cap"], replace=False))

        for name, spec in model_specs(reps_by_fold[fi]).items():
            key = f"p6_{name}_fold{fi}"
            if R.done(key):
                continue
            cols_m = list(spec["feats"])
            if spec["regime"]:
                cols_m += st_cols + mk_cols + rp_cols + ["confidence"]
            allx = {**ex, **rex}
            if spec["ix"] and spec["reps"]:
                for k in rp_cols:
                    for f in spec["reps"][:5]:
                        nm = f"ix_{k}_{f}"[:60]
                        fv = allx[f] if f in allx else p[f].to_numpy(dtype="float32")
                        allx[nm] = (rex[k] * fv).astype("float32")
                        cols_m.append(nm)
            RC.assert_no_label_leak(cols_m, f"regime_research {name} fold {fi}")
            # Only the rows each stage needs are ever materialised.
            Xfit = _gather(p, allx, cols_m, fit_i)
            Xcal = _gather(p, allx, cols_m, cal_i)
            Xte = _gather(p, allx, cols_m, te_i)
            mdl = _hgb(cfg["seed"])
            mdl.fit(Xfit, y.iloc[fit_i].astype(int).to_numpy())
            raw_cal = mdl.predict_proba(Xcal)[:, 1]
            raw_te = mdl.predict_proba(Xte)[:, 1]
            del Xfit, Xcal, Xte
            iso = IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1)
            iso.fit(raw_cal, y.iloc[cal_i].astype(int))
            pr = pd.DataFrame({
                "fold": fi, "timestamp": ts.iloc[te_i].to_numpy(),
                "symbol": p["symbol"].iloc[te_i].to_numpy(),
                "y": y.iloc[te_i].astype(int).to_numpy(),
                "p_raw": raw_te, "p_cal": iso.predict(raw_te),
                "regime": reg_lab[te_i],
                "exit_ret": exit_ret[te_i], "state_obs": state_obs[te_i]})
            pr.to_parquet(R.path("p6_pred", f"{name}_fold{fi}.parquet"), index=False)
            R.mark(key, n_features=len(cols_m))
            R.log(f"[6] {name} fold {fi}: {len(cols_m)} inputs")

    # ---------------------------------------------------------- PHASE 6b
    lock = None
    if lb_start is not None:
        R.log("[6b] lockbox")
        hyp = lock_hypothesis(R, list(models), splits, cfg)
        lock = {"hypothesis": hyp,
                "result": evaluate_lockbox(R, panel_path, p, ex, y, ts, sessions, cfg,
                                           research, lockbox, Xst, st_cols, mk_cols,
                                           final_reps, model_specs, have, rng,
                                           research_end, hyp, exit_ret, state_obs)}

    # ---------------------------------------------------------- PHASE 7
    R.log("[7] report")
    rep = build_report(R, models, splits, cfg, base_feats, rep_feats,
                       st_cols, mk_cols, p, y, ex, lock=lock, timing=timing,
                       reps_by_fold=reps_by_fold, panel_path=panel_path)
    if not R.done("ledger"):          # once per run: a resume is not a new experiment
        RC.ledger_append(panel_path, {"kind": "research", "tool": "regime_research",
                                      "run": rid, "hash": R.hash, "models": list(models),
                                      "lockbox_used": lock is not None})
        R.mark("ledger")
    R.log(f"=== done in {(time.perf_counter()-t_all)/60:.1f} min -> "
          f"{R.dir / 'report.md'}")
    return R.dir



# ======================================================================
# LOCKBOX - hypothesis locked from research folds, tested exactly once
# ======================================================================
def _ev(pred: pd.DataFrame, n: int, cfg: dict) -> dict:
    return RC.topn_evidence(pred, n, cost_bps=cfg["cost_bps"], B=cfg["boot_B"],
                            seed=cfg["seed"])


def _score(ev: dict) -> float:
    """What a hypothesis is ranked by: mean net return if known, else hit rate."""
    return ev["net"]["mean"] if ev.get("net") else ev["hit"]["mean"]


def lock_hypothesis(R, model_names, splits, cfg) -> dict:
    """
    Decide what the lockbox will test, from RESEARCH predictions only.

    This is aggressive by design - best model, then every regime whose daily
    top-3 NET return interval sits above zero - and that is fine, because the
    lockbox exists to catch exactly this optimisation. It answers "does THIS
    selected hypothesis survive untouched data", not "does regime research
    work". Written to disk before the lockbox is scored; a changed hypothesis
    within the same run is refused.
    """
    hp = R.path("lockbox_hypothesis.json")
    best, best_s, evs, preds = None, -np.inf, {}, {}
    for nm in model_names:
        fs = [R.path("p6_pred", f"{nm}_fold{i}.parquet") for i in range(1, len(splits) + 1)]
        fs = [f for f in fs if f.exists()]
        if not fs:
            continue
        pr = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
        ev = _ev(pr, 3, cfg)
        evs[nm], preds[nm] = ev, pr
        if _score(ev) > best_s:
            best, best_s = nm, _score(ev)
    pr = preds[best]
    pr = pr[pr["regime"] >= 0]
    locked = []
    for rg, g in pr.groupby("regime"):
        e = _ev(g, 3, cfg)
        if e["hit"]["n_dates"] >= cfg["min_regime_dates"] and e.get("clears"):
            locked.append(int(rg))
    hyp = {"model": best, "research_top3": evs[best], "locked_regimes": sorted(locked),
           "cost_bps": cfg["cost_bps"],
           "rule": "daily top-3; regime filter = stock-state regimes whose research "
                   "top-3 net-return 95% block-bootstrap interval is above zero, "
                   f"with >= {cfg['min_regime_dates']} dates"}
    if hp.exists():
        old = json.loads(hp.read_text(encoding="utf-8"))
        if (old["model"], old["locked_regimes"]) != (hyp["model"], hyp["locked_regimes"]):
            raise RuntimeError(
                f"lockbox hypothesis changed within {R.run_id} "
                f"({old['model']} {old['locked_regimes']} -> {hyp['model']} "
                f"{hyp['locked_regimes']}). Refusing - that is re-selecting after "
                f"the fact.")
        return old
    hyp["locked_at"] = dt.datetime.now().isoformat()
    hp.write_text(json.dumps(hyp, indent=2, default=str), encoding="utf-8")
    R.log(f"    HYPOTHESIS LOCKED: {best}, regimes {sorted(locked) or 'none'}")
    return hyp


def evaluate_lockbox(R, panel_path, p, ex, y, ts, sessions, cfg, research,
                     lockbox, Xst, st_cols, mk_cols, final_reps, model_specs,
                     have, rng, research_end, hyp, exit_ret, state_obs) -> dict:
    """
    Fit on all research data, score the untouched lockbox ONCE.

    The regime engine here is fitted ONCE on the whole research period - the
    deployment protocol. The walk-forward engines refit per fold. Different
    training procedures, so this engine's drift is not comparable to theirs.
    """
    import base_model as BM
    from sklearn.isotonic import IsotonicRegression
    rp = R.path("lockbox_result.json")
    if R.done("lockbox") and rp.exists():
        return json.loads(rp.read_text(encoding="utf-8"))
    ref = json.loads(R.path("p2_regimes", "fold1_engine.json").read_text(encoding="utf-8"))
    eng = fit_regime_engine(Xst[research], cfg["k_range"],
                            select_rows=cfg["gmm_select_rows"],
                            fit_rows=cfg["gmm_fit_rows"], seed=cfg["seed"],
                            k_fixed=int(ref["k"]))
    ref_means = np.array([ref["centroids_raw"][str(k)] for k in range(int(ref["k"]))])
    eng["perm"], drift = RC.align_components(ref_means, eng["gmm"].means_)
    idx = np.where(research | lockbox)[0]
    proba, hard, conf = apply_regime_engine(eng, Xst[idx])
    rex = {}
    for k in range(proba.shape[1]):
        a = np.full(len(p), np.nan, "float32"); a[idx] = proba[:, k]; rex[f"rp_{k}"] = a
    a = np.full(len(p), np.nan, "float32"); a[idx] = conf; rex["confidence"] = a
    lab = np.full(len(p), -1, "int16"); lab[idx] = hard

    spec = model_specs(final_reps)[hyp["model"]]
    rp_cols = [f"rp_{k}" for k in range(proba.shape[1])]
    cols = list(spec["feats"]) + ((st_cols + mk_cols + rp_cols + ["confidence"])
                                  if spec["regime"] else [])
    allx = {**ex, **rex}
    if spec["ix"] and spec["reps"]:
        for k in rp_cols:
            for f in spec["reps"][:5]:
                nm = f"ix_{k}_{f}"[:60]
                fv = allx[f] if f in allx else p[f].to_numpy(dtype="float32")
                allx[nm] = (rex[k] * fv).astype("float32"); cols.append(nm)
    RC.assert_no_label_leak(cols, "regime_research lockbox model")
    a_m, b_m = _split_train(ts, sessions, pd.Timestamp(research_end),
                            cfg["calib_fraction"], cfg["embargo"])
    fit_i = np.where(a_m & have & research)[0]
    cal_i = np.where(b_m & have & research)[0]
    lb_i = np.where(lockbox & have)[0]
    if len(fit_i) > cfg["fit_cap"]:
        fit_i = np.sort(rng.choice(fit_i, cfg["fit_cap"], replace=False))
    mdl = _hgb(cfg["seed"])
    mdl.fit(_gather(p, allx, cols, fit_i), y.iloc[fit_i].astype(int).to_numpy())
    iso = IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1)
    iso.fit(mdl.predict_proba(_gather(p, allx, cols, cal_i))[:, 1],
            y.iloc[cal_i].astype(int).to_numpy())
    raw = mdl.predict_proba(_gather(p, allx, cols, lb_i))[:, 1]
    pred = pd.DataFrame({"timestamp": ts.iloc[lb_i].to_numpy(),
                         "symbol": p["symbol"].iloc[lb_i].to_numpy(),
                         "y": y.iloc[lb_i].astype(int).to_numpy(),
                         "p_cal": iso.predict(raw), "regime": lab[lb_i],
                         "exit_ret": exit_ret[lb_i], "state_obs": state_obs[lb_i]})
    pred.to_parquet(R.path("lockbox_predictions.parquet"), index=False)

    m = BM._metrics(pred["y"], pred["p_cal"])
    cal = BM.calibration_table(pred).to_dict(orient="records")
    evs = {int(n): _ev(pred, n, cfg) for n in cfg["top_n"]}
    filt = (_ev(pred[pred["regime"].isin(hyp["locked_regimes"])], 3, cfg)
            if hyp["locked_regimes"] else None)
    # BUY-EVERYTHING BASELINE. Net return alone cannot separate stock-picking
    # from the market moving: in a falling market a good model can lose money
    # and still add value; in a rising one a useless model can profit. Excess
    # over the equal-weight average of every lockbox stock, same bracket and
    # cost, is the model's contribution.
    pn = pred.assign(net=pred["exit_ret"] - cfg["cost_bps"] / 1e4)
    uni_day = pn.groupby("timestamp")["net"].mean().sort_index()
    universe = RC.block_bootstrap_mean(uni_day.to_numpy(), B=cfg["boot_B"], seed=cfg["seed"])
    excess = {}
    for n in cfg["top_n"]:
        top = RC.daily_topn_values(pn, n, "net")
        excess[int(n)] = RC.block_bootstrap_mean(
            (top - uni_day.reindex(top.index)).dropna().to_numpy(),
            B=cfg["boot_B"], seed=cfg["seed"])
    yr = pd.to_datetime(pred["timestamp"]).dt.year
    by_year = {int(y_): _ev(pred[yr == y_], 3, cfg) for y_ in sorted(yr.unique())}
    pick = pred.copy()
    pick["_rk"] = pick.groupby("timestamp")["p_cal"].rank(ascending=False, method="first")
    top3 = pick[pick["_rk"] <= 3]
    reg_dist = {int(k): {"rows": float((pred["regime"] == k).mean()),
                         "top3_picks": float((top3["regime"] == k).mean())}
                for k in sorted(pred["regime"].unique())}
    compl = {int(k): _ev(pred[pred["state_obs"] == k], 3, cfg)
             for k in sorted(pred["state_obs"].unique())
             if pred.loc[pred["state_obs"] == k, "timestamp"].nunique() >= 30}
    res = {"model": hyp["model"], "lockbox_rows": int(len(lb_i)),
           "lockbox_sessions": int(pred["timestamp"].nunique()),
           "engine": "fitted once on all research data (deployment protocol)",
           "regime_drift_vs_fold1": drift, "metrics": m, "calibration": cal,
           "topn": evs, "top3_locked_regimes": filt, "by_year": by_year,
           "universe": universe, "excess": excess,
           "regime_distribution": reg_dist, "by_state_completeness": compl,
           "research_top3": hyp["research_top3"], "cost_bps": cfg["cost_bps"]}
    rp.write_text(json.dumps(res, indent=2, default=str), encoding="utf-8")
    R.mark("lockbox", hypothesis=hyp["model"])
    n = RC.ledger_append(panel_path, {"kind": "lockbox", "tool": "regime_research",
                                      "run": R.run_id, "hash": R.hash,
                                      "hypothesis": {k: hyp[k] for k in
                                                     ("model", "locked_regimes")},
                                      "top3": evs.get(3)})
    t3 = evs.get(3, {})
    R.log(f"    LOCKBOX scored once: top-3 hit {t3['hit']['mean']:.3f}"
          + (f", net {t3['net']['mean']*1e4:+.0f}bp "
             f"[{t3['net']['lo']*1e4:+.0f},{t3['net']['hi']*1e4:+.0f}]"
             if t3.get("net") else "") + f" | ledger entries now {n}")
    return res


# ======================================================================
# PHASE 7 - REPORT
# ======================================================================
def _eval_model(pred: pd.DataFrame, cfg: dict) -> dict:
    import base_model as BM
    return {"metrics": BM._metrics(pred["y"], pred["p_cal"]),
            "ev": {int(n): _ev(pred, n, cfg) for n in cfg["top_n"]}}


def _fmt_net(e) -> str:
    if not e or not e.get("net"):
        return "-"
    n = e["net"]
    return f"{n['mean']*1e4:+.0f} [{n['lo']*1e4:+.0f},{n['hi']*1e4:+.0f}]"


def build_report(R: Run, models, splits, cfg, base_feats, rep_feats,
                 st_cols, mk_cols, p, y, ex=None, lock=None, timing=None,
                 reps_by_fold=None, panel_path=None) -> dict:
    ex = ex or {}
    cost = cfg["cost_bps"]
    L = [f"# Regime + Feature Research - {R.run_id}", "",
         f"Panel: `{R.fingerprint['panel']}`  ",
         f"Build signature: `{R.fingerprint.get('build_signature')}`  ",
         f"Code: {CODE_VERSION} | config hash `{R.hash}`", "",
         "## Timing contract", "", f"_{RC.TIMING_CONTRACT}_", ""]
    if timing and "corr_fwd_vs_same_day" in timing:
        L += [f"Checked against the data on {timing['rows_checked']:,} rows: "
              f"corr(forward return, same-day return) "
              f"**{timing['corr_fwd_vs_same_day']:+.3f}** (must be ~0); "
              f"corr(forward return, next-day return) "
              f"**{timing['corr_fwd_vs_next_day']:+.3f}** (must be clearly "
              f"positive). A label containing session T would fail the first.", ""]
    else:
        L += ["**Timing contract NOT checked** (no close column).", ""]
    if reps_by_fold:
        L += ["## Features per fold (fold-local selection)", "",
              "Fold k uses only screens from folds 1..k, each computed on a "
              "train window that ends before fold k's test. The all-folds set "
              "is used for the lockbox model alone.", "",
              "Each name REPRESENTS A FAMILY: permutation importance shuffled the "
              "whole family together, so the named feature is a proxy for the "
              "family's information, not independently proven. Family clustering "
              "is fold-local and survival is tracked per FEATURE - family IDs are "
              "not comparable across folds. 'Beats the null' is a screen, not a "
              "significance test.", ""]
        for k, v in reps_by_fold.items():
            L.append(f"- fold {k}: " + (", ".join(f"`{x}`" for x in v) or "_none_"))
        L.append("")

    # ---- model comparison
    L += ["## Incremental model comparison", "",
          f"Net return per trade = realised bracket return (`label_exit_ret`) "
          f"minus {cost:.0f} bp. Intervals are 95% circular block bootstraps over "
          f"TRADING DAYS (block {RC.BOOT_BLOCK}) - 5-session labels overlap, so "
          f"trades are not independent and a binomial SE would be ~2x too "
          f"narrow. **clears** = the lower end of the net interval is above 0.", "",
          "**M0** uses every panel feature with no regimes - the model the "
          "feasibility test passed with. If M0 beats M2-M4, the regime machinery "
          "adds nothing beyond using all the information.", "",
          "**How to read the steps.** M1->M2: does a STATE REPRESENTATION of "
          "variables largely already in the library add out-of-sample "
          "information? (It is not a test of whether regime discovery found a "
          "new information source.) M2->M3: do the selected feature families "
          "add to that? M3->M4: do regime x feature interactions add - but only "
          "the first five representatives are crossed, so a null M4 means THAT "
          "subset added nothing, not that interactions do not matter.", "",
          "| model | AUC | brier | top-1 net bp | top-3 hit | top-3 net bp [95%] | clears |",
          "|---|---|---|---|---|---|---|"]
    results = {}
    for name in models:
        preds = [R.path("p6_pred", f"{name}_fold{i}.parquet")
                 for i in range(1, len(splits) + 1)]
        preds = [pd.read_parquet(x) for x in preds if x.exists()]
        if not preds:
            continue
        pred = pd.concat(preds, ignore_index=True)
        ev = _eval_model(pred, cfg)
        results[name] = (pred, ev)
        e1, e3 = ev["ev"].get(1), ev["ev"].get(3)
        mm = ev["metrics"]
        clr = ", ".join(f"top-{n}" for n, e in ev["ev"].items() if e.get("clears")) or "none"
        L.append(f"| {name} | {mm['auc']:.4f} | {mm['brier']:.4f} | "
                 f"{(e1['net']['mean']*1e4 if e1 and e1.get('net') else float('nan')):+.0f} | "
                 f"{e3['hit']['mean']:.3f} | {_fmt_net(e3)} | {clr} |")
    L.append("")

    # ---- regimes as a trade filter: HYPOTHESIS GENERATION only
    final = next((n for n in ("M4_interactions", "M3_families", "M2_regime")
                  if n in results), None)
    if final:
        pred = results[final][0]
        pred = pred[pred["regime"] >= 0]
        L += [f"## Stock-state regime as a trade filter ({final}, daily top-3) "
              f"- HYPOTHESIS GENERATION", "",
              "Research folds only. Choosing the regimes that clear here and "
              "then quoting their performance would be another backtest. The "
              "choice is LOCKED below and tested once on the untouched lockbox; "
              "only that lockbox figure is evidence.", "",
              "| regime | dates | top-3 hit | top-3 net bp [95%] | clears |",
              "|---|---|---|---|---|"]
        for rg, g in pred.groupby("regime"):
            e = _ev(g, 3, cfg)
            ok = ("thin" if e["hit"]["n_dates"] < cfg["min_regime_dates"]
                  else ("YES" if e.get("clears") else "no"))
            L.append(f"| R{int(rg)} | {e['hit']['n_dates']} | {e['hit']['mean']:.3f} | "
                     f"{_fmt_net(e)} | {ok} |")
        L += ["", "Regime IDs are ALIGNED across folds (K fixed from fold 1, "
              "Hungarian matching on centroids); check drift below before "
              "trusting an ID's identity over time.", ""]
        # state completeness: do partial observations degrade the model?
        L += ["### Performance by stock-state completeness (research folds)", "",
              "Rows with missing state inputs are scored on observed axes. If "
              "partial rows perform materially worse, they need a confidence "
              "adjustment or a missingness-aware feature.", "",
              "| state inputs observed | dates | top-3 hit | top-3 net bp [95%] |",
              "|---|---|---|---|"]
        allp = results[final][0]
        for k in sorted(allp["state_obs"].dropna().unique(), reverse=True):
            g = allp[allp["state_obs"] == k]
            if g["timestamp"].nunique() < 30:
                L.append(f"| {int(k)}/{len(st_cols)} | {g['timestamp'].nunique()} | thin | |")
                continue
            e = _ev(g, 3, cfg)
            L.append(f"| {int(k)}/{len(st_cols)} | {e['hit']['n_dates']} | "
                     f"{e['hit']['mean']:.3f} | {_fmt_net(e)} |")
        L.append("")

    # ---- feature-by-regime matrix (DESCRIPTIVE - drives nothing)
    #
    # Rank IC of each surviving representative WITHIN each regime, on the
    # last fold's test window. This is the table the brief asked for - "which
    # features matter where" - and it is deliberately descriptive: selecting
    # features per regime would cut each selection's sample ~K-fold and
    # multiply the tests by K. Read it to understand the model, not to
    # choose its inputs.
    rep_fams = json.loads(R.path("p5_families.json").read_text(
        encoding="utf-8"))["representatives"]
    last = len(splits)
    rgl = R.path("p2_regimes", f"fold{last}.parquet")
    if rep_fams and rgl.exists():
        rgf = pd.read_parquet(rgl)
        sp = splits[-1]
        tsv = p["timestamp"].iloc[rgf["row"]]
        in_te = ((tsv >= pd.Timestamp(sp["test_start"])) &
                 (tsv <= pd.Timestamp(sp["test_end"]))).to_numpy()
        rows_te = rgf["row"].to_numpy()[in_te]
        reg_te = rgf["regime"].to_numpy()[in_te]
        yt = y.iloc[rows_te].to_numpy()
        L += [f"## Feature-by-regime rank IC (descriptive, fold {last} test)", "",
              "Rank IC of each representative against the target, computed "
              "separately inside each regime. `.` = |IC| < 0.01.", "",
              "| feature | " + " | ".join(f"R{k}" for k in sorted(set(reg_te)))
              + " |", "|---|" + "---|" * len(set(reg_te))]
        for f in rep_fams[:15]:
            src = ex[f] if f in ex else p[f].to_numpy()
            xv = np.asarray(src[rows_te], dtype="float64")
            cells = []
            for k in sorted(set(reg_te)):
                m = (reg_te == k) & ~np.isnan(xv) & ~np.isnan(yt)
                if m.sum() < 200:
                    cells.append("thin"); continue
                ic = pd.Series(xv[m]).rank().corr(pd.Series(yt[m]).rank())
                cells.append("." if abs(ic) < 0.01 else f"{ic:+.3f}")
            L.append(f"| `{f}` | " + " | ".join(cells) + " |")
        L.append("")

    # ---- regime description (last fold, descriptive)
    engs = sorted(R.dir.glob("p2_regimes/fold*_engine.json"))
    if engs:
        e = json.loads(engs[-1].read_text(encoding="utf-8"))
        drifts = [json.loads(x.read_text(encoding="utf-8")).get("drift", 0.0)
                  for x in engs]
        miss = [json.loads(x.read_text(encoding="utf-8")).get("missing", {})
                for x in engs]
        L += [f"## Stock-state regimes (K={e['k']})", "",
              "These are RELATIVE STOCK states - per-date cross-sectional ranks, "
              "so 'high RSI' means high versus peers TODAY, not RSI above some "
              "level - and not market regimes. Market state enters the models as "
              "separate features.", "",
              "**What BIC does and does not say.** K was chosen by BIC on fold 1: "
              "the mixture that best DESCRIBES the state distribution. That is "
              "a clustering criterion, not evidence the states predict anything. "
              "Three separate questions, three separate answers:", "",
              f"- description (BIC): K={e['k']}",
              "- stability (centroid drift vs fold 1): "
              + ", ".join(f"f{i+1} {d:.3f}" for i, d in enumerate(drifts)),
              "- predictive value: M2 minus M1 in the comparison table above", ""]
        if miss and miss[0]:
            L += ["**Missing state inputs** (scored on observed axes, never imputed):", "",
                  "| fold | rows with any missing | all missing | conf complete | "
                  "conf partial | conf all-missing |", "|---|---|---|---|---|---|"]
            for i, m in enumerate(miss, 1):
                if m:
                    L.append(f"| {i} | {m['pct_rows_any_missing']:.2%} | "
                             f"{m['pct_rows_all_missing']:.2%} | "
                             f"{m['mean_conf_complete']:.3f} | "
                             f"{m['mean_conf_partial']:.3f} | "
                             f"{m['mean_conf_all_missing']:.3f} |")
            L.append("")
        L += [f"### Centroids (fold {len(engs)} engine, aligned)", "",
              "Centroids are centred per-date ranks: +0.5 = top of the "
              "cross-section today, -0.5 = bottom.", "",
              "| regime | " + " | ".join(c.replace("st_", "") for c in st_cols) + " |",
              "|---|" + "---|" * len(st_cols)]
        for k, cen in e["centroids"].items():
            L.append(f"| R{k} | " + " | ".join(f"{cen.get(c, 0):+.2f}"
                                               for c in st_cols) + " |")
        L += ["", "K chosen by BIC per fold: " + ", ".join(
            f"fold {i+1}: {json.loads(x.read_text())['k']}"
            for i, x in enumerate(engs)), ""]
        # transitions + durations
        rgf = pd.read_parquet(R.path("p2_regimes", f"fold{len(engs)}.parquet"))
        seq = pd.DataFrame({"symbol": p["symbol"].iloc[rgf["row"]].to_numpy(),
                            "timestamp": p["timestamp"].iloc[rgf["row"]].to_numpy(),
                            "regime": rgf["regime"].to_numpy()}
                           ).sort_values(["symbol", "timestamp"])
        seq["nxt"] = seq.groupby("symbol")["regime"].shift(-1)
        tr = pd.crosstab(seq["regime"], seq["nxt"], normalize="index")
        stay = np.diag(tr.reindex(index=tr.index, columns=tr.index,
                                  fill_value=0).to_numpy())
        runs = (seq["regime"] != seq.groupby("symbol")["regime"].shift()).cumsum()
        dur = seq.groupby(runs)["regime"].agg(["first", "size"])
        dstat = dur.groupby("first")["size"].agg(["mean", "median"])
        L += ["## Persistence (measured, never imposed)", "",
              "| regime | P(stay) | mean run | median run |", "|---|---|---|---|"]
        for i, k in enumerate(tr.index):
            if k in dstat.index:
                L.append(f"| R{int(k)} | {stay[i]:.2f} | "
                         f"{dstat.loc[k,'mean']:.1f} | {dstat.loc[k,'median']:.0f} |")
        L.append("")

    # ---- feature funnel + survival
    cj = json.loads(R.path("p1_candidates.json").read_text(encoding="utf-8"))
    fj = json.loads(R.path("p5_families.json").read_text(encoding="utf-8"))
    L += ["## Feature survival funnel", "",
          f"- hygiene rejected: {cj['hygiene_rejected']}",
          f"- duplicates removed (|r|>=0.999): {cj['duplicates']}",
          f"- candidates entering each fold: {len(cj['candidates'])}",
          f"- stable (beat fold-local null in >= "
          f"{fj['min_fold_survival']:.0%} of folds): {fj['n_stable_features']}",
          f"- family representatives kept: {len(fj['representatives'])}", "",
          "Representatives: " + (", ".join(f"`{x}`" for x in fj["representatives"])
                                 or "_none_"), ""]
    surv = pd.read_csv(R.path("p5_feature_survival.csv")).sort_values(
        ["survival", "mean_family_imp"], ascending=False)
    L += ["| feature | folds survived | survival | mean family importance |",
          "|---|---|---|---|"]
    for _, r in surv.head(30).iterrows():
        L.append(f"| `{r['feature']}` | {int(r['folds_survived'])}/"
                 f"{int(r['folds'])} | {r['survival']:.0%} | "
                 f"{r['mean_family_imp']:+.5f} |")
    L.append("")

    # ---- lockbox: the only figure that counts as evidence
    if lock:
        h, r = lock["hypothesis"], lock["result"]
        looks = RC.ledger_count(panel_path, "lockbox") if panel_path else 1
        rt = h["research_top3"]
        L += ["## Lockbox - the only evidence in this report", "",
              f"Hypothesis locked at {h.get('locked_at', '?')[:19]}, BEFORE any "
              f"lockbox row was scored: model **{h['model']}**, regime filter "
              f"**{h['locked_regimes'] or 'none'}**.", "",
              "This tests whether THIS research-selected hypothesis survives "
              "untouched data. It does not test whether regime research works "
              "in general. The regime engine here was fitted ONCE on all research "
              "data (the deployment protocol), unlike the per-fold walk-forward "
              "engines, so its drift is not comparable to theirs.", "",
              f"Lockbox: **{r['lockbox_sessions']} sessions**, {r['lockbox_rows']:,} rows. "
              f"AUC {r['metrics']['auc']:.4f} | brier {r['metrics']['brier']:.4f} | "
              f"logloss {r['metrics']['logloss']:.4f} | base rate "
              f"{r['metrics']['base_rate']:.3f}.", "",
              f"**Buy everything** (equal weight, same bracket and cost): "
              f"{r['universe']['mean']*1e4:+.0f} bp [{r['universe']['lo']*1e4:+.0f},"
              f"{r['universe']['hi']*1e4:+.0f}] per trade. The model's contribution is "
              f"its excess over this.", "",
              "| | dates | hit | net bp [95%] | clears |", "|---|---|---|---|---|",
              f"| research top-3 (in-sample choice) | {rt['hit']['n_dates']} | "
              f"{rt['hit']['mean']:.3f} | {_fmt_net(rt)} | - |"]
        for n, e in r["topn"].items():
            L.append(f"| **lockbox top-{n}** | {e['hit']['n_dates']} | "
                     f"**{e['hit']['mean']:.3f}** | **{_fmt_net(e)}** | "
                     f"**{'YES' if e.get('clears') else 'no'}** |")
        L += ["", "| excess over buy-everything | bp [95%] | above zero |", "|---|---|---|"]
        for n, x in r["excess"].items():
            ok_ = np.isfinite(x["lo"]) and x["lo"] > 0
            L.append(f"| **lockbox top-{n}** | **{x['mean']*1e4:+.0f} [{x['lo']*1e4:+.0f},"
                     f"{x['hi']*1e4:+.0f}]** | **{'YES' if ok_ else 'no'}** |")
        L.append("")
        if r.get("top3_locked_regimes"):
            f_ = r["top3_locked_regimes"]
            L.append(f"| **lockbox, locked regimes, top-3** | {f_['hit']['n_dates']} | "
                     f"**{f_['hit']['mean']:.3f}** | **{_fmt_net(f_)}** | "
                     f"**{'YES' if f_.get('clears') else 'no'}** |")
        L += ["", "**By year (top-3):** " + " | ".join(
                  f"{yy}: {e['hit']['mean']:.3f} hit, {_fmt_net(e)} bp"
                  for yy, e in r["by_year"].items()), "",
              "**Regime mix:** " + " | ".join(
                  f"R{k} {v['rows']:.0%} of rows / {v['top3_picks']:.0%} of picks"
                  for k, v in r["regime_distribution"].items()), "",
              "**By state completeness (top-3):** " + (" | ".join(
                  f"{k}/{len(st_cols)}: {e['hit']['mean']:.3f}, {_fmt_net(e)} bp"
                  for k, e in r["by_state_completeness"].items()) or "_too thin_"), "",
              "**Calibration (lockbox deciles):** " + ", ".join(
                  f"{c['predicted']:.2f}->{c['realised']:.2f}" for c in r["calibration"]), ""]
        if looks > 1:
            L += [f"**WARNING: this panel's lockbox has now been evaluated "
                  f"{looks} times** (research_ledger.jsonl). Every look after the "
                  f"first lets lockbox results steer choices, and the figure stops "
                  f"being untouched.", ""]

    # ---- honest verdict
    L += ["## Verdict", ""]
    if "M1_base" in results and final:
        b = results["M1_base"][1]["metrics"]["auc"]
        f_ = results[final][1]["metrics"]["auc"]
        L.append(f"- Research AUC {b:.4f} -> {f_:.4f} ({f_-b:+.4f}) from M1 to {final}.")
        cl = [f"{n} top-{k}" for n in results for k, e in results[n][1]["ev"].items()
              if e.get("clears")]
        L.append("- Research-fold net return clears zero for: "
                 + (", ".join(cl) if cl else "nothing") + " (in-sample choice).")
        if lock:
            t3 = lock["result"]["topn"].get(3) or lock["result"]["topn"].get("3")
            x3 = lock["result"]["excess"].get(3) or lock["result"]["excess"].get("3")
            beats = bool(x3 and np.isfinite(x3["lo"]) and x3["lo"] > 0)
            L.append("- **Lockbox top-3: net " + ("CLEARS" if t3 and t3.get("clears")
                                                  else "does not clear") + "; beats buying "
                     "everything: " + ("YES" if beats else "NO") + "** - the only result "
                     "here that was not selected on the data it is scored on. Both are "
                     "needed: net above zero, and above the market.")
    L += ["",
          "_Not a backtest: no slippage, sizing, capacity, borrow or MTF "
          "financing; net return uses one flat cost. Regime IDs are aligned "
          "across folds. Every result is OOS on walk-forward folds with a "
          f"{cfg['embargo']}-session embargo; the calibrator never saw a test "
          "window._"]
    R.path("report.md").write_text("\n".join(L), encoding="utf-8")
    return {"models": list(results)}


def list_runs(root: Path) -> None:
    base = Path(root) / "panel" / "research"
    for d in sorted(base.glob("RUN_*")):
        c = json.loads((d / "config.json").read_text(encoding="utf-8"))
        done = len(list((d / "checkpoints").glob("*.done"))) if (d / "checkpoints").exists() else 0
        print(f"  {d.name}  created {c['created'][:19]}  {done} checkpoints  "
              f"{'report' if (d/'report.md').exists() else 'in progress'}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("cmd", choices=["run", "report", "list"])
    ap.add_argument("--root", default=None)
    ap.add_argument("--resume", default=None)
    ap.add_argument("--run", default=None)
    ap.add_argument("--splits", type=int, default=None)
    ap.add_argument("--cost-bps", type=float, default=None)
    a = ap.parse_args()
    root = a.root or os.environ.get("CACHE_DAILY_ROOT")
    if not root:
        raise SystemExit("CACHE_DAILY_ROOT not set and --root not given")
    ppq = Path(root) / "panel" / "panel.parquet"
    ov = {k: v for k, v in {"n_splits": a.splits, "cost_bps": a.cost_bps}.items()
          if v is not None}
    if a.cmd == "run":
        run(ppq, resume=a.resume, overrides=ov)
    elif a.cmd == "list":
        list_runs(Path(root))
    else:
        rid = a.run or a.resume
        if not rid:
            raise SystemExit("report needs --run RUN_ID")
        print((ppq.parent / "research" / rid / "report.md").read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
