#!/usr/bin/env python3
"""
research_common.py - discipline shared by every research tool.

Four things live here so that no two tools can define them differently:

    TIMING CONTRACT   what is known when, checked against the data itself
    REGIME POSTERIOR  Gaussian-mixture assignment that never imputes
    LOCKBOX           the final period no research step may look at
    RESEARCH LEDGER   an append-only count of every experiment and every
                      lockbox look

THE PROBLEM THIS MODULE EXISTS FOR
==================================
The pipeline is now good at preventing classic lookahead - using tomorrow's
price. The larger risk has moved: RESEARCH-SELECTION LEAKAGE. Run a thousand
reasonable experiments, keep what survives, call it an edge. Nothing in any
single experiment is wrong; the selection across them is. The lockbox and
the ledger are the defence, and they only work if every tool uses the same
ones.
"""

from __future__ import annotations

import datetime as dt
import json
import math
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd

# ----------------------------------------------------------------------
# TIMING CONTRACT
# ----------------------------------------------------------------------
TIMING_CONTRACT = (
    "Prediction is made at the CLOSE of session T. Every feature uses data "
    "through the close of T and nothing later. The target covers sessions "
    "T+1..T+H, entered at the close of T. Same-day market state (breadth, "
    "median move, dispersion) is therefore legitimate: it is known at T close.")


class TimingContractError(RuntimeError):
    pass


def assert_timing_contract(close: np.ndarray, sym_code: np.ndarray,
                           fwd_ret: np.ndarray, *, max_same: float = 0.10,
                           min_next: float = 0.15, sample: int = 300_000,
                           seed: int = 0) -> Dict[str, float]:
    """
    Check the label timing against the DATA, not against anyone's reading
    of the code.

    If the forward return spans T+1..T+H, it contains day T+1's return and
    not day T's. So:
        corr(fwd_ret[T], ret1[T])    should be ~0     (not in the window)
        corr(fwd_ret[T], ret1[T+1])  should be ~0.45  (1 of 5 days)
    A label that leaked day T would push the first figure to ~0.45 too. The
    thresholds leave room for genuine short-term reversal, which can make the
    first figure mildly negative.

    Rows must be in (timestamp, symbol) order, which is also time order
    within each symbol.
    """
    s = pd.Series(np.asarray(close, dtype="float64"))
    g = s.groupby(np.asarray(sym_code))
    r1 = (s / g.shift(1) - 1).to_numpy()
    r1_next = pd.Series(r1).groupby(np.asarray(sym_code)).shift(-1).to_numpy()
    fr = np.asarray(fwd_ret, dtype="float64")
    ok = np.isfinite(fr) & np.isfinite(r1) & np.isfinite(r1_next)
    idx = np.where(ok)[0]
    if len(idx) < 1000:
        raise TimingContractError(f"only {len(idx)} rows to check timing on")
    rng = np.random.default_rng(seed)
    if len(idx) > sample:
        idx = rng.choice(idx, sample, replace=False)

    def sp(a, b):     # Spearman: returns are fat-tailed
        return float(pd.Series(a).rank().corr(pd.Series(b).rank()))

    c_same = sp(fr[idx], r1[idx])
    c_next = sp(fr[idx], r1_next[idx])
    out = {"corr_fwd_vs_same_day": round(c_same, 4),
           "corr_fwd_vs_next_day": round(c_next, 4), "rows_checked": int(len(idx))}
    if abs(c_same) > max_same or c_next < min_next:
        raise TimingContractError(
            f"label timing does not match the contract.\n"
            f"  corr(forward return, SAME-day return) = {c_same:+.3f} "
            f"(must be within +/-{max_same})\n"
            f"  corr(forward return, NEXT-day return) = {c_next:+.3f} "
            f"(must exceed {min_next})\n"
            f"  Contract: {TIMING_CONTRACT}")
    return out


def forward_return_for_check(close: np.ndarray, sym_code: np.ndarray,
                             horizon: int) -> np.ndarray:
    """Fallback when the panel carries no forward-return label."""
    s = pd.Series(np.asarray(close, dtype="float64"))
    return (s.groupby(np.asarray(sym_code)).shift(-horizon) / s - 1).to_numpy()


