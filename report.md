# Regime + Feature Research - RUN_20260926_002

Panel: `C:\QuantData\cache_daily\panel\panel.parquet`  
Build signature: `b7feac2e004393a3`  
Code: regime_research v9 | config hash `dbb1474f59033a76`

## Timing contract

_Prediction is made at the CLOSE of session T. Every feature uses data through the close of T and nothing later. The target covers sessions T+1..T+H, entered at the close of T. Same-day market state (breadth, median move, dispersion) is therefore legitimate: it is known at T close._

Checked against the data on 300,000 rows: corr(forward return, same-day return) **+0.008** (must be ~0); corr(forward return, next-day return) **+0.425** (must be clearly positive). A label containing session T would fail the first.

## Features per fold (fold-local selection)

Fold k uses only screens from folds 1..k, each computed on a train window that ends before fold k's test. The all-folds set is used for the lockbox model alone.

Each name REPRESENTS A FAMILY: permutation importance shuffled the whole family together, so the named feature is a proxy for the family's information, not independently proven. Family clustering is fold-local and survival is tracked per FEATURE - family IDs are not comparable across folds. 'Beats the null' is a screen, not a significance test.

- fold 1: `D_bb_pctB_20`, `D_close_roll_slope_20`, `D_days_since_boh_20`, `D_dist_from_20h`, `D_mdi14`, `D_midpoint_slope`, `D_pdi14`, `ema50_slope10`, `D_atr_pct_z252`, `D_atr_ratio_14_30`, `INDIAVIX_close`, `D_dist_from_52wl`, `D_atr14`, `D_obv`, `D_amihud_20`, `D_realvol_ratio_20_60`, `D_donch_pos_20_rmean50`, `D_upside_vol_ratio`, `MKT_D_rsi14`, `NIFTYMETAL_ret_1d`, `D_WQ_13`, `MKT_D_adx14`, `INDIAVIX_ret_1d`, `NIFTYPHARMA_close`, `NIFTYPSUBANK_close`
- fold 2: `MKT_D_drawdown_252`, `D_bb_pctB_20`, `D_close_roll_slope_20`, `D_days_since_boh_20`, `ema50_slope10`, `X_rank_D_dist_from_52wl`, `NIFTYCONSUMPTION_close`, `D_atr_pct_z252`, `D_donch_pos_20_rmean50`, `MKT_D_realvol_20`, `D_atr14`, `D_amihud_20`, `volume`, `D_WQ_13`, `INDIAVIX_ret_1d`, `D_macd_hist`, `NIFTYIT_ret_1d`, `NIFTYPHARMA_ret_1d`, `D_WQ_33`, `D_WQ_20`, `X_rank_D_gap_pct`, `D_body_ratio_rmean20`, `X_relvol_20`
- fold 3: `MKT_D_drawdown_252`, `MKT_D_rsi14`, `D_atr_pct_z252`, `D_dist_from_52wh`, `D_dist_from_52wl`, `D_donch_pos_20_rmean50`, `MKT_D_realvol_20`, `D_atr14`, `D_dollar_vol`, `D_WQ_33`, `D_macd_hist`, `D_WQ_20`, `X_rank_D_gap_pct`, `NIFTYPHARMA_ret_1d`
- fold 4: `MKT_D_rsi14`, `D_atr_pct_z252`, `D_dist_from_52wh`, `D_dist_from_52wl`, `D_donch_pos_50_rmean50`, `MKT_D_realvol_20`, `D_atr14`, `D_WQ_33`, `D_WQ_41`, `D_macd_hist`, `D_dollar_vol`, `D_WQ_20`, `X_rank_D_gap_pct`, `NIFTYPHARMA_ret_1d`
- fold 5: `D_dist_from_52wh`, `D_dist_from_52wl`, `D_donch_pos_50_rmean50`, `D_atr14`, `D_WQ_33`, `D_WQ_41`, `D_macd_hist`, `macd_slope5`, `D_WQ_20`, `X_rank_D_gap_pct`, `NIFTYPHARMA_ret_1d`, `D_atr_ratio_14_30`, `D_days_since_boh_20`, `D_close_roll_slope_20`, `NIFTYMEDIA_close`, `NIFTYINFRA_ret_1d`, `NIFTYREALTY_ret_1d`, `D_atr_pct_z252`, `MKT_D_rsi14`, `CRUDEOIL_close`, `D_realvol_ratio_20_60`, `D_downside_dev_60`, `D_realvol_20`, `D_vol_yz_20`, `D_amihud_20`

