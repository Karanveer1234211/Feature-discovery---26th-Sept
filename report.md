# Feature Atlas - ATLAS_20260926_003

Target `label_exit_ret` | per-date rank IC | BH-FDR q<0.05 | sign-stable in >= 80% of folds | |IC| >= 0.01

**Exploratory. Nothing here feeds a model.** A 'working' cell is a feature whose cross-sectional ranking predicted the target inside that regime, out of sample, after correcting for the number of tests.

**Timing:** Prediction is made at the CLOSE of session T. Every feature uses data through the close of T and nothing later. The target covers sessions T+1..T+H, entered at the close of T. Same-day market state (breadth, median move, dispersion) is therefore legitimate: it is known at T close.

Verified on the data: corr(fwd, same day) +0.008, corr(fwd, next day) +0.425.

**Lockbox:** sessions from 2025-03-05 are EXCLUDED from every statistic here. It is the same lockbox regime_research uses; looking at it here would spend it.

**Missing state:** 0.02% of rows have a missing stock-state input and are scored on observed axes only (mean confidence 0.808 vs 0.799 for complete rows).

## Library

- features generated: 443 (0 failed to compute)
- evaluated (coverage >= 30%): 443
- by category: distribution 5, existing 265, interaction 10, location 8, market-relative 5, momentum 5, representation 138, structure 3, volatility 2, volume 2
- cells tested: 5,885 (feature x layer x regime)
- working cells: 181 | working features: 104 | families: 53
- expected false discoveries among working cells at q<0.05: ~9

## Stock regimes (K=9, chosen by BIC on fold-1 train)

Alignment drift across folds (mean centroid distance to the fold-1 reference): 0.00, 0.24, 0.33, 0.30, 0.24. Large values mean a regime ID no longer describes the same state.

| regime | st_trend | st_trend_strength | st_vol_level | st_vol_change | st_momentum | st_participation | st_location | st_shock | share | base rate |
|---|---|---|---|---|---|---|---|---|---|---|
| S0 | -0.35 | -0.07 | +0.02 | -0.03 | -0.33 | +0.01 | -0.18 | +0.26 | 14.7% | 0.002 |
| S1 | +0.12 | -0.05 | -0.07 | +0.01 | +0.11 | +0.14 | -0.08 | -0.02 | 20.1% | 0.002 |
| S2 | -0.15 | -0.06 | -0.39 | -0.24 | -0.24 | +0.01 | -0.17 | -0.14 | 9.2% | 0.002 |
| S3 | -0.32 | -0.10 | -0.05 | -0.04 | -0.33 | -0.06 | -0.21 | -0.23 | 12.0% | 0.003 |
| S4 | +0.42 | +0.38 | +0.37 | +0.22 | +0.39 | +0.05 | +0.34 | +0.07 | 6.4% | 0.002 |
| S5 | +0.39 | +0.04 | +0.18 | +0.11 | +0.34 | +0.41 | +0.17 | +0.43 | 5.5% | 0.002 |
| S6 | -0.06 | -0.08 | -0.08 | -0.06 | -0.05 | -0.35 | -0.04 | -0.09 | 13.8% | 0.002 |
| S7 | -0.01 | +0.05 | +0.36 | +0.13 | +0.01 | -0.08 | -0.03 | +0.09 | 7.7% | 0.002 |
| S8 | +0.21 | +0.11 | -0.05 | -0.01 | +0.25 | +0.02 | +0.35 | -0.04 | 10.4% | 0.002 |

## Market regimes (K=6, chosen by BIC on fold-1 train)

Alignment drift across folds (mean centroid distance to the fold-1 reference): 0.00, 1.21, 3.36, 4.43, 4.36. Large values mean a regime ID no longer describes the same state.

| regime | mk_trend20 | mk_vol20 | mk_breadth20 | mk_disp20 | share | base rate |
|---|---|---|---|---|---|---|
| M0 | -0.03 | +1.16 | +0.26 | +0.61 | 3.3% | 0.008 |
| M1 | -2.53 | +2.74 | -1.46 | +2.00 | 2.6% | 0.003 |
| M2 | +0.80 | -0.25 | +0.84 | -0.63 | 22.1% | 0.001 |
| M3 | -1.01 | +0.49 | -1.19 | +0.36 | 29.0% | 0.004 |
| M4 | +0.17 | -0.46 | +0.00 | +0.79 | 15.0% | 0.000 |
| M5 | +0.27 | -0.79 | +0.08 | -0.65 | 28.0% | 0.001 |

