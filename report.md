# Feature Atlas - ATLAS_20260926_001

Target `label_tp_before_sl` | per-date rank IC | BH-FDR q<0.05 | sign-stable in >= 80% of folds | |IC| >= 0.01

**Exploratory. Nothing here feeds a model.** A 'working' cell is a feature whose cross-sectional ranking predicted the target inside that regime, out of sample, after correcting for the number of tests.

**Timing:** Prediction is made at the CLOSE of session T. Every feature uses data through the close of T and nothing later. The target covers sessions T+1..T+H, entered at the close of T. Same-day market state (breadth, median move, dispersion) is therefore legitimate: it is known at T close.

Verified on the data: corr(fwd, same day) +0.008, corr(fwd, next day) +0.425.

**Lockbox:** sessions from 2025-03-05 are EXCLUDED from every statistic here. It is the same lockbox regime_research uses; looking at it here would spend it.

**Missing state:** 0.02% of rows have a missing stock-state input and are scored on observed axes only (mean confidence 0.000 vs 0.454 for complete rows).

## Library

- features generated: 443 (0 failed to compute)
- evaluated (coverage >= 30%): 443
- by category: distribution 5, existing 265, interaction 10, location 8, market-relative 5, momentum 5, representation 138, structure 3, volatility 2, volume 2
- cells tested: 5,885 (feature x layer x regime)
- working cells: 1,687 | working features: 322 | families: 137
- expected false discoveries among working cells at q<0.05: ~84

## Stock regimes (K=9, chosen by BIC on fold-1 train)

Alignment drift across folds (mean centroid distance to the fold-1 reference): 0.00, 0.24, 0.33, 0.30, 0.23. Large values mean a regime ID no longer describes the same state.

| regime | st_trend | st_trend_strength | st_vol_level | st_vol_change | st_momentum | st_participation | st_location | st_shock | share | base rate |
|---|---|---|---|---|---|---|---|---|---|---|
| S0 | -0.35 | -0.07 | +0.02 | -0.03 | -0.33 | +0.01 | -0.18 | +0.26 | 7.3% | 0.271 |
| S1 | +0.12 | -0.05 | -0.07 | +0.01 | +0.11 | +0.14 | -0.08 | -0.02 | 10.9% | 0.297 |
| S2 | -0.15 | -0.06 | -0.39 | -0.24 | -0.24 | +0.01 | -0.17 | -0.14 | 5.2% | 0.308 |
| S3 | -0.32 | -0.10 | -0.05 | -0.04 | -0.33 | -0.06 | -0.21 | -0.23 | 7.5% | 0.291 |
| S4 | +0.42 | +0.38 | +0.37 | +0.22 | +0.39 | +0.05 | +0.34 | +0.07 | 3.7% | 0.286 |
| S5 | +0.39 | +0.04 | +0.18 | +0.11 | +0.34 | +0.41 | +0.17 | +0.43 | 3.4% | 0.328 |
| S6 | -0.06 | -0.08 | -0.08 | -0.06 | -0.05 | -0.35 | -0.04 | -0.09 | 6.0% | 0.290 |
| S7 | -0.01 | +0.05 | +0.36 | +0.13 | +0.01 | -0.08 | -0.03 | +0.09 | 4.7% | 0.244 |
| S8 | +0.21 | +0.11 | -0.05 | -0.01 | +0.25 | +0.02 | +0.35 | -0.04 | 8.1% | 0.295 |

## Market regimes (K=6, chosen by BIC on fold-1 train)

Alignment drift across folds (mean centroid distance to the fold-1 reference): 0.00, 1.21, 3.36, 4.43, 4.36. Large values mean a regime ID no longer describes the same state.

| regime | mk_trend20 | mk_vol20 | mk_breadth20 | mk_disp20 | share | base rate |
|---|---|---|---|---|---|---|
| M0 | -0.03 | +1.16 | +0.26 | +0.61 | 3.3% | 0.340 |
| M1 | -2.53 | +2.74 | -1.46 | +2.00 | 2.6% | 0.216 |
| M2 | +0.80 | -0.25 | +0.84 | -0.63 | 11.7% | 0.296 |
| M3 | -1.01 | +0.49 | -1.19 | +0.36 | 12.4% | 0.268 |
| M4 | +0.17 | -0.46 | +0.00 | +0.79 | 10.9% | 0.285 |
| M5 | +0.27 | -0.79 | +0.08 | -0.65 | 15.9% | 0.306 |

Stock-regime persistence (measured): S0 mean run 2.4d, S1 mean run 2.5d, S2 mean run 2.4d, S3 mean run 2.4d, S4 mean run 2.5d, S5 mean run 2.5d, S6 mean run 2.4d, S7 mean run 2.4d, S8 mean run 2.4d