## Incremental model comparison

Net return per trade = realised bracket return (`label_exit_ret`) minus 35 bp. Intervals are 95% circular block bootstraps over TRADING DAYS (block 10) - 5-session labels overlap, so trades are not independent and a binomial SE would be ~2x too narrow. **clears** = the lower end of the net interval is above 0.

**M0** uses every panel feature with no regimes - the model the feasibility test passed with. If M0 beats M2-M4, the regime machinery adds nothing beyond using all the information.

**How to read the steps.** M1->M2: does a STATE REPRESENTATION of variables largely already in the library add out-of-sample information? (It is not a test of whether regime discovery found a new information source.) M2->M3: do the selected feature families add to that? M3->M4: do regime x feature interactions add - but only the first five representatives are crossed, so a null M4 means THAT subset added nothing, not that interactions do not matter.

| model | AUC | brier | top-1 net bp | top-3 hit | top-3 net bp [95%] | clears |
|---|---|---|---|---|---|---|
| M0_all_features | 0.5297 | 0.2102 | +85 | 0.411 | +45 [+21,+71] | top-1, top-3, top-5, top-10 |
| M1_base | 0.5377 | 0.2035 | +79 | 0.394 | +35 [+12,+59] | top-1, top-3, top-5 |
| M2_regime | 0.5242 | 0.2040 | +42 | 0.382 | +18 [-3,+41] | top-1 |
| M3_families | 0.5280 | 0.2043 | +64 | 0.421 | +42 [+19,+66] | top-1, top-3, top-5, top-10 |
| M4_interactions | 0.5259 | 0.2055 | +72 | 0.426 | +51 [+27,+76] | top-1, top-3, top-5, top-10 |

### Picks are ranked by the raw model score

Ranking M4_interactions's research predictions by the CALIBRATED probability (897 distinct values across all rows) would have left the daily top-3 to an alphabetical tie-break on **77% of 1801 days**, and on average only **55%** of those picks would have matched the model's actual top-3. Calibration is monotone, so the raw score has the same ordering without the ties; calibrated probabilities are used only where a probability is needed (calibration table, Brier, logloss).

## Stock-state regime as a trade filter (M4_interactions, daily top-3) - HYPOTHESIS GENERATION

Research folds only. Choosing the regimes that clear here and then quoting their performance would be another backtest. The choice is LOCKED below and tested once on the untouched lockbox; only that lockbox figure is evidence.

| regime | dates | top-3 hit | top-3 net bp [95%] | clears |
|---|---|---|---|---|
| R0 | 1801 | 0.312 | -5 [-36,+27] | no |
| R1 | 1801 | 0.342 | +5 [-19,+31] | no |
| R2 | 1800 | 0.317 | -8 [-36,+20] | no |
| R3 | 1801 | 0.376 | +8 [-13,+30] | no |
| R4 | 1801 | 0.338 | -1 [-25,+24] | no |
| R5 | 1801 | 0.367 | +16 [-9,+44] | no |
| R6 | 1801 | 0.378 | +4 [-14,+24] | no |
| R7 | 1801 | 0.408 | +41 [+21,+61] | YES |
| R8 | 1801 | 0.367 | +2 [-18,+23] | no |

Regime IDs are ALIGNED across folds (K fixed from fold 1, Hungarian matching on centroids); check drift below before trusting an ID's identity over time.

### Performance by stock-state completeness (research folds)

Rows with missing state inputs are scored on observed axes. If partial rows perform materially worse, they need a confidence adjustment or a missingness-aware feature.

| state inputs observed | dates | top-3 hit | top-3 net bp [95%] |
|---|---|---|---|
| 8/8 | 1801 | 0.426 | +51 [+27,+76] |
| 7/8 | 42 | 0.167 | -35 [-35,-35] |

## Feature-by-regime rank IC (descriptive, fold 5 test)

Rank IC of each representative against the target, computed separately inside each regime. `.` = |IC| < 0.01.

