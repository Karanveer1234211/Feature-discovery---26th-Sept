#!/usr/bin/env python3
"""
bucket_report.py - every model, every bucket, every exit bracket, every quarter.

    python bucket_report.py --root %CACHE_DAILY_ROOT%
    python bucket_report.py --root %CACHE_DAILY_ROOT% --run RUN_20260926_002

Reads a finished regime_research run. NO RETRAINING: the saved walk-forward
predictions already are the out-of-sample backtest of each model.

    models    every model in the run (M0..M4), research folds
              + the locked model on the lockbox (descriptive: already spent)
    buckets   daily top-1 / top-3 / top-5 / top-10 by RAW score,
              and score deciles 1..10 (10 = the model's favourites)
    brackets  every exit bracket stored in the panel (label_exit_ret_<suffix>)
              - the SAME picks, scored under each exit rule
    quarters  calendar quarters

Net return per trade = realised bracket return - cost. Excess = the bucket's
daily net minus the equal-weight average of every stock that day under the
same bracket and cost ("buy everything"). One number per day, then averaged:
the day is the unit, because the decision is made once per day.

READ IT AS DESCRIPTION, NOT SELECTION. Many cells compared on data already
studied: the best-looking cell is partly luck. The models were trained for the
atr1p5_1p0 bracket, so other brackets show how the exit rule changes outcomes
for picks that were not built for it. What gets traded is decided forward.

Writes <run>/bucket_report.html (open in a browser) and bucket_report.csv.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import research_common as RC  # noqa: E402

TOP_N = (1, 3, 5, 10)
PRIMARY = "atr1p5_1p0"
BRACKET_NAMES = {"5p3": "fixed +5% / -3%", "3p2": "fixed +3% / -2%",
                 "atr1p5_1p0": "ATR +1.5 / -1.0 (trained on)",
                 "atr2p0_1p0": "ATR +2.0 / -1.0", "atr1p0_1p0": "ATR +1.0 / -1.0"}
MODEL_NOTES = {"M0_all_features": "every panel feature, no states",
               "M1_base": "5 base features",
               "M2_regime": "base + stock-state inputs",
               "M3_families": "base + selected feature families",
               "M4_interactions": "base + families + state x feature interactions"}


def _naive(ts):
    t = pd.to_datetime(ts)
    if getattr(t.dt, "tz", None) is not None:
        t = t.dt.tz_localize(None)
    return t


def load_run(root: Path, run: str | None):
    base = root / "panel" / "research"
    runs = sorted(p for p in base.glob("RUN_*") if (p / "p6_pred").exists())
    if not runs:
        raise SystemExit(f"no finished runs under {base}")
    rd = base / run if run else runs[-1]
    files = sorted((rd / "p6_pred").glob("*_fold*.parquet"))
    research = []
    for f in files:
        d = pd.read_parquet(f, columns=["timestamp", "symbol", "p_raw"])
        d["model"] = f.stem.rsplit("_fold", 1)[0]
        research.append(d)
    research = pd.concat(research, ignore_index=True)
    research["timestamp"] = _naive(research["timestamp"])
    lock, locked_model = None, None
    lp, hp = rd / "lockbox_predictions.parquet", rd / "lockbox_hypothesis.json"
    if lp.exists() and hp.exists():
        locked_model = json.loads(hp.read_text(encoding="utf-8"))["model"]
        lock = pd.read_parquet(lp, columns=["timestamp", "symbol", "p_raw"])
        lock["timestamp"] = _naive(lock["timestamp"])
        lock["model"] = locked_model
    return rd, research, lock, locked_model


def labels(root: Path, brackets):
    cols = ["timestamp", "symbol"] + [f"label_exit_ret_{b}" for b in brackets]
    lab = pd.read_parquet(root / "panel" / "panel.parquet", columns=cols)
    lab["timestamp"] = _naive(lab["timestamp"])
    return lab


def analyse(d: pd.DataFrame, brackets, cost: float, period: str, boot_B: int = 1000):
    """One model's predictions -> tidy rows (model, bracket, bucket, quarter, ...)."""
    d = d.sort_values(["timestamp", "symbol"]).reset_index(drop=True)
    g = d.groupby("timestamp")["p_raw"]
    d["rk"] = g.rank(ascending=False, method="first")
    n_day = g.transform("size")
    d["dec"] = np.clip(np.ceil((1 - (d["rk"] - 1) / n_day) * 10), 1, 10).astype(int)
    q = d["timestamp"].dt.to_period("Q").astype(str)
    rows, pooled = [], []
    model = d["model"].iloc[0]
    for b in brackets:
        net = d[f"label_exit_ret_{b}"] - cost / 1e4
        ok = net.notna()
        uni = net[ok].groupby(d.loc[ok, "timestamp"]).mean()
        dq = pd.Series(pd.DatetimeIndex(uni.index).to_period("Q").astype(str), index=uni.index)
        for qq, v in uni.groupby(dq):
            rows.append({"period": period, "model": model, "bracket": b, "bucket": "all",
                         "quarter": qq, "days": len(v), "net_bp": v.mean() * 1e4,
                         "excess_bp": 0.0, "hit": float((net[ok & (q == qq)] > 0).mean())})
        buckets = [(f"top-{n}", d["rk"] <= n) for n in TOP_N] + \
                  [(f"decile-{k}", d["dec"] == k) for k in range(1, 11)]
        for name, m in buckets:
            mm = m & ok
            day = net[mm].groupby(d.loc[mm, "timestamp"]).mean()
            ex = (day - uni.reindex(day.index)).dropna()
            hit_day = (net[mm] > 0).groupby(d.loc[mm, "timestamp"]).mean()
            dqq = pd.Series(pd.DatetimeIndex(day.index).to_period("Q").astype(str),
                            index=day.index)
            for qq in sorted(dqq.unique()):
                sel = dqq == qq
                rows.append({"period": period, "model": model, "bracket": b, "bucket": name,
                             "quarter": qq, "days": int(sel.sum()),
                             "net_bp": day[sel].mean() * 1e4,
                             "excess_bp": ex.reindex(day.index[sel]).mean() * 1e4,
                             "hit": hit_day[sel].mean()})
            if name.startswith("top-") or name in ("decile-10", "decile-1"):
                bn = RC.block_bootstrap_mean(day.to_numpy(), B=boot_B)
                bx = RC.block_bootstrap_mean(ex.to_numpy(), B=boot_B)
                pooled.append({"period": period, "model": model, "bracket": b, "bucket": name,
                               "days": len(day), "net_bp": bn["mean"] * 1e4,
                               "net_lo": bn["lo"] * 1e4, "net_hi": bn["hi"] * 1e4,
                               "excess_bp": bx["mean"] * 1e4, "excess_lo": bx["lo"] * 1e4,
                               "excess_hi": bx["hi"] * 1e4, "hit": float(hit_day.mean())})
            elif name.startswith("decile-"):
                pooled.append({"period": period, "model": model, "bracket": b, "bucket": name,
                               "days": len(day), "net_bp": day.mean() * 1e4,
                               "excess_bp": ex.mean() * 1e4, "hit": float(hit_day.mean())})
        bu = RC.block_bootstrap_mean(uni.to_numpy(), B=boot_B)
        pooled.append({"period": period, "model": model, "bracket": b, "bucket": "all",
                       "days": len(uni), "net_bp": bu["mean"] * 1e4, "net_lo": bu["lo"] * 1e4,
                       "net_hi": bu["hi"] * 1e4, "excess_bp": 0.0})
    return rows, pooled