## Works across all stocks (unconditional)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|
| `D_atr_pct_z252` | existing | -0.0743 | -18.8 | 0 | 100% | -0.096 | 1801 |
| `R_atr_pct__tsz60` | representation | -0.0712 | -18.8 | 0 | 100% | -0.091 | 1801 |
| `R_atr_pct__d20` | representation | -0.0667 | -17.8 | 0 | 100% | -0.084 | 1801 |
| `R_atr_ratio_14_30__csz` | representation | -0.0610 | -12.8 | 0 | 100% | -0.081 | 1801 |
| `R_atr_ratio_14_30__csrank` | representation | -0.0610 | -12.8 | 0 | 100% | -0.081 | 1801 |
| `D_atr_ratio_14_30` | existing | -0.0610 | -12.8 | 0 | 100% | -0.081 | 1801 |
| `X_z_D_realvol_ratio_20_60` | existing | -0.0553 | -16.9 | 0 | 100% | -0.073 | 1801 |
| `D_realvol_ratio_20_60` | existing | -0.0553 | -16.9 | 0 | 100% | -0.073 | 1801 |
| `R_realvol_ratio_20_60__csrank` | representation | -0.0553 | -16.9 | 0 | 100% | -0.073 | 1801 |
| `R_realvol_ratio_20_60__csz` | representation | -0.0553 | -16.9 | 0 | 100% | -0.073 | 1801 |
| `X_rank_D_realvol_ratio_20_60` | existing | -0.0553 | -16.9 | 0 | 100% | -0.073 | 1801 |
| `R_realvol_20__tsz60` | representation | -0.0546 | -16.4 | 0 | 100% | -0.071 | 1801 |
| `N_dist_hi10` | location | +0.0544 | +13.8 | 0 | 100% | +0.064 | 1801 |
| `X_z_D_realvol_20` | existing | -0.0471 | -12.2 | 0 | 100% | -0.057 | 1801 |
| `R_realvol_20__csz` | representation | -0.0471 | -12.2 | 0 | 100% | -0.057 | 1801 |
| `X_relvol_20` | existing | -0.0471 | -12.2 | 0 | 100% | -0.057 | 1801 |
| `X_rank_D_realvol_20` | existing | -0.0471 | -12.2 | 0 | 100% | -0.057 | 1801 |
| `D_realvol_20` | existing | -0.0471 | -12.2 | 0 | 100% | -0.057 | 1801 |
| `R_realvol_20__csrank` | representation | -0.0471 | -12.2 | 0 | 100% | -0.057 | 1801 |
| `R_realvol_20__d20` | representation | -0.0454 | -14.8 | 0 | 100% | -0.060 | 1801 |
| `D_vol_yz_20` | existing | -0.0450 | -10.4 | 0 | 100% | -0.056 | 1801 |
| `R_atr_ratio_14_30__tsz60` | representation | -0.0449 | -12.2 | 0 | 100% | -0.058 | 1801 |
| `N_min_ret20` | distribution | +0.0448 | +12.4 | 0 | 100% | +0.053 | 1801 |
| `R_atr_ratio_14_30__d20` | representation | -0.0443 | -12.5 | 0 | 100% | -0.058 | 1801 |
| `R_atr_pct__csrank` | representation | -0.0402 | -8.9 | 0 | 100% | -0.050 | 1801 |

### Works in stock regime S0 (117 cells)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|
| `D_atr_ratio_14_30` | existing | -0.0861 | -9.5 | 0 | 100% | -0.115 | 1425 |
| `R_atr_ratio_14_30__csz` | representation | -0.0861 | -9.5 | 0 | 100% | -0.115 | 1425 |
| `R_atr_ratio_14_30__csrank` | representation | -0.0861 | -9.5 | 0 | 100% | -0.115 | 1425 |
| `R_atr_pct__d20` | representation | -0.0758 | -8.8 | 0 | 100% | -0.100 | 1425 |
| `D_atr_pct_z252` | existing | -0.0746 | -8.8 | 0 | 100% | -0.097 | 1425 |
| `R_atr_pct__tsz60` | representation | -0.0737 | -8.4 | 0 | 100% | -0.095 | 1425 |
| `D_realvol_ratio_20_60` | existing | -0.0641 | -7.8 | 3e-13 | 100% | -0.077 | 1425 |
| `R_realvol_ratio_20_60__csrank` | representation | -0.0641 | -7.8 | 3e-13 | 100% | -0.077 | 1425 |
| `R_realvol_ratio_20_60__csz` | representation | -0.0641 | -7.8 | 3e-13 | 100% | -0.077 | 1425 |
| `X_z_D_realvol_ratio_20_60` | existing | -0.0641 | -7.8 | 3e-13 | 100% | -0.077 | 1425 |
| `X_rank_D_realvol_ratio_20_60` | existing | -0.0641 | -7.8 | 3e-13 | 100% | -0.077 | 1425 |
| `R_realvol_20__tsz60` | representation | -0.0636 | -7.5 | 3.1e-12 | 100% | -0.079 | 1425 |

### Works in stock regime S1 (112 cells)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|
| `D_atr_ratio_14_30` | existing | -0.0757 | -10.6 | 0 | 100% | -0.091 | 1435 |
| `R_atr_ratio_14_30__csz` | representation | -0.0757 | -10.6 | 0 | 100% | -0.091 | 1435 |
| `R_atr_ratio_14_30__csrank` | representation | -0.0757 | -10.6 | 0 | 100% | -0.091 | 1435 |
| `D_atr_pct_z252` | existing | -0.0708 | -10.0 | 0 | 100% | -0.091 | 1435 |
| `R_atr_pct__tsz60` | representation | -0.0662 | -9.5 | 0 | 100% | -0.082 | 1431 |
| `R_atr_pct__d20` | representation | -0.0626 | -8.9 | 0 | 100% | -0.078 | 1433 |
| `R_atr_ratio_14_30__tsz60` | representation | -0.0522 | -7.9 | 1.4e-13 | 100% | -0.064 | 1431 |
| `R_atr_ratio_14_30__d20` | representation | -0.0487 | -7.4 | 8e-12 | 100% | -0.057 | 1433 |
| `X_z_D_realvol_ratio_20_60` | existing | -0.0456 | -7.0 | 8.4e-11 | 100% | -0.054 | 1435 |
| `X_rank_D_realvol_ratio_20_60` | existing | -0.0456 | -7.0 | 8.4e-11 | 100% | -0.054 | 1435 |
| `D_realvol_ratio_20_60` | existing | -0.0456 | -7.0 | 8.4e-11 | 100% | -0.054 | 1435 |
| `R_realvol_ratio_20_60__csrank` | representation | -0.0456 | -7.0 | 8.4e-11 | 100% | -0.054 | 1435 |