Stock-regime persistence (measured): S0 mean run 2.3d, S1 mean run 2.3d, S2 mean run 2.3d, S3 mean run 2.3d, S4 mean run 2.4d, S5 mean run 2.4d, S6 mean run 2.3d, S7 mean run 2.3d, S8 mean run 2.4d

## Works across all stocks (unconditional)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|
| `D_WQ_40` | existing | +0.0247 | +6.7 | 2.6e-08 | 100% | +0.003 | 1801 |
| `X_z_D_range_pct` | existing | -0.0241 | -3.5 | 0.024 | 100% | -0.002 | 1801 |
| `D_range_pct` | existing | -0.0241 | -3.5 | 0.024 | 100% | -0.002 | 1801 |
| `X_rank_D_range_pct` | existing | -0.0241 | -3.5 | 0.024 | 100% | -0.002 | 1801 |
| `D_WQ_29` | existing | +0.0232 | +4.7 | 0.00071 | 100% | +0.003 | 1801 |
| `N_dist_lo10` | location | -0.0232 | -5.2 | 0.00011 | 100% | -0.002 | 1801 |
| `D_ema20_angle_z252` | existing | -0.0225 | -4.8 | 0.00066 | 100% | -0.003 | 1801 |
| `R_pos_in_52w_range__d5` | representation | -0.0219 | -4.7 | 0.00077 | 100% | -0.003 | 1801 |
| `D_WQ_16` | existing | +0.0214 | +6.7 | 2.6e-08 | 100% | +0.003 | 1801 |
| `D_WQ_44` | existing | +0.0213 | +6.9 | 2e-08 | 100% | +0.002 | 1801 |
| `D_pdi14` | existing | -0.0210 | -5.3 | 9.1e-05 | 100% | -0.002 | 1801 |
| `D_WQ_13` | existing | +0.0208 | +6.9 | 2e-08 | 100% | +0.003 | 1801 |
| `D_dist_from_20l` | existing | -0.0196 | -4.5 | 0.0019 | 100% | -0.002 | 1801 |
| `R_drawdown_252__d5` | representation | -0.0194 | -3.5 | 0.025 | 100% | -0.003 | 1801 |
| `N_dist_lo50` | location | -0.0194 | -3.7 | 0.018 | 100% | -0.002 | 1801 |
| `D_weekly_trend` | existing | -0.0192 | -5.1 | 0.00024 | 100% | +nan | 1801 |
| `M_rel_ret5` | market-relative | -0.0190 | -3.2 | 0.045 | 100% | -0.003 | 1801 |
| `R_ema20_angle_deg__tsz60` | representation | -0.0187 | -4.1 | 0.0059 | 100% | -0.002 | 1801 |
| `R_rsi14__d5` | representation | -0.0185 | -4.0 | 0.0059 | 100% | -0.002 | 1801 |
| `D_rsi14_z252` | existing | -0.0182 | -4.2 | 0.0051 | 100% | -0.002 | 1801 |
| `R_atr_ratio_14_30__tsz60` | representation | -0.0178 | -4.5 | 0.0019 | 100% | -0.002 | 1801 |
| `R_rsi7__tsz60` | representation | -0.0175 | -3.9 | 0.0081 | 100% | -0.002 | 1801 |
| `R_atr_ratio_14_30__d5` | representation | -0.0173 | -4.6 | 0.0011 | 100% | -0.002 | 1801 |
| `R_pos_in_52w_range__accel` | representation | -0.0171 | -4.5 | 0.0018 | 100% | -0.002 | 1801 |
| `R_rsi7__d5` | representation | -0.0165 | -3.8 | 0.012 | 100% | -0.002 | 1801 |

### Works in stock regime S0 (2 cells)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|
| `N_min_ret20` | distribution | +0.0330 | +3.8 | 0.014 | 100% | +0.003 | 1800 |
| `D_pdi14` | existing | -0.0227 | -3.3 | 0.037 | 100% | -0.002 | 1800 |