| feature | R0 | R1 | R2 | R3 | R4 | R5 | R6 | R7 | R8 |
|---|---|---|---|---|---|---|---|---|---|
| `D_dist_from_52wh` | -0.014 | +0.040 | +0.041 | +0.062 | +0.020 | -0.015 | +0.014 | . | +0.045 |
| `D_dist_from_52wl` | +0.028 | +0.052 | +0.032 | +0.051 | +0.039 | +0.014 | +0.018 | +0.029 | +0.047 |
| `D_donch_pos_50_rmean50` | +0.014 | +0.034 | . | +0.025 | +0.012 | . | +0.016 | . | +0.022 |
| `D_atr14` | -0.034 | -0.026 | -0.010 | -0.030 | -0.019 | -0.035 | . | -0.049 | -0.019 |
| `D_WQ_33` | +0.043 | -0.027 | +0.015 | -0.045 | -0.013 | . | . | -0.020 | -0.015 |
| `D_macd_hist` | . | . | . | . | . | . | -0.021 | -0.046 | -0.015 |
| `macd_slope5` | -0.042 | . | . | . | -0.026 | -0.039 | -0.039 | -0.024 | -0.024 |
| `D_WQ_20` | . | -0.037 | . | -0.031 | -0.030 | -0.014 | . | -0.025 | -0.028 |
| `X_rank_D_gap_pct` | +0.017 | . | . | +0.012 | . | . | -0.022 | +0.024 | . |
| `NIFTYPHARMA_ret_1d` | . | +0.051 | +0.015 | +0.023 | +0.040 | +0.029 | +0.034 | +0.014 | +0.028 |
| `D_atr_ratio_14_30` | -0.022 | -0.029 | -0.017 | . | -0.015 | -0.030 | -0.027 | . | -0.025 |
| `D_days_since_boh_20` | +0.010 | -0.012 | -0.024 | -0.037 | . | +0.034 | . | +0.011 | . |
| `D_close_roll_slope_20` | +0.023 | +0.020 | +0.013 | . | +0.023 | . | +0.011 | -0.038 | . |
| `NIFTYMEDIA_close` | -0.036 | +0.061 | +0.011 | +0.057 | +0.022 | . | +0.023 | +0.020 | +0.041 |
| `NIFTYINFRA_ret_1d` | . | +0.081 | +0.013 | +0.055 | +0.068 | +0.061 | +0.054 | +0.031 | +0.054 |

## Stock-state regimes (K=9)

These are RELATIVE STOCK states - per-date cross-sectional ranks, so 'high RSI' means high versus peers TODAY, not RSI above some level - and not market regimes. Market state enters the models as separate features.

**What BIC does and does not say.** K was chosen by BIC on fold 1: the mixture that best DESCRIBES the state distribution. That is a clustering criterion, not evidence the states predict anything. Three separate questions, three separate answers:

- description (BIC): K=9
- stability (centroid drift vs fold 1): f1 0.000, f2 0.318, f3 0.189, f4 0.270, f5 0.270
- predictive value: M2 minus M1 in the comparison table above

**Missing state inputs** (scored on observed axes, never imputed):

| fold | rows with any missing | all missing | conf complete | conf partial | conf all-missing |
|---|---|---|---|---|---|
| 1 | 0.00% | 0.00% | 0.804 | nan | nan |
| 2 | 0.00% | 0.00% | 0.800 | nan | nan |
| 3 | 0.00% | 0.00% | 0.796 | nan | nan |
| 4 | 0.00% | 0.00% | 0.795 | nan | nan |
| 5 | 0.00% | 0.00% | 0.788 | 0.878 | nan |

### Centroids (fold 5 engine, aligned)

Centroids are centred per-date ranks: +0.5 = top of the cross-section today, -0.5 = bottom.

| regime | trend | trend_strength | vol_level | vol_change | momentum | participation | location | shock |
|---|---|---|---|---|---|---|---|---|
| R0 | -0.38 | +0.06 | +0.36 | +0.12 | -0.26 | -0.05 | -0.14 | +0.12 |
| R1 | -0.00 | -0.34 | -0.10 | -0.07 | -0.02 | +0.03 | -0.04 | -0.06 |
| R2 | +0.23 | +0.21 | +0.40 | +0.40 | +0.18 | -0.03 | +0.04 | +0.06 |
| R3 | +0.33 | +0.00 | +0.14 | +0.08 | +0.28 | +0.39 | +0.10 | +0.41 |
| R4 | -0.17 | -0.06 | -0.05 | -0.09 | -0.16 | -0.38 | -0.07 | -0.08 |
| R5 | -0.28 | -0.00 | +0.01 | -0.01 | -0.27 | +0.07 | -0.16 | +0.03 |
| R6 | -0.15 | -0.02 | -0.38 | -0.20 | -0.26 | +0.02 | -0.15 | -0.14 |
| R7 | +0.37 | +0.18 | +0.07 | +0.06 | +0.38 | +0.08 | +0.41 | -0.00 |
| R8 | +0.15 | +0.13 | -0.05 | -0.02 | +0.17 | +0.02 | +0.04 | -0.05 |