### Works in stock regime S2 (72 cells)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|
| `R_atr_pct__d20` | representation | -0.0669 | -7.0 | 7e-11 | 100% | -0.085 | 1419 |
| `D_atr_pct_z252` | existing | -0.0643 | -6.8 | 3.6e-10 | 100% | -0.080 | 1422 |
| `R_atr_pct__tsz60` | representation | -0.0621 | -6.4 | 3.3e-09 | 100% | -0.076 | 1418 |
| `D_atr_ratio_14_30` | existing | -0.0609 | -6.2 | 1.2e-08 | 100% | -0.076 | 1422 |
| `R_atr_ratio_14_30__csrank` | representation | -0.0609 | -6.2 | 1.2e-08 | 100% | -0.076 | 1422 |
| `R_atr_ratio_14_30__csz` | representation | -0.0609 | -6.2 | 1.2e-08 | 100% | -0.076 | 1422 |
| `R_atr_ratio_14_30__d20` | representation | -0.0464 | -5.3 | 2.2e-06 | 100% | -0.055 | 1419 |
| `R_atr_ratio_14_30__tsz60` | representation | -0.0445 | -4.9 | 1.2e-05 | 100% | -0.053 | 1418 |
| `R_realvol_ratio_20_60__csrank` | representation | -0.0444 | -5.0 | 6.3e-06 | 100% | -0.058 | 1422 |
| `X_z_D_realvol_ratio_20_60` | existing | -0.0444 | -5.0 | 6.3e-06 | 100% | -0.058 | 1422 |
| `D_realvol_ratio_20_60` | existing | -0.0444 | -5.0 | 6.3e-06 | 100% | -0.058 | 1422 |
| `R_realvol_ratio_20_60__csz` | representation | -0.0444 | -5.0 | 6.3e-06 | 100% | -0.058 | 1422 |

### Works in stock regime S3 (134 cells)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|
| `R_atr_ratio_14_30__csz` | representation | -0.0842 | -8.8 | 0 | 100% | -0.110 | 1350 |
| `D_atr_ratio_14_30` | existing | -0.0842 | -8.8 | 0 | 100% | -0.110 | 1350 |
| `R_atr_ratio_14_30__csrank` | representation | -0.0842 | -8.8 | 0 | 100% | -0.110 | 1350 |
| `R_atr_pct__tsz60` | representation | -0.0802 | -8.8 | 0 | 100% | -0.103 | 1336 |
| `D_atr_pct_z252` | existing | -0.0775 | -8.7 | 0 | 100% | -0.099 | 1350 |
| `R_atr_pct__d20` | representation | -0.0735 | -8.2 | 1.5e-14 | 100% | -0.089 | 1340 |
| `R_realvol_20__tsz60` | representation | -0.0624 | -7.2 | 3e-11 | 100% | -0.078 | 1336 |
| `N_min_ret20` | distribution | +0.0598 | +7.0 | 8.9e-11 | 100% | +0.075 | 1344 |
| `R_atr_ratio_14_30__tsz60` | representation | -0.0597 | -6.7 | 7.6e-10 | 100% | -0.072 | 1336 |
| `R_realvol_ratio_20_60__csrank` | representation | -0.0593 | -6.8 | 2.5e-10 | 100% | -0.071 | 1350 |
| `D_realvol_ratio_20_60` | existing | -0.0593 | -6.8 | 2.5e-10 | 100% | -0.071 | 1350 |
| `R_realvol_ratio_20_60__csz` | representation | -0.0593 | -6.8 | 2.5e-10 | 100% | -0.071 | 1350 |

### Works in stock regime S4 (136 cells)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|
| `D_atr_pct_z252` | existing | -0.0794 | -6.7 | 4.8e-10 | 100% | -0.098 | 1028 |
| `R_atr_pct__d20` | representation | -0.0679 | -5.8 | 1.5e-07 | 100% | -0.087 | 980 |
| `N_dist_hi10` | location | +0.0625 | +5.4 | 1.1e-06 | 100% | +0.078 | 1013 |
| `N_dist_hi100` | location | +0.0599 | +4.5 | 8.2e-05 | 100% | +0.069 | 948 |
| `R_atr_pct__tsz60` | representation | -0.0594 | -4.7 | 3e-05 | 100% | -0.080 | 977 |
| `N_dist_hi50` | location | +0.0583 | +4.7 | 3.5e-05 | 100% | +0.067 | 977 |
| `D_donch_pos_50` | existing | +0.0530 | +4.4 | 9.5e-05 | 100% | +0.065 | 1028 |
| `D_dist_from_20h` | existing | +0.0521 | +4.4 | 9.3e-05 | 100% | +0.058 | 1028 |
| `R_dist_from_20h__csrank` | representation | +0.0521 | +4.4 | 9.3e-05 | 100% | +0.058 | 1028 |
| `R_dist_from_20h__csz` | representation | +0.0521 | +4.4 | 9.3e-05 | 100% | +0.058 | 1028 |
| `R_rsi7__csrank` | representation | +0.0519 | +4.3 | 0.00016 | 100% | +0.053 | 1028 |
| `R_rsi7__csz` | representation | +0.0519 | +4.3 | 0.00016 | 100% | +0.053 | 1028 |

### Works in stock regime S5 (118 cells)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|
| `D_atr_pct_z252` | existing | -0.0691 | -5.9 | 8.3e-08 | 100% | -0.092 | 1222 |
| `N_dist_hi10` | location | +0.0587 | +5.0 | 7e-06 | 100% | +0.071 | 1214 |
| `X_z_D_bb_pctB_20` | existing | +0.0568 | +4.9 | 1.4e-05 | 100% | +0.067 | 1222 |
| `X_rank_D_bb_pctB_20` | existing | +0.0568 | +4.9 | 1.4e-05 | 100% | +0.067 | 1222 |
| `R_bb_pctB_20__csz` | representation | +0.0568 | +4.9 | 1.4e-05 | 100% | +0.067 | 1222 |
| `D_bb_pctB_20` | existing | +0.0568 | +4.9 | 1.4e-05 | 100% | +0.067 | 1222 |
| `R_bb_pctB_20__csrank` | representation | +0.0568 | +4.9 | 1.4e-05 | 100% | +0.067 | 1222 |
| `R_atr_pct__d20` | representation | -0.0564 | -4.7 | 2.9e-05 | 100% | -0.073 | 1200 |
| `R_bb_pctB_20__tsz60` | representation | +0.0540 | +4.6 | 4.9e-05 | 100% | +0.072 | 1194 |
| `R_atr_pct__tsz60` | representation | -0.0534 | -4.3 | 0.00016 | 100% | -0.070 | 1194 |
| `N_clv` | structure | +0.0527 | +4.6 | 4.8e-05 | 100% | +0.068 | 1222 |
| `N_body_range` | structure | +0.0511 | +4.6 | 4.8e-05 | 100% | +0.065 | 1222 |

