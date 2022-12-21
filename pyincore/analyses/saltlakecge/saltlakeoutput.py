# Copyright (c) 2021 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
import pandas as pd


def gams_to_dataframes(iNum, variables, H, L, soln):
    # CG0
    CG0 = variables.get('CG', x=soln[0])

    # CH0
    CH0 = variables.get('CH', x=soln[0])

    # CMI0
    CMI0 = variables.get('CMI', x=soln[0])

    # CMO0
    CMO0 = variables.get('CMO', x=soln[0])

    # CN0
    CN0 = variables.get('CN', x=soln[0])

    # CPI0
    CPI0 = variables.get('CPI', x=soln[0])

    # CX0
    CX0 = variables.get('CX', x=soln[0])

    # D0
    D0 = variables.get('D', x=soln[0])

    # DD0
    DD0 = variables.get('DD', x=soln[0])

    # DS0
    DS0 = variables.get('DS', x=soln[0])

    # FD
    FD0 = variables.get('FD', x=soln[0])

    # IGT
    IGT0 = variables.get('IGT', x=soln[0])

    # KS
    KS0 = variables.get('KS', x=soln[0])

    # LAS
    # LAS0 = variables.get('LAS', x=soln[0])

    # HH
    HH0 = variables.get('HH', x=soln[0])

    # HN
    HN0 = variables.get('HN', x=soln[0])

    # HW
    HW0 = variables.get('HW', x=soln[0])

    # M
    M0 = variables.get('M', x=soln[0])

    # N
    N0 = variables.get('N', x=soln[0])

    # NKI
    NKI0 = variables.get('NKI', x=soln[0])

    # LNFOR
    # LNFOR0 = variables.get('LNFOR', x=soln[0])

    # KPFOR
    KPFOR0 = variables.get('KPFOR', x=soln[0])

    # GVFOR
    GVFOR0 = variables.get('GVFOR', x=soln[0])

    # P
    P0 = variables.get('P', x=soln[0])

    # PD
    PD0 = variables.get('PD', x=soln[0])

    # PVA
    PVA0 = variables.get('PVA', x=soln[0])

    # RA
    RA0 = variables.get('RA', x=soln[0])

    # R
    R0 = variables.get('R', x=soln[0])

    # S
    S0 = variables.get('S', x=soln[0])

    # SPI
    SPI0 = variables.get('SPI', x=soln[0])

    # V
    V0 = variables.get('V', x=soln[0])

    # Y
    Y0 = variables.get('Y', x=soln[0])

    # Yd
    YD0 = variables.get('YD', x=soln[0])

    for i in range(iNum):
        CGL = variables.get('CG', x=soln[i + 1])
        CHL = variables.get('CH', x=soln[i + 1])
        CMIL = variables.get('CMI', x=soln[i + 1])
        CMOL = variables.get('CMO', x=soln[i + 1])
        CNL = variables.get('CN', x=soln[i + 1])
        CPIL = variables.get('CPI', x=soln[i + 1])
        CXL = variables.get('CX', x=soln[i + 1])
        DL = variables.get('D', x=soln[i + 1])
        DDL = variables.get('DD', x=soln[i + 1])
        DSL = variables.get('DS', x=soln[i + 1])
        FDL = variables.get('FD', x=soln[i + 1])
        IGTL = variables.get('IGT', x=soln[i + 1])
        KSL = variables.get('KS', x=soln[i + 1])
        # LASL = variables.get('LAS', x=soln[i+1])
        HHL = variables.get('HH', x=soln[i + 1])
        HNL = variables.get('HN', x=soln[i + 1])
        HWL = variables.get('HW', x=soln[i + 1])
        ML = variables.get('M', x=soln[i + 1])
        NL = variables.get('N', x=soln[i + 1])
        NKIL = variables.get('NKI', x=soln[i + 1])
        # LNFORL = variables.get('LNFOR', x=soln[i+1])
        KPFORL = variables.get('KPFOR', x=soln[i + 1])
        GVFORL = variables.get('GVFOR', x=soln[i + 1])
        PL = variables.get('P', x=soln[i + 1])
        PDL = variables.get('PD', x=soln[i + 1])
        PVAL = variables.get('PVA', x=soln[i + 1])
        RAL = variables.get('RA', x=soln[i + 1])
        RL = variables.get('R', x=soln[i + 1])
        SL = variables.get('S', x=soln[i + 1])
        SPIL = variables.get('SPI', x=soln[i + 1])
        VL = variables.get('V', x=soln[i + 1])
        YL = variables.get('Y', x=soln[i + 1])
        YDL = variables.get('YD', x=soln[i + 1])

        # DFCG.L(I,G)      = CG.L(I,G)-CG0(I,G);
        DFCG = CGL - CG0

        # DFFD.L(F,Z)      = FD.L(F,Z)-FD0(F,Z);
        DFFD = FDL - FD0

        # DK.L(K,Z)        = FD.L(K,Z)-FD0(K,Z);
        DK = KSL - KS0

        # DY.L(Z)          = Y.L(Z)-Y0(Z);
        # DY = YL - Y0
        DY = (YL / CPIL) - Y0

        # DDS.L(I)         = DS.L(I)-DS0(I);
        DDS = DSL - DS0

        # DDD.L(I)         = DD.L(I) - DD0(I);
        DDD = DDL - DD0

        # DCX.L(I)         = CX.L(I) -CX0(I);
        DCX = CXL - CX0

        # DCH.L(I,H)       = CH.L(I,H) - CH0(I,H);
        DCH = CHL - CH0

        # DRR.L(F,Z)       = R.L(F,Z)-R0(F,Z);
        DR = RL - R0

        # DCMI.L(L)        = CMI.L(L) - CMI0(L);
        DCMI = CMIL - CMI0

        # DCMO.L(CM)       = CMO.L(CM) - CMO0(CM);
        DCMO = CMOL - CMO0

        DM = ML - M0

        DV = VL - V0

        DN = NL - N0

        s_name = 'Simulation ' + str(i + 1)

    '''
    export domestic supply, household income (gross income), number of household, and factor demand
    '''
    # domestic supply
    cols = {'DS0': DS0,
            'DSL': DSL}
    df = pd.DataFrame.from_dict(cols)
    df.index.name = 'Sectors'
    # df.to_csv('domestic-supply.csv')
    domestic_supply_df = df

    # gross income
    cols = {'Y0': Y0.loc[H],
            'YL': YL.loc[H]}
    df = pd.DataFrame.from_dict(cols)
    df.index.name = 'Household Group'
    # df.to_csv('gross-income.csv')
    gross_income_df = df

    # household count
    cols = {'HH0': HH0,
            'HHL': HHL}
    df = pd.DataFrame.from_dict(cols)
    df.index.name = 'Household Group'
    # df.to_csv('household-count.csv')
    household_count_df = df

    # pre-disaster-factor-demand
    df = FD0.loc[L]
    df.index.name = 'Labor Group'
    # df.to_csv('pre-disaster-factor-demand.csv')
    pre_disaster_demand_df = df

    # post-disaster-factor-demand
    df = FDL.loc[L]
    df.index.name = 'Labor Group'
    # df.to_csv('post-disaster-factor-demand.csv')
    post_disater_demand_df = df

    return domestic_supply_df, gross_income_df, household_count_df, pre_disaster_demand_df, post_disater_demand_df
