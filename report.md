# Feature Atlas - ATLAS_20260926_002

Target `label_tp_before_sl` | per-date rank IC | BH-FDR q<0.05 | sign-stable in >= 80% of folds | |IC| >= 0.01

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
- working cells: 2,154 | working features: 333 | families: 142
- expected false discoveries among working cells at q<0.05: ~107

## Stock regimes (K=9, chosen by BIC on fold-1 train)

Alignment drift across folds (mean centroid distance to the fold-1 reference): 0.00, 0.24, 0.33, 0.30, 0.24. Large values mean a regime ID no longer describes the same state.

| regime | st_trend | st_trend_strength | st_vol_level | st_vol_change | st_momentum | st_participation | st_location | st_shock | share | base rate |
|---|---|---|---|---|---|---|---|---|---|---|
| S0 | -0.35 | -0.07 | +0.02 | -0.03 | -0.33 | +0.01 | -0.18 | +0.26 | 14.7% | 0.270 |
| S1 | +0.12 | -0.05 | -0.07 | +0.01 | +0.11 | +0.14 | -0.08 | -0.02 | 20.1% | 0.293 |
| S2 | -0.15 | -0.06 | -0.39 | -0.24 | -0.24 | +0.01 | -0.17 | -0.14 | 9.2% | 0.302 |
| S3 | -0.32 | -0.10 | -0.05 | -0.04 | -0.33 | -0.06 | -0.21 | -0.23 | 12.0% | 0.280 |
| S4 | +0.42 | +0.38 | +0.37 | +0.22 | +0.39 | +0.05 | +0.34 | +0.07 | 6.4% | 0.272 |
| S5 | +0.39 | +0.04 | +0.18 | +0.11 | +0.34 | +0.41 | +0.17 | +0.43 | 5.5% | 0.324 |
| S6 | -0.06 | -0.08 | -0.08 | -0.06 | -0.05 | -0.35 | -0.04 | -0.09 | 13.8% | 0.281 |
| S7 | -0.01 | +0.05 | +0.36 | +0.13 | +0.01 | -0.08 | -0.03 | +0.09 | 7.7% | 0.247 |
| S8 | +0.21 | +0.11 | -0.05 | -0.01 | +0.25 | +0.02 | +0.35 | -0.04 | 10.4% | 0.297 |

## Market regimes (K=6, chosen by BIC on fold-1 train)

Alignment drift across folds (mean centroid distance to the fold-1 reference): 0.00, 1.21, 3.36, 4.43, 4.36. Large values mean a regime ID no longer describes the same state.

| regime | mk_trend20 | mk_vol20 | mk_breadth20 | mk_disp20 | share | base rate |
|---|---|---|---|---|---|---|
| M0 | -0.03 | +1.16 | +0.26 | +0.61 | 3.3% | 0.340 |
| M1 | -2.53 | +2.74 | -1.46 | +2.00 | 2.6% | 0.216 |
| M2 | +0.80 | -0.25 | +0.84 | -0.63 | 22.1% | 0.277 |
| M3 | -1.01 | +0.49 | -1.19 | +0.36 | 29.0% | 0.285 |
| M4 | +0.17 | -0.46 | +0.00 | +0.79 | 15.0% | 0.281 |
| M5 | +0.27 | -0.79 | +0.08 | -0.65 | 28.0% | 0.291 |

Stock-regime persistence (measured): S0 mean run 2.3d, S1 mean run 2.3d, S2 mean run 2.3d, S3 mean run 2.3d, S4 mean run 2.4d, S5 mean run 2.4d, S6 mean run 2.3d, S7 mean run 2.3d, S8 mean run 2.4d

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

### Works in stock regime S0 (167 cells)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|
| `D_atr_ratio_14_30` | existing | -0.0863 | -11.4 | 0 | 100% | -0.113 | 1790 |
| `R_atr_ratio_14_30__csz` | representation | -0.0863 | -11.4 | 0 | 100% | -0.113 | 1790 |
| `R_atr_ratio_14_30__csrank` | representation | -0.0863 | -11.4 | 0 | 100% | -0.113 | 1790 |
| `R_atr_pct__d20` | representation | -0.0766 | -10.6 | 0 | 100% | -0.099 | 1790 |
| `R_atr_pct__tsz60` | representation | -0.0759 | -10.2 | 0 | 100% | -0.098 | 1790 |
| `D_atr_pct_z252` | existing | -0.0747 | -10.4 | 0 | 100% | -0.097 | 1790 |
| `R_realvol_20__tsz60` | representation | -0.0659 | -9.2 | 0 | 100% | -0.081 | 1790 |
| `X_z_D_realvol_ratio_20_60` | existing | -0.0653 | -9.5 | 0 | 100% | -0.080 | 1790 |
| `X_rank_D_realvol_ratio_20_60` | existing | -0.0653 | -9.5 | 0 | 100% | -0.080 | 1790 |
| `D_realvol_ratio_20_60` | existing | -0.0653 | -9.5 | 0 | 100% | -0.080 | 1790 |
| `R_realvol_ratio_20_60__csrank` | representation | -0.0653 | -9.5 | 0 | 100% | -0.080 | 1790 |
| `R_realvol_ratio_20_60__csz` | representation | -0.0653 | -9.5 | 0 | 100% | -0.080 | 1790 |