### Works in stock regime S1 (53 cells)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|
| `N_dist_lo10` | location | -0.0382 | -5.5 | 3e-05 | 100% | -0.003 | 1801 |
| `D_ema20_angle_z252` | existing | -0.0303 | -4.9 | 0.00045 | 80% | -0.003 | 1801 |
| `D_bb_bw_20` | existing | -0.0297 | -3.6 | 0.021 | 100% | -0.002 | 1801 |
| `R_bb_bw_20__csrank` | representation | -0.0297 | -3.6 | 0.021 | 100% | -0.002 | 1801 |
| `R_bb_bw_20__csz` | representation | -0.0297 | -3.6 | 0.021 | 100% | -0.002 | 1801 |
| `R_pos_in_52w_range__d5` | representation | -0.0291 | -5.0 | 0.00036 | 80% | -0.003 | 1801 |
| `R_drawdown_252__d5` | representation | -0.0282 | -4.4 | 0.0019 | 80% | -0.003 | 1801 |
| `X_z_D_range_pct` | existing | -0.0263 | -3.5 | 0.024 | 80% | -0.002 | 1801 |
| `D_range_pct` | existing | -0.0263 | -3.5 | 0.024 | 80% | -0.002 | 1801 |
| `X_rank_D_range_pct` | existing | -0.0263 | -3.5 | 0.024 | 80% | -0.002 | 1801 |
| `D_rsi14_z252` | existing | -0.0263 | -4.4 | 0.0024 | 80% | -0.003 | 1801 |
| `D_dist_from_20l` | existing | -0.0255 | -4.6 | 0.001 | 80% | -0.003 | 1801 |

### Works in stock regime S2 (0 cells)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|

### Works in stock regime S3 (3 cells)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|
| `D_WQ_16` | existing | +0.0262 | +3.7 | 0.016 | 100% | +0.003 | 1738 |
| `D_WQ_44` | existing | +0.0258 | +3.6 | 0.021 | 100% | +0.003 | 1738 |
| `D_WQ_13` | existing | +0.0237 | +3.5 | 0.025 | 100% | +0.003 | 1738 |

### Works in stock regime S4 (6 cells)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|
| `N_dist_lo10` | location | -0.0370 | -3.6 | 0.021 | 100% | -0.005 | 1376 |
| `D_atr_pct_z252` | existing | -0.0351 | -3.2 | 0.049 | 100% | -0.004 | 1391 |
| `D_range_pct` | existing | -0.0350 | -3.2 | 0.049 | 100% | -0.004 | 1391 |
| `X_rank_D_range_pct` | existing | -0.0350 | -3.2 | 0.049 | 100% | -0.004 | 1391 |
| `X_z_D_range_pct` | existing | -0.0350 | -3.2 | 0.049 | 100% | -0.004 | 1391 |
| `D_days_since_5pct_up` | existing | +0.0330 | +3.2 | 0.047 | 100% | +0.004 | 1391 |

### Works in stock regime S5 (4 cells)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|
| `N_dist_hi10` | location | +0.0440 | +4.0 | 0.0073 | 100% | +0.005 | 1570 |
| `N_clv` | structure | +0.0419 | +4.2 | 0.0043 | 100% | +0.005 | 1577 |
| `N_body_range` | structure | +0.0407 | +4.1 | 0.0051 | 100% | +0.005 | 1577 |
| `D_body_ratio` | existing | +0.0407 | +4.1 | 0.0051 | 100% | +0.005 | 1577 |

### Works in stock regime S6 (0 cells)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|

