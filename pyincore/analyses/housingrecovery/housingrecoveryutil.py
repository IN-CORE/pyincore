# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

class HousingRecoveryUtil:
    # The models here are as they were originally in Hamideh et al.(2018)

    # Urban Core (GUC) model coefficients
    B_GUC_intercept = 11.122470

    # Year indicator dummies
    B_GUC_year = {}
    B_GUC_year[-1] = 0.000000 # 2008 tax assessment year
    B_GUC_year[0] = 0.159436  # 2009 tax assessment year
    B_GUC_year[1] = 0.041048  # 2010 tax assessment year
    B_GUC_year[2] = -0.005587 # 2011 tax assessment year
    B_GUC_year[3] = 0.032986  # 2012 tax assessment year
    B_GUC_year[4] = 0.027376  # 2013 tax assessment year
    B_GUC_year[5] = 0.044295  # 2014 tax assessment year
    B_GUC_year[6] = 0.244297  # 2015 tax assessment year

    # House Characteristics
    B_GUC_age = -0.020186
    B_GUC_sqm = 0.005287

    # Damage and year dummy interactions
    B_GUC_dmg_year = {}
    B_GUC_dmg_year[-1] = 0.000000
    B_GUC_dmg_year[0] = -0.032428  # base effect
    B_GUC_dmg_year[1] = 0.010592 + B_GUC_dmg_year[0]
    B_GUC_dmg_year[2] = 0.011031 + B_GUC_dmg_year[0]
    B_GUC_dmg_year[3] = 0.012701 + B_GUC_dmg_year[0]
    B_GUC_dmg_year[4] = 0.013632 + B_GUC_dmg_year[0]
    B_GUC_dmg_year[5] = 0.014702 + B_GUC_dmg_year[0]
    B_GUC_dmg_year[6] = 0.014662 + B_GUC_dmg_year[0]

    # Owner-occupied and year dummy interactions
    B_GUC_own_year = {}
    B_GUC_own_year[-1] = 0.136650  # base effect
    B_GUC_own_year[0] = 0.067860 + B_GUC_own_year[-1]
    B_GUC_own_year[1] = 0.108552 + B_GUC_own_year[-1]
    B_GUC_own_year[2] = 0.134914 + B_GUC_own_year[-1]
    B_GUC_own_year[3] = 0.150882 + B_GUC_own_year[-1]
    B_GUC_own_year[4] = 0.167397 + B_GUC_own_year[-1]
    B_GUC_own_year[5] = 0.188566 + B_GUC_own_year[-1]
    B_GUC_own_year[6] = 0.174687 + B_GUC_own_year[-1]

    # Median household income and year dummy interactions
    B_GUC_inc_year = {}
    B_GUC_inc_year[-1] = 0.002524  # base effect
    B_GUC_inc_year[0] = 0.003436 + B_GUC_inc_year[-1]
    B_GUC_inc_year[1] = 0.004832 + B_GUC_inc_year[-1]
    B_GUC_inc_year[2] = 0.005796 + B_GUC_inc_year[-1]
    B_GUC_inc_year[3] = 0.005063 + B_GUC_inc_year[-1]
    B_GUC_inc_year[4] = 0.005003 + B_GUC_inc_year[-1]
    B_GUC_inc_year[5] = 0.005244 + B_GUC_inc_year[-1]
    B_GUC_inc_year[6] = 0.004602 + B_GUC_inc_year[-1]

    # Block Group percent Hispanic and year dummy interactions
    B_GUC_his_year = {}
    B_GUC_his_year[-1] = -0.004388  # base effect
    B_GUC_his_year[0] = 0.002976 + B_GUC_his_year[-1]
    B_GUC_his_year[1] = 0.003595 + B_GUC_his_year[-1]
    B_GUC_his_year[2] = 0.003777 + B_GUC_his_year[-1]
    B_GUC_his_year[3] = 0.003150 + B_GUC_his_year[-1]
    B_GUC_his_year[4] = 0.003479 + B_GUC_his_year[-1]
    B_GUC_his_year[5] = 0.003072 + B_GUC_his_year[-1]
    B_GUC_his_year[6] = 0.003074 + B_GUC_his_year[-1]

    # Block Group percent non-Hispanic Black and year dummy interactions
    B_GUC_blk_year = {}
    B_GUC_blk_year[-1] = -0.006032  # base effect
    B_GUC_blk_year[0] = 0.006244 + B_GUC_blk_year[-1]
    B_GUC_blk_year[1] = 0.007769 + B_GUC_blk_year[-1]
    B_GUC_blk_year[2] = 0.007629 + B_GUC_blk_year[-1]
    B_GUC_blk_year[3] = 0.005728 + B_GUC_blk_year[-1]
    B_GUC_blk_year[4] = 0.005227 + B_GUC_blk_year[-1]
    B_GUC_blk_year[5] = 0.004501 + B_GUC_blk_year[-1]
    B_GUC_blk_year[6] = 0.004186 + B_GUC_blk_year[-1]

    # Galveston Island Vacation (GIV) model coefficients
    B_GIV_intercept = 11.418632

    # Year indicator dummies
    B_GIV_year = {}
    B_GIV_year[-1] = 0.000000  # 2008 tax assessment year
    B_GIV_year[0] = 0.940114  # 2009 tax assessment year
    B_GIV_year[1] = 1.149180  # 2010 tax assessment year
    B_GIV_year[2] = 1.377877  # 2011 tax assessment year
    B_GIV_year[3] = 1.376843  # 2012 tax assessment year
    B_GIV_year[4] = 1.584727  # 2013 tax assessment year
    B_GIV_year[5] = 1.629853  # 2014 tax assessment year
    B_GIV_year[6] = 1.810897  # 2015 tax assessment year

    # House Characteristics
    B_GIV_age = -0.018019
    B_GIV_sqm = 0.005397

    # Damage and year dummy interactions
    B_GIV_dmg_year = {}
    B_GIV_dmg_year[-1] = 0.000000
    B_GIV_dmg_year[0] = -0.057289  # base effect
    B_GIV_dmg_year[1] = -0.000739 + B_GIV_dmg_year[0]
    B_GIV_dmg_year[2] = -0.005998 + B_GIV_dmg_year[0]
    B_GIV_dmg_year[3] = -0.005508 + B_GIV_dmg_year[0]
    B_GIV_dmg_year[4] = -0.002321 + B_GIV_dmg_year[0]
    B_GIV_dmg_year[5] = -0.002999 + B_GIV_dmg_year[0]
    B_GIV_dmg_year[6] = -0.002789 + B_GIV_dmg_year[0]

    # Owner-occupied and year dummy interactions
    B_GIV_own_year = {}
    B_GIV_own_year[-1] = -0.069173  # base effect
    B_GIV_own_year[0] = 0.113631 + B_GIV_own_year[-1]
    B_GIV_own_year[1] = 0.070640 + B_GIV_own_year[-1]
    B_GIV_own_year[2] = 0.141091 + B_GIV_own_year[-1]
    B_GIV_own_year[3] = 0.085612 + B_GIV_own_year[-1]
    B_GIV_own_year[4] = 0.082388 + B_GIV_own_year[-1]
    B_GIV_own_year[5] = 0.101504 + B_GIV_own_year[-1]
    B_GIV_own_year[6] = 0.100316 + B_GIV_own_year[-1]

    # Median household income and year dummy interactions
    B_GIV_inc_year = {}
    B_GIV_inc_year[-1] = -0.000441  # base effect
    B_GIV_inc_year[0] = -0.005350 + B_GIV_inc_year[-1]
    B_GIV_inc_year[1] = -0.007168 + B_GIV_inc_year[-1]
    B_GIV_inc_year[2] = -0.009839 + B_GIV_inc_year[-1]
    B_GIV_inc_year[3] = -0.008677 + B_GIV_inc_year[-1]
    B_GIV_inc_year[4] = -0.011600 + B_GIV_inc_year[-1]
    B_GIV_inc_year[5] = -0.011268 + B_GIV_inc_year[-1]
    B_GIV_inc_year[6] = -0.010935 + B_GIV_inc_year[-1]

    # Block Group percent Hispanic and year dummy interactions
    B_GIV_his_year = {}
    B_GIV_his_year[-1] = 0.000605  # base effect
    B_GIV_his_year[0] = 0.033432 + B_GIV_his_year[-1]
    B_GIV_his_year[1] = 0.050704 + B_GIV_his_year[-1]
    B_GIV_his_year[2] = 0.051041 + B_GIV_his_year[-1]
    B_GIV_his_year[3] = 0.050761 + B_GIV_his_year[-1]
    B_GIV_his_year[4] = 0.044682 + B_GIV_his_year[-1]
    B_GIV_his_year[5] = 0.046444 + B_GIV_his_year[-1]
    B_GIV_his_year[6] = 0.043717 + B_GIV_his_year[-1]

    # Block Group percent non-Hispanic Black and year dummy interactions
    B_GIV_blk_year = {}
    B_GIV_blk_year[-1] = -0.011487  # base effect
    B_GIV_blk_year[0] = -0.022091 + B_GIV_blk_year[-1]
    B_GIV_blk_year[1] = -0.030755 + B_GIV_blk_year[-1]
    B_GIV_blk_year[2] = -0.032295 + B_GIV_blk_year[-1]
    B_GIV_blk_year[3] = -0.035537 + B_GIV_blk_year[-1]
    B_GIV_blk_year[4] = -0.034764 + B_GIV_blk_year[-1]
    B_GIV_blk_year[5] = -0.036632 + B_GIV_blk_year[-1]
    B_GIV_blk_year[6] = -0.037520 + B_GIV_blk_year[-1]

    # Bolivar Island Vacation (BIV) model coefficients
    B_BIV_intercept = 13.294258

    # Year indicator, year dummy variable
    B_BIV_year = {}
    B_BIV_year[-1] = 0.000000  # 2008 tax assessment year
    B_BIV_year[0] = 10.215025  # 2009 tax assessment year
    B_BIV_year[1] = 13.727035  # 2010 tax assessment year
    B_BIV_year[2] = 17.919863  # 2011 tax assessment year
    B_BIV_year[3] = 20.984438  # 2012 tax assessment year
    B_BIV_year[4] = 23.861400  # 2013 tax assessment year
    B_BIV_year[5] = 24.704598  # 2014 tax assessment year
    B_BIV_year[6] = 25.790369  # 2015 tax assessment year

    # House Characteristics
    B_BIV_age = -0.052518
    B_BIV_sqm = 0.005306

    # Damage and year dummy interactions
    B_BIV_dmg_year = {}
    B_BIV_dmg_year[-1] = 0.000000
    B_BIV_dmg_year[0] = -0.123153  # base effect
    B_BIV_dmg_year[1] = 0.006965 + B_BIV_dmg_year[0]
    B_BIV_dmg_year[2] = 0.019198 + B_BIV_dmg_year[0]
    B_BIV_dmg_year[3] = 0.026882 + B_BIV_dmg_year[0]
    B_BIV_dmg_year[4] = 0.033723 + B_BIV_dmg_year[0]
    B_BIV_dmg_year[5] = 0.037554 + B_BIV_dmg_year[0]
    B_BIV_dmg_year[6] = 0.041385 + B_BIV_dmg_year[0]

    # Owner-occupied and year dummy interactions
    B_BIV_own_year = {}
    B_BIV_own_year[-1] = 0.078294  # base effect
    B_BIV_own_year[0] = 0.069819 + B_BIV_own_year[-1]
    B_BIV_own_year[1] = 0.021936 + B_BIV_own_year[-1]
    B_BIV_own_year[2] = -0.030344 + B_BIV_own_year[-1]
    B_BIV_own_year[3] = 0.273516 + B_BIV_own_year[-1]
    B_BIV_own_year[4] = 0.244671 + B_BIV_own_year[-1]
    B_BIV_own_year[5] = 0.369090 + B_BIV_own_year[-1]
    B_BIV_own_year[6] = 0.353242 + B_BIV_own_year[-1]

    # Median household income and year dummy interactions
    B_BIV_inc_year = {}
    B_BIV_inc_year[-1] = -0.049252  # base effect
    B_BIV_inc_year[0] = -0.250567 + B_BIV_inc_year[-1]
    B_BIV_inc_year[1] = -0.353807 + B_BIV_inc_year[-1]
    B_BIV_inc_year[2] = -0.476699 + B_BIV_inc_year[-1]
    B_BIV_inc_year[3] = -0.566724 + B_BIV_inc_year[-1]
    B_BIV_inc_year[4] = -0.651935 + B_BIV_inc_year[-1]
    B_BIV_inc_year[5] = -0.676623 + B_BIV_inc_year[-1]
    B_BIV_inc_year[6] = -0.704993 + B_BIV_inc_year[-1]

    # Block Group percent Hispanic and year dummy interactions
    B_BIV_his_year = {}
    B_BIV_his_year[-1] = -0.008111  # base effect
    B_BIV_his_year[0] = 0.041060 + B_BIV_his_year[-1]
    B_BIV_his_year[1] = 0.015282 + B_BIV_his_year[-1]
    B_BIV_his_year[2] = -0.015872 + B_BIV_his_year[-1]
    B_BIV_his_year[3] = -0.038443 + B_BIV_his_year[-1]
    B_BIV_his_year[4] = -0.054903 + B_BIV_his_year[-1]
    B_BIV_his_year[5] = -0.065536 + B_BIV_his_year[-1]
    B_BIV_his_year[6] = -0.070076 + B_BIV_his_year[-1]

    # Block Group percent non-Hispanic Black and year dummy interactions
    B_BIV_blk_year = {}
    B_BIV_blk_year[-1] = 0.000000  # base effect
    B_BIV_blk_year[0] = 0.000000 + B_BIV_blk_year[-1]
    B_BIV_blk_year[1] = 0.000000 + B_BIV_blk_year[-1]
    B_BIV_blk_year[2] = 0.000000 + B_BIV_blk_year[-1]
    B_BIV_blk_year[3] = 0.000000 + B_BIV_blk_year[-1]
    B_BIV_blk_year[4] = 0.000000 + B_BIV_blk_year[-1]
    B_BIV_blk_year[5] = 0.000000 + B_BIV_blk_year[-1]
    B_BIV_blk_year[6] = 0.000000 + B_BIV_blk_year[-1]

    # Chained analysis
    # The models presented in this section are based on models developed in Hamideh et al. (2018).
    # The modifications from the original models include (1) combining non-Hispanic Black
    # and Hispanic block group percentages into a minority block group percentage variable,
    # and (2) having both parcel and block group level intercepts. The original model only had parcel level
    # intercepts. Considering that multiple levels of data are used (parcel and block group), it is appropriate
    # to have both levels of intercepts.

    # Primary housing market (PHM) model coefficients
    B_PHM_intercept = 11.407594

    # Year indicator dummy variables
    B_PHM_year = {}
    B_PHM_year[-1] =  0.000000  # year -1, tax assessment immediately before disaster
    B_PHM_year[0]  =  0.263500  # year  0, tax assessment immediately after disaster, damage year
    B_PHM_year[1]  =  0.147208  # year +1
    B_PHM_year[2]  =  0.110004  # year +2
    B_PHM_year[3]  =  0.122228  # year +3
    B_PHM_year[4]  =  0.102886  # year +4
    B_PHM_year[5]  =  0.102806  # year +5
    B_PHM_year[6]  =  0.276548  # year +6

    # House Characteristics
    B_PHM_age = -0.030273
    B_PHM_sqm =  0.005596

    # Damage and year dummy interactions
    B_PHM_dmg_year = {}
    B_PHM_dmg_year[-1] =  0.000000
    B_PHM_dmg_year[0]  = -0.037458 # base effect
    B_PHM_dmg_year[1]  =  0.009310 + B_PHM_dmg_year[0]
    B_PHM_dmg_year[2]  =  0.009074 + B_PHM_dmg_year[0]
    B_PHM_dmg_year[3]  =  0.010340 + B_PHM_dmg_year[0]
    B_PHM_dmg_year[4]  =  0.011293 + B_PHM_dmg_year[0]
    B_PHM_dmg_year[5]  =  0.012178 + B_PHM_dmg_year[0]
    B_PHM_dmg_year[6]  =  0.012188 + B_PHM_dmg_year[0]

    # Owner-occupied and year dummy interactions
    B_PHM_own_year = {}
    B_PHM_own_year[-1] = 0.017153   # base effect
    B_PHM_own_year[0]  = 0.129077 + B_PHM_own_year[-1]
    B_PHM_own_year[1]  = 0.188217 + B_PHM_own_year[-1]
    B_PHM_own_year[2]  = 0.235435 + B_PHM_own_year[-1]
    B_PHM_own_year[3]  = 0.246437 + B_PHM_own_year[-1]
    B_PHM_own_year[4]  = 0.261220 + B_PHM_own_year[-1]
    B_PHM_own_year[5]  = 0.281015 + B_PHM_own_year[-1]
    B_PHM_own_year[6]  = 0.265465 + B_PHM_own_year[-1]

    # Median household income and year dummy interactions
    B_PHM_inc_year = {}
    B_PHM_inc_year[-1] = 0.002724   # base effect
    B_PHM_inc_year[0]  = 0.001190 + B_PHM_inc_year[-1]
    B_PHM_inc_year[1]  = 0.001480 + B_PHM_inc_year[-1]
    B_PHM_inc_year[2]  = 0.001746 + B_PHM_inc_year[-1]
    B_PHM_inc_year[3]  = 0.001494 + B_PHM_inc_year[-1]
    B_PHM_inc_year[4]  = 0.001480 + B_PHM_inc_year[-1]
    B_PHM_inc_year[5]  = 0.001849 + B_PHM_inc_year[-1]
    B_PHM_inc_year[6]  = 0.001400 + B_PHM_inc_year[-1]

    # Block Group percent Minority and year dummy interactions
    B_PHM_min_year = {}
    B_PHM_min_year[-1] = -0.004783   # base effect
    B_PHM_min_year[0]  =  0.005609 + B_PHM_min_year[-1]
    B_PHM_min_year[1]  =  0.007343 + B_PHM_min_year[-1]
    B_PHM_min_year[2]  =  0.007459 + B_PHM_min_year[-1]
    B_PHM_min_year[3]  =  0.006421 + B_PHM_min_year[-1]
    B_PHM_min_year[4]  =  0.006308 + B_PHM_min_year[-1]
    B_PHM_min_year[5]  =  0.005770 + B_PHM_min_year[-1]
    B_PHM_min_year[6]  =  0.005620 + B_PHM_min_year[-1]

    # Seasonal/Vacation Housing Market (SVHM) model coefficients
    B_SVHM_intercept = 11.125636

    # Year indicator dummy variables
    B_SVHM_year =  {}
    B_SVHM_year[-1] =  0.000000  # year -1, tax assessment immediately before disaster
    B_SVHM_year[0]  =  1.489008  # year  0, tax assessment immediately after disaster, damage year
    B_SVHM_year[1]  =  1.858770  # year +1
    B_SVHM_year[2]  =  2.163492  # year +2
    B_SVHM_year[3]  =  2.071690  # year +3
    B_SVHM_year[4]  =  2.110245  # year +4
    B_SVHM_year[5]  =  2.208577  # year +5
    B_SVHM_year[6]  =  2.273867  # year +6

    # House Characteristics
    B_SVHM_age = -0.014260
    B_SVHM_sqm =  0.005505

    # Damage and year dummy interactions
    B_SVHM_dmg_year = {}
    B_SVHM_dmg_year[-1] =  0.000000
    B_SVHM_dmg_year[0]  = -0.051913 # base effect
    B_SVHM_dmg_year[1]  =  0.001504 + B_SVHM_dmg_year[0]
    B_SVHM_dmg_year[2]  = -0.004172 + B_SVHM_dmg_year[0]
    B_SVHM_dmg_year[3]  = -0.002016 + B_SVHM_dmg_year[0]
    B_SVHM_dmg_year[4]  =  0.001687 + B_SVHM_dmg_year[0]
    B_SVHM_dmg_year[5]  =  0.000876 + B_SVHM_dmg_year[0]
    B_SVHM_dmg_year[6]  =  0.001129 + B_SVHM_dmg_year[0]

    # Owner-occupied and year dummy interactions
    B_SVHM_own_year = {}
    B_SVHM_own_year[-1] = -0.017167   # base effect
    B_SVHM_own_year[0]  =  0.043263 + B_SVHM_own_year[-1]
    B_SVHM_own_year[1]  =  0.003315 + B_SVHM_own_year[-1]
    B_SVHM_own_year[2]  =  0.034372 + B_SVHM_own_year[-1]
    B_SVHM_own_year[3]  = -0.014929 + B_SVHM_own_year[-1]
    B_SVHM_own_year[4]  = -0.021078 + B_SVHM_own_year[-1]
    B_SVHM_own_year[5]  =  0.001161 + B_SVHM_own_year[-1]
    B_SVHM_own_year[6]  =  0.017562 + B_SVHM_own_year[-1]

    # Median household income and year dummy interactions
    B_SVHM_inc_year = {}
    B_SVHM_inc_year[-1] =  0.003786   # base effect
    B_SVHM_inc_year[0]  = -0.013662 + B_SVHM_inc_year[-1]
    B_SVHM_inc_year[1]  = -0.017401 + B_SVHM_inc_year[-1]
    B_SVHM_inc_year[2]  = -0.021541 + B_SVHM_inc_year[-1]
    B_SVHM_inc_year[3]  = -0.019756 + B_SVHM_inc_year[-1]
    B_SVHM_inc_year[4]  = -0.020789 + B_SVHM_inc_year[-1]
    B_SVHM_inc_year[5]  = -0.021555 + B_SVHM_inc_year[-1]
    B_SVHM_inc_year[6]  = -0.019781 + B_SVHM_inc_year[-1]