### Works in stock regime S6 (61 cells)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|
| `R_atr_pct__tsz60` | representation | -0.0690 | -8.0 | 6.7e-14 | 100% | -0.089 | 1408 |
| `D_atr_ratio_14_30` | existing | -0.0619 | -6.9 | 1.6e-10 | 100% | -0.083 | 1410 |
| `R_atr_ratio_14_30__csrank` | representation | -0.0619 | -6.9 | 1.6e-10 | 100% | -0.083 | 1410 |
| `R_atr_ratio_14_30__csz` | representation | -0.0619 | -6.9 | 1.6e-10 | 100% | -0.083 | 1410 |
| `D_atr_pct_z252` | existing | -0.0612 | -7.5 | 2.6e-12 | 100% | -0.077 | 1410 |
| `R_atr_pct__d20` | representation | -0.0511 | -5.9 | 6.5e-08 | 100% | -0.068 | 1408 |
| `R_atr_ratio_14_30__tsz60` | representation | -0.0494 | -6.0 | 4.4e-08 | 100% | -0.060 | 1408 |
| `R_realvol_ratio_20_60__csrank` | representation | -0.0494 | -5.9 | 7.7e-08 | 100% | -0.062 | 1410 |
| `R_realvol_ratio_20_60__csz` | representation | -0.0494 | -5.9 | 7.7e-08 | 100% | -0.062 | 1410 |
| `X_z_D_realvol_ratio_20_60` | existing | -0.0494 | -5.9 | 7.7e-08 | 100% | -0.062 | 1410 |
| `X_rank_D_realvol_ratio_20_60` | existing | -0.0494 | -5.9 | 7.7e-08 | 100% | -0.062 | 1410 |
| `D_realvol_ratio_20_60` | existing | -0.0494 | -5.9 | 7.7e-08 | 100% | -0.062 | 1410 |

### Works in stock regime S7 (77 cells)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|
| `D_atr_pct_z252` | existing | -0.0869 | -8.9 | 0 | 100% | -0.103 | 1348 |
| `D_atr_ratio_14_30` | existing | -0.0823 | -7.9 | 1.4e-13 | 100% | -0.098 | 1348 |
| `R_atr_ratio_14_30__csz` | representation | -0.0823 | -7.9 | 1.4e-13 | 100% | -0.098 | 1348 |
| `R_atr_ratio_14_30__csrank` | representation | -0.0823 | -7.9 | 1.4e-13 | 100% | -0.098 | 1348 |
| `R_atr_pct__tsz60` | representation | -0.0746 | -6.9 | 2e-10 | 100% | -0.092 | 1319 |
| `R_atr_pct__d20` | representation | -0.0726 | -7.0 | 7.9e-11 | 100% | -0.094 | 1326 |
| `N_dist_hi10` | location | +0.0552 | +5.7 | 2.9e-07 | 100% | +0.067 | 1345 |
| `R_atr_ratio_14_30__tsz60` | representation | -0.0486 | -4.5 | 6.5e-05 | 100% | -0.055 | 1319 |
| `D_vol_yz_20` | existing | -0.0471 | -4.8 | 2.6e-05 | 100% | -0.060 | 1348 |
| `X_z_D_atr_pct` | existing | -0.0456 | -4.7 | 3.1e-05 | 100% | -0.055 | 1348 |
| `X_rank_D_atr_pct` | existing | -0.0456 | -4.7 | 3.1e-05 | 100% | -0.055 | 1348 |
| `D_atr_pct` | existing | -0.0456 | -4.7 | 3.1e-05 | 100% | -0.055 | 1348 |

### Works in stock regime S8 (110 cells)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|
| `D_atr_pct_z252` | existing | -0.0711 | -9.0 | 0 | 100% | -0.088 | 1427 |
| `R_atr_pct__tsz60` | representation | -0.0565 | -7.2 | 3.1e-11 | 100% | -0.068 | 1426 |
| `X_rank_D_dist_from_52wl` | existing | +0.0538 | +6.8 | 4.3e-10 | 100% | +0.060 | 1427 |
| `D_dist_from_52wl` | existing | +0.0538 | +6.8 | 4.3e-10 | 100% | +0.060 | 1427 |
| `X_z_D_dist_from_52wl` | existing | +0.0538 | +6.8 | 4.3e-10 | 100% | +0.060 | 1427 |
| `D_atr_ratio_14_30` | existing | -0.0526 | -6.8 | 4.1e-10 | 100% | -0.061 | 1427 |
| `R_atr_ratio_14_30__csz` | representation | -0.0526 | -6.8 | 4.1e-10 | 100% | -0.061 | 1427 |
| `R_atr_ratio_14_30__csrank` | representation | -0.0526 | -6.8 | 4.1e-10 | 100% | -0.061 | 1427 |
| `R_atr_pct__d20` | representation | -0.0526 | -6.7 | 6.8e-10 | 100% | -0.062 | 1427 |
| `X_z_D_bb_pctB_20` | existing | +0.0427 | +5.6 | 4.3e-07 | 100% | +0.047 | 1427 |
| `D_bb_pctB_20` | existing | +0.0427 | +5.6 | 4.3e-07 | 100% | +0.047 | 1427 |
| `X_rank_D_bb_pctB_20` | existing | +0.0427 | +5.6 | 4.3e-07 | 100% | +0.047 | 1427 |