### Works in stock regime S7 (18 cells)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|
| `X_z_D_downside_dev_60` | existing | -0.0412 | -4.1 | 0.0059 | 100% | -0.004 | 1731 |
| `D_downside_dev_60` | existing | -0.0412 | -4.1 | 0.0059 | 100% | -0.004 | 1731 |
| `X_rank_D_downside_dev_60` | existing | -0.0412 | -4.1 | 0.0059 | 100% | -0.004 | 1731 |
| `X_z_D_atr_pct` | existing | -0.0397 | -3.5 | 0.025 | 100% | -0.003 | 1731 |
| `R_atr_pct__csrank` | representation | -0.0397 | -3.5 | 0.025 | 100% | -0.003 | 1731 |
| `D_atr_pct` | existing | -0.0397 | -3.5 | 0.025 | 100% | -0.003 | 1731 |
| `X_rank_D_atr_pct` | existing | -0.0397 | -3.5 | 0.025 | 100% | -0.003 | 1731 |
| `R_atr_pct__csz` | representation | -0.0397 | -3.5 | 0.025 | 100% | -0.003 | 1731 |
| `D_vol_yz_20` | existing | -0.0388 | -3.6 | 0.021 | 100% | -0.003 | 1731 |
| `X_z_D_range_pct` | existing | -0.0381 | -4.1 | 0.0059 | 100% | -0.005 | 1731 |
| `X_rank_D_range_pct` | existing | -0.0381 | -4.1 | 0.0059 | 100% | -0.005 | 1731 |
| `D_range_pct` | existing | -0.0381 | -4.1 | 0.0059 | 100% | -0.005 | 1731 |

### Works in stock regime S8 (6 cells)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|
| `D_range_pct` | existing | -0.0312 | -3.5 | 0.025 | 100% | -0.002 | 1801 |
| `X_rank_D_range_pct` | existing | -0.0312 | -3.5 | 0.025 | 100% | -0.002 | 1801 |
| `X_z_D_range_pct` | existing | -0.0312 | -3.5 | 0.025 | 100% | -0.002 | 1801 |
| `D_dist_from_52wl` | existing | +0.0286 | +3.6 | 0.021 | 100% | +0.002 | 1801 |
| `X_rank_D_dist_from_52wl` | existing | +0.0286 | +3.6 | 0.021 | 100% | +0.002 | 1801 |
| `X_z_D_dist_from_52wl` | existing | +0.0286 | +3.6 | 0.021 | 100% | +0.002 | 1801 |

### Works in market regime M0 (0 cells)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|

### Works in market regime M1 (0 cells)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|

### Works in market regime M2 (2 cells)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|
| `N_dist_lo10` | location | -0.0297 | -3.3 | 0.04 | 100% | -0.003 | 366 |
| `D_WQ_40` | existing | +0.0281 | +3.5 | 0.024 | 100% | +0.003 | 366 |

### Works in market regime M3 (18 cells)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|
| `R_rsi14__d5` | representation | -0.0342 | -3.4 | 0.025 | 100% | -0.004 | 466 |
| `D_mdi14_diff5` | existing | +0.0330 | +3.6 | 0.021 | 100% | +0.004 | 466 |
| `R_rsi7__d5` | representation | -0.0309 | -3.4 | 0.025 | 100% | -0.004 | 466 |
| `R_dist_from_20h__d5` | representation | -0.0308 | -3.5 | 0.025 | 100% | -0.004 | 466 |
| `D_mdi14_rrank10` | existing | +0.0301 | +3.5 | 0.024 | 100% | +0.003 | 466 |
| `D_WQ_13` | existing | +0.0280 | +4.1 | 0.0054 | 100% | +0.003 | 466 |
| `D_WQ_44` | existing | +0.0276 | +4.6 | 0.0011 | 100% | +0.003 | 466 |
| `D_WQ_16` | existing | +0.0273 | +4.0 | 0.0077 | 100% | +0.003 | 466 |
| `R_pos_in_52w_range__accel` | representation | -0.0263 | -3.2 | 0.043 | 100% | -0.003 | 466 |
| `D_WQ_35` | existing | +0.0260 | +3.4 | 0.031 | 100% | +0.003 | 466 |
| `D_WQ_40` | existing | +0.0259 | +3.4 | 0.031 | 100% | +0.003 | 466 |
| `R_rsi14__accel` | representation | -0.0239 | -3.2 | 0.045 | 100% | -0.003 | 466 |

### Works in market regime M4 (4 cells)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|
| `D_WQ_40` | existing | +0.0262 | +3.3 | 0.04 | 100% | +0.003 | 323 |
| `R_realvol_ratio_20_60__d5` | representation | -0.0238 | -3.5 | 0.025 | 100% | -0.003 | 323 |
| `R_compress_state__tsz60` | representation | -0.0234 | -3.2 | 0.043 | 100% | -0.002 | 323 |
| `D_WQ_44` | existing | +0.0233 | +3.3 | 0.038 | 100% | +0.003 | 323 |