### Works in stock regime S1 (155 cells)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|
| `D_atr_ratio_14_30` | existing | -0.0680 | -10.9 | 0 | 100% | -0.084 | 1800 |
| `R_atr_ratio_14_30__csz` | representation | -0.0680 | -10.9 | 0 | 100% | -0.084 | 1800 |
| `R_atr_ratio_14_30__csrank` | representation | -0.0680 | -10.9 | 0 | 100% | -0.084 | 1800 |
| `D_atr_pct_z252` | existing | -0.0661 | -11.1 | 0 | 100% | -0.086 | 1800 |
| `R_atr_pct__tsz60` | representation | -0.0651 | -11.0 | 0 | 100% | -0.081 | 1796 |
| `R_atr_pct__d20` | representation | -0.0601 | -10.1 | 0 | 100% | -0.075 | 1798 |
| `R_atr_ratio_14_30__tsz60` | representation | -0.0494 | -8.8 | 0 | 100% | -0.061 | 1796 |
| `R_atr_ratio_14_30__d20` | representation | -0.0458 | -8.2 | 1.1e-14 | 100% | -0.054 | 1798 |
| `R_realvol_20__tsz60` | representation | -0.0442 | -8.0 | 5.1e-14 | 100% | -0.056 | 1796 |
| `X_z_D_realvol_ratio_20_60` | existing | -0.0439 | -8.0 | 6.5e-14 | 100% | -0.054 | 1800 |
| `R_realvol_ratio_20_60__csrank` | representation | -0.0439 | -8.0 | 6.5e-14 | 100% | -0.054 | 1800 |
| `D_realvol_ratio_20_60` | existing | -0.0439 | -8.0 | 6.5e-14 | 100% | -0.054 | 1800 |

### Works in stock regime S2 (93 cells)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|
| `R_atr_pct__d20` | representation | -0.0642 | -7.8 | 2.2e-13 | 100% | -0.083 | 1784 |
| `R_atr_pct__tsz60` | representation | -0.0611 | -7.4 | 5.7e-12 | 100% | -0.077 | 1783 |
| `D_atr_pct_z252` | existing | -0.0593 | -7.1 | 2.7e-11 | 100% | -0.075 | 1787 |
| `D_atr_ratio_14_30` | existing | -0.0574 | -6.7 | 4.3e-10 | 100% | -0.073 | 1787 |
| `R_atr_ratio_14_30__csz` | representation | -0.0574 | -6.7 | 4.3e-10 | 100% | -0.073 | 1787 |
| `R_atr_ratio_14_30__csrank` | representation | -0.0574 | -6.7 | 4.3e-10 | 100% | -0.073 | 1787 |
| `R_atr_ratio_14_30__tsz60` | representation | -0.0466 | -6.0 | 3.6e-08 | 100% | -0.056 | 1783 |
| `X_rank_D_realvol_ratio_20_60` | existing | -0.0442 | -5.8 | 1.3e-07 | 100% | -0.058 | 1787 |
| `D_realvol_ratio_20_60` | existing | -0.0442 | -5.8 | 1.3e-07 | 100% | -0.058 | 1787 |
| `X_z_D_realvol_ratio_20_60` | existing | -0.0442 | -5.8 | 1.3e-07 | 100% | -0.058 | 1787 |
| `R_realvol_ratio_20_60__csrank` | representation | -0.0442 | -5.8 | 1.3e-07 | 100% | -0.058 | 1787 |
| `R_realvol_ratio_20_60__csz` | representation | -0.0442 | -5.8 | 1.3e-07 | 100% | -0.058 | 1787 |

### Works in stock regime S3 (139 cells)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|
| `R_atr_ratio_14_30__csz` | representation | -0.0796 | -9.7 | 0 | 100% | -0.104 | 1713 |
| `R_atr_ratio_14_30__csrank` | representation | -0.0796 | -9.7 | 0 | 100% | -0.104 | 1713 |
| `D_atr_ratio_14_30` | existing | -0.0796 | -9.7 | 0 | 100% | -0.104 | 1713 |
| `R_atr_pct__tsz60` | representation | -0.0771 | -9.9 | 0 | 100% | -0.099 | 1699 |
| `D_atr_pct_z252` | existing | -0.0722 | -9.4 | 0 | 100% | -0.092 | 1713 |
| `R_atr_pct__d20` | representation | -0.0717 | -9.3 | 0 | 100% | -0.088 | 1703 |
| `R_realvol_20__tsz60` | representation | -0.0596 | -8.0 | 5.8e-14 | 100% | -0.075 | 1699 |
| `R_atr_ratio_14_30__tsz60` | representation | -0.0574 | -7.5 | 2e-12 | 100% | -0.070 | 1699 |
| `N_min_ret20` | distribution | +0.0557 | +7.6 | 9.2e-13 | 100% | +0.070 | 1707 |
| `R_realvol_ratio_20_60__csrank` | representation | -0.0555 | -7.4 | 3.1e-12 | 100% | -0.066 | 1713 |
| `X_z_D_realvol_ratio_20_60` | existing | -0.0555 | -7.4 | 3.1e-12 | 100% | -0.066 | 1713 |
| `X_rank_D_realvol_ratio_20_60` | existing | -0.0555 | -7.4 | 3.1e-12 | 100% | -0.066 | 1713 |