# ----------------------------------------------------------------------
# REGIME POSTERIOR THAT NEVER IMPUTES
# ----------------------------------------------------------------------
def gmm_proba(gm, X: np.ndarray) -> np.ndarray:
    """
    Component probabilities using ONLY the observed dimensions of each row.

    Replacing a missing input with 0 - the centre of a centred rank - claims
    the stock is "average" on that axis. It is not; it is unknown. The
    previous code did exactly that and then assigned such rows to regimes
    with unearned confidence.

    The marginal of a Gaussian mixture over a subset of dimensions is itself
    a Gaussian mixture with the same weights and the corresponding sub-means
    and sub-covariances. So a row missing ADX is scored on its other axes,
    exactly, with no imputation. A row missing everything gets the prior
    weights: an honest "don't know", with correspondingly low confidence.
    """
    from scipy.stats import multivariate_normal
    X = np.asarray(X, dtype="float64")
    miss = np.isnan(X)
    K = gm.n_components
    out = np.empty((len(X), K))
    full = ~miss.any(axis=1)
    if full.any():
        out[full] = gm.predict_proba(X[full])
    part = np.where(~full)[0]
    if len(part):
        pats, inv = np.unique(miss[part], axis=0, return_inverse=True)
        inv = np.asarray(inv).reshape(-1)
        logw = np.log(np.clip(gm.weights_, 1e-300, None))
        for pi, pat in enumerate(pats):
            rows = part[inv == pi]
            obs = ~pat
            if not obs.any():
                out[rows] = gm.weights_
                continue
            Xo = X[np.ix_(rows, np.where(obs)[0])]
            ll = np.empty((len(rows), K))
            for k in range(K):
                mu = gm.means_[k][obs]
                cov = gm.covariances_[k][np.ix_(obs, obs)]
                ll[:, k] = logw[k] + multivariate_normal.logpdf(
                    Xo, mean=mu, cov=cov, allow_singular=True)
            ll -= ll.max(axis=1, keepdims=True)
            p = np.exp(ll)
            out[rows] = p / p.sum(axis=1, keepdims=True)
    return out


def missing_report(X: np.ndarray, proba: np.ndarray) -> Dict[str, float]:
    miss = np.isnan(X)
    anym = miss.any(axis=1)
    allm = miss.all(axis=1)
    conf = proba.max(axis=1)
    return {
        "rows": int(len(X)),
        "pct_rows_any_missing": float(anym.mean()),
        "pct_rows_all_missing": float(allm.mean()),
        "mean_conf_complete": float(conf[~anym].mean()) if (~anym).any() else float("nan"),
        "mean_conf_partial": float(conf[anym & ~allm].mean()) if (anym & ~allm).any() else float("nan"),
        "mean_conf_all_missing": float(conf[allm].mean()) if allm.any() else float("nan"),
    }


def align_components(ref_means: np.ndarray, means: np.ndarray) -> Tuple[np.ndarray, float]:
    """
    Map each new component to the reference component it most resembles.

    Returns perm with perm[j] = reference label of new component j, and the
    mean matched centroid distance - the DRIFT. Large drift means a regime ID
    no longer describes the same state, and per-regime conclusions do not
    transfer across time.
    """
    from scipy.optimize import linear_sum_assignment
    cost = ((ref_means[:, None, :] - means[None, :, :]) ** 2).sum(-1)
    r, c = linear_sum_assignment(cost)
    perm = np.empty(len(c), dtype=int)
    perm[c] = r
    return perm, float(np.sqrt(cost[r, c]).mean())


def permute_proba(proba: np.ndarray, perm: np.ndarray) -> np.ndarray:
    """Reorder probability columns so column k is reference regime k."""
    out = np.empty_like(proba)
    out[:, perm] = proba
    return out


# ----------------------------------------------------------------------
# LOCKBOX
# ----------------------------------------------------------------------
DEFAULT_LOCKBOX_FRACTION = 0.15