### Works in market regime M0 (40 cells)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|
| `D_atr_pct_z252` | existing | -0.0987 | -4.8 | 1.8e-05 | 100% | -0.123 | 91 |
| `D_atr_ratio_14_30` | existing | -0.0865 | -3.4 | 0.0034 | 100% | -0.113 | 91 |
| `R_atr_ratio_14_30__csrank` | representation | -0.0865 | -3.4 | 0.0034 | 100% | -0.113 | 91 |
| `R_atr_ratio_14_30__csz` | representation | -0.0865 | -3.4 | 0.0034 | 100% | -0.113 | 91 |
| `R_atr_pct__d20` | representation | -0.0852 | -4.7 | 2.7e-05 | 100% | -0.112 | 91 |
| `R_atr_pct__tsz60` | representation | -0.0770 | -4.0 | 0.00054 | 100% | -0.099 | 91 |
| `R_atr_ratio_14_30__tsz60` | representation | -0.0614 | -3.6 | 0.0022 | 100% | -0.083 | 91 |
| `R_realvol_ratio_20_60__csrank` | representation | -0.0596 | -4.1 | 0.00036 | 100% | -0.088 | 91 |
| `R_realvol_ratio_20_60__csz` | representation | -0.0596 | -4.1 | 0.00036 | 100% | -0.088 | 91 |
| `X_rank_D_realvol_ratio_20_60` | existing | -0.0596 | -4.1 | 0.00036 | 100% | -0.088 | 91 |
| `X_z_D_realvol_ratio_20_60` | existing | -0.0596 | -4.1 | 0.00036 | 100% | -0.088 | 91 |
| `D_realvol_ratio_20_60` | existing | -0.0596 | -4.1 | 0.00036 | 100% | -0.088 | 91 |

### Works in market regime M1 (24 cells)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|
| `D_atr_ratio_14_30` | existing | -0.0932 | -3.3 | 0.0045 | 100% | -0.117 | 84 |
| `R_atr_ratio_14_30__csz` | representation | -0.0932 | -3.3 | 0.0045 | 100% | -0.117 | 84 |
| `R_atr_ratio_14_30__csrank` | representation | -0.0932 | -3.3 | 0.0045 | 100% | -0.117 | 84 |
| `D_atr_pct_z252` | existing | -0.0862 | -3.7 | 0.0013 | 100% | -0.095 | 84 |
| `R_atr_ratio_14_30__d20` | representation | -0.0857 | -3.8 | 0.0011 | 100% | -0.110 | 84 |
| `R_atr_ratio_14_30__tsz60` | representation | -0.0834 | -3.8 | 0.0012 | 100% | -0.107 | 84 |
| `D_realvol_ratio_20_60` | existing | -0.0764 | -3.5 | 0.0024 | 100% | -0.093 | 84 |
| `X_rank_D_realvol_ratio_20_60` | existing | -0.0764 | -3.5 | 0.0024 | 100% | -0.093 | 84 |
| `X_z_D_realvol_ratio_20_60` | existing | -0.0764 | -3.5 | 0.0024 | 100% | -0.093 | 84 |
| `R_realvol_ratio_20_60__csrank` | representation | -0.0764 | -3.5 | 0.0024 | 100% | -0.093 | 84 |
| `R_realvol_ratio_20_60__csz` | representation | -0.0764 | -3.5 | 0.0024 | 100% | -0.093 | 84 |
| `R_realvol_20__d20` | representation | -0.0704 | -3.7 | 0.0016 | 100% | -0.086 | 84 |

### Works in market regime M2 (82 cells)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|
| `D_atr_pct_z252` | existing | -0.0919 | -10.6 | 0 | 100% | -0.122 | 306 |
| `R_atr_pct__tsz60` | representation | -0.0872 | -10.3 | 0 | 100% | -0.111 | 306 |
| `R_atr_ratio_14_30__csrank` | representation | -0.0774 | -7.5 | 3.7e-12 | 100% | -0.102 | 306 |
| `R_atr_ratio_14_30__csz` | representation | -0.0774 | -7.5 | 3.7e-12 | 100% | -0.102 | 306 |
| `D_atr_ratio_14_30` | existing | -0.0774 | -7.5 | 3.7e-12 | 100% | -0.102 | 306 |
| `R_atr_pct__d20` | representation | -0.0717 | -7.9 | 1.2e-13 | 100% | -0.093 | 306 |
| `R_realvol_20__tsz60` | representation | -0.0652 | -8.3 | 1.5e-14 | 100% | -0.084 | 306 |
| `D_realvol_ratio_20_60` | existing | -0.0642 | -8.5 | 0 | 100% | -0.081 | 306 |
| `X_z_D_realvol_ratio_20_60` | existing | -0.0642 | -8.5 | 0 | 100% | -0.081 | 306 |
| `X_rank_D_realvol_ratio_20_60` | existing | -0.0642 | -8.5 | 0 | 100% | -0.081 | 306 |
| `R_realvol_ratio_20_60__csz` | representation | -0.0642 | -8.5 | 0 | 100% | -0.081 | 306 |
| `R_realvol_ratio_20_60__csrank` | representation | -0.0642 | -8.5 | 0 | 100% | -0.081 | 306 |

### Works in market regime M3 (68 cells)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|
| `D_atr_pct_z252` | existing | -0.0599 | -6.2 | 1.3e-08 | 100% | -0.077 | 287 |
| `R_atr_pct__d20` | representation | -0.0546 | -5.8 | 1.1e-07 | 100% | -0.066 | 287 |
| `R_atr_pct__tsz60` | representation | -0.0515 | -5.9 | 9.5e-08 | 100% | -0.063 | 287 |
| `D_realvol_ratio_20_60` | existing | -0.0462 | -5.6 | 3e-07 | 100% | -0.063 | 287 |
| `X_rank_D_realvol_ratio_20_60` | existing | -0.0462 | -5.6 | 3e-07 | 100% | -0.063 | 287 |
| `X_z_D_realvol_ratio_20_60` | existing | -0.0462 | -5.6 | 3e-07 | 100% | -0.063 | 287 |
| `R_realvol_ratio_20_60__csz` | representation | -0.0462 | -5.6 | 3e-07 | 100% | -0.063 | 287 |
| `R_realvol_ratio_20_60__csrank` | representation | -0.0462 | -5.6 | 3e-07 | 100% | -0.063 | 287 |
| `X_relvol_20` | existing | -0.0453 | -4.5 | 8.9e-05 | 100% | -0.054 | 287 |
| `X_rank_D_realvol_20` | existing | -0.0453 | -4.5 | 8.9e-05 | 100% | -0.054 | 287 |
| `R_realvol_20__csrank` | representation | -0.0453 | -4.5 | 8.9e-05 | 100% | -0.054 | 287 |
| `D_realvol_20` | existing | -0.0453 | -4.5 | 8.9e-05 | 100% | -0.054 | 287 |