### Works in stock regime S4 (180 cells)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|
| `D_atr_pct_z252` | existing | -0.0779 | -7.9 | 9.2e-14 | 100% | -0.095 | 1366 |
| `R_atr_pct__d20` | representation | -0.0702 | -7.2 | 2.2e-11 | 100% | -0.091 | 1317 |
| `N_dist_hi100` | location | +0.0642 | +5.9 | 7.9e-08 | 100% | +0.077 | 1280 |
| `N_dist_hi10` | location | +0.0631 | +6.5 | 1.5e-09 | 100% | +0.078 | 1351 |
| `N_dist_hi50` | location | +0.0618 | +6.0 | 3.1e-08 | 100% | +0.074 | 1314 |
| `R_atr_pct__tsz60` | representation | -0.0609 | -5.9 | 6.6e-08 | 100% | -0.081 | 1314 |
| `D_donch_pos_50` | existing | +0.0554 | +5.6 | 3e-07 | 100% | +0.067 | 1366 |
| `R_dist_from_20h__csrank` | representation | +0.0549 | +5.7 | 2.3e-07 | 100% | +0.064 | 1366 |
| `D_dist_from_20h` | existing | +0.0549 | +5.7 | 2.3e-07 | 100% | +0.064 | 1366 |
| `R_dist_from_20h__csz` | representation | +0.0549 | +5.7 | 2.3e-07 | 100% | +0.064 | 1366 |
| `D_drawdown_252` | existing | +0.0520 | +5.0 | 5.5e-06 | 100% | +0.063 | 1366 |
| `R_drawdown_252__csrank` | representation | +0.0520 | +5.0 | 5.5e-06 | 100% | +0.063 | 1366 |

### Works in stock regime S5 (148 cells)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|
| `D_atr_pct_z252` | existing | -0.0641 | -6.4 | 2.4e-09 | 100% | -0.087 | 1563 |
| `X_z_D_bb_pctB_20` | existing | +0.0584 | +5.9 | 5.7e-08 | 100% | +0.068 | 1563 |
| `D_bb_pctB_20` | existing | +0.0584 | +5.9 | 5.7e-08 | 100% | +0.068 | 1563 |
| `X_rank_D_bb_pctB_20` | existing | +0.0584 | +5.9 | 5.7e-08 | 100% | +0.068 | 1563 |
| `R_bb_pctB_20__csrank` | representation | +0.0584 | +5.9 | 5.7e-08 | 100% | +0.068 | 1563 |
| `R_bb_pctB_20__csz` | representation | +0.0584 | +5.9 | 5.7e-08 | 100% | +0.068 | 1563 |
| `N_dist_hi10` | location | +0.0568 | +5.7 | 1.5e-07 | 100% | +0.070 | 1555 |
| `R_atr_pct__tsz60` | representation | -0.0540 | -5.2 | 2.9e-06 | 100% | -0.071 | 1535 |
| `R_atr_pct__d20` | representation | -0.0539 | -5.3 | 1.3e-06 | 100% | -0.070 | 1541 |
| `R_bb_pctB_20__tsz60` | representation | +0.0531 | +5.3 | 1.2e-06 | 100% | +0.068 | 1535 |
| `N_clv` | structure | +0.0512 | +5.3 | 1.6e-06 | 100% | +0.064 | 1563 |
| `N_body_range` | structure | +0.0480 | +5.1 | 4.3e-06 | 100% | +0.060 | 1563 |

### Works in stock regime S6 (70 cells)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|
| `R_atr_pct__tsz60` | representation | -0.0660 | -9.1 | 0 | 100% | -0.085 | 1773 |
| `D_atr_pct_z252` | existing | -0.0572 | -8.3 | 1.1e-14 | 100% | -0.073 | 1775 |
| `R_atr_ratio_14_30__csz` | representation | -0.0550 | -7.2 | 1.5e-11 | 100% | -0.074 | 1775 |
| `R_atr_ratio_14_30__csrank` | representation | -0.0550 | -7.2 | 1.5e-11 | 100% | -0.074 | 1775 |
| `D_atr_ratio_14_30` | existing | -0.0550 | -7.2 | 1.5e-11 | 100% | -0.074 | 1775 |
| `R_atr_pct__d20` | representation | -0.0503 | -7.0 | 6.4e-11 | 100% | -0.067 | 1773 |
| `R_realvol_ratio_20_60__csz` | representation | -0.0462 | -6.7 | 6.4e-10 | 100% | -0.059 | 1775 |
| `R_realvol_ratio_20_60__csrank` | representation | -0.0462 | -6.7 | 6.4e-10 | 100% | -0.059 | 1775 |
| `D_realvol_ratio_20_60` | existing | -0.0462 | -6.7 | 6.4e-10 | 100% | -0.059 | 1775 |
| `X_rank_D_realvol_ratio_20_60` | existing | -0.0462 | -6.7 | 6.4e-10 | 100% | -0.059 | 1775 |
| `X_z_D_realvol_ratio_20_60` | existing | -0.0462 | -6.7 | 6.4e-10 | 100% | -0.059 | 1775 |
| `R_atr_ratio_14_30__tsz60` | representation | -0.0455 | -6.6 | 9.6e-10 | 100% | -0.055 | 1773 |

### Works in stock regime S7 (112 cells)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|
| `D_atr_pct_z252` | existing | -0.0806 | -9.5 | 0 | 100% | -0.096 | 1708 |
| `D_atr_ratio_14_30` | existing | -0.0769 | -8.6 | 0 | 100% | -0.092 | 1708 |
| `R_atr_ratio_14_30__csz` | representation | -0.0769 | -8.6 | 0 | 100% | -0.092 | 1708 |
| `R_atr_ratio_14_30__csrank` | representation | -0.0769 | -8.6 | 0 | 100% | -0.092 | 1708 |
| `R_atr_pct__tsz60` | representation | -0.0732 | -8.0 | 5.8e-14 | 100% | -0.090 | 1679 |
| `R_atr_pct__d20` | representation | -0.0708 | -8.0 | 4.1e-14 | 100% | -0.092 | 1686 |
| `N_dist_hi10` | location | +0.0552 | +6.6 | 8.4e-10 | 100% | +0.067 | 1705 |
| `D_vol_yz_20` | existing | -0.0473 | -5.5 | 4.3e-07 | 100% | -0.059 | 1708 |
| `R_atr_ratio_14_30__tsz60` | representation | -0.0463 | -5.1 | 3.7e-06 | 100% | -0.053 | 1679 |
| `X_z_D_atr_pct` | existing | -0.0462 | -5.6 | 3.7e-07 | 100% | -0.055 | 1708 |
| `R_atr_pct__csrank` | representation | -0.0462 | -5.6 | 3.7e-07 | 100% | -0.055 | 1708 |
| `R_atr_pct__csz` | representation | -0.0462 | -5.6 | 3.7e-07 | 100% | -0.055 | 1708 |

