#!/usr/bin/env python3
"""
smoke_test.py - check the REAL panel and machine before any long research run.

    python smoke_test.py --root %CACHE_DAILY_ROOT%
    python smoke_test.py --root %CACHE_DAILY_ROOT% --run-tools

WHAT UNIT TESTS CANNOT TELL YOU
===============================
Every research test runs on synthetic fixtures. Four things only the real
panel and this machine can answer:

  1. COLUMN NAMES. The research tools look features up by name and SKIP any
     that are absent. A missing state input quietly builds regimes from fewer
     dimensions; nothing complains. (This check already found one:
     D_obv_slope5 does not exist - the real column is D_obv_slope.)
  2. THE TIMING CONTRACT on real returns, not synthetic ones.
  3. LEAKAGE IN THE FINISHED PANEL. features_daily's canary proves the
     per-symbol feature code never reads a future bar. It cannot see an
     exogenous series joined one day off or a cross-sectional step that mixed
     dates. This screens every feature against future single-day returns.
  4. RUNTIME AND MEMORY at real scale, extrapolated from a subset.

WHY THE SMOKE RUN CANNOT SPEND THE LOCKBOX
------------------------------------------
--run-tools builds a subset panel that ENDS at the research end date. The
lockbox sessions are not in it at all, so even regime_research's own lockbox
step scores dates that are ordinary research data for the real panel. The
smoke subset also keeps its own ledger, separate from the real one.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

OK, WARN, FAIL = "ok  ", "WARN", "FAIL"


def _line(status, msg):
    print(f"  [{status}] {msg}", flush=True)


def preflight(panel_path: Path) -> dict:
    import pyarrow.parquet as pq
    import research_common as RC
    import feature_atlas as FA
    import regime_research as RR
    import panel_build as PB
    problems = []

    print("\n=== 1. ENVIRONMENT ===")
    import sklearn, scipy
    _line(OK, f"python {platform.python_version()} | pandas {pd.__version__} | "
              f"numpy {np.__version__} | sklearn {sklearn.__version__} | scipy {scipy.__version__}")

    print("\n=== 2. COLUMNS THE TOOLS LOOK UP BY NAME ===")
    cols = set(pq.ParquetFile(panel_path).schema_arrow.names)
    meta_p = panel_path.parent / "panel_meta.json"
    meta = json.loads(meta_p.read_text(encoding="utf-8")) if meta_p.exists() else {}
    _line(OK, f"panel: {meta.get('rows', '?'):,} rows | {meta.get('symbols', '?')} symbols | "
              f"{meta.get('first_session')} -> {meta.get('last_session')} | {len(cols)} columns"
          if isinstance(meta.get("rows"), int) else f"panel: {len(cols)} columns")
    groups = {
        "canonical STOCK_STATE_SPEC": [c for _, c, _ in RC.STOCK_STATE_SPEC],
        "atlas CORE_SIGNALS": FA.CORE_SIGNALS,
        "base features": RR.DEFAULT_BASE,
        "raw OHLCV": ["open", "high", "low", "close", "volume"],
    }
    for g, names in groups.items():
        miss = [c for c in names if c not in cols]
        crit = g in ("canonical STOCK_STATE_SPEC", "raw OHLCV")
        st = OK if not miss else (FAIL if crit and (g == "raw OHLCV" or
                     len(names) - len(miss) < RC.MIN_STATE_DIMS) else WARN)
        _line(st, f"{g}: {len(names) - len(miss)}/{len(names)} present"
                  + (f" - MISSING {miss}" if miss else ""))
        if miss and crit and (g == "raw OHLCV" or
                              len(names) - len(miss) < RC.MIN_STATE_DIMS):
            problems.append(f"{g} missing {miss}")
    for lab in ("label_tp_before_sl", "label_exit_ret", "label_fwd_ret_5d"):
        ok_ = lab in cols
        _line(OK if ok_ else (WARN if lab != "label_tp_before_sl" else FAIL),
              f"{lab}: {'present' if ok_ else 'ABSENT'}"
              + ("" if ok_ or lab != "label_exit_ret" else
                 " - rebuild the panel (--full) to get exact trade economics"))
        if not ok_ and lab == "label_tp_before_sl":
            problems.append("target missing")

    print("\n=== 3. TIMING CONTRACT ON REAL RETURNS ===")
    keys = pd.read_parquet(panel_path, columns=["timestamp", "symbol", "close"]
                           + (["label_fwd_ret_5d"] if "label_fwd_ret_5d" in cols else []))
    keys["timestamp"] = pd.to_datetime(keys["timestamp"]).dt.tz_localize(None)
    order = np.lexsort((keys["symbol"].astype(str).to_numpy(), keys["timestamp"].to_numpy()))
    keys = keys.take(order).reset_index(drop=True)
    code_all = pd.factorize(keys["symbol"])[0]
    close_all = keys["close"].to_numpy("float64")
    # RESEARCH ROWS ONLY. The leakage screen correlates every feature with
    # future returns - an IC-like statistic - so running it over the lockbox
    # would be a peek, however it was labelled.
    sess_all = np.sort(keys["timestamp"].unique())
    r_end, _lb = RC.lockbox_bounds(sess_all, RC.DEFAULT_LOCKBOX_FRACTION, 5)
    res = (keys["timestamp"] <= pd.Timestamp(r_end)).to_numpy()
    code, close = code_all[res], close_all[res]
    fwd = (keys["label_fwd_ret_5d"].to_numpy("float64")[res] if "label_fwd_ret_5d" in keys
           else RC.forward_return_for_check(close, code, 5))
    _line(OK, f"checks below use research rows only (<= {pd.Timestamp(r_end).date()}); "
              f"the lockbox is never read")
    try:
        t = RC.assert_timing_contract(close, code, fwd)
        _line(OK, f"same-day {t['corr_fwd_vs_same_day']:+.3f} (must be ~0), next-day "
                  f"{t['corr_fwd_vs_next_day']:+.3f} (must be clearly positive)")
    except RC.TimingContractError as e:
        _line(FAIL, str(e).splitlines()[0]); problems.append("timing contract")

    print("\n=== 4. LEAKAGE SCREEN: every feature vs FUTURE single-day returns ===")
    # Screen EVERY stored column except keys, raw prices and declared labels -
    # deliberately NOT the panel_feature_columns list. Filtering first is how a
    # forward return stored under a non-label name went unscreened.
    feats = [c for c in sorted(cols)
             if c not in ("timestamp", "symbol", "open", "high", "low", "close", "volume")
             and not c.startswith("label_")]
    fwd_stored = sorted(c for c in cols if c in RC.FORWARD_COLUMNS)
    if fwd_stored:
        _line(FAIL, f"forward-looking columns stored in the panel: {fwd_stored} "
                    f"- rebuild with the current panel_build.py")
        problems.append(f"forward columns stored: {fwd_stored}")
    cache, sus, t0 = {}, [], time.perf_counter()
    for i, f in enumerate(feats):
        v = pd.read_parquet(panel_path, columns=[f])[f]
        v = pd.to_numeric(v, errors="coerce").to_numpy("float64")[order][res]
        r = RC.screen_feature_leakage(v, close, code, _cache=cache)
        if r["suspect"]:
            sus.append((f, r["max_abs_future_rho"]))
    _line(OK if not sus else FAIL,
          f"{len(feats)} features screened in {time.perf_counter()-t0:.0f}s | "
          f"{len(sus)} suspect (|rho with a future day| > 0.15)")
    for f, v in sorted(sus, key=lambda x: -x[1])[:15]:
        print(f"         {f:<36} max |rho| {v:.3f}")
    if sus:
        problems.append(f"{len(sus)} features correlate with future returns")

    sessions = np.sort(keys["timestamp"].unique())
    return {"problems": problems, "sessions": sessions, "keys": keys, "cols": cols}


def smoke_panel(panel_path: Path, sessions, n_symbols: int, seed: int = 0) -> Path:
    """A symbol subset that ENDS at the research end date - no lockbox inside."""
    import research_common as RC
    r_end, lb = RC.lockbox_bounds(sessions, RC.DEFAULT_LOCKBOX_FRACTION, 5)
    syms = pd.read_parquet(panel_path, columns=["symbol"])["symbol"].astype(str).unique()
    rng = np.random.default_rng(seed)
    pick = sorted(rng.choice(syms, min(n_symbols, len(syms)), replace=False).tolist())
    df = pd.read_parquet(panel_path, filters=[("symbol", "in", pick)])
    df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.tz_localize(None)
    df = df[df["timestamp"] <= pd.Timestamp(r_end)]
    out = panel_path.parent.parent / "smoke" / "panel"
    out.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out / "panel.parquet", index=False)
    (out / "panel_meta.json").write_text(json.dumps({
        "build_signature": f"smoke_{len(pick)}_{str(r_end)[:10]}", "rows": len(df),
        "symbols": len(pick), "last_session": str(pd.Timestamp(r_end).date()),
        "note": "SMOKE subset: ends at the real research end; no lockbox sessions"}),
        encoding="utf-8")
    print(f"  smoke panel: {len(pick)} symbols, {len(df):,} rows, ends "
          f"{pd.Timestamp(r_end).date()} (real lockbox starts {pd.Timestamp(lb).date()})")
    return out / "panel.parquet"


def run_tools(sp: Path, full_rows: int) -> None:
    import tracemalloc
    import feature_atlas as FA
    import regime_research as RR
    rows = len(pd.read_parquet(sp, columns=["symbol"]))
    scale = full_rows / max(rows, 1)
    for nm, fn in (("feature_atlas", lambda: FA.run(sp, overrides={"n_splits": 3}, verbose=False)),
                   ("regime_research", lambda: RR.run(sp, overrides={
                       "n_splits": 3, "n_sentinels": 12, "perm_repeats": 2}, verbose=False))):
        tracemalloc.start(); t0 = time.perf_counter()
        try:
            fn(); st = OK
        except Exception as e:
            st = FAIL; print(f"         {type(e).__name__}: {e}")
        el = time.perf_counter() - t0
        _, pk = tracemalloc.get_traced_memory(); tracemalloc.stop()
        _line(st, f"{nm}: {el/60:.1f} min, peak {pk/1e9:.2f} GB on {rows:,} rows "
                  f"-> rough full-panel estimate {el*scale/3600:.1f} h (scales ~linearly "
                  f"in rows; full defaults add more sentinels/repeats)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=None)
    ap.add_argument("--run-tools", action="store_true")
    ap.add_argument("--symbols", type=int, default=120)
    a = ap.parse_args()
    root = a.root or os.environ.get("CACHE_DAILY_ROOT")
    if not root:
        raise SystemExit("CACHE_DAILY_ROOT not set and --root not given")
    pp = Path(root) / "panel" / "panel.parquet"
    pf = preflight(pp)
    if a.run_tools:
        print("\n=== 5. TOOLS ON A LOCKBOX-FREE SUBSET ===")
        sp = smoke_panel(pp, pf["sessions"], a.symbols)
        run_tools(sp, len(pf["keys"]))
    print("\n" + "=" * 64)
    if pf["problems"]:
        print("  SMOKE TEST FAILED - fix before any long run:")
        for p_ in pf["problems"]:
            print(f"    - {p_}")
        return 1
    print("  SMOKE TEST PASSED" + ("" if a.run_tools else
          " (preflight only - add --run-tools to exercise the tools)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