def lockbox_bounds(sessions: np.ndarray, frac: float, horizon: int
                   ) -> Tuple[Optional[np.datetime64], Optional[np.datetime64]]:
    """
    (research_end, lockbox_start). Research may use sessions <= research_end.

    The gap between them is the label horizon: a research row within H
    sessions of the lockbox has a target window reaching INTO the lockbox, so
    it is excluded too. Every research tool must use this one function, or
    one tool's lockbox is another's research data.
    """
    sessions = np.sort(np.asarray(sessions))
    if not frac or frac <= 0:
        return sessions[-1], None
    lb_i = int(len(sessions) * (1 - frac))
    lb_i = max(horizon + 2, min(lb_i, len(sessions) - 1))
    return sessions[lb_i - horizon - 1], sessions[lb_i]


# ----------------------------------------------------------------------
# RESEARCH LEDGER
# ----------------------------------------------------------------------
def ledger_path(panel_path: Path) -> Path:
    return Path(panel_path).parent / "research_ledger.jsonl"


def ledger_append(panel_path: Path, record: dict) -> int:
    """Append one experiment; return how many are now on record."""
    p = ledger_path(panel_path)
    rec = {"at": dt.datetime.now().isoformat(), **record}
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, default=str) + "\n")
    return ledger_count(panel_path)


def ledger_entries(panel_path: Path) -> list:
    p = ledger_path(panel_path)
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def ledger_count(panel_path: Path, kind: Optional[str] = None) -> int:
    e = ledger_entries(panel_path)
    return len([x for x in e if kind is None or x.get("kind") == kind])


# ----------------------------------------------------------------------
# EVIDENCE: date-block bootstrap on per-DAY outcomes
# ----------------------------------------------------------------------
DEFAULT_COST_BPS = 35.0
BOOT_BLOCK = 10          # sessions; >= 2x the 5-session label horizon


def daily_topn_values(pred: pd.DataFrame, n: int, value_col: str,
                      score_col: str = "p_cal") -> pd.Series:
    """One number per trading day: the mean outcome of that day's top-n."""
    d = pred.dropna(subset=[score_col, value_col]).copy()
    d["_rk"] = d.groupby("timestamp")[score_col].rank(ascending=False, method="first")
    return d[d["_rk"] <= n].groupby("timestamp")[value_col].mean().sort_index()


def block_bootstrap_mean(x, *, B: int = 2000, block: int = BOOT_BLOCK,
                         seed: int = 0) -> Dict[str, float]:
    """
    95% interval for the mean of a DATE-ORDERED series, by circular
    moving-block bootstrap.

    The binomial standard error sqrt(p(1-p)/n) treats every trade as an
    independent coin. They are not: 5-session labels overlap, so today's and
    tomorrow's outcomes share four days of price path, and the top names on
    one day tend to move together. Resampling BLOCKS of consecutive days
    keeps that dependence inside each resample, so the interval widens to
    reflect what was actually learned. The day is the unit, because the
    decision is made once per day.
    """
    x = np.asarray(x, dtype="float64")
    x = x[np.isfinite(x)]
    n = len(x)
    out = {"mean": float(x.mean()) if n else float("nan"), "lo": float("nan"),
           "hi": float("nan"), "n_dates": int(n), "block": int(block)}
    if n < 2 * block:
        return out
    rng = np.random.default_rng(seed)
    nb = int(np.ceil(n / block))
    starts = rng.integers(0, n, size=(B, nb))
    idx = ((starts[:, :, None] + np.arange(block)[None, None, :]) % n).reshape(B, -1)[:, :n]
    means = x[idx].mean(axis=1)
    out["lo"], out["hi"] = float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))
    return out