### Works in stock regime S8 (160 cells)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|
| `D_atr_pct_z252` | existing | -0.0607 | -8.0 | 4.1e-14 | 100% | -0.077 | 1791 |
| `R_atr_pct__tsz60` | representation | -0.0527 | -7.0 | 5.8e-11 | 100% | -0.064 | 1790 |
| `D_dist_from_52wl` | existing | +0.0511 | +6.7 | 4e-10 | 100% | +0.062 | 1791 |
| `X_rank_D_dist_from_52wl` | existing | +0.0511 | +6.7 | 4e-10 | 100% | +0.062 | 1791 |
| `X_z_D_dist_from_52wl` | existing | +0.0511 | +6.7 | 4e-10 | 100% | +0.062 | 1791 |
| `R_atr_pct__d20` | representation | -0.0503 | -6.8 | 3e-10 | 100% | -0.063 | 1791 |
| `D_atr_ratio_14_30` | existing | -0.0496 | -6.7 | 5.8e-10 | 100% | -0.058 | 1791 |
| `R_atr_ratio_14_30__csz` | representation | -0.0496 | -6.7 | 5.8e-10 | 100% | -0.058 | 1791 |
| `R_atr_ratio_14_30__csrank` | representation | -0.0496 | -6.7 | 5.8e-10 | 100% | -0.058 | 1791 |
| `X_rank_D_realvol_ratio_20_60` | existing | -0.0442 | -6.1 | 1.6e-08 | 100% | -0.055 | 1791 |
| `R_realvol_ratio_20_60__csz` | representation | -0.0442 | -6.1 | 1.6e-08 | 100% | -0.055 | 1791 |
| `R_realvol_ratio_20_60__csrank` | representation | -0.0442 | -6.1 | 1.6e-08 | 100% | -0.055 | 1791 |

### Works in market regime M0 (43 cells)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|
| `D_atr_pct_z252` | existing | -0.0987 | -4.8 | 1.3e-05 | 100% | -0.123 | 91 |
| `D_atr_ratio_14_30` | existing | -0.0865 | -3.4 | 0.0028 | 100% | -0.113 | 91 |
| `R_atr_ratio_14_30__csrank` | representation | -0.0865 | -3.4 | 0.0028 | 100% | -0.113 | 91 |
| `R_atr_ratio_14_30__csz` | representation | -0.0865 | -3.4 | 0.0028 | 100% | -0.113 | 91 |
| `R_atr_pct__d20` | representation | -0.0852 | -4.7 | 2e-05 | 100% | -0.112 | 91 |
| `R_atr_pct__tsz60` | representation | -0.0770 | -4.0 | 0.00042 | 100% | -0.099 | 91 |
| `R_atr_ratio_14_30__tsz60` | representation | -0.0614 | -3.6 | 0.0017 | 100% | -0.083 | 91 |
| `X_z_D_realvol_ratio_20_60` | existing | -0.0596 | -4.1 | 0.00028 | 100% | -0.088 | 91 |
| `X_rank_D_realvol_ratio_20_60` | existing | -0.0596 | -4.1 | 0.00028 | 100% | -0.088 | 91 |
| `R_realvol_ratio_20_60__csrank` | representation | -0.0596 | -4.1 | 0.00028 | 100% | -0.088 | 91 |
| `D_realvol_ratio_20_60` | existing | -0.0596 | -4.1 | 0.00028 | 100% | -0.088 | 91 |
| `R_realvol_ratio_20_60__csz` | representation | -0.0596 | -4.1 | 0.00028 | 100% | -0.088 | 91 |

### Works in market regime M1 (26 cells)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|
| `D_atr_ratio_14_30` | existing | -0.0932 | -3.3 | 0.0037 | 100% | -0.117 | 84 |
| `R_atr_ratio_14_30__csz` | representation | -0.0932 | -3.3 | 0.0037 | 100% | -0.117 | 84 |
| `R_atr_ratio_14_30__csrank` | representation | -0.0932 | -3.3 | 0.0037 | 100% | -0.117 | 84 |
| `D_atr_pct_z252` | existing | -0.0862 | -3.7 | 0.00099 | 100% | -0.095 | 84 |
| `R_atr_ratio_14_30__d20` | representation | -0.0857 | -3.8 | 0.00082 | 100% | -0.110 | 84 |
| `R_atr_ratio_14_30__tsz60` | representation | -0.0834 | -3.8 | 0.00089 | 100% | -0.107 | 84 |
| `X_z_D_realvol_ratio_20_60` | existing | -0.0764 | -3.5 | 0.0019 | 100% | -0.093 | 84 |
| `D_realvol_ratio_20_60` | existing | -0.0764 | -3.5 | 0.0019 | 100% | -0.093 | 84 |
| `X_rank_D_realvol_ratio_20_60` | existing | -0.0764 | -3.5 | 0.0019 | 100% | -0.093 | 84 |
| `R_realvol_ratio_20_60__csz` | representation | -0.0764 | -3.5 | 0.0019 | 100% | -0.093 | 84 |
| `R_realvol_ratio_20_60__csrank` | representation | -0.0764 | -3.5 | 0.0019 | 100% | -0.093 | 84 |
| `R_realvol_20__d20` | representation | -0.0704 | -3.7 | 0.0012 | 100% | -0.086 | 84 |