# ----------------------------------------------------------------------
# HTML
# ----------------------------------------------------------------------
CSS = """
:root{--bg:#fff;--fg:#1d1d1f;--mut:#6e6e73;--line:#e5e5ea;--pos:22,163,74;--neg:220,38,38}
@media (prefers-color-scheme:dark){:root{--bg:#111113;--fg:#f2f2f7;--mut:#a1a1a6;--line:#2c2c2e}}
body{background:var(--bg);color:var(--fg);font:14px/1.5 -apple-system,Segoe UI,Roboto,Arial,sans-serif;
max-width:1180px;margin:0 auto;padding:24px 16px 64px}
h1{font-size:24px;margin:0 0 4px}h2{font-size:18px;margin:36px 0 6px}h3{font-size:15px;margin:22px 0 6px}
p.note,.mut{color:var(--mut)}.wrap{overflow-x:auto;border:1px solid var(--line);border-radius:10px;margin:8px 0}
table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}
th,td{padding:6px 9px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}
th{position:sticky;top:0;background:var(--bg);font-weight:600}td:first-child,th:first-child{text-align:left}
.ci{color:var(--mut);font-size:12px}.box{border-left:3px solid #f59e0b;padding:8px 12px;margin:14px 0;
background:rgba(245,158,11,.08);border-radius:4px}
"""