### Works in market regime M4 (129 cells)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|
| `D_atr_pct_z252` | existing | -0.0740 | -7.8 | 3.9e-13 | 100% | -0.093 | 296 |
| `R_atr_pct__d20` | representation | -0.0725 | -7.8 | 3e-13 | 100% | -0.088 | 296 |
| `R_atr_pct__tsz60` | representation | -0.0703 | -7.5 | 2.5e-12 | 100% | -0.087 | 296 |
| `N_dist_hi10` | location | +0.0630 | +6.6 | 1.2e-09 | 100% | +0.071 | 296 |
| `R_atr_ratio_14_30__csrank` | representation | -0.0630 | -5.4 | 9.4e-07 | 100% | -0.082 | 296 |
| `D_atr_ratio_14_30` | existing | -0.0630 | -5.4 | 9.4e-07 | 100% | -0.082 | 296 |
| `R_atr_ratio_14_30__csz` | representation | -0.0630 | -5.4 | 9.4e-07 | 100% | -0.082 | 296 |
| `X_rank_D_realvol_ratio_20_60` | existing | -0.0553 | -6.8 | 2.8e-10 | 100% | -0.071 | 296 |
| `D_realvol_ratio_20_60` | existing | -0.0553 | -6.8 | 2.8e-10 | 100% | -0.071 | 296 |
| `R_realvol_ratio_20_60__csrank` | representation | -0.0553 | -6.8 | 2.8e-10 | 100% | -0.071 | 296 |
| `X_z_D_realvol_ratio_20_60` | existing | -0.0553 | -6.8 | 2.8e-10 | 100% | -0.071 | 296 |
| `R_realvol_ratio_20_60__csz` | representation | -0.0553 | -6.8 | 2.8e-10 | 100% | -0.071 | 296 |

### Works in market regime M5 (153 cells)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|
| `R_atr_pct__tsz60` | representation | -0.0795 | -9.3 | 0 | 100% | -0.104 | 372 |
| `D_atr_pct_z252` | existing | -0.0793 | -9.3 | 0 | 100% | -0.103 | 372 |
| `R_atr_pct__d20` | representation | -0.0710 | -8.6 | 0 | 100% | -0.090 | 372 |
| `D_atr_ratio_14_30` | existing | -0.0692 | -6.8 | 3e-10 | 100% | -0.089 | 372 |
| `R_atr_ratio_14_30__csz` | representation | -0.0692 | -6.8 | 3e-10 | 100% | -0.089 | 372 |
| `R_atr_ratio_14_30__csrank` | representation | -0.0692 | -6.8 | 3e-10 | 100% | -0.089 | 372 |
| `R_realvol_20__tsz60` | representation | -0.0582 | -7.9 | 2.1e-13 | 100% | -0.075 | 372 |
| `X_rank_D_realvol_ratio_20_60` | existing | -0.0578 | -8.0 | 5.4e-14 | 100% | -0.076 | 372 |
| `D_realvol_ratio_20_60` | existing | -0.0578 | -8.0 | 5.4e-14 | 100% | -0.076 | 372 |
| `X_z_D_realvol_ratio_20_60` | existing | -0.0578 | -8.0 | 5.4e-14 | 100% | -0.076 | 372 |
| `R_realvol_ratio_20_60__csz` | representation | -0.0578 | -8.0 | 5.4e-14 | 100% | -0.076 | 372 |
| `R_realvol_ratio_20_60__csrank` | representation | -0.0578 | -8.0 | 5.4e-14 | 100% | -0.076 | 372 |

## Sign flips - works one way here, the opposite way there

HYPOTHESES, not findings: selected from many tests, so each needs its own confirmation on data not used to find it.

A feature significant with OPPOSITE signs in two regimes. An unconditional model averages these into nothing; this is exactly the information regime conditioning exists to recover.

| feature | layer | + regime | + IC | - regime | - IC |
|---|---|---|---|---|---|
| `D_drawdown_252` | stock | S4 | +0.0483 | S2 | -0.0294 |
| `R_drawdown_252__csz` | stock | S4 | +0.0483 | S2 | -0.0294 |
| `X_rank_D_drawdown_252` | stock | S4 | +0.0483 | S2 | -0.0294 |
| `X_z_D_drawdown_252` | stock | S4 | +0.0483 | S2 | -0.0294 |
| `R_drawdown_252__csrank` | stock | S4 | +0.0483 | S2 | -0.0294 |
| `X_z_D_dist_from_52wh` | stock | S4 | +0.0407 | S0 | -0.0355 |
| `D_dist_from_52wh` | stock | S4 | +0.0407 | S0 | -0.0355 |
| `X_rank_D_dist_from_52wh` | stock | S4 | +0.0407 | S0 | -0.0355 |
| `N_dist_hi250` | stock | S4 | +0.0371 | S2 | -0.0272 |
| `I_bb_pctB_20__x__adx14` | stock | S4 | +0.0353 | S1 | -0.0234 |
| `I_realvol_ratio_20_60__x__pos_in_52w_range` | stock | S0 | +0.0341 | S8 | -0.0324 |
| `I_compress_state__x__dist_from_20h` | stock | S7 | +0.0278 | S8 | -0.0219 |
| `N_volofvol20` | stock | S2 | +0.0242 | S4 | -0.0340 |
| `I_dvol_z20__x__ema20_angle_deg` | stock | S8 | +0.0207 | S3 | -0.0242 |

## Feature x regime matrix (top 40 by max |IC|)