### Works in market regime M2 (183 cells)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|
| `D_atr_pct_z252` | existing | -0.0897 | -11.2 | 0 | 100% | -0.119 | 366 |
| `R_atr_pct__tsz60` | representation | -0.0860 | -11.0 | 0 | 100% | -0.110 | 366 |
| `D_atr_ratio_14_30` | existing | -0.0738 | -7.6 | 1.3e-12 | 100% | -0.098 | 366 |
| `R_atr_ratio_14_30__csz` | representation | -0.0738 | -7.6 | 1.3e-12 | 100% | -0.098 | 366 |
| `R_atr_ratio_14_30__csrank` | representation | -0.0738 | -7.6 | 1.3e-12 | 100% | -0.098 | 366 |
| `N_dist_hi10` | location | +0.0686 | +8.7 | 0 | 100% | +0.083 | 366 |
| `R_atr_pct__d20` | representation | -0.0673 | -8.1 | 3.2e-14 | 100% | -0.088 | 366 |
| `R_realvol_20__tsz60` | representation | -0.0631 | -8.7 | 0 | 100% | -0.081 | 366 |
| `R_realvol_ratio_20_60__csz` | representation | -0.0615 | -8.8 | 0 | 100% | -0.079 | 366 |
| `D_realvol_ratio_20_60` | existing | -0.0615 | -8.8 | 0 | 100% | -0.079 | 366 |
| `X_z_D_realvol_ratio_20_60` | existing | -0.0615 | -8.8 | 0 | 100% | -0.079 | 366 |
| `X_rank_D_realvol_ratio_20_60` | existing | -0.0615 | -8.8 | 0 | 100% | -0.079 | 366 |

### Works in market regime M3 (85 cells)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|
| `R_atr_pct__d20` | representation | -0.0582 | -8.4 | 0 | 100% | -0.070 | 466 |
| `D_atr_pct_z252` | existing | -0.0581 | -7.8 | 3.1e-13 | 100% | -0.076 | 466 |
| `R_atr_pct__tsz60` | representation | -0.0578 | -8.4 | 0 | 100% | -0.072 | 466 |
| `X_z_D_realvol_ratio_20_60` | existing | -0.0477 | -8.0 | 5.8e-14 | 100% | -0.062 | 466 |
| `D_realvol_ratio_20_60` | existing | -0.0477 | -8.0 | 5.8e-14 | 100% | -0.062 | 466 |
| `R_realvol_ratio_20_60__csz` | representation | -0.0477 | -8.0 | 5.8e-14 | 100% | -0.062 | 466 |
| `X_rank_D_realvol_ratio_20_60` | existing | -0.0477 | -8.0 | 5.8e-14 | 100% | -0.062 | 466 |
| `R_realvol_ratio_20_60__csrank` | representation | -0.0477 | -8.0 | 5.8e-14 | 100% | -0.062 | 466 |
| `R_realvol_20__tsz60` | representation | -0.0473 | -7.5 | 1.8e-12 | 100% | -0.063 | 466 |
| `R_realvol_20__d20` | representation | -0.0441 | -7.6 | 1e-12 | 100% | -0.054 | 466 |
| `N_min_ret20` | distribution | +0.0416 | +5.5 | 4.4e-07 | 100% | +0.045 | 466 |
| `R_atr_ratio_14_30__csrank` | representation | -0.0415 | -4.5 | 5.9e-05 | 100% | -0.059 | 466 |

### Works in market regime M4 (132 cells)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|
| `D_atr_pct_z252` | existing | -0.0747 | -8.3 | 0 | 100% | -0.093 | 323 |
| `R_atr_pct__d20` | representation | -0.0719 | -8.2 | 1.1e-14 | 100% | -0.089 | 323 |
| `R_atr_pct__tsz60` | representation | -0.0708 | -8.0 | 4.1e-14 | 100% | -0.088 | 323 |
| `N_dist_hi10` | location | +0.0657 | +7.3 | 1.2e-11 | 100% | +0.075 | 323 |
| `R_atr_ratio_14_30__csrank` | representation | -0.0612 | -5.6 | 3e-07 | 100% | -0.079 | 323 |
| `R_atr_ratio_14_30__csz` | representation | -0.0612 | -5.6 | 3e-07 | 100% | -0.079 | 323 |
| `D_atr_ratio_14_30` | existing | -0.0612 | -5.6 | 3e-07 | 100% | -0.079 | 323 |
| `R_realvol_ratio_20_60__csrank` | representation | -0.0549 | -7.1 | 2.8e-11 | 100% | -0.071 | 323 |
| `R_realvol_ratio_20_60__csz` | representation | -0.0549 | -7.1 | 2.8e-11 | 100% | -0.071 | 323 |
| `X_rank_D_realvol_ratio_20_60` | existing | -0.0549 | -7.1 | 2.8e-11 | 100% | -0.071 | 323 |
| `X_z_D_realvol_ratio_20_60` | existing | -0.0549 | -7.1 | 2.8e-11 | 100% | -0.071 | 323 |
| `D_realvol_ratio_20_60` | existing | -0.0549 | -7.1 | 2.8e-11 | 100% | -0.071 | 323 |

