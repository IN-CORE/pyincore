# Copyright (c) 2021 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

# increase recursion limit so that LSEQ1 can be solved
import os
from pyincore import globals as pyglobals
from pyincore import BaseAnalysis
from pyincore.analyses.saltlakecge.equationlib import *
from pyincore.analyses.saltlakecge.outputfunctions import *
from pyincore.analyses.saltlakecge.saltlakeoutput import gams_to_dataframes

from pyomo.environ import *
from pyomo.opt import SolverFactory, SolverStatus, TerminationCondition

import pandas as pd
import sys


class SaltLakeCGEModel(BaseAnalysis):
    """A computable general equilibrium (CGE) model is based on fundamental economic principles.
    A CGE model uses multiple data sources to reflect the interactions of households,
    firms and relevant government entities as they contribute to economic activity.
    The model is based on (1) utility-maximizing households that supply labor and capital,
    using the proceeds to pay for goods and services (both locally produced and imported)
    and taxes; (2) the production sector, with perfectly competitive, profit-maximizing firms
    using intermediate inputs, capital, land and labor to produce goods and services for both
    domestic consumption and export; (3) the government sector that collects taxes and uses
    tax revenues in order to finance the provision of public services; and (4) the rest of the world.



    Args:
        incore_client (IncoreClient): Service authentication.

    """

    def __init__(self, incore_client):
        super(SaltLakeCGEModel, self).__init__(incore_client)
        sys.setrecursionlimit(10000)

    def run(self):
        """

        Returns:

        """
        iNum = self.get_parameter("model_iterations")

        # TODO: Update SPEC data types to be generic
        SAM = pd.read_csv(self.get_input_dataset("SAM").get_file_path('csv'), index_col=0)
        BB = pd.read_csv(self.get_input_dataset("BB").get_file_path('csv'), index_col=0)
        JOBCR = pd.read_csv(self.get_input_dataset("JOBCR").get_file_path('csv'), index_col=0)
        MISCH = pd.read_csv(self.get_input_dataset("MISCH").get_file_path('csv'), index_col=0)
        EMPLOY = pd.read_csv(self.get_input_dataset("EMPLOY").get_file_path('csv'), index_col=0)
        OUTCR = pd.read_csv(self.get_input_dataset("OUTCR").get_file_path('csv'), index_col=0)
        sector_shocks = pd.read_csv(self.get_input_dataset("sector_shocks").get_file_path('csv'), index_col=0)

        self.salt_lake_city_cge(iNum, SAM, BB, JOBCR, MISCH, EMPLOY, OUTCR, sector_shocks)

    def salt_lake_city_cge(self, iNum, SAM, BB, JOBCR, MISCH, EMPLOY, OUTCR, sector_shocks):
        """

        Args:
            iNum (int):
            SAM (pd.DataFrame):
            BB (str):
            JOBCR:
            MISCH:
            EMPLOY:
            OUTCR:
            sector_shocks:

        Returns:

        """

        def _(x):
            return ExprM(vars, m=x)

        # ----------------------------------------------------------------
        # define sets
        # ----------------------------------------------------------------

        # ALL ACCOUNTS IN SOCIAL ACCOUNTING MATRIX
        Z = [
            'AG_MI_R1',
            'UTIL_R1',
            'CONS_R1',
            'MANU_R1',
            'COMMER_R1',
            'EDU_R1',
            'HEALTH_R1',
            'ART_ACC_R1',
            'RELIG_R1',
            'AG_MI_R2',
            'UTIL_R2',
            'CONS_R2',
            'MANU_R2',
            'COMMER_R2',
            'EDU_R2',
            'HEALTH_R2',
            'ART_ACC_R2',
            'RELIG_R2',
            'L1W_R1',
            'L2W_R1',
            'L3W_R1',
            'L4W_R1',
            'L1W_R2',
            'L2W_R2',
            'L3W_R2',
            'L4W_R2',
            'KAP',
            'INVES',
            'HS1_R1',
            'HS2_R1',
            'HS3_R1',
            'HS1_R2',
            'HS2_R2',
            'HS3_R2',
            'HH1_R1',
            'HH2_R1',
            'HH3_R1',
            'HH4_R1',
            'HH1_R2',
            'HH2_R2',
            'HH3_R2',
            'HH4_R2',
            'USSOC1_R1',
            'USSOC2_R1',
            'USSOC3_R1',
            'USSOC4_R1',
            'USSOC1_R2',
            'USSOC2_R2',
            'USSOC3_R2',
            'USSOC4_R2',
            'PROTAX',
            'UTSTX',
            'COUNTYSTX',
            'UTITX',
            'USPIT',
            'OTX',
            'CYGF',
            'COUNTY',
            'STATE',
            'FED',
            'OUT1',
            'OUT2',
            'OUT3',
            'OUT4',
            'ROW']

        # FACTORS
        F = ['L1W_R1', 'L2W_R1', 'L3W_R1', 'L4W_R1', 'L1W_R2', 'L2W_R2', 'L3W_R2', 'L4W_R2', 'KAP']
        FW1 = ['L1W_R1']
        FW2 = ['L2W_R1']
        FW3 = ['L3W_R1']
        FW4 = ['L4W_R1']

        # OUT COMMUTERS
        CM = ['OUT1', 'OUT2', 'OUT3', 'OUT4']
        CM1 = ['OUT1']
        CM2 = ['OUT2']
        CM3 = ['OUT3']
        CM4 = ['OUT4']

        # LABOR SUPPLY
        LT = ['L1W_R1', 'L2W_R1', 'L3W_R1', 'L4W_R1', 'L1W_R2', 'L2W_R2', 'L3W_R2', 'L4W_R2',
              'OUT1', 'OUT2', 'OUT3', 'OUT4']

        # LABOR WORKING IN GALVESTON
        L = ['L1W_R1', 'L2W_R1', 'L3W_R1', 'L4W_R1', 'L1W_R2', 'L2W_R2', 'L3W_R2', 'L4W_R2']

        # CAPITAL
        K = ['KAP']

        # LAND
        # LA = ['LAND']

        # GOVERNMENTS
        G = ['USSOC1_R1', 'USSOC2_R1', 'USSOC3_R1', 'USSOC4_R1', 'USSOC1_R2', 'USSOC2_R2', 'USSOC3_R2', 'USSOC4_R2',
             'PROTAX', 'UTSTX', 'COUNTYSTX', 'UTITX', 'USPIT', 'OTX', 'CYGF', 'COUNTY', 'STATE', 'FED']

        # ENDOGENOUS GOVERNMENTS
        GN = ['COUNTY', 'STATE', 'FED']

        # LOCAL ENDOGENOUS GOVERNMENTS
        GNL = ['COUNTY']

        # EXOGENOUS GOVERMENTS
        GX = ['USSOC1_R1', 'USSOC2_R1', 'USSOC3_R1', 'USSOC4_R1', 'USSOC1_R2', 'USSOC2_R2', 'USSOC3_R2', 'USSOC4_R2',
              'PROTAX', 'UTSTX', 'COUNTYSTX', 'UTITX', 'USPIT', 'OTX']

        # SALES OR EXCISE TAXES
        GS = ['UTSTX', 'COUNTYSTX', 'OTX']

        # LOCAL TAX
        GC = ['UTSTX', 'COUNTYSTX', 'OTX']

        # LAND TAXES
        GL = ['PROTAX']

        # FACTOR TAXES
        GF = ['USSOC1_R1', 'USSOC2_R1', 'USSOC3_R1', 'USSOC4_R1', 'USSOC1_R2', 'USSOC2_R2', 'USSOC3_R2',
              'USSOC4_R2', 'PROTAX']

        # INCOME TAX UNITS
        GI = ['UTITX', 'USPIT']

        # HOUSEHOLD TAX UNITS
        GH = ['PROTAX']

        # SOCIAL SECURITY PAYMENT
        GFUS = ['USSOC1_R1', 'USSOC2_R1', 'USSOC3_R1', 'USSOC4_R1', 'USSOC1_R2', 'USSOC2_R2', 'USSOC3_R2', 'USSOC4_R2']

        # EXOGNOUS TRANSFER PMT
        GY = ['USSOC1_R1', 'USSOC2_R1', 'USSOC3_R1', 'USSOC4_R1', 'USSOC1_R2', 'USSOC2_R2', 'USSOC3_R2', 'USSOC4_R2',
              'PROTAX', 'UTSTX', 'COUNTYSTX', 'UTITX', 'USPIT', 'OTX', 'CYGF', 'COUNTY', 'STATE', 'FED']

        # EXOGNOUS TRANSFER PMT
        GTA = ['USSOC1_R1', 'USSOC2_R1', 'USSOC3_R1', 'USSOC4_R1', 'USSOC1_R2', 'USSOC2_R2', 'USSOC3_R2', 'USSOC4_R2',
               'PROTAX', 'UTSTX', 'COUNTYSTX', 'UTITX', 'USPIT', 'OTX', 'CYGF', 'COUNTY', 'STATE', 'FED']

        # ENDOGENOUS TRANSFER PMT
        GT = ['CYGF', 'STATE', 'FED']

        # ALL HOUSEHOLDS IN GALVESTON
        H = ['HH1_R1', 'HH2_R1', 'HH3_R1', 'HH4_R1', 'HH1_R2', 'HH2_R2', 'HH3_R2', 'HH4_R2']

        # HOUSEHOLD (INCOME i, i = 1,2,3,4)
        HH1 = ['HH1_R1', 'HH1_R2']
        HH2 = ['HH2_R1', 'HH2_R2']
        HH3 = ['HH3_R1', 'HH3_R2']
        HH4 = ['HH4_R1', 'HH4_R2']

        # I+G SECTORS
        IG = ['AG_MI_R1', 'UTIL_R1', 'CONS_R1', 'MANU_R1', 'COMMER_R1', 'EDU_R1', 'HEALTH_R1', 'ART_ACC_R1', 'RELIG_R1',
              'AG_MI_R2', 'UTIL_R2', 'CONS_R2', 'MANU_R2', 'COMMER_R2', 'EDU_R2', 'HEALTH_R2', 'ART_ACC_R2', 'RELIG_R2',
              'HS1_R1', 'HS2_R1', 'HS3_R1', 'HS1_R2', 'HS2_R2', 'HS3_R2',
              'COUNTY', 'STATE', 'FED']

        # INDUSTRY SECTORS
        I = ['AG_MI_R1', 'UTIL_R1', 'CONS_R1', 'MANU_R1', 'COMMER_R1', 'EDU_R1', 'HEALTH_R1', 'ART_ACC_R1', 'RELIG_R1',
             'AG_MI_R2', 'UTIL_R2', 'CONS_R2', 'MANU_R2', 'COMMER_R2', 'EDU_R2', 'HEALTH_R2', 'ART_ACC_R2', 'RELIG_R2',
             'HS1_R1', 'HS2_R1', 'HS3_R1', 'HS1_R2', 'HS2_R2', 'HS3_R2']

        # ENDOGENOUS GOVERNMENTS
        IG2 = ['COUNTY', 'STATE', 'FED']

        # PRODUCTION SECTORS
        IP = ['AG_MI_R1', 'UTIL_R1', 'CONS_R1', 'MANU_R1', 'COMMER_R1', 'EDU_R1', 'HEALTH_R1', 'ART_ACC_R1', 'RELIG_R1',
              'AG_MI_R2', 'UTIL_R2', 'CONS_R2', 'MANU_R2', 'COMMER_R2', 'EDU_R2', 'HEALTH_R2', 'ART_ACC_R2', 'RELIG_R2']

        # PRODUCTION GOV
        FG = ['COUNTY', 'STATE', 'FED']

        # HOUSING SERVICE DEMAND
        HSD = ['HS1_R1', 'HS2_R1', 'HS3_R1', 'HS1_R2', 'HS2_R2', 'HS3_R2', ]

        # ETA ELASTICITIES
        ETA = ['ETAL1', 'ETAI1', 'ETALB1', 'ETAPIT', 'ETAPT', 'ETARA', 'NRPG', 'ETAYD', 'ETAU', 'ETAM', 'ETAE', 'ETAY',
               'ETAOP']

        # ETALANDCAP(ETA) LANDCAP TABLE ELASTICITIES
        ETALANDCAP = ['ETAL1', 'ETAI1', 'ETALB1']

        # ETAMISCH(ETA) MISCH TABLE ELASTICITIES
        ETAMISCH = ['ETAPIT', 'ETAPT', 'ETARA', 'NRPG', 'ETAYD', 'ETAU']

        # ETAMISC(ETA) MISC TABLE ELASTICITIES
        ETAMISC = ['ETAM', 'ETAE', 'ETAY', 'ETAOP']

        # SIMMLOOP
        SM = ['BASE', 'TODAY', 'simm']

        # EPORT 1 FOR SCALARS
        R1H = ['GFREV', 'SFREV', 'PIT',
               'DGF', 'DSF', 'DDRE', 'PDRE', 'SPI', 'COMM', 'COMMO',
               'GN', 'NKI', 'HH', 'W', 'W1', 'W2', 'W3',
               'R', 'RL', 'L', 'K', 'HN', 'HW', 'GFSAV', 'LD',
               'CMO', 'CMI', 'HC', 'SSC', 'LAND', 'LAS']

        # REPORT 2FOR STATUS
        R2H = ['M-STAT', 'S-STAT']

        # LABELS FOR MODEL STATUS
        MS = ['OPTIMAL', 'LOCALOP', 'UNBOUND',
              'INFSBLE', 'INFSLOC', 'INFSINT',
              'NOOPTML', 'MIPSOLN', 'NOINTGR',
              'INFSMIP', 'UNUSED', 'UNKNOWN',
              'NOSOLUT']

        # LABELS FOR SOLVER STATUS
        SS = ['OK', 'ITERATE', 'RESRCE',
              'SOLVER', 'EVALUATE', 'NOTKNWN',
              'NOTUSED', 'PRE-PROC', 'SETUP',
              'SLVFAIL', 'SLVINTER', 'POST-PROC',
              'METSYS']

        # ----------------------------------------------------------------
        # SET ALIASES
        # ----------------------------------------------------------------

        # ALIAS
        J = I
        I1 = I
        Z1 = Z
        F1 = F
        G1 = G
        G2 = G
        GI1 = GI
        GS1 = GS
        GX1 = GX
        GN1 = GN
        GH1 = GH
        GF1 = GF
        H1 = H
        HSD1 = HSD
        JP = IP
        JG = IG
        GT1 = GT
        GNL1 = GNL
        L1 = L

        # ----------------------------------------------------------------
        # PARAMETER DECLARATION
        # ----------------------------------------------------------------

        # These are data frames with zeros to be filled during calibration.
        A = pd.DataFrame(index=Z, columns=Z).fillna(0.0)
        AD = pd.DataFrame(index=Z, columns=Z).fillna(0.0)
        AG = pd.DataFrame(index=Z, columns=G).fillna(0.0)
        ALPHA = pd.DataFrame(index=Z, columns=I).fillna(0.0)
        B = pd.DataFrame(index=I, columns=IG).fillna(0.0)
        CMOWAGE = pd.Series(index=CM, dtype="float64").fillna(0.0)
        CMIWAGE = pd.Series(index=L, dtype="float64").fillna(0.0)
        FCONST = pd.DataFrame(index=F, columns=I).fillna(0.0)
        DELTA = pd.Series(index=I, dtype="float64").fillna(0.0)
        GAMMA = pd.Series(index=I, dtype="float64").fillna(0.0)
        PIT = pd.DataFrame(index=G, columns=H).fillna(0.0)
        PIT0 = pd.DataFrame(index=G, columns=H).fillna(0.0)
        PRIVRET = pd.Series(index=H, dtype="float64").fillna(0.0)
        KFOR = pd.Series(index=K, dtype="float64").fillna(0.0)
        # LFOR = pd.Series(index=LA, dtype="float64").fillna(0.0)
        GFOR = pd.Series(index=G, dtype="float64").fillna(0.0)
        NRPG = pd.Series(index=H, dtype="float64").fillna(0.0)
        RHO = pd.Series(index=I, dtype="float64").fillna(0.0)
        SIGMA = pd.Series(index=I, dtype=float).fillna(0.0)

        # TAXES
        TAUFH = pd.DataFrame(index=G, columns=Z).fillna(0.0)
        TAUFL = pd.DataFrame(index=G, columns=L).fillna(0.0)
        TAUFK = pd.DataFrame(index=G, columns=K).fillna(0.0)
        # TAUFLA = pd.DataFrame(index=G, columns=LA).fillna(0.0)
        TAUH = pd.DataFrame(index=G, columns=H).fillna(0.0)
        TAUH0 = pd.DataFrame(index=G, columns=H).fillna(0.0)
        TAUM = pd.DataFrame(index=G, columns=IG).fillna(0.0)
        TAUQ = pd.DataFrame(index=G, columns=IG).fillna(0.0)
        TAUC = pd.DataFrame(index=G, columns=I).fillna(0.0)
        TAUCH = pd.DataFrame(index=G, columns=HSD).fillna(0.0)
        TAUV = pd.DataFrame(index=G, columns=I).fillna(0.0)
        TAUN = pd.DataFrame(index=G, columns=IG).fillna(0.0)
        TAUX = pd.DataFrame(index=G, columns=IG).fillna(0.0)
        TAUG = pd.DataFrame(index=G, columns=I).fillna(0.0)
        TAXS = pd.DataFrame(index=G, columns=GX).fillna(0.0)
        TAXS1 = pd.Series(index=GNL, dtype="float64").fillna(0.0)

        # ELASTICITIES AND TAX DATA IMPOSED
        LAMBDA = pd.DataFrame(index=I, columns=I).fillna(0.0)
        BETA = pd.DataFrame(index=I, columns=H).fillna(0.0)
        BETAH = pd.DataFrame(index=HSD, columns=H).fillna(0.0)
        ETAD = pd.Series(index=I, dtype="float64").fillna(0.0)
        ETAE = pd.Series(index=I, dtype="float64").fillna(0.0)
        ETAI = pd.Series(index=IG, dtype="float64").fillna(0.0)
        ETAIX = pd.DataFrame(index=K, columns=IG).fillna(0.0)
        # ETAL = pd.DataFrame(index=LA, columns=IG).fillna(0.0)
        ETAL1 = pd.Series(index=IG, dtype="float64").fillna(0.0)
        ETALB1 = pd.Series(index=IG, dtype="float64").fillna(0.0)
        ETALB = pd.DataFrame(index=L, columns=IG).fillna(0.0)
        ETAM = pd.Series(index=I, dtype="float64").fillna(0.0)
        ETARA = pd.Series(index=H, dtype="float64").fillna(0.0)
        ETAYD = pd.Series(index=H, dtype="float64").fillna(0.0)
        ETAU = pd.Series(index=H, dtype="float64").fillna(0.0)
        ETAYDI = pd.Series(index=H, dtype="float64").fillna(0.0)
        ETAYDO = pd.Series(index=H, dtype="float64").fillna(0.0)
        ETAUO = pd.Series(index=H, dtype="float64").fillna(0.0)
        ETAUI = pd.Series(index=H, dtype="float64").fillna(0.0)
        ETAPT = pd.Series(index=H, dtype="float64").fillna(0.0)
        ETAPIT = pd.Series(index=H, dtype="float64").fillna(0.0)
        ECOMI = pd.Series(index=L, dtype="float64").fillna(0.0)
        ECOMO = pd.Series(index=CM, dtype="float64").fillna(0.0)

        # VARIABLES FOR INTERMEDIATE CALCULATIONS
        AGFS = pd.DataFrame(index=Z, columns=G).fillna(0.0)
        ALPHA1 = pd.DataFrame(index=F, columns=I).fillna(0.0)
        B1 = pd.DataFrame(index=I, columns=I).fillna(0.0)
        PRIVRET1 = pd.Series(index=H, dtype="float64").fillna(0.0)
        OUT = pd.DataFrame(index=G, columns=G).fillna(0.0)
        KPFOR01 = pd.Series(index=K, dtype="float64").fillna(0.0)
        TT = pd.Series(index=I, dtype="float64").fillna(0.0)

        # ARRAYS BUILT TO EXPORT RESULTS TO SEPARATE FILE
        R1 = pd.DataFrame(index=R1H, columns=SM).fillna(0.0)
        R2 = pd.DataFrame(index=R2H, columns=SM).fillna(0.0)

        # INITIAL VALUES OF ENDOGENOUS VARIABLES
        CG0 = pd.DataFrame(index=I, columns=G).fillna(0.0)
        CG0T = pd.DataFrame(index=I, columns=G).fillna(0.0)
        CH0 = pd.DataFrame(index=I, columns=H).fillna(0.0)
        CH0T = pd.DataFrame(index=I, columns=H).fillna(0.0)
        CMI0 = pd.Series(index=L, dtype="float64").fillna(0.0)
        CMO0 = pd.Series(index=CM, dtype="float64").fillna(0.0)
        CN0 = pd.Series(index=I, dtype="float64").fillna(0.0)
        CN0T = pd.Series(index=I, dtype="float64").fillna(0.0)
        CPI0 = pd.Series(index=H, dtype="float64").fillna(0.0)
        CPIN0 = pd.Series(index=H, dtype="float64").fillna(0.0)
        CPIH0 = pd.Series(index=H, dtype="float64").fillna(0.0)
        CX0 = pd.Series(index=I, dtype="float64").fillna(0.0)
        D0 = pd.Series(index=I, dtype="float64").fillna(0.0)
        DD0 = pd.Series(index=Z, dtype="float64").fillna(0.0)
        DS0 = pd.Series(index=Z, dtype="float64").fillna(0.0)
        DQ0 = pd.Series(index=Z, dtype="float64").fillna(0.0)

        FD0 = pd.DataFrame(index=F, columns=Z).fillna(0.0)
        IGT0 = pd.DataFrame(index=G, columns=GX).fillna(0.0)
        KS0 = pd.DataFrame(index=K, columns=IG).fillna(0.0)
        # LAS0 = pd.DataFrame(index=LA, columns=IG).fillna(0.0)
        HH0 = pd.Series(index=H, dtype="float64").fillna(0.0)
        HN0 = pd.Series(index=H, dtype="float64").fillna(0.0)
        HW0 = pd.Series(index=H, dtype="float64").fillna(0.0)
        EXWGEO = pd.Series(index=CM, dtype="float64").fillna(0.0)

        HOUSECOR = pd.DataFrame(index=H, columns=HSD).fillna(0.0)
        JOBCOR = pd.DataFrame(index=H, columns=L).fillna(0.0)
        OUTCOR = pd.DataFrame(index=H, columns=CM).fillna(0.0)

        M0 = pd.Series(index=I, dtype="float64").fillna(0.0)
        M01 = pd.Series(index=Z, dtype="float64").fillna(0.0)
        MI0 = pd.Series(index=H, dtype="float64").fillna(0.0)
        MO0 = pd.Series(index=H, dtype="float64").fillna(0.0)
        N0 = pd.DataFrame(index=K, columns=IG).fillna(0.0)
        # NKI0
        KPFOR0 = pd.Series(index=K, dtype="float64").fillna(0.0)
        # LNFOR0 = pd.Series(index=LA, dtype="float64").fillna(0.0)
        # LNFOR01 = pd.Series(index=LA, dtype="float64").fillna(0.0)

        GVFOR0 = pd.Series(index=G, dtype="float64").fillna(0.0)
        P0 = pd.Series(index=IG, dtype="float64").fillna(0.0)
        PD0 = pd.Series(index=I, dtype="float64").fillna(0.0)
        PVA0 = pd.Series(index=I, dtype="float64").fillna(0.0)
        PW0 = pd.Series(index=I, dtype="float64").fillna(0.0)
        PWM0 = pd.Series(index=I, dtype="float64").fillna(0.0)
        Q0 = pd.Series(index=Z, dtype="float64").fillna(0.0)
        Q10 = pd.Series(index=Z, dtype="float64").fillna(0.0)
        R0 = pd.DataFrame(index=F, columns=Z).fillna(1.0)
        RA0 = pd.Series(index=Z, dtype="float64").fillna(0.0)

        S0 = pd.Series(index=Z, dtype="float64").fillna(0.0)
        # SPI0
        V0 = pd.Series(index=I, dtype="float64").fillna(0.0)
        V0T = pd.Series(index=I, dtype="float64").fillna(0.0)
        TP = pd.DataFrame(index=H, columns=G).fillna(0.0)
        # TAUF0 = Table(G,F,Z)
        YD0 = pd.Series(index=H, dtype="float64").fillna(0.0)
        Y0 = pd.Series(index=Z, dtype="float64").fillna(0.0)
        Y01 = pd.Series(index=H, dtype="float64").fillna(0.0)
        YT0 = pd.Series(index=G, dtype="float64").fillna(0.0)
        GCP10 = pd.Series(index=I, dtype="float64").fillna(0.0)
        # GCP0
        SD3 = pd.Series(index=GX, dtype="float64").fillna(0.0)
        DDCX = pd.Series(index=I, dtype="float64").fillna(0.0)

        TESTA1 = pd.DataFrame(index=F, columns=I).fillna(0.0)
        TESTA2 = pd.DataFrame(index=F, columns=I).fillna(0.0)
        TESTA3 = pd.DataFrame(index=F, columns=I).fillna(0.0)

        # Lstore(Z,L,t)
        # DYSTORE = pd.DataFrame(index=Z, columns=T).fillna(0.0)
        # DSSTORE = pd.DataFrame(index=I, columns=T).fillna(0.0)
        # HHSTORE = pd.DataFrame(index=H, columns=T).fillna(0.0)
        # FSTORE(Z,F,T)
        # CPISTORE = pd.DataFrame(index=H, columns=T).fillna(0.0)

        TPC = pd.DataFrame(index=H, columns=G).fillna(0.0)
        IGTD = pd.DataFrame(index=G, columns=G1).fillna(0.0)
        TAUFF = pd.DataFrame(index=G, columns=F).fillna(0.0)
        IOUT = pd.DataFrame(index=G1, columns=G1).fillna(0.0)
        LANDCAP = pd.DataFrame(index=IG, columns=ETALANDCAP).fillna(0.0)
        MISC = pd.DataFrame(index=IG, columns=ETAMISC).fillna(0.0)
        # MISCH= pd.DataFrame(index=H, columns=ETAMISCH).fillna(0.0)

        # -------------------------------------------------------------------------------------------------------------
        # SIMPLIFYING TABLES AND DOING AWAY WITH MISC FILES
        # -------------------------------------------------------------------------------------------------------------

        IGTD.loc[G, G1] = 0
        IGTD.loc['FED', GFUS] = 1
        IGTD.loc['FED', 'USPIT'] = 1

        IGTD.loc['CYGF', 'PROTAX'] = 1
        IGTD.loc['CYGF', 'COUNTYSTX'] = 1

        IGTD.loc['CYGF', 'OTX'] = 1

        IGTD.loc['STATE', 'UTSTX'] = 1
        IGTD.loc['STATE', 'UTITX'] = 1

        TPC.loc[H, G] = 0
        TPC.loc[H, GFUS] = 1

        TAUFF.loc[G, F] = 0
        TAUFF.loc['USSOC1_R1', 'L1W_R1'] = 1
        TAUFF.loc['USSOC2_R1', 'L2W_R1'] = 1
        TAUFF.loc['USSOC3_R1', 'L3W_R1'] = 1
        TAUFF.loc['USSOC4_R1', 'L4W_R1'] = 1

        TAUFF.loc['USSOC1_R2', 'L1W_R2'] = 1
        TAUFF.loc['USSOC2_R2', 'L2W_R2'] = 1
        TAUFF.loc['USSOC3_R2', 'L3W_R2'] = 1
        TAUFF.loc['USSOC4_R2', 'L4W_R2'] = 1

        TAUFF.loc['PROTAX', 'KAP'] = 1

        for label in G1:
            IOUT.loc[label, label] = 0
        # IOUT.loc['OTHER_LOCAL', 'CYGF'] = 1
        IOUT.loc['COUNTY', 'CYGF'] = 1

        LANDCAP.loc[IG, ETALANDCAP] = 1

        MISCH.loc[H, ETAMISCH] = 0

        MISCH.loc[HH1, 'ETAPIT'] = -0.5
        MISCH.loc[HH2, 'ETAPIT'] = -0.15
        MISCH.loc[HH3, 'ETAPIT'] = -0.15
        MISCH.loc[HH4, 'ETAPIT'] = -0.15

        MISCH.loc[HH1, 'ETAPT'] = -0.5
        MISCH.loc[H, 'NRPG'] = 1
        MISCH.loc[H, 'ETARA'] = 1

        MISCH.loc[HH1, 'ETAYD'] = 1.3
        MISCH.loc[HH2, 'ETAYD'] = 1.3
        MISCH.loc[HH3, 'ETAYD'] = 1.6
        MISCH.loc[HH4, 'ETAYD'] = 1.6

        MISCH.loc[HH1, 'ETAU'] = -0.8
        MISCH.loc[HH2, 'ETAU'] = -0.8
        MISCH.loc[HH3, 'ETAU'] = -0.8
        MISCH.loc[HH4, 'ETAU'] = -0.6

        MISC.loc[IG, ETAMISC] = 0
        MISC.loc[IP, 'ETAM'] = 1
        MISC.loc[IP, 'ETAE'] = -1.65
        MISC.loc[I, 'ETAY'] = 1
        MISC.loc[I, 'ETAOP'] = -1

        # -------------------------------------------------------------------------------------------------------------
        # CALCULATIONS OF PARAMETERS AND INITIAL VALUES
        # -------------------------------------------------------------------------------------------------------------

        # CALCULATE COLUMN AND ROW TOTALS OF SAM TO COMPARE FOR BALANCE
        Q10.loc[Z] = SAM.loc[Z].sum(0)  # Column Totals of SAM table

        Q0.loc[Z] = SAM.loc[Z].sum(1)  # Row Totals of SAM table

        DQ0.loc[Z] = Q10.loc[Z] - Q0.loc[Z]  # difference of SAM row and coloumn totals

        B1.loc[I, I] = SAM.loc[I, I]

        # READ IN ELASTICITY PARAMETERS FROM MISC.PRN
        OUT.loc[G, G] = IOUT.loc[G, G]

        BETA.loc[I, H] = MISC.loc[I, 'ETAY']

        BETAH.loc[HSD, H] = MISC.loc[HSD, 'ETAY']

        LAMBDA.loc[I, I] = MISC.loc[I, 'ETAOP']

        ETAE.loc[I] = MISC.loc[I, 'ETAE']

        ETAM.loc[I] = MISC.loc[I, 'ETAM']

        ETARA.loc[H] = MISCH.loc[H, 'ETARA']

        ETAPIT.loc[H] = MISCH.loc[H, 'ETAPIT']

        ETAPT.loc[H] = MISCH.loc[H, 'ETAPT']

        ETAYD.loc[H] = MISCH.loc[H, 'ETAYD']

        NRPG.loc[H] = MISCH.loc[H, 'NRPG']

        ETAU.loc[H] = MISCH.loc[H, 'ETAU']

        ECOMI.loc[L] = 1.0
        ECOMO.loc[CM] = 1.0
        EXWGEO.loc[CM] = 1.0

        ETAI.loc[IG] = LANDCAP.loc[IG, 'ETAI1']
        ETAL1.loc[IG] = LANDCAP.loc[IG, 'ETAL1']

        ETAIX.loc['KAP', IG] = ETAI.loc[IG]
        # ETAL.loc['LAND',IG] = ETAL1.loc[IG]

        # CALCULATE TAX RATES FROM SAM INFORMATION
        TAUQ_1 = SAM.loc[GS, I]
        TAUQ_2 = SAM.loc[I, I].sum(1)
        TAUQ_3 = SAM.loc[I, H].sum(1)
        TAUQ_4 = SAM.loc[I, ['INVES']].sum(1)
        TAUQ_5 = SAM.loc[I, G].sum(1)
        TAUQ_6 = SAM.loc[I, ['ROW']].sum(1)
        TAUQ_7 = SAM.loc[GS1, I].sum(0)

        TAUQ.loc[GS, I] = TAUQ_1 / (TAUQ_2 + TAUQ_3 + TAUQ_4 + TAUQ_5 + TAUQ_6 - TAUQ_7)

        TAUC.loc[GS, I] = TAUQ.loc[GS, I]
        TAUV.loc[GS, I] = TAUQ.loc[GS, I]
        TAUN.loc[GS, I] = TAUQ.loc[GS, I]
        TAUG.loc[GS, I] = TAUQ.loc[GS, I]
        TAUX.loc[GS, I] = TAUQ.loc[GS, I]

        # FACTOR TAX RATES
        TAUFarray = [[[0 for k in range(len(Z))] for j in range(len(F))] for i in range(len(G))]
        for i in range(len(GF)):
            for j in range(len(F)):
                for k in range(len(I)):
                    if SAM.loc[F[j], I[k]] != 0 and TAUFF.loc[GF[i], F[j]] != 0:
                        TAUFarray[G.index(GF[i])][j][Z.index(I[k])] = SAM.loc[GF[i], I[k]] / SAM.loc[F[j], I[k]]

        for i in range(len(GF)):
            for j in range(len(F)):
                for k in range(len(G)):
                    if SAM.loc[F[j], G[k]] != 0 and TAUFF.loc[GF[i], F[j]] != 0:
                        TAUFarray[G.index(GF[i])][j][Z.index(G[k])] = SAM.loc[GF[i], G[k]] / SAM.loc[F[j], G[k]]

        TAUFX_SUM_array = [[0 for j in range(len(Z))] for i in range(len(F))]
        for i in range(len(F)):
            for j in range(len(Z)):
                tmp = 0
                for k in range(len(G)):
                    tmp += TAUFarray[k][i][j]
                TAUFX_SUM_array[i][j] = tmp

        # TAUFX summed over GX
        TAUFX_SUM = pd.DataFrame(TAUFX_SUM_array, index=F, columns=Z).fillna(0.0)

        TAUFX_GF = pd.DataFrame(TAUFX_SUM_array, index=F, columns=Z).fillna(0.0)

        TAUFXgx = {}
        for i in range(len(GX)):
            TAUFXgx[GX[i]] = pd.DataFrame(TAUFarray[i], index=F, columns=Z).fillna(0.0)

        # SS TAX RATES
        # TAUFH(GF,F)$(TAUFF(GF,F)) =SAM(GF,F) / SUM(Z, SAM(Z,F));
        for i in GF:
            for j in F:
                if TAUFF.loc[i, j] != 0:
                    #            TAUFH.set_value(i, j, SAM.loc[i, j] / SAM.loc[Z, F].sum(0).loc[j])
                    TAUFH.at[i, j] = SAM.at[i, j] / SAM.loc[Z, F].sum(0).at[j]

        # TAUFH(GFUS,L)  =SAM(GFUS,L) / SUM(IG, SAM(L,IG));
        for i in GFUS:
            for j in L:
                if TAUFF.loc[i, j] != 0:
                    #            TAUFH.set_value(i, j, SAM.loc[i, j] / SAM.loc[L, IG].sum(1).loc[j])
                    TAUFH.at[i, j] = SAM.at[i, j] / SAM.loc[L, IG].sum(1).at[j]

        # EMPLOYEE PORTION OF FACTOR TAXES
        TAUFL.loc[GF, L] = SAM.loc[GF, L] / SAM.loc[Z, L].sum(0)
        TAUFK.loc[GF, K] = SAM.loc[GF, K] / SAM.loc[Z, K].sum(0)

        # SHARES OF ENDOGENOUS GOVERNMENTS TRANFERS TO REVENUE
        TAXS.loc[G, GX] = SAM.loc[G, GX] / SAM.loc[G, GX].sum(0)
        TAXS1.loc[GNL] = SAM.loc[GNL, ['CYGF']].sum(1) / SAM.loc[GNL, ['CYGF']].sum(1).sum(0)

        # SET INITIAL INTER GOVERNMENTAL TRANSFERS
        IGT0.loc[G, GX] = SAM.loc[G, GX]

        PW0.loc[I] = 1.0
        PWM0.loc[I] = 1.0
        P0.loc[I] = 1.0
        PD0.loc[I] = 1.0
        CPI0.loc[H] = 1.0
        CPIN0.loc[H] = 1.0
        CPIH0.loc[H] = 1.0

        # HOUSEHOLD TRANSFER PAYMENTS AND PERSONAL INCOME TAXES

        # TOTAL HH
        HH0.loc[H] = MISCH.loc[H, 'HH0']

        # TOTAL WORKING HH
        HW0.loc[H] = MISCH.loc[H, 'HW0']

        # NON WORKING HH
        HN0.loc[H] = HH0.loc[H] - HW0.loc[H]

        # NOMINAL GOVERNMENT SS PAYMENTS
        TP.loc[H, G] = SAM.loc[H, G].div(HH0.loc[H], axis='index').fillna(0.0)

        # FACTOR RENTALS
        JOBCOR.loc[H, L] = JOBCR.loc[H, L]

        # COMMUTERS
        CMO0.loc[CM] = (OUTCR.loc[H, CM].mul(HW0.loc[H], axis='index')).sum(0)

        # RENTAL RATE FOR FACTORS
        R0.loc[F, Z] = 1.0

        R0.loc[F, IG] = (SAM.loc[F, IG] / EMPLOY.loc[IG, F].T).fillna(1.0)

        # REAL FACTOR DEMAND
        FD0.loc[F, IG] = EMPLOY.loc[IG, F].T
        KS0.loc[K, IG] = FD0.loc[K, IG]

        # SHARES FOUND IN THE SOCIAL ACCOUNTING MATRIX DATA
        A.loc[Z, Z] = SAM.loc[Z, Z].div(Q0.loc[Z], axis='columns')

        # AGFS: LABOR PAYMENTS BY G SECTOR + USSOC PAYMENTS BY LABOR (GROSS LABOR PAYMENTS)
        AGFS.loc['L1W_R1', G] = SAM.loc['L1W_R1', G] + SAM.loc['USSOC1_R1', G]
        AGFS.loc['L2W_R1', G] = SAM.loc['L2W_R1', G] + SAM.loc['USSOC2_R1', G]
        AGFS.loc['L3W_R1', G] = SAM.loc['L3W_R1', G] + SAM.loc['USSOC3_R1', G]
        AGFS.loc['L4W_R1', G] = SAM.loc['L4W_R1', G] + SAM.loc['USSOC4_R1', G]

        AGFS.loc['L1W_R2', G] = SAM.loc['L1W_R2', G] + SAM.loc['USSOC1_R2', G]
        AGFS.loc['L2W_R2', G] = SAM.loc['L2W_R2', G] + SAM.loc['USSOC2_R2', G]
        AGFS.loc['L3W_R2', G] = SAM.loc['L3W_R2', G] + SAM.loc['USSOC3_R2', G]
        AGFS.loc['L4W_R2', G] = SAM.loc['L4W_R2', G] + SAM.loc['USSOC4_R2', G]

        # AG - GOVERNMENT SPENDING SHARES OF NET INCOME
        AG_1 = SAM.loc[I, G]
        AG_2 = SAM.loc[I, G].sum(0) + SAM.loc[F, G].sum(0) + SAM.loc[GF, G].sum(0)
        AG.loc[I, G] = AG_1 / AG_2

        AG_1 = SAM.loc[F, G]
        AG.loc[F, G] = AG_1 / AG_2

        AG_1 = AGFS.loc[L, G]
        AG.loc[L, G] = AG_1 / AG_2
        AG = AG.fillna(0.0)

        # TRADE INTERMEDIATES CONSUMPTION INVESTMENT INITIAL LEVELS

        # REAL EXPORT CONSUMPTION
        CX0.loc[I] = SAM.loc[I, ["ROW"]].div(P0.loc[I], axis='index').div(1.0 + TAUQ.loc[GS, I].sum(0),
                                                                          axis='index').sum(1)

        # REAL IMPORTS
        # M01.loc[I] = SAM.loc[["ROW"], I].sum(0) / PWM0[I].T
        M0.loc[IP] = SAM.loc[IP, Z].sum(1) - (B1.loc[I, IP].sum(0) + SAM.loc[F, IP].sum(0) + SAM.loc[G, IP].sum(0))
        M0.loc[I] = (M0[I] / PWM0[I])
        M0 = M0.fillna(0.0)

        # REAL INTERMEDIATE DEMAND
        V0.loc[I] = SAM.loc[I, I].sum(1) / P0.loc[I] / (1.0 + TAUQ.loc[GS, I].sum(0))
        V0T.loc[I] = SAM.loc[I, I].sum(1) / P0.loc[I]

        # REAL PRIVATE CONSUMPTION
        CH0.loc[I, H] = SAM.loc[I, H].div(P0.loc[I], axis='index').div(1.0 + TAUQ.loc[GS, I].sum(0), axis='index')

        CH0T.loc[I, H] = SAM.loc[I, H].div(P0[I], axis='index')

        CG0.loc[I, GN] = SAM.loc[I, GN].div(P0.loc[I], axis='index').div((1.0 + TAUQ.loc[GS, I].sum(0)), axis='index')

        CG0T.loc[I, GN] = SAM.loc[I, GN].div(P0.loc[I], axis='index')

        DEPR = float((SAM.loc[IG, ["INVES"]].sum(0)) / (KS0.loc[K, IG].sum(1).sum(0)))

        N0.loc[K, IG] = KS0.loc[K, IG] * DEPR

        # INVESTMENT BY SECTOR OF SOURCE
        CN0.loc[I] = 0.0

        B.loc[I, IG] = BB.loc[I, IG].fillna(0.0)

        CN0.loc[I] = (B.loc[I, IG].mul(N0.loc[K, IG].sum(0), axis='columns')).sum(1).div(P0.loc[I], axis='index').div(
            1.0 + TAUN.loc[GS, I].sum(0), axis='index').transpose()

        CN0T.loc[I] = (B.loc[I, IG].mul(N0.loc[K, IG].sum(0), axis='columns')).sum(1).div(P0.loc[I], axis='index')

        DD0.loc[I] = CH0.loc[I, H].sum(1) + CG0.loc[I, G].sum(1) + CN0.loc[I] + V0.loc[I]

        D0.loc[I] = 1.0 - (M0.loc[I] / DD0.loc[I])

        # CORRECT IMPORT ELASTICITY TO DOMESTIC SHARE ELASTICITY
        ETAD.loc[I] = -1.0 * ETAM.loc[I] * M0.loc[I] / (DD0.loc[I] * D0.loc[I])

        # PRODUCTION DATA
        DS0.loc[I] = DD0.loc[I] + CX0.loc[I] - M0.loc[I];

        AD.loc[I, I] = SAM.loc[I, I].div(P0.loc[I], axis='index').div(1.0 + TAUQ.loc[GS, I].sum(0), axis='index') / \
                       DS0.loc[I]

        PVA0.loc[I] = PD0.loc[I] - (
            (AD.loc[I, I].mul(P0.loc[I], axis='index').mul(1.0 + TAUQ.loc[GS, I].sum(0).T, axis='index')).sum(0).T)

        # AVERAGE RENTAL RATES FOR FACTORS (NORMALIZED)
        RA0.loc[F] = 1.0

        '''
        # CALIBRATION OF PRODUCTION EXPONENTS FOR COBB DOUGLAS
        a = pd.Series(index=I, dtype="float64").fillna(0.0)
        a = SAM.loc[USSOCL, I].append(a, ignore_index=True).append(SAM.loc[GL, I]) # labor, land, capital
        a.index = F
        
        ALPHA.loc[F, I] = (SAM.loc[F, I] + a.loc[F, I]) / (SAM.loc[F, I].sum(0) + SAM.loc[GF, I].sum(0))
        ALPHA.loc[F, I] = ALPHA.loc[F, I] / ALPHA.loc[F, I].sum(0)
        '''

        # DELTA(I) = DS0(I)/ (PROD(F$ALPHA(F,I),FD0(F,I)**ALPHA(F,I)));
        # replace takes care of multiplying by zeros, by changing zeros to ones.
        # DELTA.loc[I] = DS0.loc[I] / (FD0.loc[F, I] ** ALPHA.loc[F, I]).replace({0: 1}).product(0)

        SIGMA.loc[I] = 0.67
        RHO.loc[I] = (SIGMA.loc[I] - 1) / SIGMA.loc[I]

        TESTA1.loc[F, I] = 0.0

        # TESTA1(F,I)      = R0(F,I) * RA0(F)*(1 + SUM(GF,TAUFX(GF,F,I)))*((FD0(F,I))**(1-RHO(I)));
        TESTA1.loc[F, I] = R0.loc[F, I].mul(RA0.loc[F], axis='index') * (1 + TAUFX_SUM.loc[F, I]) * (
                    FD0.loc[F, I] ** (1 - RHO.loc[I]))

        # TESTA2(F,I)      = SUM(F1, R0(F1,I) * RA0(F1) * (1 + SUM(GF,TAUFX(GF,F1,I)))*((FD0(F1,I))**(1-RHO(I))));
        TESTA2_pre = (R0.loc[F, I].mul(RA0.loc[F], axis='index') * (1 + TAUFX_SUM.loc[F, I]) * (
                    FD0.loc[F, I] ** (1 - RHO.loc[I]))).sum(0)
        TESTA2.loc[F, I] = 1
        TESTA2.loc[F, I] = TESTA2.loc[F, I] * TESTA2_pre

        TESTA3.loc[F, I] = TESTA1.loc[F, I] / TESTA2.loc[F, I]

        ALPHA.loc[F, I] = TESTA3.loc[F, I]

        # add THETA to make FDEQ work
        THETA = ALPHA.where(ALPHA == 0, 1)

        ATEST1 = pd.Series(index=I, dtype=float).fillna(0.0)
        ATEST1.loc[I] = ALPHA.loc[F, I].sum(0)

        # GAMMA(I)    = DS0(I) / ( SUM(F, ALPHA(F,I) *  FD0(F,I)) ** ( RHO(I) ) ) ** ( 1 / RHO(I) );
        GAMMA.loc[I] = DS0.loc[I] / (((ALPHA.loc[F, I] * FD0.loc[F, I] ** (RHO.loc[I])).sum(0)) ** (1 / RHO.loc[I]))

        # OTHER DATA
        # HH INVESTMENT INCOME FROM ROW
        PRIVRET.loc[H] = SAM.loc[Z, H].sum(0) - (SAM.loc[H, F].sum(1) + SAM.loc[H, CM].sum(1) + SAM.loc[H, GX].sum(1))

        PRIVRET.loc[H] = PRIVRET.loc[H] / HH0.loc[H]

        # TOTAL OUTPUT
        Y0.loc[F] = SAM.loc[F, IG].sum(1)

        KPFOR01.loc[K] = SAM.loc[K, ["ROW"]].sum(1)

        # NOMINAL CAPITAL OUTFLOW
        KPFOR0[K] = SAM.loc[Z, K].sum(0).T - SAM.loc[K, IG].sum(1)

        # NOMINAL GOVERNMENT OUTFLOWS
        GVFOR0.loc[G] = SAM.loc[G, ["ROW"]].sum(1)

        '''
        GVFOR0.loc[GT] = SAM.loc[Z, GT].sum(0) - (
                SAM.loc[GT, I].sum(1)
                + SAM.loc[GT, F].sum(1)
                + SAM.loc[GT, H].sum(1)
                + SAM.loc[GT, G].sum(1)
                )
        '''
        # original:
        # A.loc[H, L] = SAM.loc[H, L].div(HW0.loc[H], axis='index') / (
        #        Y0.loc[L] + SAM.loc[Z, L].sum(0) - SAM.loc[L, IG].sum(1)) * (1.0 - TAUFL.loc[G, L].sum(0))
        A.loc[H, L] = SAM.loc[H, L].div(HW0.loc[H], axis='index') / (Y0.loc[L] + SAM.loc[L, ["ROW"]].sum(1)) * (
                    1.0 - TAUFL.loc[G, L].sum(0))

        A.loc[H, K] = SAM.loc[H, K].div(HW0.loc[H], axis='index') / (
                    Y0.loc[K] + SAM.loc[Z, K].sum(0) - SAM.loc[K, IG].sum(1))

        # HH TAXES OTHER THAN PIT
        TAUH.loc[GH, H] = SAM.loc[GH, H].div(HH0.loc[H], axis='columns')

        TAUH0.loc[GH, H] = SAM.loc[GH, H] / HH0.loc[H]

        S0.loc[H] = SAM.loc[["INVES"], H].T.sum(1)

        YD0.loc[H] = SAM.loc[I, H].sum(0).T + S0.loc[H]

        Y0.loc[G] = SAM.loc[G, Z].sum(1) - SAM.loc[G, ["ROW"]].sum(1)

        S0.loc[G] = SAM.loc[["INVES"], G].sum(0)

        CMI0.loc[L] = EMPLOY.loc[IG, L].sum(0) - (JOBCOR.loc[H, L].mul(HW0.loc[H], axis='index')).sum(0)

        # AVERAGE WAGE FLOWING INTO
        CMOWAGE.loc[CM] = SAM.loc[CM, ["ROW"]].sum(1).div(CMO0.loc[CM], axis='index').fillna(0.0)

        # AVERAGE WAGES FLOWING OUT OF Robeson
        CMIWAGE.loc[L] = (-1) * (SAM.loc[L, ["ROW"]].sum(1).div(CMI0.loc[L], axis='index').fillna(0.0))

        # PROPORTION OF CAPITAL INCOME OUTFLOW
        KFOR.loc[K] = KPFOR0.loc[K] / SAM.loc[["KAP"], IG].sum(1)

        # PROPORTION OF GOVERNMENT INCOME OUTFLOW
        GFOR.loc[G] = GVFOR0.loc[G] / Y0.loc[G]

        A.loc[H, CM] = SAM.loc[H, CM] / SAM.loc[Z, CM].sum(0)

        # NOMINAL NET CAPITAL INFLOW
        NKI0 = (M0.loc[I] * PWM0.loc[I]).sum(0) - (CX0.loc[I] * PD0.loc[I]).sum(0) - \
               (PRIVRET.loc[H] * HH0.loc[H]).sum(0) - KPFOR0.loc[K].sum(0) - GVFOR0.loc[G].sum(0) - \
               (CMOWAGE.loc[CM] * CMO0.loc[CM]).sum(0) + \
               (CMIWAGE.loc[L] * CMI0.loc[L]).sum(0)

        # REAL HH NET INCOME
        Y0.loc[H] = (A.loc[H, L].mul(HW0[H], axis='index').div(A.loc[H, L].mul(HW0[H], axis='index').sum(0),
                                                               axis='columns') \
                     .mul(Y0.loc[L] - (CMIWAGE.loc[L] * CMI0.loc[L]), axis='columns').mul(1.0 - TAUFL.loc[G, L].sum(0),
                                                                                          axis='columns')).sum(1) \
                    + (A.loc[H, CM].mul((CMOWAGE.loc[CM] * CMO0.loc[CM]), axis='columns')).sum(1) \
                    + (A.loc[H, K].mul(HW0[H], axis='index') / A.loc[H, K].mul(HW0[H], axis='index').sum(0) \
                       * (Y0[K] * (1.0 - TAUFK.loc[G, K].sum(0)) + KPFOR0.loc[K])).sum(1)

        # PERSONAL INCOME OBJECTIVE FUNCTION
        SPI0 = (Y0.loc[H].sum(0) +
                TP.loc[H, G].mul(HH0.loc[H], axis='index').sum(1).sum(0) +
                (PRIVRET[H] * HH0[H]).sum(0))

        # PERSONAL INCOME TAX
        PIT.loc[GI, H] = SAM.loc[GI, H].div(Y0[H], axis='columns')
        PIT0.loc[GI, H] = SAM.loc[GI, H].div(Y0[H], axis='columns')

        MI0.loc[H] = HH0.loc[H] * 0.04

        MO0.loc[H] = HH0.loc[H] * 0.04

        GCP0 = CH0.loc[I, H].sum(1).sum(0) + CN0.loc[I].sum(0) + CG0.loc[I, GN].sum(1).sum(0) + CX0.loc[I].sum(0) - \
               M0.loc[I].sum(0)

        GCP10.loc[I] = CH0.loc[I, H].sum(1) + CN0.loc[I] + CG0.loc[I, GN].sum(1) + CX0.loc[I] - M0.loc[I]

        ###########################################
        # VARIABLE DECLARATION
        ###########################################

        vars = VarContainer()

        # PUBLIC CONSUMPTION
        CG = vars.add('CG', rows=I, cols=G)

        # PRIVATE CONSUMPTION
        CH = vars.add('CH', rows=I, cols=H)

        # GROSS INVESTMENT BY SECTOR OF SOURCE
        CN = vars.add('CN', rows=I)

        # CONSUMER PRICE INDEX
        CPI = vars.add('CPI', rows=H)

        # NONHOUSING CONSUMER PRICE INDEX
        CPIN = vars.add('CPIN', rows=H)

        # NONHOUSING CONSUMER PRICE INDEX
        CPIH = vars.add('CPIH', rows=H)

        # EXPORT DEMAND
        CX = vars.add('CX', rows=I)

        # DOMESTIC SHARE OF DOMESTIC DEMAND
        D = vars.add('D', rows=I)

        # DOMESTIC DEMAND
        DD = vars.add('DD', rows=I)

        # DOMESTIC SUPPLY
        DS = vars.add('DS', rows=I)

        # SECTORAL FACTOR DEMAND
        FD = vars.add('FD', rows=F, cols=Z)

        # GROSS AGGREGATE CITY PRODUCT
        GCP = vars.add('GCP')

        # GROSS CITY PRODUCT BY SECTOR
        GCP1 = vars.add('GCP1', rows=I)

        # NUMBER OF HOUSEHOLDS
        HH = vars.add('HH', rows=H)

        # NUMBER OF NONWORKING HOUSEHOLDS
        HN = vars.add('HN', rows=H)

        # NUMBER OF WORKING HOUSEHOLDS
        HW = vars.add('HW', rows=H)

        # INTER GOVERNMENTAL TRANSFERS
        IGT = vars.add('IGT', rows=G, cols=GX)

        # CAPITAL FLOW
        KS = vars.add('KS', rows=K, cols=IG)

        # LAND FLOW
        # LAS = vars.add('LAS', rows=LA, cols=IG)

        # IMPORTS
        M = vars.add('M', rows=I)

        # GROSS INVESTMENT BY SECTOR OF DESTINATION
        N = vars.add('N', rows=K, cols=IG)

        # NET CAPITAL INFLOW
        NKI = vars.add('NKI')

        # LAND OUTFLOW
        # LNFOR = vars.add('LNFOR', rows=LA)

        # CAPITAL OUTFLOW
        KPFOR = vars.add('KPFOR', rows=K)

        # GOVT OUTFLOW
        GVFOR = vars.add('GVFOR', rows=G)

        # AGGREGATE DOMESTIC PRICE PAID BY PURCHASERS
        P = vars.add('P', rows=I)

        # DOMESTIC PRICE RECEIVED BY SUPPLIERS
        PD = vars.add('PD', rows=I)

        # VALUE ADDED PRICE
        PVA = vars.add('PVA', rows=I)

        # ECONOMY WIDE SCALAR RENTAL RATES OF FACTORS
        RA = vars.add('RA', rows=F)

        # SECTORAL RENTAL RATES
        R = vars.add('R', rows=F, cols=Z)

        # SAVINGS
        S = vars.add('S', rows=Z)

        # PERSONAL INCOME (OBJECTIVE FUNCTION)
        SPI = vars.add('SPI')

        # INTERMEDIATE GOODS
        V = vars.add('V', rows=I)

        # GROSS INCOMES
        Y = vars.add('Y', rows=Z)

        # AFTER TAX TOTAL HOUSEHOLD INCOMES
        YD = vars.add('YD', rows=H)

        # OUT COMMUTERS
        CMO = vars.add('CMO', rows=CM)

        # IN COMMUTERS
        CMI = vars.add('CMI', rows=L)

        ###########################################
        # INITIALIZE VARIABLES FOR SOLVER
        ###########################################

        vars.init('CG', CG0.loc[I, G])
        vars.init('CH', CH0.loc[I, H])
        vars.init('CN', CN0.loc[I])
        vars.init('CPI', CPI0.loc[H])
        vars.init('CPIN', CPIN0.loc[H])
        vars.init('CPIH', CPIH0.loc[H])
        vars.init('CX', CX0.loc[I])
        vars.init('D', D0.loc[I])
        vars.init('DD', DD0.loc[I])
        vars.init('DS', DS0.loc[I])
        vars.init('FD', FD0.loc[F, Z])
        vars.init('GCP', GCP0)
        vars.init('GCP1', GCP10.loc[I])
        vars.init('HH', HH0.loc[H])
        vars.init('HN', HN0.loc[H])
        vars.init('HW', HW0.loc[H])
        vars.init('IGT', IGT0.loc[G, GX])
        vars.init('KS', KS0.loc[K, IG])
        # vars.init('LAS', LAS0.loc[LA, IG])
        vars.init('M', M0.loc[I])
        vars.init('N', N0.loc[K, IG])
        vars.init('NKI', NKI0)
        # vars.init('LNFOR', LNFOR0.loc[LA])
        vars.init('KPFOR', KPFOR0.loc[K])
        vars.init('GVFOR', GVFOR0.loc[G])
        vars.init('P', P0.loc[I])
        vars.init('PD', PD0.loc[I])
        vars.init('PVA', PVA0.loc[I])
        vars.init('RA', RA0.loc[F])
        vars.init('R', R0.loc[F, Z])
        vars.init('S', S0.loc[Z])
        vars.init('SPI', SPI0)
        vars.init('V', V0.loc[I])
        vars.init('Y', Y0.loc[Z])
        vars.init('YD', YD0.loc[H])
        vars.init('CMO', CMO0.loc[CM])
        vars.init('CMI', CMI0.loc[L])

        # -------------------------------------------------------------------------------------------------------------
        # DEFINE BOUNDS FOR VARIABLES
        # -------------------------------------------------------------------------------------------------------------

        vars.lo('P', vars.get('P') / 1000)
        vars.up('P', vars.get('P') * 1000)
        vars.lo('PD', vars.get('PD') / 1000)
        vars.up('PD', vars.get('PD') * 1000)
        vars.lo('PVA', vars.get('PVA') / 1000)
        vars.up('PVA', vars.get('PVA') * 1000)
        vars.lo('RA', vars.get('RA') / 1000)
        vars.up('RA', vars.get('RA') * 1000)
        vars.lo('CPI', vars.get('CPI') / 1000)
        vars.up('CPI', vars.get('CPI') * 1000)
        vars.lo('DS', vars.get('DS') / 1000)
        vars.up('DS', vars.get('DS') * 1000)
        vars.lo('DD', vars.get('DD') / 1000)
        vars.up('DD', vars.get('DD') * 1000)
        vars.lo('D', vars.get('D') / 1000)
        vars.up('D', vars.get('D') * 1000)
        vars.lo('V', vars.get('V') / 1000)
        vars.up('V', vars.get('V') * 1000)
        vars.lo('FD', vars.get('FD') / 1000)
        vars.up('FD', vars.get('FD') * 1000)
        vars.lo('HH', vars.get('HH') / 1000)
        vars.up('HH', vars.get('HH') * 1000)
        vars.lo('HW', vars.get('HW') / 1000)
        vars.up('HW', vars.get('HW') * 1000)
        vars.lo('HN', vars.get('HN') / 1000)
        vars.up('HN', vars.get('HN') * 1000)
        vars.lo('KS', vars.get('KS') / 1000)
        vars.up('KS', vars.get('KS') * 1000)
        # vars.lo('LAS',vars.get('LAS')/1000); vars.up('LAS',vars.get('LAS')*1000)
        vars.lo('M', vars.get('M') / 1000)
        vars.up('M', vars.get('M') * 1000)
        vars.lo('Y', vars.get('Y') / 1000)
        vars.up('Y', vars.get('Y') * 1000)
        vars.lo('YD', vars.get('YD') / 1000)
        vars.up('YD', vars.get('YD') * 1000)
        vars.lo('CH', vars.get('CH') / 1000)
        vars.up('CH', vars.get('CH') * 1000)
        vars.lo('CG', vars.get('CG') / 1000)
        vars.up('CG', vars.get('CG') * 1000)
        vars.lo('CX', vars.get('CX') / 1000)
        vars.up('CX', vars.get('CX') * 1000)
        vars.lo('R', vars.get('R') / 1000)
        vars.up('R', vars.get('R') * 1000)
        vars.lo('CMI', vars.get('CMI') / 1000)
        vars.up('CMI', vars.get('CMI') * 1000)
        vars.lo('CMO', vars.get('CMO') / 1000)
        vars.up('CMO', vars.get('CMO') * 1000)
        vars.lo('N', 0)
        vars.lo('CN', 0)

        def set_variable(filname):

            # clear the file before write the variables
            with open(filename, 'w') as f:
                f.write("")

            vars.write(filename)

        # -------------------------------------------------------------------------------------------------------------
        # DEFINE EQUATIONS AND SET CONDITIONS
        # -------------------------------------------------------------------------------------------------------------

        def set_equation(filename):

            count = [0]

            #   CPIEQ(H)..
            #   CPI(H)=E=
            #   SUM(I, P(I) * ( 1 + SUM(GS, TAUC(GS,I) ) ) * CH(I,H) )
            #       / SUM(I, P0(I) * ( 1 + SUM(GS, TAUQ(GS,I) ) ) * CH(I,H) );
            print('CPIEQ(H)')
            line1 = (P.loc(I) * ExprM(vars, m=1 + TAUC.loc[GS, I].sum(0)) * CH.loc(I, H)).sum(I)
            line2 = (ExprM(vars, m=P0.loc[I] * (1 + TAUQ.loc[GS, I].sum(0))) * CH.loc(I, H)).sum(I)

            CPIEQ = (line1 / line2 - ~CPI.loc(H))
            print(CPIEQ.test(vars.initialVals))
            CPIEQ.write(count, filename)

            # YEQ(H).. Y(H) =E= SUM(L,  A(H,L) * HW(H) / SUM(H1, A(H1,L) * HW(H1) ) * (Y(L)-(CMIWAGE(L)*CMI(L))) * ( 1 - SUM(G, TAUFL(G,L))))
            #                + SUM(CM, A(H,CM)*(CMOWAGE(CM)*CMO(CM)))
            #                + SUM(K,  A(H,K) * HW(H) / SUM(H1, A(H1,K) * HW(H1)) * (Y(K) + KPFOR(K)) * ( 1 - SUM(G, TAUFK(G,K) ) ) ) ;
            print('YEQ(H)')
            line1 = (ExprM(vars, m=A.loc[H, L]) * HW.loc(H) / (ExprM(vars, m=A.loc[H1, L]) * HW.loc(H1)).sum(H1) * (
                        Y.loc(L) - ExprM(vars, m=CMIWAGE.loc[L]) * CMI.loc(L)) * ExprM(vars, m=1 - TAUFL.loc[G, L].sum(
                0))).sum(L)
            line2 = (ExprM(vars, m=A.loc[H, CM] * CMOWAGE.loc[CM]) * CMO.loc(CM)).sum(CM)
            # line3 = (ExprM(vars, m= A.loc[H,LA]) * HW.loc(H) / (ExprM(vars, m= A.loc[H1,LA]) * HW.loc(H1)).sum(H1) * ExprM(vars, m= 1 - TAUFLA.loc[G,LA].sum(0))).sum(LA)
            line4 = (ExprM(vars, m=A.loc[H, K]) * HW.loc(H) / (ExprM(vars, m=A.loc[H1, K]) * HW.loc(H1)).sum(H1) * (
                        Y.loc(K) + KPFOR.loc(K)) * ExprM(vars, m=1 - TAUFK.loc[G, K].sum(0))).sum(K)

            YEQ = ((line1 + line2 + line4) - Y.loc(H))
            print(YEQ.test(vars.initialVals))
            YEQ.write(count, filename)
            # print(YEQ)

            #  YDEQ(H).. YD(H)          =E=   Y(H) + (PRIVRET(H) * HH(H))
            #                                         + SUM(G, TP(H,G) * HH(H))
            #                                         - SUM(GI, PIT0(GI,H)  * Y(H))
            #                                         - SUM(G, TAUH(G,H)  * HH(H));
            print('YDEQ(H)')
            line1 = Y.loc(H) + ExprM(vars, m=PRIVRET.loc[H]) * HH.loc(H)
            line2 = (ExprM(vars, m=TP.loc[H, G]) * HH.loc(H)).sum(G)
            line3 = ~(ExprM(vars, m=PIT0.loc[GI, H]) * Y.loc(H)).sum(GI)
            line4 = ~(ExprM(vars, m=TAUH.loc[G, H]) * HH.loc(H)).sum(G)

            YDEQ = ((line1 + line2 - line3 - line4) - YD.loc(H))
            YDEQ.write(count, filename)
            print(YDEQ.test(vars.initialVals))
            # print(YDEQ)

            #  CHEQ(I,H).. CH(I,H)      =E= CH0(I,H)* ((YD(H) / YD0(H)) / ( CPI(H) / CPI0(H)))**(BETA(I,H))
            #                                 * PROD(J, ((P(J)*( 1 + SUM(GS, TAUC(GS,J))))/ (P0(J)*(1 + SUM(GS, TAUQ(GS,J)))))** (LAMBDA(J,I)));
            print('CHEQ(I,H)')
            line1 = ExprM(vars, m=CH0.loc[I, H]) * (
                        (YD.loc(H) / ExprM(vars, m=YD0.loc[H])) / (CPI.loc(H) / ExprM(vars, m=CPI0.loc[H]))) ** ExprM(
                vars, m=BETA.loc[I, H])
            line2 = (((P.loc(J) * ExprM(vars, m=1 + TAUC.loc[GS, J].sum(0))) / (
                        ExprM(vars, m=P0.loc[J]) * ExprM(vars, m=1 + TAUQ.loc[GS, J].sum(0)))) ** ExprM(vars,
                                                                                                        m=LAMBDA.loc[
                                                                                                            J, I])).prod(
                0)

            CHEQ = ((line1 * line2) - CH.loc(I, H))
            CHEQ.write(count, filename)
            print(CHEQ.test(vars.initialVals))
            # print(CHEQ)

            #  SHEQ(H).. S(H)           =E= YD(H) - SUM(I, P(I) * CH(I,H) * ( 1 + SUM(GS, TAUC(GS,I))));
            print('SHEQ(H)')
            line = YD.loc(H) - ~((P.loc(I) * CH.loc(I, H) * ExprM(vars, m=1 + TAUC.loc[GS, I].sum(0))).sum(I))

            SHEQ = (line - S.loc(H))
            SHEQ.write(count, filename)
            print(SHEQ.test(vars.initialVals))
            # print(SHEQ)

            #  PVAEQ(I).. PVA(I)        =E= PD(I) - SUM(J, AD(J,I) * P(J) * (1 + SUM(GS, TAUQ(GS, J))));
            print('PVAEQ(I)')
            line = PD.loc(I) - ~(
                (ExprM(vars, m=AD.loc[J, I]) * P.loc(J) * ExprM(vars, m=1 + TAUQ.loc[GS, J].sum(0))).sum(0))

            PVAEQ = (line - PVA.loc(I))
            PVAEQ.write(count, filename)
            print(PVAEQ.test(vars.initialVals))
            # print(PVAEQ)

            # Cobb-Douglas production function

            #  PFEQ(I)..DS(I)           =E= DELTA(I)*PROD(F, (FD(F,I))**ALPHA(F,I));
            #  print('PFEQ(I)')
            #  line =  ExprM(vars, m =DELTA.loc[I]) *((FD.loc(F, I)) ** ExprM(vars, m = ALPHA.loc[F, I])).prod(F)

            #  PFEQ = (line - DS.loc(I))
            #  PFEQ.write(count,filename)
            # print(PFEQ)

            # CES production function
            # PFEQ(I)..DS(I) =E= GAMMA(I)*(SUM(F, ALPHA(F,I)*(FD(F,I)**(RHO(I)))))**(1/RHO(I));
            print('PFEQ(I)')
            line = ExprM(vars, m=GAMMA.loc[I]) * (
                (ExprM(vars, m=ALPHA.loc[F, I]) * (FD.loc(F, I) ** ExprM(vars, m=RHO.loc[I]))).sum(F)) ** ExprM(vars,
                                                                                                                m=1 /
                                                                                                                  RHO.loc[
                                                                                                                      I])

            PFEQ = (line - DS.loc(I))
            PFEQ.write(count, filename)
            print(PFEQ.test(vars.initialVals))
            # print(PFEQ)

            # Cobb-Douglas factor demand function
            # FDEQ(F,I).. R(F,I) * RA(F) * (1 + SUM(GF,TAUFX(GF,F,I) ) )* (FD(F,I))
            #                         =E= PVA(I) * DS(I) * ALPHA(F,I);
            #  print('FDEQ(F,I)')
            #  left = R.loc(F,I) * RA.loc(F) * ExprM(vars, m = 1 + TAUFX_SUM.loc[F,I])* (FD.loc(F,I))
            #  right = ~(PVA.loc(I) * DS.loc(I) * ExprM(vars, m = ALPHA.loc[F, I]))

            #  FDEQ = (right - left)

            # FDEQ.test(vars.initialVals)
            #  FDEQ.write(count,filename)
            # print(FDEQ)

            # CES factor demand function
            # FDEQ(F,I).. (R(F,I) * RA(F)*(1 + SUM(GF,TAUFX(GF,F,I))))* (FD(F,I)**(1-RHO(I)))
            #               =E= PVA(I)* ALPHA(F,I)*(GAMMA(I)**RHO(I))*(DS(I)**(1-RHO(I)));
            print('FDEQ(F,I)')
            left = (R.loc(F, I) * RA.loc(F) * ExprM(vars, m=1 + TAUFX_SUM.loc[F, I])) * (
                        FD.loc(F, I) ** ExprM(vars, m=1 - RHO.loc[I]))
            right = ~(PVA.loc(I) * (ExprM(vars, m=ALPHA.loc[F, I] * (GAMMA.loc[I] ** RHO.loc[I])) * (
                        DS.loc(I) ** ExprM(vars, m=1 - RHO.loc[I]))))
            FDEQ = (right - left)
            FDEQ.setCondition(FD0.loc[F, I], 'INEQ', 0)

            # FDEQ.test(vars.initialVals)
            FDEQ.write(count, filename)
            print(FDEQ.test(vars.initialVals))
            # print(FDEQ)

            #   VEQ(I).. V(I) =E= SUM(J, AD(I,J) * DS(J) );
            print('VEQ(I)')
            line = (ExprM(vars, m=AD.loc[I, J]) * ~DS.loc(J)).sum(1)

            VEQ = (line - V.loc(I))
            VEQ.write(count, filename)
            print(VEQ.test(vars.initialVals))
            # print(VEQ)

            #   YFEQL(F).. Y(F) =E= SUM(IG, R(F,IG)* RA(F)*FD(F,IG));
            print('YFEQL(F)')
            line = (R.loc(F, IG) * RA.loc(F) * FD.loc(F, IG)).sum(IG)

            YFEQL = (line - Y.loc(F))
            YFEQL.write(count, filename)
            print(YFEQL.test(vars.initialVals))
            # print(YFEQL)

            # YFEQK(K).. Y('KAP') =E= SUM(IG, R('KAP',IG) * RA('KAP') * FD('KAP',IG));
            print('YFEQK(K)')
            line = (R.loc(['KAP'], IG) * RA.loc(['KAP']) * FD.loc(['KAP'], IG)).sum(IG)

            YFEQK = (line - Y.loc(['KAP']))
            YFEQK.write(count, filename)
            print(YFEQK.test(vars.initialVals))
            # print(YFEQK)

            #  YFEQLA(LA).. Y('LAND')   =E= SUM(IG, R('LAND',IG) * RA('LAND') * FD('LAND',IG));
            #  print('YFEQLA(LA)')
            #  line = (R.loc(['LAND'],IG) * RA.loc(['LAND']) * FD.loc(['LAND'],IG)).sum(IG)

            #  YFEQLA = (line - Y.loc(['LAND']))
            #  YFEQLA.write(count,filename)
            #  print(YFEQLA.test(vars.initialVals))
            # print(YFEQLA)

            #  LANFOR(LA).. LNFOR(LA)   =E= LFOR(LA) * Y(LA);
            #  print('LANFOR(LA)')
            #  line = ExprM(vars, m = LFOR.loc[LA])*Y.loc(LA)

            #  LANFOR = (line - LNFOR.loc(LA))
            #  LANFOR.write(count,filename)
            #  print(LANFOR.test(vars.initialVals))
            # print(LANFOR)

            #  KAPFOR(K).. KPFOR(K)     =E= KFOR(K) * Y(K);
            print('KAPFOR(K)')
            line = ExprM(vars, m=KFOR.loc[K]) * Y.loc(K)

            KAPFOR = (line - KPFOR.loc(K))
            KAPFOR.write(count, filename)
            print(KAPFOR.test(vars.initialVals))
            # print(KAPFOR)

            # XEQ(I).. CX(I) =E= CX0(I)*( (PD(I)*(1+SUM(GS,TAUX(GS,I))))
            #                  /(PW0(I)*(1+SUM(GS,TAUQ(GS,I))))) **(ETAE(I));
            print('XEQ(I)')
            line = ExprM(vars, m=CX0.loc[I]) * ((PD.loc(I) * ExprM(vars, m=1 + TAUX.loc[GS, I].sum(0))) / ExprM(vars, m=
            PW0.loc[I] * (1 + TAUQ.loc[GS, I].sum(0)))) ** ExprM(vars, m=ETAE.loc[I])

            XEQ = (line - CX.loc(I))
            XEQ.write(count, filename)
            print(XEQ.test(vars.initialVals))
            # print(XEQ)

            #  DEQ(I)$PWM0(I).. D(I)    =E= D0(I) *(PD(I)/PWM0(I))**(ETAD(I)*0.1);
            print('DEQ(I)$PWM0(I)')
            line = ExprM(vars, m=D0.loc[I]) * (PD.loc(I) / ExprM(vars, m=PWM0.loc[I])) ** ExprM(vars,
                                                                                                m=ETAD.loc[I] * 0.1)

            DEQ = (line - D.loc(I))
            #  DEQ.setCondition(PWM0.loc[I])
            DEQ.write(count, filename)
            print(DEQ.test(vars.initialVals))
            # print(DEQ)

            #  PEQ(I)..  P(I)           =E= D(I) * PD(I) + ( 1 - D(I) ) * PWM0(I);
            print('PEQ(I)')
            line = (D.loc(I) * PD.loc(I) + (1 - D.loc(I)) * ExprM(vars, m=PWM0.loc[I]))

            PEQ = (line - P.loc(I))
            PEQ.write(count, filename)
            print(PEQ.test(vars.initialVals))
            # print(PEQ)

            #  MEQ(I).. M(I)            =E= ( 1 - D(I) ) * DD(I);
            print('MEQ(I)')
            line = (1 - D.loc(I)) * DD.loc(I)

            MEQ = (line - M.loc(I))
            MEQ.write(count, filename)
            print(MEQ.test(vars.initialVals))
            # print(MEQ)

            #  NKIEQ.. NKI              =E= SUM(I, M(I) * PWM0(I) )
            #                                 - SUM(I, CX(I) * PD(I) )
            #                                 - SUM(H, PRIVRET(H)*HH(H))
            #                                 - SUM(K, KPFOR(K))
            #                                 - SUM(G, GVFOR(G))
            #                                 - SUM(CM,CMOWAGE(CM)*CMO(CM))
            #                                 + SUM(L,CMIWAGE(L)*CMI(L));

            print('NKIEQ')
            line1 = (M.loc(I) * ExprM(vars, m=PWM0.loc[I])).sum(I)
            line2 = (CX.loc(I) * PD.loc(I)).sum(I)
            line3 = (ExprM(vars, m=PRIVRET.loc[H]) * HH.loc(H)).sum(H)
            line5 = KPFOR.loc(K).sum(K)
            line6 = GVFOR.loc(G).sum(G)
            line7 = (ExprM(vars, m=CMOWAGE.loc[CM]) * CMO.loc(CM)).sum(CM)
            line8 = (ExprM(vars, m=CMIWAGE.loc[L]) * CMI.loc(L)).sum(L)

            NKIEQ = ((line1 - line2 - line3 - line5 - line6 - line7 + line8) - NKI)
            NKIEQ.write(count, filename)
            print(NKIEQ.test(vars.initialVals))
            # print(NKIEQ)

            #  NEQ(K,I).. N(K,I)        =E= N0(K,I)*(R(K,I)/R0(K,I))**(ETAIX(K,I)*0.1);
            print('NEQ(K,I)')
            line = ExprM(vars, m=N0.loc[K, I]) * (R.loc(K, I) / ExprM(vars, m=R0.loc[K, I])) ** ExprM(vars, m=ETAIX.loc[
                                                                                                                  K, I] * 0.1)

            NEQ = (line - N.loc(K, I))
            NEQ.write(count, filename)
            print(NEQ.test(vars.initialVals))
            # print(NEQ)

            #  CNEQ(I).. P(I)*(1 + SUM(GS, TAUN(GS,I)))*CN(I)
            #                         =E= SUM(IG, B(I,IG)*(SUM(K, N(K,IG))));
            print('CNEQ(I)')
            left = P.loc(I) * ExprM(vars, m=1 + TAUN.loc[GS, I].sum(0)) * CN.loc(I)
            right = (ExprM(vars, m=B.loc[I, IG]) * N.loc(K, IG).sum(K)).sum(IG)

            CNEQ = (right - left)
            CNEQ.write(count, filename)
            print(CNEQ.test(vars.initialVals))
            # print(CNEQ)

            #  KSEQ(K,IG).. KS(K,IG)    =E= KS0(K,IG) * ( 1 - DEPR) + N(K,IG) ;
            print('KSEQ(K,IG)')
            line = ExprM(vars, m=KS0.loc[K, IG] * (1 - DEPR)) + N.loc(K, IG)

            KSEQ = (line - KS.loc(K, IG))
            KSEQ.write(count, filename)
            print(KSEQ.test(vars.initialVals))
            # print(KSEQ)

            # LSEQ1(H).. HW(H)/HH(H)   =E= (HW0(H)/HH0(H))
            #                              *((SUM(L, RA(L) / RA0(L))/24)/ (CPI(H) / CPI0(H))*(SUM((Z,L), FD(L,Z))/(SUM(H1, HW(H1)* SUM(L, JOBCOR(H1,L)))+ SUM(CM, CMO(CM)) + SUM(L,CMI(L))))+ SUM((CM,L), EXWGEO(CM)/RA(L))/96 *(SUM(CM, CMO(CM))/(SUM(H1, HW(H1)* SUM(L,JOBCOR(H1,L)))+ SUM(CM, CMO(CM)) +SUM(L,CMI(L)))))** (ETARA(H))
            #                              * ( SUM(G, TP(H,G) / CPI(H) )/ SUM(G, TP(H,G) / CPI0(H) )) ** ETAPT(H)
            #                              *  ((SUM(GI, PIT0(GI,H)* HH0(H))+ SUM(G, TAUH(G,H)*HH0(H)))/(SUM(GI, PIT(GI,H)* HH(H))+ SUM(G, TAUH(G,H)*HH(H))))**(ETAPIT(H));
            print('LSEQ1(H)')
            line1 = ExprM(vars, m=HW0.loc[H] / HH0.loc[H])
            LSEQ1line2pre = FD.loc(L, Z).sum(1)
            line2 = (((RA.loc(L) / ExprM(vars, m=RA0.loc[L])).sum(L) / 8) / (CPI.loc(H) / ExprM(vars, m=CPI0[H])) \
                     * (LSEQ1line2pre.sum(0) / (
                                (HW.loc(H1) * ExprM(vars, m=JOBCOR.loc[H1, L].sum(1))).sum(H1) + CMO.loc(CM).sum(
                            CM) + CMI.loc(L).sum(L))) \
                     + ((ExprM(vars, m=EXWGEO.loc[CM].sum(0)) / RA.loc(L)).sum(0) / 32) \
                     * (CMO.loc(CM).sum(CM) / (
                                (HW.loc(H1) * ExprM(vars, m=JOBCOR.loc[H1, L].sum(1))).sum(H1) + CMO.loc(CM).sum(
                            CM) + CMI.loc(L).sum(L)))) \
                    ** (ExprM(vars, m=ETARA.loc[H]) * 0.1)
            line3 = ((ExprM(vars, m=TP.loc[H, G]) / CPI.loc(H)).sum(G) / (
                        ExprM(vars, m=TP.loc[H, G]) / ExprM(vars, m=CPI0.loc[H])).sum(G)) ** ExprM(vars, m=ETAPT.loc[H])
            line4 = (((ExprM(vars, m=PIT0.loc[GI, H]) * ExprM(vars, m=HH0.loc[H])).sum(GI) + (
                        ExprM(vars, m=TAUH0.loc[G, H]) * ExprM(vars, m=HH0.loc[H])).sum(G)) \
                     / ((ExprM(vars, m=PIT.loc[GI, H]) * HH.loc(H)).sum(GI) + (
                                ExprM(vars, m=TAUH.loc[G, H]) * HH.loc(H)).sum(G))) ** ExprM(vars, m=ETAPIT.loc[H])

            LSEQ1 = ((line1 * line2 * line3 * line4) - HW.loc(H) / HH.loc(H))
            LSEQ1.write(count, filename)
            print(LSEQ1.test(vars.initialVals))
            # print(LSEQ1)

            # LSEQ2A('OUT1').. CMO('OUT1')=E= CMO0('OUT1')* (((EXWGEO('OUT1') /RA('L1WA') ))** ECOMO('OUT1'));
            print('LSEQ2A')
            line = ExprM(vars, m=CMO0.loc[CM1]) * (
                        (ExprM(vars, m=EXWGEO.loc[CM1].sum(0)) / RA.loc(FW1)) ** (ExprM(vars, m=ECOMO.loc[CM1])))

            LSEQ2A = (line - CMO.loc(CM1))
            LSEQ2A.write(count, filename)
            print(LSEQ2A.test(vars.initialVals))
            # print(LSEQ2A)

            # LSEQ2B('OUT2').. CMO('OUT2')=E= CMO0('OUT2')* (((EXWGEO('OUT2') /RA('L2WA') ))** ECOMO('OUT2'));
            print('LSEQ2B')
            line = ExprM(vars, m=CMO0.loc[CM2]) * (
                        (ExprM(vars, m=EXWGEO.loc[CM2].sum(0)) / RA.loc(FW2)) ** (ExprM(vars, m=ECOMO.loc[CM2])))

            LSEQ2B = (line - CMO.loc(CM2))
            LSEQ2B.write(count, filename)
            print(LSEQ2B.test(vars.initialVals))
            # print(LSEQ2B)

            # LSEQ2C('OUT3').. CMO('OUT3')=E= CMO0('OUT3')* (((EXWGEO('OUT3') /RA('L3WA') ))** ECOMO('OUT3'));
            print('LSEQ2C')
            line = ExprM(vars, m=CMO0.loc[CM3]) * (
                        (ExprM(vars, m=EXWGEO.loc[CM3].sum(0)) / RA.loc(FW3)) ** (ExprM(vars, m=ECOMO.loc[CM3])))

            LSEQ2C = (line - CMO.loc(CM3))
            LSEQ2C.write(count, filename)
            print(LSEQ2C.test(vars.initialVals))
            # print(LSEQ2C)

            # LSEQ2D('OUT4').. CMO('OUT4')=E= CMO0('OUT4')* (((EXWGEO('OUT4') /RA('L4WA') ))** ECOMO('OUT4'));
            print('LSEQ2D')
            line = ExprM(vars, m=CMO0.loc[CM4]) * (
                        (ExprM(vars, m=EXWGEO.loc[CM4].sum(0)) / RA.loc(FW4)) ** (ExprM(vars, m=ECOMO.loc[CM4])))

            LSEQ2D = (line - CMO.loc(CM4))
            LSEQ2D.write(count, filename)
            print(LSEQ2D.test(vars.initialVals))
            # print(LSEQ2D)

            # LSEQ3(L).. CMI(L)  =E= CMI0(L)* ((( RA(L)/(SUM( H, CPI(H))/30))** ECOMI(L)));
            print('LSEQ3')
            line = ExprM(vars, m=CMI0.loc[L]) * ((RA.loc(L) / (CPI.loc(H).sum(H) / 8)) ** (ExprM(vars, m=ECOMI.loc[L])))

            LSEQ3 = (line - CMI.loc(L))
            LSEQ3.write(count, filename)
            print(LSEQ3.test(vars.initialVals))
            # print(LSEQ3)

            #  LASEQ1(LA,I).. LAS(LA,I) =E= LAS0(LA,I)*(R(LA, I)/R0(LA, I))**(ETAL(LA,I));
            #  print('LASEQ1(LA,I)')
            #  line = ExprM(vars, m = LAS0.loc[LA, I]) * (R.loc(LA,I) / ExprM(vars, m = R0.loc[LA, I]))**ExprM(vars, m = ETAL.loc[LA,I])

            #  LASEQ1 = (line - LAS.loc(LA, I))
            #  LASEQ1.write(count,filename)
            #  print(LASEQ1.test(vars.initialVals))
            # print(LASEQ1)

            #  POPEQ(H).. HH(H)         =E= HH0(H) * NRPG(H)
            #                                + MI0(H) * ((YD(H)/HH(H))/(YD0(H)/HH0(H))/(CPI(H)/CPI0(H))) ** (ETAYD(H))
            #                                         *((HN(H)/HH(H))/(HN0(H)/HH0(H))) ** (ETAU(H))
            #                                - MO0(H) *((YD0(H)/HH0(H))/(YD(H)/HH(H))/(CPI0(H)/CPI(H))) ** (ETAYD(H))
            #                                         *((HN0(H)/HH0(H))/(HN(H)/HH(H))) ** (ETAU(H))  ;

            print('POPEQ(H)')
            line1 = ExprM(vars, m=HH0.loc[H] * NRPG.loc[H])
            line2 = ExprM(vars, m=MI0.loc[H]) * ((YD.loc(H) / HH.loc(H)) / ExprM(vars, m=YD0.loc[H] / HH0.loc[H]) / (
                        CPI.loc(H) / ExprM(vars, m=CPI0.loc[H]))) ** ExprM(vars, m=ETAYD.loc[H])
            line3 = ((HN.loc(H) / HH.loc(H)) / ExprM(vars, m=HN0.loc[H] / HH0.loc[H])) ** ExprM(vars, m=ETAU.loc[H])
            line4 = ExprM(vars, m=MO0.loc[H]) * (ExprM(vars, m=YD0.loc[H] / HH0.loc[H]) / (YD.loc(H) / HH.loc(H)) / (
                        ExprM(vars, m=CPI0.loc[H]) / CPI.loc(H))) ** ExprM(vars, m=ETAYD.loc[H])
            line5 = (ExprM(vars, m=HN0.loc[H] / HH0.loc[H]) / (HN.loc(H) / HH.loc(H))) ** ExprM(vars, m=ETAU.loc[H])

            POPEQ = (line1 + line2 * line3 - line4 * line5 - HH.loc(H))
            POPEQ.write(count, filename)
            print(POPEQ.test(vars.initialVals))
            # print(POPEQ)

            #  ANEQ(H).. HN(H)          =E= HH(H) - HW(H);
            print('ANEQ(H)')
            line = HH.loc(H) - HW.loc(H)

            ANEQ = (line - HN.loc(H))
            ANEQ.write(count, filename)
            print(ANEQ.test(vars.initialVals))
            # print(ANEQ)

            #  YGEQ(GX).. Y(GX)         =E=   SUM(I, TAUV(GX,I) * V(I) * P(I) )
            #                                 + SUM(I, TAUX(GX,I)* CX(I) *PD(I))
            #                                 + SUM((H,I), TAUC(GX,I) * CH(I,H) * P(I) )
            #                                 + SUM(I, TAUN(GX,I) * CN(I) * P(I) )
            #                                 + SUM((GN,I), TAUG(GX,I) * CG(I,GN) * P(I) )
            #                                 + SUM((F,I), TAUFX(GX,F,I) * RA(F) * R(F,I) * FD(F,I) )
            #                                 + SUM((F,GN), TAUFX(GX,F,GN) * RA(F) * R(F,GN) * FD(F,GN) )
            #                                 + SUM(F, TAUFH(GX,F) * (Y(F)))
            #                                 + SUM(H, PIT0(GX,H) * Y(H) )
            #                                 + SUM(H, TAUH(GX,H) * HH(H) )
            #                                 + SUM(GX1, IGT(GX,GX1));
            print('YGEQ')
            line1 = (ExprM(vars, m=TAUV.loc[GX, I]) * V.loc(I) * P.loc(I)).sum(I)
            line2 = (ExprM(vars, m=TAUX.loc[GX, I]) * CX.loc(I) * PD.loc(I)).sum(I)

            YGEQline3pre = ExprM(vars,
                                 m=pd.DataFrame(index=GX, columns=H).fillna(0.0))  # first just set it to correct size
            for label in GX:
                for hlabel in H:
                    YGEQline3pre.m[GX.index(label)][H.index(hlabel)] = Expr(
                        (ExprM(vars, m=TAUC.loc[[label], I]) * CH.loc(I, [hlabel]) * P.loc(I)).sum().m[0][0])

            line3 = YGEQline3pre.sum(1)
            line4 = (ExprM(vars, m=TAUN.loc[GX, I]) * CN.loc(I) * P.loc(I)).sum(I)

            YGEQline5pre = ExprM(vars, m=TAUG.loc[GX, I]).sum(I)  # first just set it to correct size
            for label in GX:
                YGEQline5pre.m[GX.index(label)][0] = Expr(
                    (ExprM(vars, m=TAUG.loc[[label], I]) * CG.loc(I, GN) * P.loc(I)).sum().m[0][0])
            line5 = YGEQline5pre

            line6 = ExprM(vars, m=TAUG.loc[GX, I]).sum(I)
            for label in GX:
                line6.m[GX.index(label)][0] = Expr(
                    (ExprM(vars, m=TAUFXgx[label].loc[F, I]) * RA.loc(F) * R.loc(F, I) * FD.loc(F, I)).sum().m[0][0])

            line7 = ExprM(vars, m=TAUG.loc[GX, I]).sum(I)
            for label in GX:
                line7.m[GX.index(label)][0] = Expr(
                    (ExprM(vars, m=TAUFXgx[label].loc[F, GN]) * RA.loc(F) * R.loc(F, GN) * FD.loc(F, GN)).sum().m[0][0])

            line8 = (ExprM(vars, m=TAUFH.loc[GX, F]) * Y.loc(F)).sum(F)
            line9 = (ExprM(vars, m=PIT0.loc[GX, H]) * Y.loc(H)).sum(H)
            line10 = (ExprM(vars, m=TAUH.loc[GX, H]) * HH.loc(H)).sum(H)
            line11 = IGT.loc(GX, GX1).sum(1)

            YGEQ = ((line1 + line2 + line3 + line4 + line5 + line6 + line7 + line8 + line9 + line10 + line11) - Y.loc(
                GX))
            YGEQ.write(count, filename)
            print(YGEQ.test(vars.initialVals))
            # print(YGEQ)

            #    YGEQ2(GT).. Y(GT)        =E= SUM(GX, IGT(GT,GX));
            print('YGEQ2')
            line = IGT.loc(GT, GX).sum(GX)
            YGEQ2 = (line - Y.loc(GT))
            YGEQ2.write(count, filename)
            print(YGEQ2.test(vars.initialVals))
            # print(YGEQ2)

            #  YGEQL(GNL).. Y(GNL)      =E= TAXS1(GNL)*Y('CYGF');
            print('YGEQL(GNL)')
            line = ExprM(vars, m=TAXS1.loc[GNL]) * Y.loc(['CYGF'])
            YGEQ1 = (line - Y.loc(GNL))
            YGEQ1.write(count, filename)
            print(YGEQ1.test(vars.initialVals))
            # print(YGEQ1)

            #  GOVFOR(G).. GVFOR(G)     =E= GFOR(G)*Y(G);
            print('GOVFOR(G)')
            line = ExprM(vars, m=GFOR.loc[G]) * Y.loc(G)

            GOVFOR = (line - GVFOR.loc(G))
            GOVFOR.write(count, filename)
            print(GOVFOR.test(vars.initialVals))
            # print(GOVFOR)

            #  CGEQ(I,GN).. P(I)*(1 + SUM(GS, TAUG(GS,I))) * CG(I,GN)
            #                         =E= AG(I,GN) * (Y(GN)+ GFOR(GN)*Y(GN));
            print('CGEQ(I,GN)')
            left = P.loc(I) * ExprM(vars, m=1 + TAUG.loc[GS, I].sum(0)) * CG.loc(I, GN)
            right = ExprM(vars, m=AG.loc[I, GN]) * (Y.loc(GN) + ExprM(vars, m=GFOR.loc[GN]) * Y.loc(GN))

            CGEQ = (right - left)
            CGEQ.write(count, filename)
            print(CGEQ.test(vars.initialVals))
            # print(CGEQ)

            #  GFEQ(F,GN)..  FD(F,GN) * R(F,GN) * RA(F)*( 1 + SUM(GF, TAUFX(GF,F,GN)))
            #                         =E= AG(F,GN) * (Y(GN)+ GFOR(GN)*Y(GN));
            print('GFEQ(F,GN)')
            left = FD.loc(F, GN) * R.loc(F, GN) * RA.loc(F) * (1 + ExprM(vars, m=TAUFX_SUM.loc[F, GN]))
            right = ExprM(vars, m=AG.loc[F, GN]) * (Y.loc(GN) + ExprM(vars, m=GFOR.loc[GN]) * Y.loc(GN))

            GFEQ = left - right
            GFEQ.write(count, filename)
            print(GFEQ.test(vars.initialVals))
            # print(GFEQ)

            #  GSEQL(GN).. S(GN)        =E= (Y(GN)+ GVFOR(GN))
            #                                 - SUM(I, CG(I,GN)*P(I)*(1 + SUM(GS, TAUG(GS,I))))
            #                                 - SUM(F, FD(F,GN)*R(F,GN)*RA(F)*(1 + SUM(GF, TAUFX(GF,F,GN))));
            print('GSEQL(GN)')
            line1 = Y.loc(GN) + GVFOR.loc(GN)
            line2 = (CG.loc(I, GN) * P.loc(I) * (1 + ExprM(vars, m=TAUG.loc[GS, I]).sum(GS))).sum(I)
            line3 = (FD.loc(F, GN) * R.loc(F, GN) * RA.loc(F) * (1 + ExprM(vars, m=TAUFX_SUM.loc[F, GN]))).sum(F)

            GSEQL = ((line1 - ~line2 - ~line3) - S.loc(GN))
            GSEQL.write(count, filename)
            print(GSEQL.test(vars.initialVals))
            # print(GSEQL)

            #  GSEQ(GX).. S(GX)         =E= (Y(GX) + GFOR(GX)*Y(GX)) - SUM(H, (TP(H,GX)*HH(H))) - SUM(G,IGT(G,GX));
            print('GSEQ(GX)')
            line1 = (Y.loc(GX) + ExprM(vars, m=GFOR.loc[GX]) * Y.loc(GX))
            line2 = (ExprM(vars, m=TP.loc[H, GX]) * HH.loc(H)).sum(H)
            line3 = IGT.loc(G, GX).sum(G)

            GSEQ = ((line1 - ~line2 - ~line3) - S.loc(GX))
            GSEQ.write(count, filename)
            print(GSEQ.test(vars.initialVals))
            # print(GSEQ)

            #  TDEQ(G,GX)$(IGTD(G,GX) EQ 1).. IGT(G,GX)
            #                         =E= TAXS(G,GX)*(Y(GX) + GVFOR(GX)- SUM(H, (TP(H,GX)*HH(H))));
            print('TDEQ(G,GX)$(IGTD(G,GX) EQ 1)')
            line = ExprM(vars, m=TAXS.loc[G, GX]) * (
                        Y.loc(GX) + GVFOR.loc(GX) - ~(ExprM(vars, m=TP.loc[H, GX]) * HH.loc(H)).sum(H))

            TDEQ = line - IGT.loc(G, GX)
            TDEQ.setCondition(IGTD.loc[G, GX], 'EQ', 1)
            TDEQ.write(count, filename)
            print(TDEQ.test(vars.initialVals))
            # print(TDEQ)

            #  SPIEQ.. SPI =E= SUM(H, Y(H)) + SUM((H,G), TP(H,G)*HH(H)) + SUM(H, PRIVRET(H)*HH(H));
            print('SPIEQ')
            line = Y.loc(H).sum(H) + (ExprM(vars, m=TP.loc[H, G]) * HH.loc(H)).sum() + (
                        ExprM(vars, m=PRIVRET.loc[H]) * HH.loc(H)).sum(H)

            SPIEQ = (line - SPI)
            SPIEQ.write(count, filename)
            print(SPIEQ.test(vars.initialVals))
            # print(SPIEQ)

            #  LMEQ1(L).. SUM(H, HW(H)* JOBCOR(H,L)) + CMI(L) =E= SUM(Z, FD(L,Z)));
            print('LMEQ1')
            left = (ExprM(vars, m=JOBCOR.loc[H, L]) * HW.loc(H)).sum(H) + CMI.loc(L)
            right = FD.loc(L, Z).sum(Z)
            # right = FD.loc(['L1'], Z).sum(Z) + CMO.loc(CM1).sum(CM1)

            LMEQ1 = (right - left)
            LMEQ1.write(count, filename)
            print(LMEQ1.test(vars.initialVals))
            # print(LMEQ1)

            #  KMEQ(K,IG).. KS(K,IG)    =E= FD(K,IG);
            print('KMEQ(K,IG)')
            KMEQ = (FD.loc(K, IG) - KS.loc(K, IG))
            KMEQ.write(count, filename)
            print(KMEQ.test(vars.initialVals))
            # print(KMEQ)

            #  LAMEQ(LA,IG).. LAS(LA,IG)=E= FD(LA,IG);
            #  print('LAMEQ(LA,IG)')
            #  LAMEQ = (FD.loc(LA, IG) - LAS.loc(LA, IG))
            #  LAMEQ.write(count,filename)
            #  print(LAMEQ.test(vars.initialVals))
            # print(LAMEQ)

            #  GMEQ(I).. DS(I)          =E= DD(I) + CX(I) - M(I);
            print('GMEQ(I)')
            GMEQ = (DD.loc(I) + CX.loc(I) - M.loc(I) - DS.loc(I))
            GMEQ.write(count, filename)
            print(GMEQ.test(vars.initialVals))
            # print(GMEQ)

            #  DDEQ(I).. DD(I)          =E= V(I) + SUM(H, CH(I,H) ) + SUM(G, CG(I,G) ) + CN(I);
            print('DDEQ(I)')
            DDEQ = (V.loc(I) + CH.loc(I, H).sum(H) + CG.loc(I, G).sum(G) + CN.loc(I) - DD.loc(I))
            DDEQ.write(count, filename)
            print(DDEQ.test(vars.initialVals))
            # print(DDEQ)

            # IGT.FX(G,GX)$(NOT IGT0(G,GX))=0;
            print('IGT.FX(G,GX)$(NOT IGT0(G,GX))=0')
            FX1 = IGT.loc(G, GX)
            FX1.setCondition(IGT0.loc[G, GX], 'EQ', 0)
            FX1.write(count, filename)
            # print(FX1)

            # IGT.FX(G,GX)$(IGTD(G,GX) EQ 2)=IGT0(G,GX);
            print('IGT.FX(G,GX)$(IGTD(G,GX) EQ 2)=IGT0(G,GX)')
            FX2 = IGT.loc(G, GX) - ExprM(vars, m=IGT0.loc[G, GX])
            FX2.setCondition(IGTD.loc[G, GX], 'EQ', 2)
            FX2.write(count, filename)
            # print(FX2)

            # R.FX(L,Z)=R0(L,Z);
            print('R.FX(L,Z)=R0(L,Z)')
            FX3 = R.loc(L, Z) - ExprM(vars, m=R0.loc[L, Z])
            FX3.write(count, filename)
            # print(FX3)

            '''
            #RA.FX(LA)=RA0(LA);
            print('RA.FX(LA)=RA0(LA)')
            FX4 = RA.loc(LA) - ExprM(vars, m = RA0.loc[LA])
            FX4.write(count,filename)
            # print(FX4)
            '''

            # RA.FX(K)=RA0(K);
            print('RA.FX(K)=RA0(K)')
            FX5 = RA.loc(K) - ExprM(vars, m=RA0.loc[K])
            FX5.write(count, filename)
            # print(FX5)

            print("Objective")
            obj = vars.getIndex('SPI')

            with open(filename, 'a') as f:
                f.write('model.obj = Objective(expr=-1*model.x' + str(obj) + ')')

        def run_solver(cons_filename, temp_file_name="tmp.py"):
            solver = 'ipopt'
            solver_io = 'nl'
            stream_solver = True  # True prints solver output to screen
            keepfiles = False  # True prints intermediate file names (.nl,.sol,...)

            executable_path = self.get_parameter("solver_path") \
                if self.get_parameter("solver_path") is not None else pyglobals.IPOPT_PATH
            if not os.path.exists(executable_path):
                print("Invalid executable path, please make sure you have Pyomo installed.")

            opt = SolverFactory(solver, solver_io=solver_io, executable=executable_path)

            if opt is None:
                print("")
                print("ERROR: Unable to create solver plugin for %s "
                      "using the %s interface" % (solver, solver_io))
                print("")
                exit(1)

            ### Create the model
            model = ConcreteModel()
            set_variable(cons_filename)
            set_equation(cons_filename)
            ###

            ### read the model
            exec(open(cons_filename).read())
            ###

            ### Declare all suffixes

            # Ipopt bound multipliers (obtained from solution)
            model.ipopt_zL_out = Suffix(direction=Suffix.IMPORT)
            model.ipopt_zU_out = Suffix(direction=Suffix.IMPORT)

            # Ipopt bound multipliers (sent to solver)
            model.ipopt_zL_in = Suffix(direction=Suffix.EXPORT)
            model.ipopt_zU_in = Suffix(direction=Suffix.EXPORT)

            # Obtain dual solutions from first solve and send to warm start
            model.dual = Suffix(direction=Suffix.IMPORT_EXPORT)

            # opt.options['halt_on_ampl_error'] = 'yes'
            # opt.options['acceptable_tol'] = '1e-3'
            # Send the model to ipopt and collect the solution
            # results = opt.solve(model,keepfiles=keepfiles,tee=stream_solver)

            # IMPORT / IMPORT_EXPORT Suffix components)
            # model.solutions.load_from(results)

            # Set Ipopt options for warm-start
            # The current values on the ipopt_zU_out and
            # ipopt_zL_out suffixes will be used as initial
            # conditions for the bound multipliers to solve
            # the new problem
            model.ipopt_zL_in.update(model.ipopt_zL_out)
            model.ipopt_zU_in.update(model.ipopt_zU_out)
            opt.options['warm_start_init_point'] = 'yes'
            opt.options['warm_start_bound_push'] = 1e-6
            opt.options['warm_start_mult_bound_push'] = 1e-6
            opt.options['mu_init'] = 1e-6
            # opt.options['acceptable_tol'] = 10
            # opt.options['max_iter'] = 15
            # opt.options['compl_inf_tol'] = 1e-3
            # opt.options['bound_relax_factor'] = 0
            # opt.options['start_with_resto'] = 'yes'
            # opt.options['acceptable_iter'] = 15
            # opt.options['halt_on_ampl_error'] = 'yes'
            # opt.options['fixed_variable_treatment'] = 'relax_bounds'
            # opt.options['print_options_documentation'] = 'yes'

            ###

            # Send the model and suffix information to ipopt and collect the solution
            # The solver plugin will scan the model for all active suffixes
            # valid for importing, which it will store into the results object

            results = opt.solve(model, keepfiles=keepfiles, tee=stream_solver)

            if results.solver.status == SolverStatus.ok and results.solver.termination_condition == TerminationCondition.optimal:

                x = [None for i in range(vars.nvars)]

                with open(temp_file_name, 'w') as f:
                    for i in range(vars.nvars):
                        f.write('x[' + str(i) + ']=value(model.x' + str(i) + ')\n')

                exec(open(temp_file_name).read())

                soln.append(x[:])

                return True
            elif results.solver.termination_condition == TerminationCondition.infeasible:
                print("Solution is not feasible.")
                return False
            else:
                print("Solver Status: ", results.solver.status)
                return False

        '''
        Calibrate the model 
        '''

        soln = []
        # TODO: I am not sure this is needed here. We might want to leave the python version
        # of the models out for now
        filename = "ipopt_cons.py"
        tmp = "tmp.py"
        print("Calibration: ")
        run_solver(filename, tmp)

        # sys.exit()

        '''
        Simulation code below:
        In each simulation:
        
        1. Apply simulation code (for instance PI(I) = 1.02).
        2. Rewrite all equations
        3. Solve the new model with the result from last run as initial guess.
        
        '''

        '''
        ######## The following is for individual shocks. ######## 
        
        iNum = 1 # dynamic model itterations
        
        for ittr in range(iNum):
          print("Simulation: ", ittr+1)
          if ittr == 0: # if it is the first simulation, apply the shock
        
              #DELTA.loc[I] = 1.02 * DELTA.loc[I]
        
              KS0.loc[K, I] = KS0.loc[K, I]*0.7
        
              #KS0.loc[K, ['HS1']] = KS0.loc[K, ['HS1']] * 0.675
              #KS0.loc[K, ['HS2']] = KS0.loc[K, ['HS2']] * 0.739
              #KS0.loc[K, ['HS3']] = KS0.loc[K, ['HS3']] * 0.958
              #KS0.loc[K, ['GOODS']] = KS0.loc[K, ['GOODS']] * 0.658
              #KS0.loc[K, ['TRADE']] = KS0.loc[K, ['TRADE']] * 0.961
              #KS0.loc[K, ['OTHER']] = KS0.loc[K, ['OTHER']] * 0.673
        
        
          else: # other simulations
        
              #KS0 = KSNEW*(1-DEPR)+vars.get('N', x=soln[-1])
              KS0 = vars.get('KS', x=soln[-1])
        
          run_solver(filename, tmp)
        
        '''

        # The following is for random shocks. #
        sims = sector_shocks
        iNum = 1  # dynamic model itterations
        # iNum = len(sims.columns)
        KS00 = KS0.copy()

        solver_status = False
        for num in range(iNum):
            KS0.loc[K, I] = KS00.loc[K, I].mul(sims.iloc[:, num])
            KS0 = KS0.fillna(0.0)
            solver_status = run_solver(filename, tmp)

        if solver_status:
            domestic_supply, gross_income, household_count, pre_disaster_demand, post_disaster_demand = \
                gams_to_dataframes(iNum, vars, H, L, soln)

            self.set_result_csv_data("domestic-supply", domestic_supply, name="domestic-supply", source="dataframe",
                                     index=True)
            self.set_result_csv_data("pre-disaster-factor-demand", pre_disaster_demand,
                                     name="pre-disaster-factor-demand", source="dataframe", index=True)
            self.set_result_csv_data("post-disaster-factor-demand", post_disaster_demand,
                                     name="post-disaster-factor-demand", source="dataframe", index=True)
            self.set_result_csv_data("gross-income", gross_income, name="gross-income", source="dataframe", index=True)
            self.set_result_csv_data("household-count", household_count, name="household-count", source="dataframe",
                                     index=True)
        else:
            raise ValueError("Solution infeasible - no output to save")

    def get_spec(self):
        return {
            'name': 'Salt-Lake-cge',
            'description': 'CGE model for Salt Lake City.',
            'input_parameters': [
                {
                    'id': 'model_iterations',
                    'required': True,
                    'description': 'Number of dynamic model iterations.',
                    'type': int
                },
                {
                    'id': 'solver_path',
                    'required': False,
                    'description': 'Path to ipopt package. If none is provided, it will default to your environment\'ts'
                                   'path to the package.',
                    'type': str
                }

            ],
            'input_datasets': [
                {
                    'id': 'SAM',
                    'required': True,
                    'description': 'Social accounting matrix (SAM) contains data for firms, '
                                   'households and government which are organized in a way to '
                                   'represent the interactions of all three entities in a typical economy.',
                    'type': ['incore:CGEsam']
                },
                {
                    'id': 'BB',
                    'required': True,
                    'description': 'BB is a matrix which describes how investment in physical infrastructure is'
                                   ' transformed into functioning capital such as commercial and residential buildings.'
                                   ' These data are collected from the Bureau of Economic Analysis (BEA).',
                    'type': ['incore:CGEbb']
                },
                {
                    'id': 'IOUT',
                    'required': False,
                    'description': 'IOUT is a matrix that describes the transfer of tax revenue collected by the local'
                                   ' government to help finance local government expenditures.',
                    'type': ['incore:CGEiout']
                },
                {
                    'id': 'MISC',
                    'required': False,
                    'description': 'MISC is the name of a file that contains data for commercial sector employment'
                                   ' and physical capital. It also contains data for the number of households and'
                                   ' working households in the economy.',
                    'type': ['incore:CGEmisc']
                },
                {
                    'id': 'MISCH',
                    'required': True,
                    'description': 'MISCH is a file that contains elasticities for the supply of labor with'
                                   ' respect to paying income taxes.',
                    'type': ['incore:CGEmisch']
                },
                {
                    'id': 'EMPLOY',
                    'required': True,
                    'description': 'EMPLOY is a table name containing data for commercial sector employment.',
                    'type': ['incore:CGEemploy']
                },
                {
                    'id': 'JOBCR',
                    'required': True,
                    'description': 'JOBCR is a matrix describing the supply of workers'
                                   ' coming from each household group in the economy.',
                    'type': ['incore:CGEjobcr']
                },
                {
                    'id': 'OUTCR',
                    'required': True,
                    'description': 'OUTCR is a matrix describing the number of workers who'
                                   ' live in Salt Lake City but commute outside of town to work.',
                    'type': ['incore:CGEoutcr']
                },
                {
                    'id': 'sector_shocks',
                    'required': True,
                    'description': 'Aggregation of building functionality states to capital shocks per sector',
                    'type': ['incore:capitalShocks']
                }
            ],
            'output_datasets': [
                {
                    'id': 'domestic-supply',
                    'parent_type': '',
                    'description': 'CSV file of resulting domestic supply',
                    'type': 'incore:Employment'
                },
                {
                    'id': 'gross-income',
                    'parent_type': '',
                    'description': 'CSV file of resulting gross income',
                    'type': 'incore:Employment'
                },
                {
                    'id': 'pre-disaster-factor-demand',
                    'parent_type': '',
                    'description': 'CSV file of factor demand before disaster',
                    'type': 'incore:FactorDemand'
                },
                {
                    'id': 'post-disaster-factor-demand',
                    'parent_type': '',
                    'description': 'CSV file of resulting factor-demand',
                    'type': 'incore:FactorDemand'
                },
                {
                    'id': 'household-count',
                    'parent_type': '',
                    'description': 'CSV file of household count',
                    'type': 'incore:HouseholdCount'
                }
            ]
        }