K chosen by BIC per fold: fold 1: 9, fold 2: 9, fold 3: 9, fold 4: 9, fold 5: 9

## Persistence (measured, never imposed)

| regime | P(stay) | mean run | median run |
|---|---|---|---|
| R0 | 0.72 | 3.5 | 2 |
| R1 | 0.65 | 2.9 | 2 |
| R2 | 0.73 | 3.6 | 2 |
| R3 | 0.20 | 1.3 | 1 |
| R4 | 0.43 | 1.7 | 1 |
| R5 | 0.57 | 2.3 | 1 |
| R6 | 0.68 | 3.1 | 2 |
| R7 | 0.73 | 3.6 | 2 |
| R8 | 0.66 | 2.9 | 2 |

## Feature survival funnel

- hygiene rejected: 19
- duplicates removed (|r|>=0.999): 21
- candidates entering each fold: 236
- stable (beat fold-local null in >= 80% of folds): 111
- family representatives kept: 25

Representatives: `D_dist_from_52wh`, `D_dist_from_52wl`, `D_donch_pos_50_rmean50`, `D_atr14`, `D_WQ_33`, `D_macd_hist`, `macd_slope5`, `D_WQ_20`, `X_rank_D_gap_pct`, `NIFTYPHARMA_ret_1d`, `D_atr_ratio_14_30`, `D_days_since_boh_20`, `D_close_roll_slope_20`, `NIFTYMEDIA_close`, `NIFTYINFRA_ret_1d`, `NIFTYREALTY_ret_1d`, `D_atr_pct_z252`, `MKT_D_rsi14`, `CRUDEOIL_close`, `D_realvol_ratio_20_60`, `D_downside_dev_60`, `D_realvol_20`, `D_vol_yz_20`, `D_amihud_20`, `D_obv`

| feature | folds survived | survival | mean family importance |
|---|---|---|---|
| `D_dist_from_52wh` | 5/5 | 100% | +0.00329 |
| `D_dist_from_52wl` | 5/5 | 100% | +0.00329 |
| `D_drawdown_252` | 5/5 | 100% | +0.00329 |
| `D_ema_stack_20_50_100` | 5/5 | 100% | +0.00329 |
| `D_pos_in_52w_range` | 5/5 | 100% | +0.00329 |
| `X_rank_D_dist_from_52wh` | 5/5 | 100% | +0.00329 |
| `X_rank_D_drawdown_252` | 5/5 | 100% | +0.00329 |
| `X_rank_D_pos_in_52w_range` | 5/5 | 100% | +0.00329 |
| `X_z_D_dist_from_52wh` | 5/5 | 100% | +0.00329 |
| `X_z_D_drawdown_252` | 5/5 | 100% | +0.00329 |
| `X_z_D_pos_in_52w_range` | 5/5 | 100% | +0.00329 |
| `dist_ema20_ema50_atr` | 5/5 | 100% | +0.00329 |
| `X_rank_D_dist_from_52wl` | 5/5 | 100% | +0.00297 |
| `X_z_D_dist_from_52wl` | 5/5 | 100% | +0.00297 |
| `D_donch_pos_50_rmean50` | 5/5 | 100% | +0.00278 |
| `D_atr14` | 5/5 | 100% | +0.00188 |
| `D_atr30` | 5/5 | 100% | +0.00188 |
| `D_close_roll_slope_20_rstd10` | 5/5 | 100% | +0.00188 |
| `D_close_roll_slope_20_rstd20` | 5/5 | 100% | +0.00188 |
| `D_ema50` | 5/5 | 100% | +0.00188 |
| `D_macd_hist_rstd10` | 5/5 | 100% | +0.00188 |
| `D_slope_stability` | 5/5 | 100% | +0.00188 |
| `D_slope_stability_rmean50` | 5/5 | 100% | +0.00188 |
| `D_slope_stability_rstd10` | 5/5 | 100% | +0.00188 |
| `D_slope_stability_rstd20` | 5/5 | 100% | +0.00188 |
| `D_sma200` | 5/5 | 100% | +0.00188 |
| `open` | 5/5 | 100% | +0.00188 |
| `D_WQ_33` | 5/5 | 100% | +0.00095 |
| `D_WQ_41` | 5/5 | 100% | +0.00095 |
| `D_body_ratio` | 5/5 | 100% | +0.00095 |