### Works in market regime M5 (207 cells)

| feature | category | IC | t | q | fold sign | top-bot hit | dates |
|---|---|---|---|---|---|---|---|
| `R_atr_pct__tsz60` | representation | -0.0738 | -9.7 | 0 | 100% | -0.097 | 471 |
| `D_atr_pct_z252` | existing | -0.0715 | -9.4 | 0 | 100% | -0.095 | 471 |
| `R_atr_pct__d20` | representation | -0.0679 | -9.4 | 0 | 100% | -0.085 | 471 |
| `R_atr_ratio_14_30__csz` | representation | -0.0596 | -6.7 | 5.9e-10 | 100% | -0.078 | 471 |
| `R_atr_ratio_14_30__csrank` | representation | -0.0596 | -6.7 | 5.9e-10 | 100% | -0.078 | 471 |
| `D_atr_ratio_14_30` | existing | -0.0596 | -6.7 | 5.9e-10 | 100% | -0.078 | 471 |
| `N_dist_hi10` | location | +0.0594 | +9.2 | 0 | 100% | +0.073 | 471 |
| `R_realvol_20__tsz60` | representation | -0.0546 | -8.4 | 0 | 100% | -0.071 | 471 |
| `R_realvol_ratio_20_60__csrank` | representation | -0.0536 | -8.4 | 0 | 100% | -0.072 | 471 |
| `X_z_D_realvol_ratio_20_60` | existing | -0.0536 | -8.4 | 0 | 100% | -0.072 | 471 |
| `D_realvol_ratio_20_60` | existing | -0.0536 | -8.4 | 0 | 100% | -0.072 | 471 |
| `X_rank_D_realvol_ratio_20_60` | existing | -0.0536 | -8.4 | 0 | 100% | -0.072 | 471 |

## Sign flips - works one way here, the opposite way there

HYPOTHESES, not findings: selected from many tests, so each needs its own confirmation on data not used to find it.

A feature significant with OPPOSITE signs in two regimes. An unconditional model averages these into nothing; this is exactly the information regime conditioning exists to recover.

| feature | layer | + regime | + IC | - regime | - IC |
|---|---|---|---|---|---|
| `I_rsi14__x__realvol_20` | stock | S0 | +0.0549 | S8 | -0.0277 |
| `X_rank_D_drawdown_252` | stock | S4 | +0.0520 | S2 | -0.0243 |
| `D_drawdown_252` | stock | S4 | +0.0520 | S2 | -0.0243 |
| `R_drawdown_252__csrank` | stock | S4 | +0.0520 | S2 | -0.0243 |
| `R_drawdown_252__csz` | stock | S4 | +0.0520 | S2 | -0.0243 |
| `X_z_D_drawdown_252` | stock | S4 | +0.0520 | S2 | -0.0243 |
| `D_mdi14` | market | M1 | +0.0465 | M5 | -0.0211 |
| `X_z_D_dist_from_52wh` | stock | S4 | +0.0452 | S0 | -0.0353 |
| `D_dist_from_52wh` | stock | S4 | +0.0452 | S0 | -0.0353 |
| `X_rank_D_dist_from_52wh` | stock | S4 | +0.0452 | S0 | -0.0353 |
| `I_dvol_z20__x__realvol_ratio_20_60` | stock | S6 | +0.0410 | S2 | -0.0180 |
| `I_realvol_ratio_20_60__x__pos_in_52w_range` | stock | S0 | +0.0390 | S8 | -0.0345 |
| `I_bb_pctB_20__x__adx14` | stock | S4 | +0.0313 | S1 | -0.0223 |
| `I_dvol_z20__x__ema20_angle_deg` | stock | S5 | +0.0310 | S3 | -0.0279 |
| `I_compress_state__x__dist_from_20h` | stock | S4 | +0.0295 | S8 | -0.0210 |
| `D_realvol_60` | stock | S2 | +0.0287 | S0 | -0.0171 |
| `X_rank_D_downside_dev_60` | stock | S2 | +0.0259 | S4 | -0.0259 |
| `D_downside_dev_60` | stock | S2 | +0.0259 | S4 | -0.0259 |
| `X_z_D_downside_dev_60` | stock | S2 | +0.0259 | S4 | -0.0259 |
| `D_pdi14` | stock | S8 | +0.0255 | S0 | -0.0267 |
| `M_ivol60` | stock | S2 | +0.0248 | S0 | -0.0193 |
| `D_ret_5d_roll_std` | stock | S2 | +0.0236 | S0 | -0.0189 |
| `N_volofvol20` | stock | S2 | +0.0218 | S4 | -0.0404 |

## Feature x regime matrix (top 40 by max |IC|)

`*` = working (FDR + stable + material). Blank = too few dates.