`*` = working (FDR + stable + material). Blank = too few dates.

| feature | ALL | S0 | S1 | S2 | S3 | S4 | S5 | S6 | S7 | S8 | M0 | M1 | M2 | M3 | M4 | M5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `D_atr_pct_z252` | -0.074* | -0.075* | -0.071* | -0.064* | -0.078* | -0.079* | -0.069* | -0.061* | -0.087* | -0.071* | -0.099* | -0.086* | -0.092* | -0.060* | -0.074* | -0.079* |
| `D_atr_ratio_14_30` | -0.061* | -0.086* | -0.076* | -0.061* | -0.084* | -0.033* | -0.043* | -0.062* | -0.082* | -0.053* | -0.086* | -0.093* | -0.077* | -0.041* | -0.063* | -0.069* |
| `R_atr_ratio_14_30__csz` | -0.061* | -0.086* | -0.076* | -0.061* | -0.084* | -0.033* | -0.043* | -0.062* | -0.082* | -0.053* | -0.086* | -0.093* | -0.077* | -0.041* | -0.063* | -0.069* |
| `R_atr_ratio_14_30__csrank` | -0.061* | -0.086* | -0.076* | -0.061* | -0.084* | -0.033* | -0.043* | -0.062* | -0.082* | -0.053* | -0.086* | -0.093* | -0.077* | -0.041* | -0.063* | -0.069* |
| `R_atr_pct__tsz60` | -0.071* | -0.074* | -0.066* | -0.062* | -0.080* | -0.059* | -0.053* | -0.069* | -0.075* | -0.056* | -0.077* | -0.063* | -0.087* | -0.052* | -0.070* | -0.079* |
| `R_atr_ratio_14_30__d20` | -0.044* | -0.055* | -0.049* | -0.046* | -0.055* | -0.039* | -0.038* | -0.042* | -0.040* | -0.033* | -0.051* | -0.086* | -0.052* | -0.036* | -0.049* | -0.045* |
| `R_atr_pct__d20` | -0.067* | -0.076* | -0.063* | -0.067* | -0.073* | -0.068* | -0.056* | -0.051* | -0.073* | -0.053* | -0.085* | -0.065* | -0.072* | -0.055* | -0.073* | -0.071* |
| `R_atr_ratio_14_30__tsz60` | -0.045* | -0.056* | -0.052* | -0.045* | -0.060* | -0.021 | -0.034* | -0.049* | -0.049* | -0.033* | -0.061* | -0.083* | -0.054* | -0.028* | -0.046* | -0.051* |
| `D_realvol_ratio_20_60` | -0.055* | -0.064* | -0.046* | -0.044* | -0.059* | -0.032* | -0.030* | -0.049* | -0.044* | -0.041* | -0.060* | -0.076* | -0.064* | -0.046* | -0.055* | -0.058* |
| `X_z_D_realvol_ratio_20_60` | -0.055* | -0.064* | -0.046* | -0.044* | -0.059* | -0.032* | -0.030* | -0.049* | -0.044* | -0.041* | -0.060* | -0.076* | -0.064* | -0.046* | -0.055* | -0.058* |
| `X_rank_D_realvol_ratio_20_60` | -0.055* | -0.064* | -0.046* | -0.044* | -0.059* | -0.032* | -0.030* | -0.049* | -0.044* | -0.041* | -0.060* | -0.076* | -0.064* | -0.046* | -0.055* | -0.058* |
| `R_realvol_ratio_20_60__csrank` | -0.055* | -0.064* | -0.046* | -0.044* | -0.059* | -0.032* | -0.030* | -0.049* | -0.044* | -0.041* | -0.060* | -0.076* | -0.064* | -0.046* | -0.055* | -0.058* |
| `R_realvol_ratio_20_60__csz` | -0.055* | -0.064* | -0.046* | -0.044* | -0.059* | -0.032* | -0.030* | -0.049* | -0.044* | -0.041* | -0.060* | -0.076* | -0.064* | -0.046* | -0.055* | -0.058* |
| `R_realvol_20__d20` | -0.045* | -0.052* | -0.034* | -0.041* | -0.046* | -0.046* | -0.027 | -0.032* | -0.035* | -0.029* | -0.037* | -0.070* | -0.050* | -0.042* | -0.050* | -0.043* |
| `R_realvol_20__tsz60` | -0.055* | -0.064* | -0.044* | -0.037* | -0.062* | -0.035* | -0.027 | -0.046* | -0.044* | -0.042* | -0.054* | -0.058* | -0.065* | -0.045* | -0.055* | -0.058* |
| `N_dist_hi10` | +0.054* | +0.047* | +0.038* | +0.018 | +0.053* | +0.062* | +0.059* | +0.039* | +0.055* | +0.037 | +0.059* | +0.024 | +0.061* | +0.033* | +0.063* | +0.057* |
| `X_rank_D_realvol_20` | -0.047* | -0.062* | -0.031* | -0.010 | -0.053* | -0.034* | -0.019 | -0.035* | -0.040* | -0.034* | -0.030 | -0.031 | -0.056* | -0.045* | -0.049* | -0.052* |
| `D_realvol_20` | -0.047* | -0.062* | -0.031* | -0.010 | -0.053* | -0.034* | -0.019 | -0.035* | -0.040* | -0.034* | -0.030 | -0.031 | -0.056* | -0.045* | -0.049* | -0.052* |
| `X_relvol_20` | -0.047* | -0.062* | -0.031* | -0.010 | -0.053* | -0.034* | -0.019 | -0.035* | -0.040* | -0.034* | -0.030 | -0.031 | -0.056* | -0.045* | -0.049* | -0.052* |
| `R_realvol_20__csz` | -0.047* | -0.062* | -0.031* | -0.010 | -0.053* | -0.034* | -0.019 | -0.035* | -0.040* | -0.034* | -0.030 | -0.031 | -0.056* | -0.045* | -0.049* | -0.052* |
| `R_realvol_20__csrank` | -0.047* | -0.062* | -0.031* | -0.010 | -0.053* | -0.034* | -0.019 | -0.035* | -0.040* | -0.034* | -0.030 | -0.031 | -0.056* | -0.045* | -0.049* | -0.052* |
| `X_z_D_realvol_20` | -0.047* | -0.062* | -0.031* | -0.010 | -0.053* | -0.034* | -0.019 | -0.035* | -0.040* | -0.034* | -0.030 | -0.031 | -0.056* | -0.045* | -0.049* | -0.052* |
| `N_dist_hi100` | +0.015 | -0.010 | -0.006 | -0.019 | -0.017 | +0.060* | +0.019 | -0.004 | +0.004 | +0.019 | -0.021 | -0.037 | +0.008 | +0.023 | +0.014 | +0.013 |
| `N_min_ret20` | +0.045* | +0.057* | +0.021* | -0.002 | +0.060* | +0.034* | +0.026 | +0.030* | +0.033* | +0.030* | +0.041* | +0.010 | +0.046* | +0.045* | +0.045* | +0.051* |
| `N_dist_hi50` | +0.023* | +0.002 | -0.003 | -0.017 | -0.006 | +0.058* | +0.026 | -0.002 | +0.013 | +0.024 | +0.004 | -0.040 | +0.016 | +0.023 | +0.026 | +0.020 |
| `X_z_D_bb_pctB_20` | +0.023* | +0.007 | +0.012 | +0.018 | +0.011 | +0.047* | +0.057* | +0.011 | +0.017 | +0.043* | +0.024 | -0.010 | +0.018 | +0.010 | +0.030* | +0.027* |
| `X_rank_D_bb_pctB_20` | +0.023* | +0.007 | +0.012 | +0.018 | +0.011 | +0.047* | +0.057* | +0.011 | +0.017 | +0.043* | +0.024 | -0.010 | +0.018 | +0.010 | +0.030* | +0.027* |
| `D_bb_pctB_20` | +0.023* | +0.007 | +0.012 | +0.018 | +0.011 | +0.047* | +0.057* | +0.011 | +0.017 | +0.043* | +0.024 | -0.010 | +0.018 | +0.010 | +0.030* | +0.027* |
| `R_bb_pctB_20__csz` | +0.023* | +0.007 | +0.012 | +0.018 | +0.011 | +0.047* | +0.057* | +0.011 | +0.017 | +0.043* | +0.024 | -0.010 | +0.018 | +0.010 | +0.030* | +0.027* |
| `R_bb_pctB_20__csrank` | +0.023* | +0.007 | +0.012 | +0.018 | +0.011 | +0.047* | +0.057* | +0.011 | +0.017 | +0.043* | +0.024 | -0.010 | +0.018 | +0.010 | +0.030* | +0.027* |
| `R_realvol_ratio_20_60__d20` | -0.036* | -0.040* | -0.023* | -0.030* | -0.032* | -0.029 | -0.024 | -0.030* | -0.012 | -0.018* | -0.022 | -0.055* | -0.036* | -0.032* | -0.040* | -0.037* |
| `D_vol_yz_20` | -0.045* | -0.050* | -0.036* | -0.014 | -0.044* | -0.032* | -0.020 | -0.031* | -0.047* | -0.030 | -0.017 | -0.051 | -0.054* | -0.039* | -0.042* | -0.050* |
| `R_bb_pctB_20__tsz60` | +0.029* | +0.021 | +0.015 | +0.023 | +0.026* | +0.029 | +0.054* | +0.015 | +0.026* | +0.034* | +0.037 | -0.006 | +0.025 | +0.013 | +0.038* | +0.033* |
| `D_dist_from_52wl` | +0.030* | +0.009 | +0.022 | +0.009 | +0.013 | +0.048* | +0.033 | +0.015 | +0.018 | +0.054* | +0.022 | +0.008 | +0.029 | +0.027* | +0.031 | +0.025* |
| `X_rank_D_dist_from_52wl` | +0.030* | +0.009 | +0.022 | +0.009 | +0.013 | +0.048* | +0.033 | +0.015 | +0.018 | +0.054* | +0.022 | +0.008 | +0.029 | +0.027* | +0.031 | +0.025* |
| `X_z_D_dist_from_52wl` | +0.030* | +0.009 | +0.022 | +0.009 | +0.013 | +0.048* | +0.033 | +0.015 | +0.018 | +0.054* | +0.022 | +0.008 | +0.029 | +0.027* | +0.031 | +0.025* |
| `R_bb_bw_20__csz` | -0.039* | -0.044* | -0.036* | -0.009 | -0.039* | -0.019 | -0.029* | -0.028* | -0.036* | -0.035* | -0.032 | -0.003 | -0.053* | -0.029* | -0.042* | -0.047* |
| `D_bb_bw_20` | -0.039* | -0.044* | -0.036* | -0.009 | -0.039* | -0.019 | -0.029* | -0.028* | -0.036* | -0.035* | -0.032 | -0.003 | -0.053* | -0.029* | -0.042* | -0.047* |
| `R_bb_bw_20__csrank` | -0.039* | -0.044* | -0.036* | -0.009 | -0.039* | -0.019 | -0.029* | -0.028* | -0.036* | -0.035* | -0.032 | -0.003 | -0.053* | -0.029* | -0.042* | -0.047* |
| `D_donch_pos_50` | +0.008 | -0.013 | -0.012 | -0.012 | -0.012 | +0.053* | +0.019 | -0.003 | -0.003 | +0.018 | +0.000 | -0.044 | -0.004 | +0.004 | +0.013 | +0.006 |

## Caveats

- Exploratory. A working cell is evidence to test, not a validated edge.
- About 5% of working cells are expected to be false discoveries by construction of the FDR bar.
- IC is cross-sectional ranking skill. It is not a return, and it ignores costs; `top-bot hit` is the hit-rate gap between the top and bottom quintile within the regime.
- Regime IDs are aligned across folds by centroid matching; check the drift figures before trusting a regime's identity over time.
- In-sample regime labels (before the first test window) never enter the statistics.