## Lockbox - the only evidence in this report

Hypothesis locked at 2026-09-26T23:31:19, BEFORE any lockbox row was scored: model **M4_interactions**, regime filter **[7]**.

This tests whether THIS research-selected hypothesis survives untouched data. It does not test whether regime research works in general. The regime engine here was fitted ONCE on all research data (the deployment protocol), unlike the per-fold walk-forward engines, so its drift is not comparable to theirs.

Lockbox: **378 sessions**, 434,231 rows. AUC 0.5216 | brier 0.2072 | logloss 0.6245 | base rate 0.276.

**Buy everything** (equal weight, same bracket and cost): -23 bp [-55,+14] per trade. The model's contribution is its excess over this.

| | dates | hit | net bp [95%] | clears |
|---|---|---|---|---|
| research top-3 (in-sample choice) | 1801 | 0.426 | +51 [+27,+76] | - |
| **lockbox top-1** | 378 | **0.397** | **+43 [+2,+83]** | **YES** |
| **lockbox top-3** | 378 | **0.392** | **+23 [-8,+54]** | **no** |
| **lockbox top-5** | 378 | **0.368** | **+12 [-18,+42]** | **no** |
| **lockbox top-10** | 378 | **0.367** | **+7 [-21,+35]** | **no** |

| excess over buy-everything | bp [95%] | above zero |
|---|---|---|
| **lockbox top-1** | **+66 [+24,+106]** | **YES** |
| **lockbox top-3** | **+46 [+21,+71]** | **YES** |
| **lockbox top-5** | **+35 [+13,+56]** | **YES** |
| **lockbox top-10** | **+30 [+12,+46]** | **YES** |

| **lockbox, locked regimes, top-3** | 378 | **0.352** | **-4 [-30,+21]** | **no** |

**By year (top-3):** 2025: 0.417 hit, +35 [-1,+71] bp | 2026: 0.364 hit, +10 [-42,+69] bp

**Regime mix:** R0 13% of rows / 4% of picks | R1 8% of rows / 0% of picks | R2 5% of rows / 1% of picks | R3 5% of rows / 4% of picks | R4 13% of rows / 8% of picks | R5 16% of rows / 14% of picks | R6 9% of rows / 23% of picks | R7 12% of rows / 26% of picks | R8 19% of rows / 20% of picks

**By state completeness (top-3):** 7/8: 0.078, -35 [-35,-35] bp | 8/8: 0.392, +23 [-8,+54] bp

**Calibration (lockbox deciles):** 0.26->0.23, 0.29->0.26, 0.30->0.27, 0.31->0.27, 0.31->0.28, 0.32->0.28, 0.33->0.30, 0.35->0.29, 0.36->0.29, 0.50->0.29

**WARNING: this panel's lockbox has now been evaluated 2 times** (research_ledger.jsonl). Every look after the first lets lockbox results steer choices, and the figure stops being untouched.

## Verdict

- Research AUC 0.5377 -> 0.5259 (-0.0118) from M1 to M4_interactions.
- Research-fold net return clears zero for: M0_all_features top-1, M0_all_features top-3, M0_all_features top-5, M0_all_features top-10, M1_base top-1, M1_base top-3, M1_base top-5, M2_regime top-1, M3_families top-1, M3_families top-3, M3_families top-5, M3_families top-10, M4_interactions top-1, M4_interactions top-3, M4_interactions top-5, M4_interactions top-10 (in-sample choice).
- **Lockbox top-3: net does not clear; beats buying everything: YES** - the only result here that was not selected on the data it is scored on. Both are needed: net above zero, and above the market.

_Not a backtest: no slippage, sizing, capacity, borrow or MTF financing; net return uses one flat cost. Regime IDs are aligned across folds. Every result is OOS on walk-forward folds with a 5-session embargo; the calibrator never saw a test window._