def _cell(v, scale=100.0, ci=None, pct=False):
    if v is None or not np.isfinite(v):
        return "<td class='mut'>-</td>"
    a = min(abs(v) / scale, 1.0) * 0.55
    rgb = "var(--pos)" if v > 0 else "var(--neg)"
    txt = f"{v:.0%}" if pct else f"{v:+.0f}"
    extra = f"<br><span class='ci'>[{ci[0]:+.0f}, {ci[1]:+.0f}]</span>" if ci else ""
    return f"<td style='background:rgba({rgb},{a:.2f})'>{txt}{extra}</td>"


def _table(head, body):
    h = "".join(f"<th>{html.escape(str(x))}</th>" for x in head)
    return f"<div class='wrap'><table><tr>{h}</tr>{''.join(body)}</table></div>"


def build_html(rd, grid, pooled, brackets, cost, locked_model, models):
    P = pooled
    R = P[P["period"] == "research"]
    out = [f"<!doctype html><html><head><meta charset='utf-8'>"
           f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
           f"<title>Bucket report - {rd.name}</title><style>{CSS}</style></head><body>",
           f"<h1>Models x buckets x brackets x quarters</h1>",
           f"<p class='mut'>{html.escape(rd.name)} | walk-forward out-of-sample predictions, "
           f"no retraining | net of {cost:.0f} bp per trade | built "
           f"{dt.datetime.now():%Y-%m-%d %H:%M}</p>",
           "<div class='box'><b>Description, not selection.</b> Many cells are compared on data "
           "already studied, so the best-looking one is partly luck. The models were trained for "
           "the ATR +1.5 / -1.0 bracket; other brackets show the same picks under different exit "
           "rules. What gets traded is decided by the forward paper test.</div>"]

    # 1. headline
    out.append("<h2>1. Research folds, all quarters pooled (trained bracket)</h2>"
               "<p class='note'>Net return and excess over buying everything, bp per trade, with "
               "95% block-bootstrap intervals over trading days.</p>")
    body = []
    for m in models:
        cells = [f"<td><b>{html.escape(m)}</b><br><span class='ci'>{html.escape(MODEL_NOTES.get(m, ''))}</span></td>"]
        for n in TOP_N:
            r = R[(R.model == m) & (R.bracket == PRIMARY) & (R.bucket == f"top-{n}")]
            if len(r):
                r = r.iloc[0]
                cells.append(_cell(r.net_bp, ci=(r.net_lo, r.net_hi)))
                cells.append(_cell(r.excess_bp, ci=(r.excess_lo, r.excess_hi)))
            else:
                cells += ["<td>-</td>", "<td>-</td>"]
        body.append("<tr>" + "".join(cells) + "</tr>")
    head = ["model"] + [f"{k} top-{n}" for n in TOP_N for k in ("net", "excess")]
    out.append(_table(head, body))
    u = R[(R.bucket == "all") & (R.bracket == PRIMARY)]
    if len(u):
        u = u.iloc[0]
        out.append(f"<p class='note'>Buy everything (same bracket and cost): {u.net_bp:+.0f} bp "
                   f"[{u.net_lo:+.0f}, {u.net_hi:+.0f}] per trade.</p>")

    # 2. quarters
    G = grid[(grid.bracket == PRIMARY)]
    for metric, title in (("excess_bp", "excess over buying everything"), ("net_bp", "net return")):
        out.append(f"<h2>2{'a' if metric == 'excess_bp' else 'b'}. Top-3 {title} by quarter "
                   f"(trained bracket)</h2>")
        qs = sorted(G["quarter"].unique())
        body = []
        for qq in qs:
            cells = [f"<td>{qq}</td>"]
            allq = G[(G.quarter == qq) & (G.bucket == "all")]
            cells.append(_cell(allq["net_bp"].mean() if len(allq) else np.nan)
                         if metric == "net_bp" else "")
            for m in models:
                for per in ("research", "lockbox"):
                    r = G[(G.quarter == qq) & (G.model == m) & (G.bucket == "top-3") & (G.period == per)]
                    if len(r):
                        cells.append(_cell(r.iloc[0][metric]) if per == "research" else
                                     _cell(r.iloc[0][metric]).replace("<td", "<td title='lockbox'"))
                        break
                else:
                    cells.append("<td class='mut'>-</td>")
            body.append("<tr>" + "".join(c for c in cells if c) + "</tr>")
        head = ["quarter"] + (["buy everything"] if metric == "net_bp" else []) + models
        out.append(_table(head, body))
    out.append(f"<p class='note'>Quarters after the research end come from the lockbox and exist "
               f"only for the locked model ({html.escape(str(locked_model))}); every other model "
               f"shows '-' there.</p>")

    # 3. deciles
    out.append("<h2>3. Does a higher score mean a better trade? Score deciles (research, trained "
               "bracket)</h2><p class='note'>Mean net return per trade by decile of the model's daily "
               "score; 10 = its favourites. A working model slopes upward from left to right.</p>")
    body = []
    for m in models:
        cells = [f"<td>{html.escape(m)}</td>"]
        for k in range(1, 11):
            r = R[(R.model == m) & (R.bracket == PRIMARY) & (R.bucket == f"decile-{k}")]
            cells.append(_cell(r.iloc[0].net_bp, scale=60) if len(r) else "<td>-</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    out.append(_table(["model"] + [f"D{k}" for k in range(1, 11)], body))

    # 4. brackets
    out.append("<h2>4. Bracket by bracket - the same picks under each exit rule (research, "
               "top-3)</h2><p class='note'>Net return, then excess, bp per trade. Picks were built "
               "for the ATR +1.5 / -1.0 bracket.</p>")
    body = []
    for b in brackets:
        cells = [f"<td>{html.escape(BRACKET_NAMES.get(b, b))}</td>"]
        uu = R[(R.bracket == b) & (R.bucket == "all")]
        cells.append(_cell(uu.iloc[0].net_bp) if len(uu) else "<td>-</td>")
        for m in models:
            r = R[(R.model == m) & (R.bracket == b) & (R.bucket == "top-3")]
            if len(r):
                r = r.iloc[0]
                cells.append(_cell(r.net_bp, ci=(r.net_lo, r.net_hi)))
                cells.append(_cell(r.excess_bp, ci=(r.excess_lo, r.excess_hi)))
            else:
                cells += ["<td>-</td>", "<td>-</td>"]
        body.append("<tr>" + "".join(cells) + "</tr>")
    head = ["bracket", "buy everything"] + [f"{m} {k}" for m in models for k in ("net", "excess")]
    out.append(_table(head, body))
    base = "M0_all_features" if "M0_all_features" in models else models[0]
    out.append(f"<h3>{html.escape(base)}, top-3 net return by quarter and bracket (research)</h3>")
    Gm = grid[(grid.model == base) & (grid.bucket == "top-3") & (grid.period == "research")]
    body = []
    for qq in sorted(Gm["quarter"].unique()):
        cells = [f"<td>{qq}</td>"]
        for b in brackets:
            r = Gm[(Gm.quarter == qq) & (Gm.bracket == b)]
            cells.append(_cell(r.iloc[0].net_bp) if len(r) else "<td>-</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    out.append(_table(["quarter"] + [BRACKET_NAMES.get(b, b) for b in brackets], body))

    # 5. lockbox
    L = P[P["period"] == "lockbox"]
    if len(L):
        out.append(f"<h2>5. Lockbox - {html.escape(str(locked_model))} only (already spent; "
                   f"descriptive)</h2><p class='note'>Every bucket and bracket. These numbers can no "
                   f"longer choose anything; they show how the locked model behaved on the two "
                   f"hardest years.</p>")
        body = []
        for b in brackets:
            cells = [f"<td>{html.escape(BRACKET_NAMES.get(b, b))}</td>"]
            uu = L[(L.bracket == b) & (L.bucket == "all")]
            cells.append(_cell(uu.iloc[0].net_bp) if len(uu) else "<td>-</td>")
            for n in TOP_N:
                r = L[(L.bracket == b) & (L.bucket == f"top-{n}")]
                if len(r):
                    r = r.iloc[0]
                    cells.append(_cell(r.net_bp, ci=(r.net_lo, r.net_hi)))
                    cells.append(_cell(r.excess_bp, ci=(r.excess_lo, r.excess_hi)))
                else:
                    cells += ["<td>-</td>", "<td>-</td>"]
            body.append("<tr>" + "".join(cells) + "</tr>")
        out.append(_table(["bracket", "buy everything"] +
                          [f"{k} top-{n}" for n in TOP_N for k in ("net", "excess")], body))

    out.append("<h2>Caveats</h2><p class='note'>One flat cost per trade; no slippage beyond it, no "
               "gaps through stops, no position sizing, capacity or tax. Excess is measured against "
               "an equal-weight basket that cannot itself be shorted. Quarter cells cover roughly "
               "60 trading days each, so single quarters are noisy - look for patterns across many "
               "quarters, not one standout cell.</p></body></html>")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=None)
    ap.add_argument("--run", default=None, help="run folder name; default = latest finished run")
    ap.add_argument("--cost-bps", type=float, default=35.0)
    a = ap.parse_args()
    root = Path(a.root or os.environ.get("CACHE_DAILY_ROOT") or "")
    if not str(root):
        raise SystemExit("CACHE_DAILY_ROOT not set and --root not given")
    import pyarrow.parquet as pq
    schema = pq.ParquetFile(root / "panel" / "panel.parquet").schema_arrow.names
    brackets = [b for b in BRACKET_NAMES if f"label_exit_ret_{b}" in schema]
    rd, research, lock, locked_model = load_run(root, a.run)
    print(f"run {rd.name}: {research['model'].nunique()} models, {len(research):,} research "
          f"predictions" + (f", lockbox {len(lock):,} ({locked_model})" if lock is not None else "")
          + f" | brackets: {', '.join(brackets)}", flush=True)
    lab = labels(root, brackets)
    models = [m for m in MODEL_NOTES if m in set(research["model"])] + \
             sorted(set(research["model"]) - set(MODEL_NOTES))
    rows, pooled = [], []
    for m in models:
        d = research[research["model"] == m].merge(lab, on=["timestamp", "symbol"], how="left")
        r, p_ = analyse(d, brackets, a.cost_bps, "research")
        rows += r; pooled += p_
        print(f"  {m}: done", flush=True)
    if lock is not None:
        d = lock.merge(lab, on=["timestamp", "symbol"], how="left")
        r, p_ = analyse(d, brackets, a.cost_bps, "lockbox")
        rows += r; pooled += p_
        print(f"  lockbox ({locked_model}): done", flush=True)
    grid, pooled = pd.DataFrame(rows), pd.DataFrame(pooled)
    grid.to_csv(rd / "bucket_report.csv", index=False)
    (rd / "bucket_report.html").write_text(
        build_html(rd, grid, pooled, brackets, a.cost_bps, locked_model, models), encoding="utf-8")
    print(f"\nreport: {rd / 'bucket_report.html'}\ndata:   {rd / 'bucket_report.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