| feature | ALL | S0 | S1 | S2 | S3 | S4 | S5 | S6 | S7 | S8 | M0 | M1 | M2 | M3 | M4 | M5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `D_atr_pct_z252` | -0.074* | -0.075* | -0.066* | -0.059* | -0.072* | -0.078* | -0.064* | -0.057* | -0.081* | -0.061* | -0.099* | -0.086* | -0.090* | -0.058* | -0.075* | -0.071* |
| `D_atr_ratio_14_30` | -0.061* | -0.086* | -0.068* | -0.057* | -0.080* | -0.038* | -0.039* | -0.055* | -0.077* | -0.050* | -0.086* | -0.093* | -0.074* | -0.041* | -0.061* | -0.060* |
| `R_atr_ratio_14_30__csrank` | -0.061* | -0.086* | -0.068* | -0.057* | -0.080* | -0.038* | -0.039* | -0.055* | -0.077* | -0.050* | -0.086* | -0.093* | -0.074* | -0.041* | -0.061* | -0.060* |
| `R_atr_ratio_14_30__csz` | -0.061* | -0.086* | -0.068* | -0.057* | -0.080* | -0.038* | -0.039* | -0.055* | -0.077* | -0.050* | -0.086* | -0.093* | -0.074* | -0.041* | -0.061* | -0.060* |
| `R_atr_pct__tsz60` | -0.071* | -0.076* | -0.065* | -0.061* | -0.077* | -0.061* | -0.054* | -0.066* | -0.073* | -0.053* | -0.077* | -0.063* | -0.086* | -0.058* | -0.071* | -0.074* |
| `R_atr_ratio_14_30__d20` | -0.044* | -0.055* | -0.046* | -0.044* | -0.052* | -0.038* | -0.034* | -0.039* | -0.039* | -0.032* | -0.051* | -0.086* | -0.047* | -0.034* | -0.047* | -0.042* |
| `R_atr_pct__d20` | -0.067* | -0.077* | -0.060* | -0.064* | -0.072* | -0.070* | -0.054* | -0.050* | -0.071* | -0.050* | -0.085* | -0.065* | -0.067* | -0.058* | -0.072* | -0.068* |
| `R_atr_ratio_14_30__tsz60` | -0.045* | -0.056* | -0.049* | -0.047* | -0.057* | -0.019 | -0.032* | -0.046* | -0.046* | -0.032* | -0.061* | -0.083* | -0.050* | -0.030* | -0.044* | -0.046* |
| `X_z_D_realvol_ratio_20_60` | -0.055* | -0.065* | -0.044* | -0.044* | -0.056* | -0.036* | -0.027* | -0.046* | -0.045* | -0.044* | -0.060* | -0.076* | -0.061* | -0.048* | -0.055* | -0.054* |
| `R_realvol_ratio_20_60__csz` | -0.055* | -0.065* | -0.044* | -0.044* | -0.056* | -0.036* | -0.027* | -0.046* | -0.045* | -0.044* | -0.060* | -0.076* | -0.061* | -0.048* | -0.055* | -0.054* |
| `X_rank_D_realvol_ratio_20_60` | -0.055* | -0.065* | -0.044* | -0.044* | -0.056* | -0.036* | -0.027* | -0.046* | -0.045* | -0.044* | -0.060* | -0.076* | -0.061* | -0.048* | -0.055* | -0.054* |
| `D_realvol_ratio_20_60` | -0.055* | -0.065* | -0.044* | -0.044* | -0.056* | -0.036* | -0.027* | -0.046* | -0.045* | -0.044* | -0.060* | -0.076* | -0.061* | -0.048* | -0.055* | -0.054* |
| `R_realvol_ratio_20_60__csrank` | -0.055* | -0.065* | -0.044* | -0.044* | -0.056* | -0.036* | -0.027* | -0.046* | -0.045* | -0.044* | -0.060* | -0.076* | -0.061* | -0.048* | -0.055* | -0.054* |
| `R_realvol_20__d20` | -0.045* | -0.054* | -0.033* | -0.038* | -0.045* | -0.047* | -0.022 | -0.032* | -0.037* | -0.032* | -0.037* | -0.070* | -0.046* | -0.044* | -0.050* | -0.041* |
| `N_dist_hi10` | +0.054* | +0.048* | +0.037* | +0.017 | +0.052* | +0.063* | +0.057* | +0.040* | +0.055* | +0.033* | +0.059* | +0.024 | +0.069* | +0.035* | +0.066* | +0.059* |
| `R_realvol_20__tsz60` | -0.055* | -0.066* | -0.044* | -0.040* | -0.060* | -0.035* | -0.025* | -0.045* | -0.045* | -0.041* | -0.054* | -0.058* | -0.063* | -0.047* | -0.054* | -0.055* |
| `N_dist_hi100` | +0.015 | -0.010 | +0.000 | -0.017 | -0.012 | +0.064* | +0.027 | +0.004 | +0.010 | +0.020* | -0.021 | -0.037 | +0.015 | +0.024 | +0.019 | +0.020 |
| `X_relvol_20` | -0.047* | -0.063* | -0.028* | -0.010 | -0.054* | -0.041* | -0.015 | -0.034* | -0.043* | -0.031* | -0.030 | -0.031 | -0.060* | -0.040* | -0.049* | -0.049* |
| `R_realvol_20__csz` | -0.047* | -0.063* | -0.028* | -0.010 | -0.054* | -0.041* | -0.015 | -0.034* | -0.043* | -0.031* | -0.030 | -0.031 | -0.060* | -0.040* | -0.049* | -0.049* |
| `D_realvol_20` | -0.047* | -0.063* | -0.028* | -0.010 | -0.054* | -0.041* | -0.015 | -0.034* | -0.043* | -0.031* | -0.030 | -0.031 | -0.060* | -0.040* | -0.049* | -0.049* |
| `R_realvol_20__csrank` | -0.047* | -0.063* | -0.028* | -0.010 | -0.054* | -0.041* | -0.015 | -0.034* | -0.043* | -0.031* | -0.030 | -0.031 | -0.060* | -0.040* | -0.049* | -0.049* |
| `X_rank_D_realvol_20` | -0.047* | -0.063* | -0.028* | -0.010 | -0.054* | -0.041* | -0.015 | -0.034* | -0.043* | -0.031* | -0.030 | -0.031 | -0.060* | -0.040* | -0.049* | -0.049* |
| `X_z_D_realvol_20` | -0.047* | -0.063* | -0.028* | -0.010 | -0.054* | -0.041* | -0.015 | -0.034* | -0.043* | -0.031* | -0.030 | -0.031 | -0.060* | -0.040* | -0.049* | -0.049* |
| `N_dist_hi50` | +0.023* | +0.004 | +0.003 | -0.015 | -0.002 | +0.062* | +0.034 | +0.006 | +0.020 | +0.024* | +0.004 | -0.040 | +0.024* | +0.028 | +0.031 | +0.027* |
| `D_vol_yz_20` | -0.045* | -0.052* | -0.032* | -0.014 | -0.048* | -0.036* | -0.016 | -0.030* | -0.047* | -0.031* | -0.017 | -0.051 | -0.060* | -0.036* | -0.044* | -0.047* |
| `D_bb_pctB_20` | +0.023* | +0.006 | +0.013 | +0.014 | +0.009 | +0.047* | +0.058* | +0.015 | +0.021* | +0.036* | +0.024 | -0.010 | +0.025* | +0.015 | +0.032* | +0.029* |
| `X_z_D_bb_pctB_20` | +0.023* | +0.006 | +0.013 | +0.014 | +0.009 | +0.047* | +0.058* | +0.015 | +0.021* | +0.036* | +0.024 | -0.010 | +0.025* | +0.015 | +0.032* | +0.029* |
| `R_bb_pctB_20__csz` | +0.023* | +0.006 | +0.013 | +0.014 | +0.009 | +0.047* | +0.058* | +0.015 | +0.021* | +0.036* | +0.024 | -0.010 | +0.025* | +0.015 | +0.032* | +0.029* |
| `R_bb_pctB_20__csrank` | +0.023* | +0.006 | +0.013 | +0.014 | +0.009 | +0.047* | +0.058* | +0.015 | +0.021* | +0.036* | +0.024 | -0.010 | +0.025* | +0.015 | +0.032* | +0.029* |
| `X_rank_D_bb_pctB_20` | +0.023* | +0.006 | +0.013 | +0.014 | +0.009 | +0.047* | +0.058* | +0.015 | +0.021* | +0.036* | +0.024 | -0.010 | +0.025* | +0.015 | +0.032* | +0.029* |
| `N_min_ret20` | +0.045* | +0.057* | +0.019* | -0.001 | +0.056* | +0.039* | +0.025* | +0.029* | +0.035* | +0.031* | +0.041* | +0.010 | +0.052* | +0.042* | +0.047* | +0.048* |
| `R_atr_pct__csrank` | -0.040* | -0.040* | -0.022* | -0.008 | -0.040* | -0.047* | -0.018 | -0.023* | -0.046* | -0.035* | -0.016 | -0.026 | -0.057* | -0.030* | -0.044* | -0.042* |
| `D_atr_pct` | -0.040* | -0.040* | -0.022* | -0.008 | -0.040* | -0.047* | -0.018 | -0.023* | -0.046* | -0.035* | -0.016 | -0.026 | -0.057* | -0.030* | -0.044* | -0.042* |
| `X_rank_D_atr_pct` | -0.040* | -0.040* | -0.022* | -0.008 | -0.040* | -0.047* | -0.018 | -0.023* | -0.046* | -0.035* | -0.016 | -0.026 | -0.057* | -0.030* | -0.044* | -0.042* |
| `R_atr_pct__csz` | -0.040* | -0.040* | -0.022* | -0.008 | -0.040* | -0.047* | -0.018 | -0.023* | -0.046* | -0.035* | -0.016 | -0.026 | -0.057* | -0.030* | -0.044* | -0.042* |
| `X_z_D_atr_pct` | -0.040* | -0.040* | -0.022* | -0.008 | -0.040* | -0.047* | -0.018 | -0.023* | -0.046* | -0.035* | -0.016 | -0.026 | -0.057* | -0.030* | -0.044* | -0.042* |
| `D_donch_pos_50` | +0.008 | -0.012 | -0.005 | -0.011 | -0.009 | +0.055* | +0.026 | +0.005 | +0.006 | +0.019* | +0.000 | -0.044 | +0.002 | +0.012 | +0.017 | +0.015 |
| `R_bb_bw_20__csz` | -0.039* | -0.045* | -0.033* | -0.009 | -0.040* | -0.022 | -0.027* | -0.026* | -0.036* | -0.033* | -0.032 | -0.003 | -0.055* | -0.025* | -0.042* | -0.045* |
| `R_bb_bw_20__csrank` | -0.039* | -0.045* | -0.033* | -0.009 | -0.040* | -0.022 | -0.027* | -0.026* | -0.036* | -0.033* | -0.032 | -0.003 | -0.055* | -0.025* | -0.042* | -0.045* |
| `D_bb_bw_20` | -0.039* | -0.045* | -0.033* | -0.009 | -0.040* | -0.022 | -0.027* | -0.026* | -0.036* | -0.033* | -0.032 | -0.003 | -0.055* | -0.025* | -0.042* | -0.045* |

## Caveats

- Exploratory. A working cell is evidence to test, not a validated edge.
- About 5% of working cells are expected to be false discoveries by construction of the FDR bar.
- IC is cross-sectional ranking skill. It is not a return, and it ignores costs; `top-bot hit` is the hit-rate gap between the top and bottom quintile within the regime.
- Regime IDs are aligned across folds by centroid matching; check the drift figures before trusting a regime's identity over time.
- In-sample regime labels (before the first test window) never enter the statistics.