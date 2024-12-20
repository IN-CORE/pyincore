# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


class HousingValuationRecoveryUtil:
    BASEYEAR = 2008

    DMG_YEARS = [-1, 0, 1, 2, 3, 4, 5, 6]

    # The models presented in this section are based on models developed in Hamideh et al. (2018).
    # The modifications from the original Galveston models include (1) combining non-Hispanic Black
    # and Hispanic block group percentages into a minority block group percentage variable,
    # and (2) having both parcel and block group level intercepts. The original model only had parcel level
    # intercepts. Considering that multiple levels of data are used (parcel and block group), it is appropriate
    # to have both levels of intercepts.

    # Primary housing market (PHM) model coefficients
    B_PHM_intercept = 11.407594

    # Year indicator dummy variables
    B_PHM_year = {}
    B_PHM_year[-1] = 0.000000  # year -1, tax assessment immediately before disaster
    B_PHM_year[
        0
    ] = 0.263500  # year  0, tax assessment immediately after disaster, damage year
    B_PHM_year[1] = 0.147208  # year +1
    B_PHM_year[2] = 0.110004  # year +2
    B_PHM_year[3] = 0.122228  # year +3
    B_PHM_year[4] = 0.102886  # year +4
    B_PHM_year[5] = 0.102806  # year +5
    B_PHM_year[6] = 0.276548  # year +6

    # House Characteristics
    B_PHM_age = -0.030273
    B_PHM_sqm = 0.005596

    # Damage and year dummy interactions
    B_PHM_dmg_year = {}
    B_PHM_dmg_year[-1] = 0.000000
    B_PHM_dmg_year[0] = -0.037458  # base effect
    B_PHM_dmg_year[1] = 0.009310 + B_PHM_dmg_year[0]
    B_PHM_dmg_year[2] = 0.009074 + B_PHM_dmg_year[0]
    B_PHM_dmg_year[3] = 0.010340 + B_PHM_dmg_year[0]
    B_PHM_dmg_year[4] = 0.011293 + B_PHM_dmg_year[0]
    B_PHM_dmg_year[5] = 0.012178 + B_PHM_dmg_year[0]
    B_PHM_dmg_year[6] = 0.012188 + B_PHM_dmg_year[0]

    # Owner-occupied and year dummy interactions
    B_PHM_own_year = {}
    B_PHM_own_year[-1] = 0.017153  # base effect
    B_PHM_own_year[0] = 0.129077 + B_PHM_own_year[-1]
    B_PHM_own_year[1] = 0.188217 + B_PHM_own_year[-1]
    B_PHM_own_year[2] = 0.235435 + B_PHM_own_year[-1]
    B_PHM_own_year[3] = 0.246437 + B_PHM_own_year[-1]
    B_PHM_own_year[4] = 0.261220 + B_PHM_own_year[-1]
    B_PHM_own_year[5] = 0.281015 + B_PHM_own_year[-1]
    B_PHM_own_year[6] = 0.265465 + B_PHM_own_year[-1]

    # Median household income and year dummy interactions
    B_PHM_inc_year = {}
    B_PHM_inc_year[-1] = 0.002724  # base effect
    B_PHM_inc_year[0] = 0.001190 + B_PHM_inc_year[-1]
    B_PHM_inc_year[1] = 0.001480 + B_PHM_inc_year[-1]
    B_PHM_inc_year[2] = 0.001746 + B_PHM_inc_year[-1]
    B_PHM_inc_year[3] = 0.001494 + B_PHM_inc_year[-1]
    B_PHM_inc_year[4] = 0.001480 + B_PHM_inc_year[-1]
    B_PHM_inc_year[5] = 0.001849 + B_PHM_inc_year[-1]
    B_PHM_inc_year[6] = 0.001400 + B_PHM_inc_year[-1]

    # Block Group percent Minority and year dummy interactions
    B_PHM_min_year = {}
    B_PHM_min_year[-1] = -0.004783  # base effect
    B_PHM_min_year[0] = 0.005609 + B_PHM_min_year[-1]
    B_PHM_min_year[1] = 0.007343 + B_PHM_min_year[-1]
    B_PHM_min_year[2] = 0.007459 + B_PHM_min_year[-1]
    B_PHM_min_year[3] = 0.006421 + B_PHM_min_year[-1]
    B_PHM_min_year[4] = 0.006308 + B_PHM_min_year[-1]
    B_PHM_min_year[5] = 0.005770 + B_PHM_min_year[-1]
    B_PHM_min_year[6] = 0.005620 + B_PHM_min_year[-1]

    # Seasonal/Vacation Housing Market (SVHM) model coefficients
    B_SVHM_intercept = 11.125636

    # Year indicator dummy variables
    B_SVHM_year = {}
    B_SVHM_year[-1] = 0.000000  # year -1, tax assessment immediately before disaster
    B_SVHM_year[
        0
    ] = 1.489008  # year  0, tax assessment immediately after disaster, damage year
    B_SVHM_year[1] = 1.858770  # year +1
    B_SVHM_year[2] = 2.163492  # year +2
    B_SVHM_year[3] = 2.071690  # year +3
    B_SVHM_year[4] = 2.110245  # year +4
    B_SVHM_year[5] = 2.208577  # year +5
    B_SVHM_year[6] = 2.273867  # year +6

    # House Characteristics
    B_SVHM_age = -0.014260
    B_SVHM_sqm = 0.005505

    # Damage and year dummy interactions
    B_SVHM_dmg_year = {}
    B_SVHM_dmg_year[-1] = 0.000000
    B_SVHM_dmg_year[0] = -0.051913  # base effect
    B_SVHM_dmg_year[1] = 0.001504 + B_SVHM_dmg_year[0]
    B_SVHM_dmg_year[2] = -0.004172 + B_SVHM_dmg_year[0]
    B_SVHM_dmg_year[3] = -0.002016 + B_SVHM_dmg_year[0]
    B_SVHM_dmg_year[4] = 0.001687 + B_SVHM_dmg_year[0]
    B_SVHM_dmg_year[5] = 0.000876 + B_SVHM_dmg_year[0]
    B_SVHM_dmg_year[6] = 0.001129 + B_SVHM_dmg_year[0]

    # Owner-occupied and year dummy interactions
    B_SVHM_own_year = {}
    B_SVHM_own_year[-1] = -0.017167  # base effect
    B_SVHM_own_year[0] = 0.043263 + B_SVHM_own_year[-1]
    B_SVHM_own_year[1] = 0.003315 + B_SVHM_own_year[-1]
    B_SVHM_own_year[2] = 0.034372 + B_SVHM_own_year[-1]
    B_SVHM_own_year[3] = -0.014929 + B_SVHM_own_year[-1]
    B_SVHM_own_year[4] = -0.021078 + B_SVHM_own_year[-1]
    B_SVHM_own_year[5] = 0.001161 + B_SVHM_own_year[-1]
    B_SVHM_own_year[6] = 0.017562 + B_SVHM_own_year[-1]

    # Median household income and year dummy interactions
    B_SVHM_inc_year = {}
    B_SVHM_inc_year[-1] = 0.003786  # base effect
    B_SVHM_inc_year[0] = -0.013662 + B_SVHM_inc_year[-1]
    B_SVHM_inc_year[1] = -0.017401 + B_SVHM_inc_year[-1]
    B_SVHM_inc_year[2] = -0.021541 + B_SVHM_inc_year[-1]
    B_SVHM_inc_year[3] = -0.019756 + B_SVHM_inc_year[-1]
    B_SVHM_inc_year[4] = -0.020789 + B_SVHM_inc_year[-1]
    B_SVHM_inc_year[5] = -0.021555 + B_SVHM_inc_year[-1]
    B_SVHM_inc_year[6] = -0.019781 + B_SVHM_inc_year[-1]