### Works in market regime M5 (2 cells)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|
| `D_WQ_40` | existing | +0.0227 | +3.2 | 0.046 | 100% | +0.002 | 471 |
| `D_WQ_13` | existing | +0.0160 | +3.3 | 0.039 | 100% | +0.002 | 471 |

## Sign flips - works one way here, the opposite way there

HYPOTHESES, not findings: selected from many tests, so each needs its own confirmation on data not used to find it.

A feature significant with OPPOSITE signs in two regimes. An unconditional model averages these into nothing; this is exactly the information regime conditioning exists to recover.

_None survived the FDR and stability bars._

## Feature x regime matrix (top 40 by max |IC|)

`*` = working (FDR + stable + material). Blank = too few dates.

| feature | ALL | S0 | S1 | S2 | S3 | S4 | S5 | S6 | S7 | S8 | M0 | M1 | M2 | M3 | M4 | M5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `D_atr_pct` | -0.020 | -0.022 | -0.021 | +0.003 | -0.019 | -0.042 | -0.022 | -0.018 | -0.040* | -0.027 | +0.065 | -0.034 | -0.031 | -0.002 | -0.049 | -0.026 |
| `X_rank_D_atr_pct` | -0.020 | -0.022 | -0.021 | +0.003 | -0.019 | -0.042 | -0.022 | -0.018 | -0.040* | -0.027 | +0.065 | -0.034 | -0.031 | -0.002 | -0.049 | -0.026 |
| `R_atr_pct__csz` | -0.020 | -0.022 | -0.021 | +0.003 | -0.019 | -0.042 | -0.022 | -0.018 | -0.040* | -0.027 | +0.065 | -0.034 | -0.031 | -0.002 | -0.049 | -0.026 |
| `R_atr_pct__csrank` | -0.020 | -0.022 | -0.021 | +0.003 | -0.019 | -0.042 | -0.022 | -0.018 | -0.040* | -0.027 | +0.065 | -0.034 | -0.031 | -0.002 | -0.049 | -0.026 |
| `X_z_D_atr_pct` | -0.020 | -0.022 | -0.021 | +0.003 | -0.019 | -0.042 | -0.022 | -0.018 | -0.040* | -0.027 | +0.065 | -0.034 | -0.031 | -0.002 | -0.049 | -0.026 |
| `R_pos_in_52w_range__d5` | -0.022* | -0.022 | -0.029* | -0.013 | -0.013 | -0.014 | -0.004 | -0.013 | -0.025 | -0.014 | -0.048 | -0.060 | -0.017 | -0.033 | -0.004 | -0.016 |
| `D_WQ_29` | +0.023* | +0.016 | +0.024* | +0.013 | +0.007 | +0.025 | +0.008 | +0.007 | +0.028* | +0.014 | +0.041 | +0.059 | +0.019 | +0.031 | +0.011 | +0.018 |
| `D_vol_yz_50` | -0.019 | -0.022 | -0.018 | +0.011 | -0.020 | -0.029 | -0.015 | -0.018 | -0.036* | -0.019 | +0.059 | -0.047 | -0.027 | -0.002 | -0.043 | -0.024 |
| `D_vol_yz_20` | -0.022 | -0.024 | -0.022 | +0.011 | -0.018 | -0.037 | -0.023 | -0.019 | -0.039* | -0.017 | +0.057 | -0.055 | -0.030 | -0.006 | -0.043 | -0.025 |
| `R_atr_ratio_14_30__d20` | -0.012 | -0.005 | -0.016 | -0.005 | -0.004 | -0.016 | -0.024 | -0.003 | -0.008 | +0.003 | -0.009 | -0.057 | -0.013 | -0.005 | -0.017 | -0.008 |
| `R_donch_pos_20__tsz60` | -0.013* | -0.001 | -0.020* | -0.006 | -0.005 | -0.011 | +0.009 | -0.007 | -0.012 | -0.006 | -0.015 | -0.056 | -0.014 | -0.024 | +0.003 | -0.006 |
| `D_dist_from_20l` | -0.020* | -0.013 | -0.026* | -0.012 | -0.011 | -0.014 | -0.011 | -0.005 | -0.020 | -0.006 | -0.033 | -0.056 | -0.025 | -0.023 | -0.010 | -0.010 |
| `N_dist_hi100` | +0.008 | +0.013 | +0.013 | +0.004 | +0.005 | +0.027 | +0.029 | +0.020 | +0.019 | +0.014 | -0.055 | +0.004 | +0.003 | +0.013 | +0.017 | +0.014 |
| `R_rsi14__tsz60` | -0.016* | -0.003 | -0.022* | -0.006 | -0.006 | -0.012 | -0.005 | -0.006 | -0.012 | -0.008 | -0.019 | -0.055 | -0.020 | -0.021 | -0.001 | -0.012 |
| `R_ema20_angle_deg__tsz60` | -0.019* | -0.006 | -0.022* | -0.009 | -0.006 | -0.021 | -0.007 | -0.010 | -0.019 | -0.009 | -0.023 | -0.055 | -0.021 | -0.026 | -0.003 | -0.013 |
| `D_dollar_vol` | -0.007 | -0.013 | -0.004 | -0.009 | -0.005 | -0.026 | -0.001 | +0.003 | -0.014 | -0.007 | -0.054 | +0.023 | -0.003 | -0.013 | +0.000 | -0.006 |
| `X_z_D_range_pct` | -0.024* | -0.010 | -0.026* | -0.001 | -0.003 | -0.035* | -0.029 | -0.014 | -0.038* | -0.031* | +0.010 | -0.054 | -0.033 | -0.006 | -0.040 | -0.025 |
| `X_rank_D_range_pct` | -0.024* | -0.010 | -0.026* | -0.001 | -0.003 | -0.035* | -0.029 | -0.014 | -0.038* | -0.031* | +0.010 | -0.054 | -0.033 | -0.006 | -0.040 | -0.025 |
| `D_range_pct` | -0.024* | -0.010 | -0.026* | -0.001 | -0.003 | -0.035* | -0.029 | -0.014 | -0.038* | -0.031* | +0.010 | -0.054 | -0.033 | -0.006 | -0.040 | -0.025 |
| `D_amihud_60` | -0.002 | +0.010 | -0.003 | +0.017 | +0.006 | +0.002 | -0.009 | -0.004 | -0.003 | -0.001 | +0.053 | -0.040 | -0.010 | +0.011 | -0.014 | -0.006 |
| `N_dist_hi250` | +0.013 | +0.013 | +0.024 | +0.004 | +0.010 | +0.024 | +0.021 | +0.022 | +0.021 | +0.016 | -0.052 | +0.017 | +0.007 | +0.018 | +0.021 | +0.019 |
| `N_dist_hi50` | +0.005 | +0.014 | +0.006 | -0.003 | +0.004 | +0.021 | +0.031 | +0.016 | +0.019 | +0.012 | -0.052 | -0.013 | -0.001 | +0.008 | +0.024 | +0.009 |
| `N_ret120` | +0.004 | +0.002 | +0.010 | +0.004 | +0.003 | +0.009 | +0.005 | +0.013 | -0.001 | -0.004 | -0.051 | +0.019 | -0.004 | +0.016 | -0.014 | +0.018 |
| `X_z_D_donch_pos_20` | -0.013 | -0.004 | -0.018* | -0.008 | -0.010 | -0.006 | +0.016 | +0.001 | -0.008 | -0.008 | -0.035 | -0.051 | -0.016 | -0.018 | +0.000 | -0.005 |
| `X_rank_D_donch_pos_20` | -0.013 | -0.004 | -0.018* | -0.008 | -0.010 | -0.006 | +0.016 | +0.001 | -0.008 | -0.008 | -0.035 | -0.051 | -0.016 | -0.018 | +0.000 | -0.005 |
| `D_donch_pos_20` | -0.013 | -0.004 | -0.018* | -0.008 | -0.010 | -0.006 | +0.016 | +0.001 | -0.008 | -0.008 | -0.035 | -0.051 | -0.016 | -0.018 | +0.000 | -0.005 |
| `R_donch_pos_20__csz` | -0.013 | -0.004 | -0.018* | -0.008 | -0.010 | -0.006 | +0.016 | +0.001 | -0.008 | -0.008 | -0.035 | -0.051 | -0.016 | -0.018 | +0.000 | -0.005 |
| `R_donch_pos_20__csrank` | -0.013 | -0.004 | -0.018* | -0.008 | -0.010 | -0.006 | +0.016 | +0.001 | -0.008 | -0.008 | -0.035 | -0.051 | -0.016 | -0.018 | +0.000 | -0.005 |
| `R_drawdown_252__d5` | -0.019* | -0.016 | -0.028* | -0.008 | -0.011 | -0.011 | -0.005 | -0.009 | -0.023 | -0.012 | -0.046 | -0.051 | -0.015 | -0.033 | +0.002 | -0.013 |
| `N_dist_lo50` | -0.019* | -0.009 | -0.026 | -0.004 | -0.005 | -0.024 | -0.014 | -0.003 | -0.035* | -0.019 | +0.006 | -0.051 | -0.033 | -0.014 | -0.016 | -0.016 |
| `M_ivol60` | -0.019 | -0.022 | -0.020 | -0.003 | -0.016 | -0.029 | -0.015 | -0.012 | -0.029 | -0.025 | +0.050 | -0.026 | -0.028 | -0.010 | -0.040 | -0.020 |
| `R_dist_from_20h__tsz60` | -0.011 | -0.004 | -0.013 | -0.005 | -0.006 | -0.011 | +0.012 | -0.004 | -0.013 | -0.006 | -0.019 | -0.050 | -0.013 | -0.020 | +0.008 | -0.006 |
| `D_amihud_20` | -0.003 | +0.011 | -0.006 | +0.014 | +0.006 | +0.005 | -0.011 | -0.005 | -0.005 | -0.002 | +0.050 | -0.040 | -0.009 | +0.008 | -0.013 | -0.006 |
| `X_rank_D_amihud_20` | -0.003 | +0.011 | -0.006 | +0.014 | +0.006 | +0.005 | -0.011 | -0.005 | -0.005 | -0.002 | +0.050 | -0.040 | -0.009 | +0.008 | -0.013 | -0.006 |
| `X_z_D_amihud_20` | -0.003 | +0.011 | -0.006 | +0.014 | +0.006 | +0.005 | -0.011 | -0.005 | -0.005 | -0.002 | +0.050 | -0.040 | -0.009 | +0.008 | -0.013 | -0.006 |
| `N_dist_lo10` | -0.023* | -0.015 | -0.038* | -0.013 | -0.009 | -0.037* | -0.021 | -0.007 | -0.038* | -0.021 | -0.005 | -0.049 | -0.030* | -0.017 | -0.024 | -0.022 |
| `D_ema20_angle_z252` | -0.022* | -0.006 | -0.030* | -0.014 | -0.009 | -0.026 | -0.014 | -0.005 | -0.023 | -0.015 | -0.040 | -0.049 | -0.026 | -0.026 | -0.011 | -0.016 |
| `R_atr_ratio_14_30__tsz60` | -0.018* | -0.007 | -0.024* | -0.007 | -0.013 | -0.018 | -0.027 | -0.009 | -0.019 | -0.000 | -0.022 | -0.049 | -0.023 | -0.009 | -0.016 | -0.018 |
| `D_weekly_trend` | -0.019* | -0.017 | -0.024* | -0.001 | -0.017 | -0.027 | -0.006 | -0.004 | -0.024 | -0.019 | -0.049 | -0.032 | -0.017 | -0.018 | -0.013 | -0.018 |
| `D_rsi14_z252` | -0.018* | -0.002 | -0.026* | -0.004 | -0.003 | -0.012 | -0.006 | -0.001 | -0.012 | -0.012 | -0.033 | -0.048 | -0.021 | -0.019 | -0.008 | -0.014 |

## Caveats

- Exploratory. A working cell is evidence to test, not a validated edge.
- About 5% of working cells are expected to be false discoveries by construction of the FDR bar.
- IC is cross-sectional ranking skill. It is not a return, and it ignores costs; `top-bot hit` is the gap in the mean target between the top and bottom quintile within the regime - a hit-rate gap for a 0/1 target, a return gap for label_exit_ret.
- Regime IDs are aligned across folds by centroid matching; check the drift figures before trusting a regime's identity over time.
- In-sample regime labels (before the first test window) never enter the statistics.