def topn_evidence(pred: pd.DataFrame, n: int, *, cost_bps: float = DEFAULT_COST_BPS,
                  B: int = 2000, seed: int = 0) -> Dict[str, object]:
    """
    Hit rate AND net return of a daily top-n, each with a block-bootstrap CI.

    There is no breakeven constant. With ATR-scaled barriers every trade's
    payoff depends on its own stock's volatility, so a single breakeven
    probability cannot be right: cost is a bigger share of a quiet stock's
    bracket. Net return per trade - realised bracket return minus cost -
    is the economic question asked directly. 'clears' means the LOWER end of
    the net-return interval is above zero.
    """
    hit = block_bootstrap_mean(daily_topn_values(pred, n, "y").to_numpy(), B=B, seed=seed)
    res = {"top_n": n, "hit": hit}
    if "exit_ret" in pred.columns and pred["exit_ret"].notna().any():
        d = pred.assign(net=pred["exit_ret"] - cost_bps / 1e4)
        net = block_bootstrap_mean(daily_topn_values(d, n, "net").to_numpy(), B=B, seed=seed)
        res["net"] = net
        res["clears"] = bool(np.isfinite(net["lo"]) and net["lo"] > 0)
    else:
        res["net"] = None
        res["clears"] = None
    return res


# ----------------------------------------------------------------------
# PANEL-LEVEL LEAKAGE SCREEN
# ----------------------------------------------------------------------
def screen_feature_leakage(values: np.ndarray, close: np.ndarray, sym_code: np.ndarray,
                           *, horizons=(1, 2, 3, 4, 5), threshold: float = 0.15,
                           sample: int = 200_000, seed: int = 0,
                           _cache: Optional[dict] = None) -> Dict[str, float]:
    """
    Does a feature at T correlate with a FUTURE single-day return?

    features_daily's canary proves the per-symbol feature CODE never reads a
    future bar - on synthetic data. It cannot see an exogenous series joined
    one day off, a cross-sectional step that mixed dates, or features a
    research tool derives itself. This checks the finished panel instead.

    A legitimate daily feature predicts tomorrow's return at |rho| of a few
    hundredths. One that contains tomorrow's close sits near 0.3 or above,
    because it IS partly tomorrow's return. Rows must be in (timestamp,
    symbol) order.
    """
    c = _cache if _cache is not None else {}
    key = id(close)
    if key not in c:
        s = pd.Series(np.asarray(close, dtype="float64"))
        r1 = (s / s.groupby(sym_code).shift(1) - 1).to_numpy()
        fut = {h: pd.Series(r1).groupby(sym_code).shift(-h).to_numpy() for h in horizons}
        rng = np.random.default_rng(seed)
        idx = rng.choice(len(r1), min(sample, len(r1)), replace=False)
        c[key] = (idx, {h: pd.Series(fut[h][idx]).rank() for h in horizons})
    idx, fr = c[key]
    fv = pd.Series(np.asarray(values, dtype="float64")[idx]).rank()
    out = {f"rho_t+{h}": float(fv.corr(fr[h])) for h in horizons}
    worst = max((abs(v) for v in out.values() if np.isfinite(v)), default=0.0)
    out["max_abs_future_rho"] = worst
    out["suspect"] = bool(worst > threshold)
    return out


# ----------------------------------------------------------------------
# LABEL FIREWALL - enforced where features are CONSUMED
# ----------------------------------------------------------------------
# Columns that look forward but are not named label_*. features_daily emits
# ret_5d_close_pct = close[t+5]/close[t]-1 and its leak canary exempts it on
# purpose. It was STORED in panel.parquet; panel_feature_columns excluded it,
# but the feature atlas built its list from the parquet schema and would have
# used the forward return as a feature. One upstream filter is not a firewall.
FORWARD_COLUMNS = frozenset({"ret_5d_close_pct"})


class LabelLeakError(RuntimeError):
    pass


def is_forbidden_feature(name: str) -> bool:
    return name.startswith("label_") or name in FORWARD_COLUMNS


def assert_no_label_leak(columns, where: str) -> None:
    """Raise if any label or known forward-looking column is about to be used as a feature."""
    bad = sorted({c for c in columns if is_forbidden_feature(str(c))})
    if bad:
        raise LabelLeakError(
            f"{where}: label / forward-looking columns in the FEATURE set: {bad}. "
            f"These encode the outcome being predicted. Refusing to continue.")
