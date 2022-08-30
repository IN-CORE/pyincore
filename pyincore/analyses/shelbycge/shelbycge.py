# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import os
import pandas as pd

from pyincore import BaseAnalysis
from pyincore import globals as pyglobals
from equationlib import *
from pyomo.environ import *
from pyomo.opt import SolverFactory


logger = pyglobals.LOGGER

class ShelbyCGEModel(BaseAnalysis):
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
        super(ShelbyCGEModel, self).__init__(incore_client)

    def get_spec(self):
        return {
            'name': 'Shelby cge',
            'description': 'CGE model for Shelby.',
            'input_parameters': [
                {
                    'id': 'print_solver_output',
                    'required': False,
                    'description': 'Print solver output.',
                    'type': bool
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
                    'type': ['incore:SeasideCGEsam']
                },
                {
                    'id': 'BB',
                    'required': True,
                    'description': 'BB is a matrix which describes how investment in physical infrastructure is'
                                   ' transformed into functioning capital such as commercial and residential buildings.'
                                   ' These data are collected from the Bureau of Economic Analysis (BEA).',
                    'type': ['incore:SeasideCGEbb']
                },
                {
                    'id': 'HHTABLE',
                    'required': True,
                    'description': 'HH Table.',
                    'type': ['incore:SeasideCGEhhtable']
                },
                {
                    'id': 'EMPLOY',
                    'required': True,
                    'description': 'EMPLOY is a table name containing data for commercial sector employment.',
                    'type': ['incore:SeasideCGEemploy']
                },
                {
                    'id': 'JOBCR',
                    'required': True,
                    'description': 'JOBCR is a matrix describing the supply of workers'
                                   ' coming from each household group in the economy.',
                    'type': ['incore:SeasideCGEjobcr']
                },
                {
                    'id': 'SIMS',
                    'required': True,
                    'description': 'Random numbers for the change of capital stocks in the CGE model.',
                    'type': ['incore:SeasideCGEsim']
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
                    'id': 'Seaside_Sims',
                    'parent_type': '',
                    'description': 'CSV file of Seaside cge simulations',
                    'type': 'incore:SeasideCGEsims'
                },
                {
                    'id': 'Seaside_output',
                    'parent_type': '',
                    'description': 'CSV file of output of Seaside cge, containing changes in employment and supply.',
                    'type': 'incore:SeasideCGEEmployDS'
                }
            ]
        }

    def run(is_cd=True, test_values=False):
        def _(x):
            return ExprM(vars, m=x)

        # ----------------------------------------------------------------
        # set file paths
        # ----------------------------------------------------------------
        modelPath = os.getcwd()
        filePath = os.path.join(modelPath, 'files')
        miscPath = os.path.join(filePath, 'MiscFile')

        # ----------------------------------------------------------------
        # define sets
        # ----------------------------------------------------------------
        # ALL ACCOUNTS IN SOCIAL ACCOUNTING MATRIX
        Z = [
            'GOODSA',
            'TRADEA',
            'OTHERA',
            'GOODSB',
            'TRADEB',
            'OTHERB',
            'GOODSC',
            'TRADEC',
            'OTHERC',
            'GOODSD',
            'TRADED',
            'OTHERD',
            'GOODSE',
            'TRADEE',
            'OTHERE',
            'GOODSF',
            'TRADEF',
            'OTHERF',
            'GOODSG',
            'TRADEG',
            'OTHERG',
            'GOODSH',
            'TRADEH',
            'OTHERH',
            'HS1A',
            'HS2A',
            'HS3A',
            'HS1B',
            'HS2B',
            'HS3B',
            'HS1C',
            'HS2C',
            'HS3C',
            'HS1D',
            'HS2D',
            'HS3D',
            'HS1E',
            'HS2E',
            'HS3E',
            'HS1F',
            'HS2F',
            'HS3F',
            'HS1G',
            'HS2G',
            'HS3G',
            'HS1H',
            'HS2H',
            'HS3H',
            'L1A',
            'L2A',
            'L3A',
            'L1B',
            'L2B',
            'L3B',
            'L1C',
            'L2C',
            'L3C',
            'L1D',
            'L2D',
            'L3D',
            'L1E',
            'L2E',
            'L3E',
            'L1F',
            'L2F',
            'L3F',
            'L1G',
            'L2G',
            'L3G',
            'L1H',
            'L2H',
            'L3H',
            'KAP',
            'HH1A',
            'HH2A',
            'HH3A',
            'HH4A',
            'HH5A',
            'HH1B',
            'HH2B',
            'HH3B',
            'HH4B',
            'HH5B',
            'HH1C',
            'HH2C',
            'HH3C',
            'HH4C',
            'HH5C',
            'HH1D',
            'HH2D',
            'HH3D',
            'HH4D',
            'HH5D',
            'HH1E',
            'HH2E',
            'HH3E',
            'HH4E',
            'HH5E',
            'HH1F',
            'HH2F',
            'HH3F',
            'HH4F',
            'HH5F',
            'HH1G',
            'HH2G',
            'HH3G',
            'HH4G',
            'HH5G',
            'HH1H',
            'HH2H',
            'HH3H',
            'HH4H',
            'HH5H',
            'INVES',
            'USSOCL1A',
            'USSOCL2A',
            'USSOCL3A',
            'USSOCL1B',
            'USSOCL2B',
            'USSOCL3B',
            'USSOCL1C',
            'USSOCL2C',
            'USSOCL3C',
            'USSOCL1D',
            'USSOCL2D',
            'USSOCL3D',
            'USSOCL1E',
            'USSOCL2E',
            'USSOCL3E',
            'USSOCL1F',
            'USSOCL2F',
            'USSOCL3F',
            'USSOCL1G',
            'USSOCL2G',
            'USSOCL3G',
            'USSOCL1H',
            'USSOCL2H',
            'USSOCL3H',
            'MEMPROPTAX',
            'OTHERPROPTAX',
            'MEMSALESTAX',
            'OTHERSALESTAX',
            'MEMFEE',
            'OTHERFEE',
            'TNSTX',
            'TNITAX',
            'USPIT',
            'CYGFM',
            'CYGFO',
            'FED',
            'STATE',
            'MEMPHIS',
            'OTHER',
            'OUTCOM1',
            'OUTCOM2',
            'OUTCOM3',
            'ROW']

        # FACTORS
        F = ['L1A', 'L2A', 'L3A', 'L1B', 'L2B', 'L3B', 'L1C', 'L2C', 'L3C', 'L1D', 'L2D', 'L3D', 'L1E', 'L2E', 'L3E',
             'L1F', 'L2F', 'L3F', 'L1G', 'L2G', 'L3G', 'L1H', 'L2H', 'L3H', 'KAP']
        F11 = ['L1A', 'L1B', 'L1C', 'L1D', 'L1E', 'L1F', 'L1G', 'L1H']
        F21 = ['L2A', 'L2B', 'L2C', 'L2D', 'L2E', 'L2F', 'L2G', 'L2H']
        F31 = ['L3A', 'L3B', 'L3C', 'L3D', 'L3E', 'L3F', 'L3G', 'L3H']

        # COMMUTERS OUT
        CM = ['OUTCOM1', 'OUTCOM2', 'OUTCOM3']

        # COMMUTERS OUT 1
        CM1 = ['OUTCOM1']

        # COMMUTERS OUT 2
        CM2 = ['OUTCOM2']

        # COMMUTERS OUT 3
        CM3 = ['OUTCOM3']

        # ALL WORKERS WHO LIVE IN SHELBY
        LT = ['L1A', 'L2A', 'L3A', 'L1B', 'L2B', 'L3B', 'L1C', 'L2C', 'L3C', 'L1D', 'L2D', 'L3D', 'L1E', 'L2E', 'L3E',
              'L1F', 'L2F', 'L3F', 'L1G', 'L2G', 'L3G', 'L1H', 'L2H', 'L3H', 'OUTCOM1', 'OUTCOM2', 'OUTCOM3']

        # LABOR
        L = ['L1A', 'L2A', 'L3A', 'L1B', 'L2B', 'L3B', 'L1C', 'L2C', 'L3C', 'L1D', 'L2D', 'L3D', 'L1E', 'L2E', 'L3E',
             'L1F', 'L2F', 'L3F', 'L1G', 'L2G', 'L3G', 'L1H', 'L2H', 'L3H']

        L1 = ['L1A', 'L1B', 'L1C', 'L1D', 'L1E', 'L1F', 'L1G', 'L1H']

        L2 = ['L2A', 'L2B', 'L2C', 'L2D', 'L2E', 'L2F', 'L2G', 'L2H']

        L3 = ['L3A', 'L3B', 'L3C', 'L3D', 'L3E', 'L3F', 'L3G', 'L3H']

        # LAND
        # LA(F) = ['LAND']

        # CAPITAL
        K = ['KAP']

        # GOVERNMENTS
        G = ['USSOCL1A', 'USSOCL2A', 'USSOCL3A', 'USSOCL1B', 'USSOCL2B', 'USSOCL3B',
             'USSOCL1C', 'USSOCL2C', 'USSOCL3C', 'USSOCL1D', 'USSOCL2D', 'USSOCL3D',
             'USSOCL1E', 'USSOCL2E', 'USSOCL3E', 'USSOCL1F', 'USSOCL2F', 'USSOCL3F',
             'USSOCL1G', 'USSOCL2G', 'USSOCL3G', 'USSOCL1H', 'USSOCL2H', 'USSOCL3H',
             'MEMPROPTAX', 'OTHERPROPTAX', 'MEMSALESTAX', 'OTHERSALESTAX', 'MEMFEE',
             'OTHERFEE', 'TNSTX', 'TNITAX', 'USPIT', 'CYGFM', 'CYGFO', 'FED',
             'STATE', 'MEMPHIS', 'OTHER']

        # ENDOGENOUS GOVERNMENTS
        GN = ['FED', 'STATE', 'MEMPHIS', 'OTHER']

        # LOCAL  ENDOGENOUS GOVERNMENTS
        GNLM = ['MEMPHIS']

        # LOCAL  ENDOGENOUS GOVERNMENTS
        GNLO = ['OTHER']

        # EXOGENOUS GOVERMENTS
        GX = ['USSOCL1A', 'USSOCL2A', 'USSOCL3A', 'USSOCL1B', 'USSOCL2B', 'USSOCL3B',
              'USSOCL1C', 'USSOCL2C', 'USSOCL3C', 'USSOCL1D', 'USSOCL2D', 'USSOCL3D',
              'USSOCL1E', 'USSOCL2E', 'USSOCL3E', 'USSOCL1F', 'USSOCL2F', 'USSOCL3F',
              'USSOCL1G', 'USSOCL2G', 'USSOCL3G', 'USSOCL1H', 'USSOCL2H', 'USSOCL3H',
              'MEMPROPTAX', 'OTHERPROPTAX', 'MEMSALESTAX', 'OTHERSALESTAX', 'MEMFEE',
              'OTHERFEE', 'TNSTX', 'TNITAX', 'USPIT']

        # SALES OR EXCISE TAXES
        GS = ['MEMSALESTAX', 'OTHERSALESTAX', 'MEMFEE', 'OTHERFEE', 'TNSTX']

        # LAND TAXES
        GL = ['MEMPROPTAX', 'OTHERPROPTAX']

        # FACTOR TAXES
        GF = ['USSOCL1A', 'USSOCL2A', 'USSOCL3A', 'USSOCL1B', 'USSOCL2B', 'USSOCL3B', 'USSOCL1C', 'USSOCL2C', 'USSOCL3C',
              'USSOCL1D', 'USSOCL2D', 'USSOCL3D', 'USSOCL1E', 'USSOCL2E', 'USSOCL3E', 'USSOCL1F', 'USSOCL2F', 'USSOCL3F',
              'USSOCL1G', 'USSOCL2G', 'USSOCL3G', 'USSOCL1H', 'USSOCL2H', 'USSOCL3H', 'MEMPROPTAX', 'OTHERPROPTAX']

        # SS PAYMENT
        GFUS = ['USSOCL1A', 'USSOCL2A', 'USSOCL3A', 'USSOCL1B', 'USSOCL2B', 'USSOCL3B', 'USSOCL1C', 'USSOCL2C', 'USSOCL3C',
                'USSOCL1D', 'USSOCL2D', 'USSOCL3D', 'USSOCL1E', 'USSOCL2E', 'USSOCL3E', 'USSOCL1F', 'USSOCL2F', 'USSOCL3F',
                'USSOCL1G', 'USSOCL2G', 'USSOCL3G', 'USSOCL1H', 'USSOCL2H', 'USSOCL3H']

        # SS PAYMENT
        GFUSC = ['USSOCL1A', 'USSOCL2A', 'USSOCL3A', 'USSOCL1B', 'USSOCL2B', 'USSOCL3B', 'USSOCL1C', 'USSOCL2C', 'USSOCL3C',
                 'USSOCL1D', 'USSOCL2D', 'USSOCL3D', 'USSOCL1E', 'USSOCL2E', 'USSOCL3E', 'USSOCL1F', 'USSOCL2F', 'USSOCL3F',
                 'USSOCL1G', 'USSOCL2G', 'USSOCL3G', 'USSOCL1H', 'USSOCL2H', 'USSOCL3H']

        # INCOME TAX UNITS
        GI = ['TNITAX', 'USPIT']

        # HOUSEHOLD TAX UNITS
        GH = ['MEMPROPTAX', 'OTHERPROPTAX', 'MEMFEE', 'OTHERFEE']

        # ENDOGENOUS TRANSFER PMT
        GT = ['CYGFM', 'CYGFO', 'FED', 'STATE']

        # HOUSEHOLDS
        H = ['HH1A', 'HH2A', 'HH3A', 'HH4A', 'HH5A', 'HH1B', 'HH2B', 'HH3B', 'HH4B', 'HH5B', 'HH1C', 'HH2C', 'HH3C', 'HH4C',
             'HH5C',
             'HH1D', 'HH2D', 'HH3D', 'HH4D', 'HH5D', 'HH1E', 'HH2E', 'HH3E', 'HH4E', 'HH5E', 'HH1F', 'HH2F', 'HH3F', 'HH4F',
             'HH5F',
             'HH1G', 'HH2G', 'HH3G', 'HH4G', 'HH5G', 'HH1H', 'HH2H', 'HH3H', 'HH4H', 'HH5H']

        # I+G SECTORS
        IG = ['GOODSA', 'TRADEA', 'OTHERA', 'HS1A', 'HS2A', 'HS3A', 'GOODSB', 'TRADEB', 'OTHERB', 'HS1B', 'HS2B', 'HS3B',
              'GOODSC', 'TRADEC', 'OTHERC', 'HS1C', 'HS2C', 'HS3C', 'GOODSD', 'TRADED', 'OTHERD', 'HS1D', 'HS2D', 'HS3D',
              'GOODSE', 'TRADEE', 'OTHERE', 'HS1E', 'HS2E', 'HS3E', 'GOODSF', 'TRADEF', 'OTHERF', 'HS1F', 'HS2F', 'HS3F',
              'GOODSG', 'TRADEG', 'OTHERG', 'HS1G', 'HS2G', 'HS3G', 'GOODSH', 'TRADEH', 'OTHERH', 'HS1H', 'HS2H', 'HS3H',
              'FED', 'STATE', 'MEMPHIS', 'OTHER']

        # INDUSTRY SECTORS
        I = ['GOODSA', 'TRADEA', 'OTHERA', 'HS1A', 'HS2A', 'HS3A', 'GOODSB', 'TRADEB', 'OTHERB', 'HS1B', 'HS2B', 'HS3B',
             'GOODSC', 'TRADEC', 'OTHERC', 'HS1C', 'HS2C', 'HS3C', 'GOODSD', 'TRADED', 'OTHERD', 'HS1D', 'HS2D', 'HS3D',
             'GOODSE', 'TRADEE', 'OTHERE', 'HS1E', 'HS2E', 'HS3E', 'GOODSF', 'TRADEF', 'OTHERF', 'HS1F', 'HS2F', 'HS3F',
             'GOODSG', 'TRADEG', 'OTHERG', 'HS1G', 'HS2G', 'HS3G', 'GOODSH', 'TRADEH', 'OTHERH', 'HS1H', 'HS2H', 'HS3H']

        # ENDOGENOUS GOVERNMENTS
        IG2 = ['FED', 'STATE', 'MEMPHIS', 'OTHER']

        # PRODUCTION SECTORS
        IP = ['GOODSA', 'TRADEA', 'OTHERA', 'GOODSB', 'TRADEB', 'OTHERB', 'GOODSC', 'TRADEC', 'OTHERC', 'GOODSD', 'TRADED',
              'OTHERD',
              'GOODSE', 'TRADEE', 'OTHERE', 'GOODSF', 'TRADEF', 'OTHERF', 'GOODSG', 'TRADEG', 'OTHERG', 'GOODSH', 'TRADEH',
              'OTHERH']

        # PRODUCTION GOV.
        FG = ['GOODSA', 'TRADEA', 'OTHERA', 'GOODSB', 'TRADEB', 'OTHERB', 'GOODSC', 'TRADEC', 'OTHERC', 'GOODSD', 'TRADED',
              'OTHERD',
              'GOODSE', 'TRADEE', 'OTHERE', 'GOODSF', 'TRADEF', 'OTHERF', 'GOODSG', 'TRADEG', 'OTHERG', 'GOODSH', 'TRADEH',
              'OTHERH']

        # HOUSING SERV.DEMAND
        HSD = ['HS1A', 'HS2A', 'HS3A', 'HS1B', 'HS2B', 'HS3B', 'HS1C', 'HS2C', 'HS3C', 'HS1D', 'HS2D', 'HS3D',
               'HS1E', 'HS2E', 'HS3E', 'HS1F', 'HS2F', 'HS3F', 'HS1G', 'HS2G', 'HS3G', 'HS1H', 'HS2H', 'HS3H']

        # SIMMLOOP
        SM = ['BASE', 'TODAY', 'SIMM']

        # REPORT 1 FOR SCALARS
        R1H = ['GFREV', 'SFREV', 'PIT',
               'DGF', 'DSF', 'DDRE', 'PDRE', 'SPI', 'COMM', 'COMMO',
               'GN', 'NKI', 'HH', 'W', 'W1', 'W2', 'W3', 'R', 'RL', 'L', 'K', 'HN', 'HW', 'GFSAVM', 'GFSAVO', 'LD',
               'CMO', 'CMI', 'HC', 'SSC', 'LAND', 'LAS']

        # REPORT 2 FOR STATUS
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

        # ===============================================================================
        # SETS FOR MISC TABLES ONLY

        # HOUSING SERVICES
        HSSET = ['HS1A', 'HS1B', 'HS1C', 'HS1D', 'HS1E', 'HS1F', 'HS1G', 'HS1H',
                 'HS2A', 'HS2B', 'HS2C', 'HS2D', 'HS2E', 'HS2F', 'HS2G', 'HS2H',
                 'HS3A', 'HS3B', 'HS3C', 'HS3D', 'HS3E', 'HS3F', 'HS3G', 'HS3H']

        # HOUSING SERVICES 2 & 3
        HS23SET = ['HS2A', 'HS2B', 'HS2C', 'HS2D', 'HS2E', 'HS2F', 'HS2G', 'HS2H',
                   'HS3A', 'HS3B', 'HS3C', 'HS3D', 'HS3E', 'HS3F', 'HS3G', 'HS3H']

        # HOUSEHOLDS (INCOME 1)
        HH1 = ['HH1A', 'HH1B', 'HH1C', 'HH1D', 'HH1E', 'HH1F', 'HH1G', 'HH1H']

        # HOUSEHOLDS (INCOME 2)
        HH2 = ['HH2A', 'HH2B', 'HH2C', 'HH2D', 'HH2E', 'HH2F', 'HH2G', 'HH2H']

        # HOUSEHOLDS (INCOME 3)
        HH3 = ['HH3A', 'HH3B', 'HH3C', 'HH3D', 'HH3E', 'HH3F', 'HH3G', 'HH3H']

        # HOUSEHOLDS (INCOME 4)
        HH4 = ['HH4A', 'HH4B', 'HH4C', 'HH4D', 'HH4E', 'HH4F', 'HH4G', 'HH4H']

        # HOUSEHOLDS (INCOME 5)
        HH5 = ['HH5A', 'HH5B', 'HH5C', 'HH5D', 'HH5E', 'HH5F', 'HH5G', 'HH5H']

        # ELASTICITIES
        ETA = ['ETAL1', 'ETAI1', 'ETALB1', 'ETAPIT', 'ETAPT', 'ETARA', 'NRPG', 'ETAYD', 'ETAU', 'ETAM', 'ETAE', 'ETAY', 'ETAOP']

        # LANDCAP TABLE ELASTICITIES
        ETALANDCAP = ['ETAL1', 'ETAI1', 'ETALB1']

        # MISCH TABLE ELASTICITIES
        ETAMISCH = ['ETAPIT', 'ETAPT', 'ETARA', 'NRPG', 'ETAYD', 'ETAU']

        # MISC TABLE ELASTICITIES
        ETAMISC = ['ETAM', 'ETAE', 'ETAY', 'ETAOP']

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
        GNLM1 = GNLM
        GNLO1 = GNLO

        # ----------------------------------------------------------------
        # IMPORT ADDITIONAL DATA FILES
        # ----------------------------------------------------------------

        # SAM
        SAM = pd.read_csv(os.path.join(filePath, 'SAM Shelby(1202).csv'), index_col=0)

        # CAPITAL COMP
        BB = pd.read_csv(os.path.join(filePath, 'capcomshelby.csv'), index_col=0)

        # MISC TABLES
        '''
        
        '''

        TPC = pd.DataFrame(index=H, columns=G).fillna(0.0)
        IGTD = pd.DataFrame(index=G, columns=G1).fillna(0.0)
        TAUFF = pd.DataFrame(index=G, columns=F).fillna(0.0)
        IOUT = pd.DataFrame(index=G1, columns=G1).fillna(0.0)
        LANDCAP = pd.DataFrame(index=IG, columns=ETALANDCAP).fillna(0.0)
        MISC = pd.DataFrame(index=Z, columns=ETAMISC).fillna(0.0)
        MISCH = pd.DataFrame(index=H, columns=ETAMISCH).fillna(0.0)

        # EMPLOY0 = pd.read_csv(os.path.join(miscPath, 'EMPLOY0(Z,F).csv'), index_col=0)
        EMPLOY = pd.read_csv(os.path.join(miscPath, 'EMPLOY(Z,F).csv'), index_col=0)
        JOBCR = pd.read_csv(os.path.join(miscPath, 'JOBCR(H,L).csv'), index_col=0)
        # JOBCR1 = pd.read_csv(os.path.join(miscPath, 'JOBCR1(H,L).csv'), index_col=0)
        HHTABLE = pd.read_csv(os.path.join(miscPath, 'HHTABLE(H,).csv'), index_col=0)
        # OUTCR = pd.read_csv(os.path.join(miscPath, 'OUTCR(H,CM).csv'), index_col=0)

        # ----------------------------------------------------------------
        # PARAMETER DECLARATION
        # ----------------------------------------------------------------

        # these are data frames with zeros to be filled during calibration
        A = pd.DataFrame(index=Z, columns=Z).fillna(0.0)
        AD = pd.DataFrame(index=Z, columns=Z).fillna(0.0)
        AG = pd.DataFrame(index=Z, columns=G).fillna(0.0)
        AGFS = pd.DataFrame(index=Z, columns=G).fillna(0.0)
        SIGMA = pd.Series(index=I, dtype=float).fillna(0.0)
        ALPHA = pd.DataFrame(index=F, columns=I).fillna(0.0)
        ALPHA1 = pd.DataFrame(index=F, columns=I).fillna(0.0)
        B = pd.DataFrame(index=I, columns=IG).fillna(0.0)
        B1 = pd.DataFrame(index=I, columns=I).fillna(0.0)
        CMOWAGE = pd.Series(index=CM, dtype=float).fillna(0.0)
        CMIWAGE = pd.Series(index=L, dtype=float).fillna(0.0)
        FCONST = pd.DataFrame(index=F, columns=I).fillna(0.0)
        GAMMA = pd.Series(index=I, dtype=float).fillna(0.0)
        DELTA = pd.Series(index=I, dtype=float).fillna(0.0)
        PIT = pd.DataFrame(index=G, columns=H).fillna(0.0)
        PIT0 = pd.DataFrame(index=G, columns=H).fillna(0.0)
        PRIVRET1 = pd.Series(index=H, dtype=float).fillna(0.0)
        PRIVRET = pd.Series(index=H, dtype=float).fillna(0.0)
        # LFOR = pd.Series(index=LA, dtype=float).fillna(0.0)
        KFOR = pd.Series(index=K, dtype=float).fillna(0.0)
        GFOR = pd.Series(index=G, dtype=float).fillna(0.0)
        out = pd.DataFrame(index=G, columns=G).fillna(0.0)
        TAUFH = pd.DataFrame(index=G, columns=F).fillna(0.0)
        TAUFL = pd.DataFrame(index=G, columns=L).fillna(0.0)
        # TAUFLA = pd.DataFrame(index=G, columns=LA).fillna(0.0)
        TAUFK = pd.DataFrame(index=G, columns=K).fillna(0.0)
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
        TAXS = pd.DataFrame(index=G, columns=G).fillna(0.0)
        TAXS1 = pd.Series(index=GNLM, dtype=float).fillna(0.0)
        TAXS2 = pd.Series(index=GNLO, dtype=float).fillna(0.0)

        # ELASTICITIES AND TAX DATA IMPOSED

        BETA = pd.DataFrame(index=I, columns=H).fillna(0.0)
        BETAH = pd.DataFrame(index=HSD, columns=H).fillna(0.0)
        ETAD = pd.Series(index=I, dtype=float).fillna(0.0)
        ETAE = pd.Series(index=I, dtype=float).fillna(0.0)
        ETAI = pd.Series(index=IG, dtype=float).fillna(0.0)
        ETAIX = pd.DataFrame(index=K, columns=IG).fillna(0.0)
        # ETAL = pd.DataFrame(index=LA, columns=IG).fillna(0.0)
        ETAL1 = pd.Series(index=IG, dtype=float).fillna(0.0)
        ETALB1 = pd.Series(index=IG, dtype=float).fillna(0.0)
        ETALB = pd.DataFrame(index=L, columns=IG).fillna(0.0)
        ETAM = pd.Series(index=I, dtype=float).fillna(0.0)
        ETARA = pd.Series(index=H, dtype=float).fillna(0.0)
        ETAYDO = pd.Series(index=H, dtype=float).fillna(0.0)
        ETAUO = pd.Series(index=H, dtype=float).fillna(0.0)
        ETAYDI = pd.Series(index=H, dtype=float).fillna(0.0)
        ETAUI = pd.Series(index=H, dtype=float).fillna(0.0)
        ETAYD = pd.Series(index=H, dtype=float).fillna(0.0)
        ETAU = pd.Series(index=H, dtype=float).fillna(0.0)
        ETAPT = pd.Series(index=H, dtype=float).fillna(0.0)
        ETAPIT = pd.Series(index=H, dtype=float).fillna(0.0)
        EXWGEO = pd.Series(index=CM, dtype=float).fillna(0.0)
        EXWGEI = pd.Series(index=L, dtype=float).fillna(0.0)
        ECOMI = pd.Series(index=L, dtype=float).fillna(0.0)
        ECOMO = pd.Series(index=CM, dtype=float).fillna(0.0)
        HOUSECOR = pd.DataFrame(index=H, columns=HSD).fillna(0.0)
        JOBCOR = pd.DataFrame(index=H, columns=L).fillna(0.0)

        LAMBDA = pd.DataFrame(index=I, columns=I).fillna(0.0)
        LAMBDAH = pd.DataFrame(index=HSD, columns=HSD1).fillna(0.0)

        NRPG = pd.Series(index=H, dtype=float).fillna(0.0)
        RHO = pd.Series(index=I, dtype=float).fillna(0.0)
        TT = pd.DataFrame(index=Z, columns=IG).fillna(0.0)

        depr = pd.Series(index=IG, dtype=float).fillna(0.1)

        # ARRAYS BUILT TO EXPORT RESULTS TO SEPARATE FILE

        R1 = pd.DataFrame(index=R1H, columns=SM).fillna(0.0)
        R2 = pd.DataFrame(index=R2H, columns=SM).fillna(0.0)

        # INITIAL VALUES OF ENDOGENOUS VARIABLES

        CG0 = pd.DataFrame(index=I, columns=G).fillna(0.0)
        CG0T = pd.DataFrame(index=I, columns=G).fillna(0.0)
        CH0 = pd.DataFrame(index=I, columns=H).fillna(0.0)
        CH0T = pd.DataFrame(index=I, columns=H).fillna(0.0)
        CMI0 = pd.Series(index=L, dtype=float).fillna(0.0)
        CMO0 = pd.Series(index=CM, dtype=float).fillna(0.0)
        CN0 = pd.Series(index=I, dtype=float).fillna(0.0)
        CN0T = pd.Series(index=I, dtype=float).fillna(0.0)
        CPI0 = pd.Series(index=H, dtype=float).fillna(0.0)
        CPIN0 = pd.Series(index=H, dtype=float).fillna(0.0)
        CPIH0 = pd.Series(index=H, dtype=float).fillna(0.0)
        CX0 = pd.Series(index=I, dtype=float).fillna(0.0)
        D0 = pd.Series(index=I, dtype=float).fillna(0.0)
        DD0 = pd.Series(index=Z, dtype=float).fillna(0.0)
        DS0 = pd.Series(index=Z, dtype=float).fillna(0.0)
        DQ0 = pd.Series(index=Z, dtype=float).fillna(0.0)

        FD0 = pd.DataFrame(index=F, columns=Z).fillna(0.0)
        IGT0 = pd.DataFrame(index=G, columns=GX).fillna(0.0)
        KS0 = pd.DataFrame(index=K, columns=IG).fillna(0.0)
        KSNEW = pd.DataFrame(index=K, columns=IG).fillna(0.0)
        KSNEW0 = pd.DataFrame(index=K, columns=IG).fillna(0.0)
        # LAS0 = pd.DataFrame(index=LA, columns=IG).fillna(0.0)
        HH0 = pd.Series(index=H, dtype=float).fillna(0.0)
        HN0 = pd.Series(index=H, dtype=float).fillna(0.0)
        HW0 = pd.Series(index=H, dtype=float).fillna(0.0)
        M0 = pd.Series(index=I, dtype=float).fillna(0.0)
        M01 = pd.Series(index=Z, dtype=float).fillna(0.0)
        MI0 = pd.Series(index=H, dtype=float).fillna(0.0)
        MO0 = pd.Series(index=H, dtype=float).fillna(0.0)
        N0 = pd.DataFrame(index=K, columns=IG).fillna(0.0)

        # NKIO

        KPFOR01 = pd.Series(index=K, dtype=float).fillna(0.0)
        KPFOR0 = pd.Series(index=K, dtype=float).fillna(0.0)
        # LNFOR0 = pd.Series(index=LA, dtype=float).fillna(0.0)
        # LNFOR01 = pd.Series(index=LA, dtype=float).fillna(0.0)
        GVFOR0 = pd.Series(index=G, dtype=float).fillna(0.0)
        P0 = pd.Series(index=IG, dtype=float).fillna(0.0)
        PH0 = pd.Series(index=HSD, dtype=float).fillna(0.0)
        PD0 = pd.Series(index=I, dtype=float).fillna(0.0)
        PVA0 = pd.Series(index=I, dtype=float).fillna(0.0)
        PWM0 = pd.Series(index=I, dtype=float).fillna(0.0)
        PW0 = pd.Series(index=I, dtype=float).fillna(0.0)
        Q0 = pd.Series(index=Z, dtype=float).fillna(0.0)
        Q10 = pd.Series(index=Z, dtype=float).fillna(0.0)
        R0 = pd.DataFrame(index=F, columns=Z).fillna(1.0)
        RA0 = pd.Series(index=F, dtype=float).fillna(0.0)
        S0 = pd.Series(index=Z, dtype=float).fillna(0.0)

        # SPIO

        V0 = pd.Series(index=I, dtype=float).fillna(0.0)
        V0T = pd.Series(index=I, dtype=float).fillna(0.0)
        V10 = pd.DataFrame(index=I, columns=I).fillna(0.0)
        TP = pd.DataFrame(index=H, columns=G).fillna(0.0)

        # TAUF0 = Table(G,F,Z)

        YD0 = pd.Series(index=H, dtype=float).fillna(0.0)
        Y0 = pd.Series(index=Z, dtype=float).fillna(0.0)
        Y01 = pd.Series(index=H, dtype=float).fillna(0.0)
        YT0 = pd.Series(index=G, dtype=float).fillna(0.0)
        GCP10 = pd.Series(index=I, dtype=float).fillna(0.0)

        # GCP0

        DDCX = pd.Series(index=I, dtype=float).fillna(0.0)

        TESTA1 = None
        TESTA2 = None
        TESTA3 = None
        if not is_cd:
            TESTA1 = pd.DataFrame(index=F, columns=I).fillna(0.0)
            TESTA2 = pd.DataFrame(index=F, columns=I).fillna(0.0)
            TESTA3 = pd.DataFrame(index=F, columns=I).fillna(0.0)

            # ===============================================================================
        # SIMPLIFYING TABLES AND DOING AWAY WITH MISC FILES
        # ===============================================================================

        for label in G1:
            out.loc[label, label] = 0
        out.loc['MEMPHIS', 'CYGFM'] = 1
        out.loc['OTHER', 'CYGFO'] = 1

        IGTD.loc[G, G1] = 0
        IGTD.loc['FED', GFUS] = 1
        IGTD.loc['FED', 'USPIT'] = 1

        IGTD.loc['CYGFM', 'MEMPROPTAX'] = 1
        IGTD.loc['CYGFM', 'MEMSALESTAX'] = 1
        IGTD.loc['CYGFM', 'MEMFEE'] = 1

        IGTD.loc['CYGFO', 'OTHERPROPTAX'] = 1
        IGTD.loc['CYGFO', 'OTHERSALESTAX'] = 1
        IGTD.loc['CYGFO', 'OTHERFEE'] = 1

        IGTD.loc['STATE', 'TNSTX'] = 1
        IGTD.loc['STATE', 'TNITAX'] = 1

        TPC.loc[H, G] = 0
        TPC.loc[H, GFUS] = 1

        TAUFF.loc[G, F] = 0
        TAUFF.loc['USSOCL1A', 'L1A'] = 1
        TAUFF.loc['USSOCL2A', 'L2A'] = 1
        TAUFF.loc['USSOCL3A', 'L3A'] = 1
        TAUFF.loc['USSOCL1B', 'L1B'] = 1
        TAUFF.loc['USSOCL2B', 'L2B'] = 1
        TAUFF.loc['USSOCL3B', 'L3B'] = 1
        TAUFF.loc['USSOCL1C', 'L1C'] = 1
        TAUFF.loc['USSOCL2C', 'L2C'] = 1
        TAUFF.loc['USSOCL3C', 'L3C'] = 1
        TAUFF.loc['USSOCL1D', 'L1D'] = 1
        TAUFF.loc['USSOCL2D', 'L2D'] = 1
        TAUFF.loc['USSOCL3D', 'L3D'] = 1
        TAUFF.loc['USSOCL1E', 'L1E'] = 1
        TAUFF.loc['USSOCL2E', 'L2E'] = 1
        TAUFF.loc['USSOCL3E', 'L3E'] = 1
        TAUFF.loc['USSOCL1F', 'L1F'] = 1
        TAUFF.loc['USSOCL2F', 'L2F'] = 1
        TAUFF.loc['USSOCL3F', 'L3F'] = 1
        TAUFF.loc['USSOCL1G', 'L1G'] = 1
        TAUFF.loc['USSOCL2G', 'L2G'] = 1
        TAUFF.loc['USSOCL3G', 'L3G'] = 1
        TAUFF.loc['USSOCL1H', 'L1H'] = 1
        TAUFF.loc['USSOCL2H', 'L2H'] = 1
        TAUFF.loc['USSOCL3H', 'L3H'] = 1

        TAUFF.loc['MEMPROPTAX', 'KAP'] = 1
        TAUFF.loc['OTHERPROPTAX', 'KAP'] = 1

        for label in G1:
            IOUT.loc[label, label] = 0
        IOUT.loc['MEMPHIS', 'CYGFM'] = 1
        IOUT.loc['OTHER', 'CYGFO'] = 1

        LANDCAP.loc[IG, ETALANDCAP] = 1
        '''
        LANDCAP.loc['CONST1', 'ETAL1']       = 0.5
        LANDCAP.loc['RETAIL1', 'ETAL1']      = 2
        LANDCAP.loc['SERV1', 'ETAL1']        = 1.4
        LANDCAP.loc['HC1', 'ETAL1']          = 1.4
        LANDCAP.loc['ACCOM1', 'ETAL1']       = 0.5
        LANDCAP.loc['REST1', 'ETAL1']       = 0.5
        LANDCAP.loc['AG2', 'ETAL1']          = 0.5
        LANDCAP.loc['CONST2', 'ETAL1']       = 0.5
        LANDCAP.loc['MANUF2', 'ETAL1']       = 0.5
        LANDCAP.loc['RETAIL2', 'ETAL1']      = 2
        LANDCAP.loc['SERV2', 'ETAL1']        = 0.5
        LANDCAP.loc['HC2', 'ETAL1']          = 0.5
        LANDCAP.loc['ACCOM2', 'ETAL1']       = 0.5
        LANDCAP.loc['REST2', 'ETAL1']        = 0.5
        LANDCAP.loc['AG3', 'ETAL1']          = 0.5
        LANDCAP.loc['UTIL', 'ETAL1']         = 1.4
        LANDCAP.loc['CONST3', 'ETAL1']       = 1.4
        LANDCAP.loc['RETAIL3', 'ETAL1']      = 2
        LANDCAP.loc['SERV3', 'ETAL1']        = 1.4
        LANDCAP.loc['HC3', 'ETAL1']          = 2
        LANDCAP.loc['HS1', 'ETAL1']          = 2
        LANDCAP.loc['HS2', 'ETAL1']          = 2
        LANDCAP.loc['HS3', 'ETAL1']          = 2
        '''

        MISCH.loc[H, ETAMISCH] = 0
        MISCH.loc[HH1, 'ETAPT'] = -0.5
        MISCH.loc[HH2, 'ETAPIT'] = -0.15
        MISCH.loc[HH3, 'ETAPIT'] = -0.2
        MISCH.loc[HH4, 'ETAPIT'] = -0.25
        MISCH.loc[HH5, 'ETAPIT'] = -0.35

        MISCH.loc[H, 'NRPG'] = 1
        # MISCH.loc[H, 'ETARA']                = 1
        '''
        # DRAM
        MISCH.loc[HH2, 'ETARA']                = 0.2
        MISCH.loc[HH3, 'ETARA']                = 0.3
        MISCH.loc[HH4, 'ETARA']                = 0.5
        MISCH.loc[HH5, 'ETARA']                = 0.8
        
        MISCH.loc[HH1, 'ETAYD']              = 1.3
        MISCH.loc[HH2, 'ETAYD']              = 1.6
        MISCH.loc[HH3, 'ETAYD']              = 1.8
        MISCH.loc[HH4, 'ETAYD']              = 2.0
        MISCH.loc[HH5, 'ETAYD']              = 2.1
        
        MISCH.loc[HH1, 'ETAU']               = -0.8
        MISCH.loc[HH2, 'ETAU']               = -0.6
        MISCH.loc[HH3, 'ETAU']               = -0.5
        MISCH.loc[HH4, 'ETAU']               = -0.4
        MISCH.loc[HH5, 'ETAU']               = -0.3
        '''
        MISC.loc[IG, ETAMISC] = 0
        MISC.loc[IP, 'ETAM'] = 1
        # MISC.loc[IP, 'ETAE']                 = -3.65
        MISC.loc[I, 'ETAY'] = 1
        MISC.loc[I, 'ETAOP'] = -1

        # ===============================================================================
        # PARAMETERS AND ELASTICITIES
        # ===============================================================================

        out.loc[G1, G1] = IOUT.loc[G1, G1];
        BETA.loc[I, H] = MISC.loc[I, 'ETAY'];
        BETAH.loc[HSD, H] = MISC.loc[HSD, 'ETAY'];

        for label in I:
            LAMBDA.loc[label, label] = MISC.loc[label, 'ETAOP'];
        '''
        for label in HD:
            LAMBDAH.loc[label,label] = MISC.loc[label,'ETAOP'];
        '''
        ETAE.loc[I] = MISC.loc[I, 'ETAE'];
        ETAM.loc[I] = MISC.loc[I, 'ETAM'];
        ETARA.loc[H] = MISCH.loc[H, 'ETARA'];

        ETAPIT.loc[H] = MISCH.loc[H, 'ETAPIT'];
        ETAPT.loc[H] = MISCH.loc[H, 'ETAPT'];
        ETAYD.loc[H] = MISCH.loc[H, 'ETAYD'];
        NRPG.loc[H] = MISCH.loc[H, 'NRPG'];
        ETAU.loc[H] = MISCH.loc[H, 'ETAU'];
        ETAI.loc[IG] = LANDCAP.loc[IG, 'ETAI1'];
        ETAIX.loc['KAP', IG] = ETAI.loc[IG];

        '''
        ETAIX.loc['KAP',IG]  = LANDCAP.loc[IG,'ETAI1'];
        ETAL.loc['LAND',IG]  = LANDCAP.loc[IG,'ETAL1'];
        ETALB.loc[L,IG]      = LANDCAP.loc[IG,'ETALB1'];
        '''

        # ========================================================================================================
        # ====================play with elasticities==============================================================
        # ========================================================================================================

        # EXPERIMENTAL ELASTICITIES
        ECOMI.loc[L] = 1;
        ECOMO.loc[CM] = 1;
        EXWGEO.loc[CM] = 1;
        EXWGEI.loc[L] = 1;
        ETAE.loc[IP] = -0.4;
        ETAIX.loc['KAP', IG] = 0.1;
        ETARA.loc[H] = 1.5;
        ETAYDO.loc[H] = 1.0;
        ETAYDI.loc[H] = 1.5;
        ETAUI.loc[H] = -0.72;
        ETAUO.loc[HH1] = -0.8;
        ETAUO.loc[HH2] = -0.6;
        ETAUO.loc[HH3] = -0.4;
        ETAUO.loc[HH4] = -0.2;
        ETAUO.loc[HH5] = -0.2;
        ETAU.loc[H] = -0.1;
        ETAYD.loc[H] = 1;
        '''
        #ETARA[H]          = 2.0;
        #ETAIX['KAP',IG]  = 0.1*ETAIX['KAP',IG];
        ETAIX.loc['KAP',IG]  = 0.1;
        ETAE.loc[IP]          = -1.5;
        
        # DRAM ELASTICITIES
        #ETAUO[H]         = MISCH[H, 'ETAU'];
        #ETAUI[H]         = MISCH[H, 'ETAU'];
        #ETAE[IP]         = -1.65;
        #ETAYDO[H]         = ETAYD[H];
        #ETAYDI[H]         = ETAYD[H];
        #ETAUI[H]          = ETAU[H];
        #ETAUO[H]          = ETAU[H];
        
        SIGMA.loc[I]         = 0.67;
        '''

        # ===============================================================================
        # CALIBRATION
        # ===============================================================================

        # Column Totals of SAM table
        Q10.loc[Z] = SAM.loc[Z, Z].sum(1)

        # Row Totals of SAM table
        Q0.loc[Z] = SAM.loc[Z, Z].sum(0)

        # difference of SAM row and coloumn totals
        DQ0.loc[Z] = Q10.loc[Z] - Q0.loc[Z]

        # Column Totals of SAM table
        Q10.loc[Z] = SAM.loc[Z].sum(0)

        B1.loc[I, I] = SAM.loc[I, I]

        # Calculate tax rates from SAM information
        TAUQ_1 = SAM.loc[GS, I]
        TAUQ_2 = SAM.loc[I, I].sum(1)
        TAUQ_3 = SAM.loc[I, H].sum(1)
        TAUQ_4 = SAM.loc[I, ['INVES']].sum(1)
        TAUQ_5 = SAM.loc[I, G].sum(1)
        TAUQ_6 = SAM.loc[I, ['ROW']].sum(1)
        TAUQ_7 = SAM.loc[GS1, I].sum(0)

        TAUQ.loc[GS, I] = TAUQ_1 / (TAUQ_2 + TAUQ_3 + TAUQ_4 + TAUQ_5 + TAUQ_6 - TAUQ_7)

        # NOTE:
        # set taxes to average if not specific to model
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
        TAUFL.loc[GF, L] = SAM.loc[GF, L] / (SAM.loc[Z, L].sum(0) - SAM.loc[L, ['ROW']].sum(1))

        TAUFK.loc[GF, K] = SAM.loc[GF, K] / SAM.loc[Z, K].sum(0)

        # SHARES OF ENDOGENOUS GOVERNMENTS TRANFERS TO REVENUE
        TAXS.loc[G, GX] = SAM.loc[G, GX] / SAM.loc[G, GX].sum(0)

        TAXS1.loc[GNLM] = SAM.loc[GNLM, ['CYGFM']].sum(1) / SAM.loc[GNLM, ['CYGFM']].sum(1).sum(0)

        TAXS2.loc[GNLO] = SAM.loc[GNLO, ['CYGFO']].sum(1) / SAM.loc[GNLO, ['CYGFO']].sum(1).sum(0)

        # SET INITIAL INTER GOVERNMENTAL TRANSFERS
        IGT0.loc[G, GX] = SAM.loc[G, GX]

        # SET INITIAL PRICES TO UNITY LESS SALES AND EXCISE TAXES
        PW0.loc[I] = 1.0
        PWM0.loc[I] = 1.0
        P0.loc[I] = 1.0
        PD0.loc[I] = 1.0
        CPI0.loc[H] = 1.0
        CPIN0.loc[H] = 1.0
        CPIH0.loc[H] = 1.0
        TT.loc[F, IG] = 1.0

        # HOUSEHOLD TRANSFER PAYMENTS AND PERSONAL INCOME TAXES
        # TOTAL HH IN Shelby
        HH0.loc[H] = HHTABLE.loc[H, 'HH0']

        # TOTAL WORKING HH IN SHELBY (WORK IN SHELBY & OUTSIDE SHELBY)
        HW0.loc[H] = HHTABLE.loc[H, 'HW0']

        # NON WORKING HH IN SHELBY
        HN0.loc[H] = HH0.loc[H] - HW0.loc[H]

        # NOMINAL GOVERNMENT SS PAYMENTS
        TP.loc[H, G] = SAM.loc[H, G].div(HH0.loc[H], axis='index').fillna(0.0)

        # FACTOR RENTALS
        JOBCOR.loc[H, L] = JOBCR.loc[H, L]

        # RENTAL RATE FOR FACTORS
        R0.loc[F, Z] = 1.0

        R0.loc[F, IG] = (SAM.loc[F, IG] / EMPLOY.loc[IG, F].T).fillna(1.0)

        # REAL FACTOR DEMAND
        FD0.loc[F, IG] = EMPLOY.loc[IG, F].T

        KS0.loc[K, IG] = FD0.loc[K, IG]

        # SHARES FOUND IN THE SOCIAL ACCOUNTING MATRIX DATA
        # A = INPUT OUTPUT COEFICIENTS
        A.loc[Z, Z] = SAM.loc[Z, Z].div(Q0.loc[Z], axis='columns')

        # SS PAYMENTS FROM IN-COMMUTERS
        # A(GFUSC, LCOM)   = TAUFL(GFUSC, LCOM);

        # AGFS: LABOR PAYMENTS BY G SECTOR + USSOC PAYMENTS BY LABOR (GROSS LABOR PAYMENTS)
        AGFS.loc['L1A', G] = SAM.loc['L1A', G] + SAM.loc['USSOCL1A', G]
        AGFS.loc['L2A', G] = SAM.loc['L2A', G] + SAM.loc['USSOCL2A', G]
        AGFS.loc['L3A', G] = SAM.loc['L3A', G] + SAM.loc['USSOCL3A', G]

        AGFS.loc['L1B', G] = SAM.loc['L1B', G] + SAM.loc['USSOCL1B', G]
        AGFS.loc['L2B', G] = SAM.loc['L2B', G] + SAM.loc['USSOCL2B', G]
        AGFS.loc['L3B', G] = SAM.loc['L3B', G] + SAM.loc['USSOCL3B', G]

        AGFS.loc['L1C', G] = SAM.loc['L1C', G] + SAM.loc['USSOCL1C', G]
        AGFS.loc['L2C', G] = SAM.loc['L2C', G] + SAM.loc['USSOCL2C', G]
        AGFS.loc['L3C', G] = SAM.loc['L3C', G] + SAM.loc['USSOCL3C', G]

        AGFS.loc['L1D', G] = SAM.loc['L1D', G] + SAM.loc['USSOCL1D', G]
        AGFS.loc['L2D', G] = SAM.loc['L2D', G] + SAM.loc['USSOCL2D', G]
        AGFS.loc['L3D', G] = SAM.loc['L3D', G] + SAM.loc['USSOCL3D', G]

        AGFS.loc['L1E', G] = SAM.loc['L1E', G] + SAM.loc['USSOCL1E', G]
        AGFS.loc['L2E', G] = SAM.loc['L2E', G] + SAM.loc['USSOCL2E', G]
        AGFS.loc['L3E', G] = SAM.loc['L3E', G] + SAM.loc['USSOCL3E', G]

        AGFS.loc['L1F', G] = SAM.loc['L1F', G] + SAM.loc['USSOCL1F', G]
        AGFS.loc['L2F', G] = SAM.loc['L2F', G] + SAM.loc['USSOCL2F', G]
        AGFS.loc['L3F', G] = SAM.loc['L3F', G] + SAM.loc['USSOCL3F', G]

        AGFS.loc['L1G', G] = SAM.loc['L1G', G] + SAM.loc['USSOCL1G', G]
        AGFS.loc['L2G', G] = SAM.loc['L2G', G] + SAM.loc['USSOCL2G', G]
        AGFS.loc['L3G', G] = SAM.loc['L3G', G] + SAM.loc['USSOCL3G', G]

        AGFS.loc['L1H', G] = SAM.loc['L1H', G] + SAM.loc['USSOCL1H', G]
        AGFS.loc['L2H', G] = SAM.loc['L2H', G] + SAM.loc['USSOCL2H', G]
        AGFS.loc['L3H', G] = SAM.loc['L3H', G] + SAM.loc['USSOCL3H', G]

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
        CX0.loc[I] = SAM.loc[I, ["ROW"]].div(P0.loc[I], axis='index').div(1.0 + TAUQ.loc[GS, I].sum(0), axis='index').sum(1)

        # REAL IMPORTS
        M01.loc[I] = SAM.loc[["ROW"], I].sum(0) / PWM0[I].T

        M0.loc[IP] = SAM.loc[IP, Z].sum(1) - (B1.loc[I, IP].sum(0) + SAM.loc[F, IP].sum(0) + SAM.loc[G, IP].sum(0))

        M0.loc[I] = (M0[I] / PWM0[I])
        M0 = M0.fillna(0.0)

        # * REAL INTERMEDIATE DEMAND
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

        CN0.loc[I] = B.loc[I, IG].mul(N0.loc[K, IG].sum(0), axis='columns').sum(1).div(P0.loc[I], axis='index').div(
            1.0 + TAUN.loc[GS, I].sum(0), axis='index').transpose()

        CN0T.loc[I] = B.loc[I, IG].mul(N0.loc[K, IG].sum(0), axis='columns').sum(1).div(P0.loc[I], axis='index')

        DD0.loc[I] = CH0.loc[I, H].sum(1) + CG0.loc[I, G].sum(1) + CN0.loc[I] + V0.loc[I]

        D0.loc[I] = 1.0 - M0.loc[I] / DD0.loc[I]

        # CORRECT IMPORT ELASTICITY TO DOMESTIC SHARE ELASTICITY
        ETAD.loc[I] = -1.0 * ETAM.loc[I] * M0.loc[I] / (DD0.loc[I] * D0.loc[I])

        # PRODUCTION DATA
        DS0.loc[I] = DD0.loc[I] + CX0.loc[I] - M0.loc[I]

        AD.loc[I, I] = SAM.loc[I, I].div(P0.loc[I], axis='index').div(1.0 + TAUQ.loc[GS, I].sum(0), axis='index') / DS0.loc[I]

        V10.loc[I, I] = SAM.loc[I, I].div(P0.loc[I], axis='index').div(1.0 + TAUQ.loc[GS, I].sum(0), axis='index')

        PVA0.loc[I] = PD0.loc[I] - (
            AD.loc[I, I].mul(P0.loc[I], axis='index').mul(1.0 + TAUQ.loc[GS, I].sum(0).T, axis='index').sum(0).T)

        # AVERAGE RENTAL RATES FOR FACTORS (NORMALIZED)
        RA0.loc[F] = 1.0

        # CALIBRATION OF PRODUCTION EXPONENTS FOR COBB DOUGLAS
        # a = pd.Series(index=I, dtype=float).fillna(0.0)
        # a = SAM.loc[GFUS, I].append(a, ignore_index=True).append(SAM.loc[GL, I]) # labor, capital
        a = SAM.loc['MEMPROPTAX', I] + SAM.loc['OTHERPROPTAX', I]
        a_new_row = pd.DataFrame([a])
        a = pd.concat([SAM.loc[GFUS, I], a_new_row])
        a.index = F

        ALPHA.loc[F, I] = (SAM.loc[F, I] + a.loc[F, I]) / (SAM.loc[F, I].sum(0) + SAM.loc[GF, I].sum(0))
        ALPHA.loc[F, I] = ALPHA.loc[F, I] / ALPHA.loc[F, I].sum(0)

        ACK = pd.Series(index=I, dtype=float).fillna(0.0)
        ACK.loc[I] = SAM.loc[F, I].sum(0)

        if is_cd:
            # replace takes care of multiplying by zeros, by changing zeros to ones.
            DELTA.loc[I] = DS0.loc[I] / (FD0.loc[F, I] ** ALPHA.loc[F, I]).replace({0: 1}).product(0)
            SIGMA.loc[I] = 0.67
            RHO.loc[I] = (SIGMA.loc[I] - 1) / SIGMA.loc[I]
        else:
            # Cobb-Douglas Technology Parameter
            # replace takes care of multiplying by zeros, by changing zeros to ones.
            # CES Production Function
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

        # ORIGINAL EQUATION
        A.loc[H, L] = SAM.loc[H, L].div(HW0.loc[H], axis='index') / (
                Y0.loc[L] * (1.0 - TAUFL.loc[G, L].sum(0)) + SAM.loc[L, ["ROW"]].sum(1))

        A.loc[H, K] = SAM.loc[H, K].div(HW0.loc[H], axis='index') / (
                Y0.loc[K] + SAM.loc[Z, K].sum(0) - SAM.loc[K, IG].sum(1))

        # HH TAXES OTHER THAN PIT
        TAUH.loc[GH, H] = SAM.loc[GH, H].div(HH0.loc[H], axis='columns')

        S0.loc[H] = SAM.loc[["INVES"], H].T.sum(1)

        YD0.loc[H] = SAM.loc[I, H].sum(0).T + S0.loc[H]

        Y0.loc[G] = SAM.loc[G, Z].sum(1) - SAM.loc[G, ["ROW"]].sum(1)

        S0.loc[G] = SAM.loc[["INVES"], G].sum(0)

        # COMMUTING IN
        CMI0.loc[L] = FD0.loc[L, IG].sum(1) - JOBCOR.loc[H, L].mul(HW0.loc[H], axis='index').sum(0)

        # COMMUTING OUT
        CMO0.loc[["OUTCOM1"]] = 46206.0
        CMO0.loc[["OUTCOM2"]] = 24294.0
        CMO0.loc[["OUTCOM3"]] = 13514.0

        # AVERAGE WAGE FLOWING INTO SHELBY
        CMOWAGE.loc[CM] = SAM.loc[CM, ["ROW"]].sum(1).div(CMO0.loc[CM], axis='index').fillna(0.0)

        # AVERAGE WAGES FLOWING OUT OF SHELBY
        CMIWAGE.loc[L] = (-1) * (SAM.loc[L, ["ROW"]].sum(1).div(CMI0.loc[L], axis='index').fillna(0.0))

        # PROPORTION OF CAPITAL INCOME OUTFLOW
        KFOR.loc[K] = KPFOR0.loc[K] / SAM.loc[["KAP"], IG].sum(1)

        # PROPORTION OF GOVERNMENT INCOME OUTFLOW
        GFOR.loc[G] = GVFOR0.loc[G] / Y0.loc[G]

        A.loc[H, CM] = SAM.loc[H, CM].div(SAM.loc[Z, CM].sum(0), axis='columns')

        # NOMINAL NET CAPITAL INFLOW
        NKI0 = (M0.loc[I] * PWM0.loc[I]).sum(0) - (CX0.loc[I] * PD0.loc[I]).sum(0) - \
               (PRIVRET.loc[H] * HH0.loc[H]).sum(0) - \
               KPFOR0.loc[K].sum(0) - GVFOR0.loc[G].sum(0) - \
               (CMOWAGE.loc[CM] * CMO0.loc[CM]).sum(0) - \
               (CMIWAGE.loc[L] * CMI0.loc[L]).sum(0)

        # REAL HH NET INCOME
        Y0.loc[H] = (A.loc[H, L].mul(HW0[H], axis='index').div(A.loc[H, L].mul(HW0[H], axis='index').sum(0), axis='columns') \
                     .mul(Y0.loc[L] * (1.0 - TAUFL.loc[G, L].sum(0)) - (CMIWAGE.loc[L] * CMI0.loc[L]), axis='columns')).sum(1) \
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

        GCP0 = CH0.loc[I, H].sum(1).sum(0) + CN0.loc[I].sum(0) + CG0.loc[I, GN].sum(1).sum(0) + CX0.loc[I].sum(0) - M0.loc[
            I].sum(0)

        GCP10.loc[I] = CH0.loc[I, H].sum(1) + CN0.loc[I] + CG0.loc[I, GN].sum(1) + CX0.loc[I] + M0.loc[I]

        ###########################################
        # VARIABLE DECLARATION
        ###########################################

        vars = VarContainer()

        # PUBLIC CONSUMPTION
        CG = vars.add('CG', rows=I, cols=G)

        # PRIVATE CONSUMPTION
        CH = vars.add('CH', rows=I, cols=H)

        # COMMUTING IN
        CMI = vars.add('CMI', rows=L)

        # COMMUTING OUT JASPER
        CMO = vars.add('CMO', rows=CM)

        # GROSS INVESTMENT BY SECTOR OF SOURCE
        CN = vars.add('CN', rows=I)

        # CONSUMER PRICE INDEX
        CPI = vars.add('CPI', rows=H)

        # NONHOUSING CONSUMER PRICE INDEX
        CPIN = vars.add('CPIN', rows=H)

        # HOUSING CONSUMER PRICE INDEX
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
        # FD = vars.add('FD', rows=F, cols=Z)
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

        # IMPORTS
        M = vars.add('M', rows=I)

        # GROSS INVESTMENT BY SECTOR OF DESTINATION
        N = vars.add('N', rows=K, cols=IG)

        # NET CAPITAL INFLOW
        NKI = vars.add('NKI')

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

        # additional variable
        V1 = vars.add('V1', rows=I, cols=I)

        # GROSS INCOMES
        Y = vars.add('Y', rows=Z)

        # additional variables
        # Y1 = vars.add('Y1', rows=H)
        # Y2 = vars.add('Y2', rows=H)
        # Y3 = vars.add('Y3', rows=H)

        # AFTER TAX TOTAL HOUSEHOLD INCOMES
        YD = vars.add('YD', rows=H)

        # GOV INCOME
        # YT = vars.add('YT', rows=G, cols=G)

        ###########################################
        # INITIALIZE VARIABLES FOR SOLVER
        ###########################################

        vars.init('CG', CG0.loc[I, G])
        vars.init('CH', CH0.loc[I, H])
        vars.init('CMI', CMI0.loc[L])
        vars.init('CMO', CMO0.loc[CM])
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
        vars.init('V1', V10.loc[I, I])
        vars.init('Y', Y0.loc[Z])
        # vars.init('Y1')
        # vars.init('Y2')
        # vars.init('Y3')
        vars.init('YD', YD0.loc[H])
        # vars.init('YT')


        # -------------------------------------------------------------------------------------------------------------
        # DEFINE BOUNDS FOR VARIABLES
        # -------------------------------------------------------------------------------------------------------------

        vars.lo('P', vars.get('P') / 1000);
        vars.up('P', vars.get('P') * 1000)
        vars.lo('PD', vars.get('PD') / 1000);
        vars.up('PD', vars.get('PD') * 1000)
        vars.lo('PVA', vars.get('PVA') / 1000);
        vars.up('PVA', vars.get('PVA') * 1000)
        vars.lo('RA', vars.get('RA') / 1000);
        vars.up('RA', vars.get('RA') * 1000)
        vars.lo('CPI', vars.get('CPI') / 1000);
        vars.up('CPI', vars.get('CPI') * 1000)
        vars.lo('CMI', vars.get('CMI') / 1000);
        vars.up('CMI', vars.get('CMI') * 1000)
        vars.lo('CMO', vars.get('CMO') / 1000);
        vars.up('CMO', vars.get('CMO') * 1000)
        vars.lo('DS', vars.get('DS') / 1000);
        vars.up('DS', vars.get('DS') * 1000)
        vars.lo('DD', vars.get('DD') / 1000);
        vars.up('DD', vars.get('DD') * 1000)
        vars.lo('D', vars.get('D') / 1000);
        vars.up('D', vars.get('D') * 1000)
        vars.lo('V', vars.get('V') / 1000);
        vars.up('V', vars.get('V') * 1000)
        vars.lo('FD', vars.get('FD') / 1000);
        vars.up('FD', vars.get('FD') * 1000)
        vars.lo('HH', vars.get('HH') / 1000);
        vars.up('HH', vars.get('HH') * 1000)
        vars.lo('HW', vars.get('HW') / 1000);
        vars.up('HW', vars.get('HW') * 1000)
        vars.lo('HN', vars.get('HN') / 1000);
        vars.up('HN', vars.get('HN') * 1000)
        vars.lo('KS', vars.get('KS') / 1000);
        vars.up('KS', vars.get('KS') * 1000)
        # vars.lo('LAS',vars.get('LAS')/1000); vars.up('LAS',vars.get('LAS')*1000)
        vars.lo('M', vars.get('M') / 1000);
        vars.up('M', vars.get('M') * 1000)
        vars.lo('Y', vars.get('Y') / 1000);
        vars.up('Y', vars.get('Y') * 1000)
        vars.lo('YD', vars.get('YD') / 1000);
        vars.up('YD', vars.get('YD') * 1000)
        vars.lo('CH', vars.get('CH') / 1000);
        vars.up('CH', vars.get('CH') * 1000)
        vars.lo('CG', vars.get('CG') / 1000);
        vars.up('CG', vars.get('CG') * 1000)
        vars.lo('CX', vars.get('CX') / 1000);
        vars.up('CX', vars.get('CX') * 1000)
        vars.lo('R', vars.get('R') / 1000);
        vars.up('R', vars.get('R') * 1000)
        vars.lo('N', 0);
        vars.lo('CN', 0);


        def set_variable(filename):
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
            if test_values:
                CPIEQ.test(vars.initialVals)
            CPIEQ.write(count, filename)

            #   YEQ(H)..
            # YEQ(H).. Y(H)  =E= SUM(L,  A(H,L) * HW(H) / SUM(H1, A(H1,L) * HW(H1) ) * (Y(L) * ( 1 - SUM(G, TAUFL(G,L))) - RA(L)*CMIWAGE(L)*CMI(L)))
            #                   + SUM(CM, A(H,CM)*(CMOWAGE(CM)*CMO(CM)))
            #                   + SUM(K,  A(H,K) * HW(H) / SUM(H1, A(H1,K) * HW(H1))
            #                   * (Y(K) + KPFOR(K)) * ( 1 - SUM(G, TAUFK(G,K) ) ) );

            print('YEQ(H)')
            line1 = (ExprM(vars, m=A.loc[H, L]) * HW.loc(H) / (ExprM(vars, m=A.loc[H1, L]) * HW.loc(H1)).sum(H1) * (
                    Y.loc(L) * ExprM(vars, m=1 - TAUFL.loc[G, L].sum(0)) - RA.loc(L) * ExprM(vars,
                                                                                             m=CMIWAGE.loc[L]) * CMI.loc(
                L))).sum(L)
            line2 = (ExprM(vars, m=A.loc[H, CM]) * (ExprM(vars, m=CMOWAGE.loc[CM]) * CMO.loc(CM))).sum(CM)
            # line3 = (ExprM(vars, m= A.loc[H,LA]) * HW.loc(H) / (ExprM(vars, m= A.loc[H1,LA]) * HW.loc(H1)).sum(H1) * (Y.loc(LA) + LNFOR.loc(LA) ) * ExprM(vars, m= 1 - TAUFLA.loc[G,LA].sum(0))).sum(LA)
            line4 = (ExprM(vars, m=A.loc[H, K]) * HW.loc(H) / (ExprM(vars, m=A.loc[H1, K]) * HW.loc(H1)).sum(H1) * (
                    Y.loc(K) + KPFOR.loc(K)) * ExprM(vars, m=1 - TAUFK.loc[G, K].sum(0))).sum(K)

            YEQ = ((line1 + line2 + line4) - Y.loc(H))
            if test_values:
                YEQ.test(vars.initialVals)
            YEQ.write(count, filename)
            # print(YEQ)

            #  YDEQ(H).. YD(H)          =E=   Y(H) + (PRIVRET(H) * HH(H))
            #                                         + SUM(G, TP(H,G) * HH(H))
            #                                         - SUM(GI, PIT0(GI,H)  * Y(H))
            #                                         - SUM(G, TAUH(G,H)  * HH(H));
            print('YDEQ(H)')
            line1 = Y.loc(H) + (ExprM(vars, m=PRIVRET.loc[H]) * HH.loc(H))
            line2 = (ExprM(vars, m=TP.loc[H, G]) * HH.loc(H)).sum(G)
            line3 = ~(ExprM(vars, m=PIT0.loc[GI, H]) * Y.loc(H)).sum(GI)
            line4 = ~(ExprM(vars, m=TAUH.loc[G, H]) * HH.loc(H)).sum(G)

            YDEQ = ((line1 + line2 - line3 - line4) - YD.loc(H))
            YDEQ.write(count, filename)
            if test_values:
                YDEQ.test(vars.initialVals)
            # print(YDEQ)

            #  CHEQ(I,H).. CH(I,H)      =E= CH0(I,H)* ((YD(H) / YD0(H)) / ( CPI(H) / CPI0(H)))**(BETA(I,H))
            #                                 * PROD(J, ((P(J)*( 1 + SUM(GS, TAUC(GS,J))))/ (P0(J)*(1 + SUM(GS, TAUQ(GS,J)))))** (LAMBDA(J,I)));
            print('CHEQ(I,H)')
            line1 = ExprM(vars, m=CH0.loc[I, H]) * (
                    (YD.loc(H) / ExprM(vars, m=YD0.loc[H])) / (CPI.loc(H) / ExprM(vars, m=CPI0.loc[H]))) ** ExprM(vars, m=
            BETA.loc[I, H])
            line2 = (((P.loc(J) * ExprM(vars, m=1 + TAUC.loc[GS, J].sum(0))) / (
                    ExprM(vars, m=P0.loc[J]) * ExprM(vars, m=1 + TAUQ.loc[GS, J].sum(0)))) ** ExprM(vars, m=LAMBDA.loc[
                J, I])).prod(0)

            CHEQ = ((line1 * line2) - CH.loc(I, H))
            CHEQ.write(count, filename)
            if test_values:
                CHEQ.test(vars.initialVals)
            # print(CHEQ)

            #  SHEQ(H).. S(H)           =E= YD(H) - SUM(I, P(I) * CH(I,H) * ( 1 + SUM(GS, TAUC(GS,I))));
            print('SHEQ(H)')
            line = YD.loc(H) - ~((P.loc(I) * CH.loc(I, H) * ExprM(vars, m=1 + TAUC.loc[GS, I].sum(0))).sum(I))

            SHEQ = (line - S.loc(H))
            SHEQ.write(count, filename)
            if test_values:
                SHEQ.test(vars.initialVals)
            # print(SHEQ)

            #  PVAEQ(I).. PVA(I)        =E= PD(I) - SUM(J, AD(J,I) * P(J) * (1 + SUM(GS, TAUQ(GS, J))));
            print('PVAEQ(I)')
            line = PD.loc(I) - ~((ExprM(vars, m=AD.loc[J, I]) * P.loc(J) * ExprM(vars, m=1 + TAUQ.loc[GS, J].sum(0))).sum(0))

            PVAEQ = (line - PVA.loc(I))
            PVAEQ.write(count, filename)
            if test_values:
                PVAEQ.test(vars.initialVals)
            # print(PVAEQ)

            # PFEQ(I)..DS(I) =E= DELTA(I)*PROD(F$ALPHA(F,I),(TT(F,I)*FD(F,I))**ALPHA(F,I));
            if is_cd:
                print('PFEQ(I)')
                line = ExprM(vars, m=DELTA.loc[I]) * (
                        (ExprM(vars, m=TT.loc[F, I]) * FD.loc(F, I)) ** ExprM(vars, m=ALPHA.loc[F, I])).prod(F)

                PFEQ = (line - DS.loc(I))
                PFEQ.write(count, filename)
                if test_values:
                    PFEQ.test(vars.initialVals)
                # print(PFEQ)
            else:
                # CES
                # PFEQ(I)..DS(I) =E= GAMMA(I)*(SUM(F, ALPHA(F,I)*(FD(F,I)**(RHO(I)))))**(1/RHO(I));
                print('PFEQ(I)')
                line = ExprM(vars, m=GAMMA.loc[I]) * \
                       ((ExprM(vars, m=ALPHA.loc[F, I]) * (FD.loc(F, I) ** ExprM(vars, m=RHO.loc[I]))).sum(F)) \
                       ** ExprM(vars, m=1 / RHO.loc[I])
                PFEQ = (line - DS.loc(I))
                PFEQ.write(count, filename)
                if test_values:
                    PFEQ.test(vars.initialVals)
                # print(PFEQ)
            if is_cd:
                # FDEQ(F,I).. R(F,I) * RA(F) * (1 + SUM(GF,TAUFX(GF,F,I) ) )* (TT(F,I)* FD(F,I))
                #                         =E= PVA(I) * DS(I) * ALPHA(F,I);
                print('FDEQ(F,I)')
                left = R.loc(F, I) * RA.loc(F) * ExprM(vars, m=1 + TAUFX_SUM.loc[F, I]) * (
                        ExprM(vars, m=TT.loc[F, I]) * FD.loc(F, I))
                right = ~(PVA.loc(I) * DS.loc(I) * ExprM(vars, m=ALPHA.loc[F, I]))

                FDEQ = (right - left)

                # FDEQ.test(vars.initialVals)
                FDEQ.write(count, filename)
                if test_values:
                    FDEQ.test(vars.initialVals)
                # print(FDEQ)
            else:
                # FD of CES
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
                if test_values:
                    FDEQ.test(vars.initialVals)
                # print(FDEQ)

            #   VEQ(I).. V(I) =E= SUM(J, AD(I,J) * DS(J) );

            print('VEQ(I)')
            line = (ExprM(vars, m=AD.loc[I, J]) * ~DS.loc(J)).sum(1)

            VEQ = (line - V.loc(I))
            VEQ.write(count, filename)
            if test_values:
                VEQ.test(vars.initialVals)
            # print(VEQ)

            # YFEQL(F).. Y(F) =E= SUM(IG, R(F,IG) * RA(F)*FD(F,IG));
            print('YFEQL(L)')
            line = (R.loc(F, IG) * RA.loc(F) * FD.loc(F, IG)).sum(IG)

            YFEQL = (line - Y.loc(F))
            YFEQL.write(count, filename)
            if test_values:
                YFEQL.test(vars.initialVals)
            # print(YFEQL)

            #  KAPFOR(K).. KPFOR(K)     =E= KFOR(K) * Y(K);
            print('KAPFOR(K)')
            line = ExprM(vars, m=KFOR.loc[K]) * Y.loc(K)

            KAPFOR = (line - KPFOR.loc(K))
            KAPFOR.write(count, filename)
            if test_values:
                KAPFOR.test(vars.initialVals)
            # print(KAPFOR)

            # XEQ(I).. CX(I) =E= CX0(I)*( (PD(I)*(1+SUM(GS,TAUX(GS,I))))
            #                  /(PW0(I)*(1+SUM(GS,TAUQ(GS,I))))) **(ETAE(I));
            print('XEQ(I)')
            line = ExprM(vars, m=CX0.loc[I]) * \
                   ((PD.loc(I) * ExprM(vars, m=1 + TAUX.loc[GS, I].sum(0))) / ExprM(vars, m=PW0.loc[I] * (1 + TAUQ.loc[GS, I].sum(0)))) \
                   ** ExprM(vars, m=ETAE.loc[I])

            XEQ = (line - CX.loc(I))
            XEQ.write(count, filename)
            if test_values:
                XEQ.test(vars.initialVals)
            # print(XEQ)

            #  DEQ(I)$PWM0(I).. D(I)    =E= D0(I) *(PD(I)/PWM0(I))**(ETAD(I));
            print('DEQ(I)$PWM0(I)')
            line = ExprM(vars, m=D0.loc[I]) * (PD.loc(I) / ExprM(vars, m=PWM0.loc[I])) ** ExprM(vars, m=ETAD.loc[I])

            DEQ = (line - D.loc(I))
            #  DEQ.setCondition(PWM0.loc[I])
            DEQ.write(count, filename)
            if test_values:
                DEQ.test(vars.initialVals)
            # print(DEQ)

            #  MEQ(I).. M(I)            =E= ( 1 - D(I) ) * DD(I);
            print('MEQ(I)')
            line = (1 - D.loc(I)) * DD.loc(I)

            MEQ = (line - M.loc(I))
            MEQ.write(count, filename)
            if test_values:
                MEQ.test(vars.initialVals)
            # print(MEQ)

            #  PEQ(I)..  P(I)           =E= D(I) * PD(I) + ( 1 - D(I) ) * PWM0(I);
            print('PEQ(I)')
            line = (D.loc(I) * PD.loc(I) + (1 - D.loc(I)) * ExprM(vars, m=PWM0.loc[I]))

            PEQ = (line - P.loc(I))
            PEQ.write(count, filename)
            if test_values:
                PEQ.test(vars.initialVals)
            # print(PEQ)

            #  NKIEQ.. NKI              =E= SUM(I, M(I) * PWM0(I) )
            #                                 - SUM(I, CX(I) * PD(I) )
            #                                 - SUM(H, PRIVRET(H)*HH(H))
            #                                 - SUM(K, KPFOR(K))
            #                                 - SUM(G, GVFOR(G))
            #                                 - SUM(CM,CMOWAGE(CM)*CMO(CM))
            #                                 - SUM(L,CMIWAGE(L)*CMI(L));

            print('NKIEQ')
            line1 = (M.loc(I) * ExprM(vars, m=PWM0.loc[I])).sum(I)
            line2 = (CX.loc(I) * PD.loc(I)).sum(I)
            line3 = (ExprM(vars, m=PRIVRET.loc[H]) * HH.loc(H)).sum(H)
            line5 = KPFOR.loc(K).sum(K)
            line6 = GVFOR.loc(G).sum(G)
            line7 = (ExprM(vars, m=CMOWAGE.loc[CM]) * CMO.loc(CM)).sum(CM)
            line8 = (ExprM(vars, m=CMIWAGE.loc[L]) * CMI.loc(L)).sum(L)

            NKIEQ = ((line1 - line2 - line3 - line5 - line6 - line7 - line8) - NKI)
            NKIEQ.write(count, filename)
            if test_values:
                NKIEQ.test(vars.initialVals)
            # print(NKIEQ)

            #  NEQ(K,I).. N(K,I)        =E= N0(K,I)*(R(K,I)/R0(K,I))**(ETAIX(K,I));
            print('NEQ(K,I)')
            line = ExprM(vars, m=N0.loc[K, I]) * (R.loc(K, I) / ExprM(vars, m=R0.loc[K, I])) ** ExprM(vars, m=ETAIX.loc[K, I])

            NEQ = (line - N.loc(K, I))
            NEQ.write(count, filename)
            if test_values:
                NEQ.test(vars.initialVals)
            # print(NEQ)

            #  CNEQ(I).. P(I)*(1 + SUM(GS, TAUN(GS,I)))*CN(I)
            #                         =E= SUM(IG, B(I,IG)*(SUM(K, N(K,IG))));
            print('CNEQ(I)')
            left = P.loc(I) * ExprM(vars, m=1 + TAUN.loc[GS, I].sum(0)) * CN.loc(I)
            right = (ExprM(vars, m=B.loc[I, IG]) * N.loc(K, IG).sum(K)).sum(IG)

            CNEQ = (right - left)
            CNEQ.write(count, filename)
            if test_values:
                CNEQ.test(vars.initialVals)
            # print(CNEQ)

            #  KSEQ(K,IG).. KS(K,IG)    =E= KS0(K,IG) * ( 1 - DEPR) + N(K,IG) ;
            print('KSEQ(K,IG)')
            line = ExprM(vars, m=KS0.loc[K, IG] * (1 - DEPR)) + N.loc(K, IG)

            KSEQ = (line - KS.loc(K, IG))
            KSEQ.write(count, filename)
            if test_values:
                KSEQ.test(vars.initialVals)
            # print(KSEQ)

            # LSEQ1(H).. HW(H)/HH(H)   =E= (HW0(H)/HH0(H))
            #                              *((SUM(L, RA(L) / RA0(L))/24)/ (CPI(H) / CPI0(H))*(SUM((Z,L), FD(L,Z))/(SUM(H1, HW(H1)* SUM(L, JOBCOR(H1,L)))+ SUM(CM, CMO(CM)) + SUM(L,CMI(L))))+ SUM((CM,L), EXWGEO(CM)/RA0(L))/72 *(SUM(CM, CMO(CM))/(SUM(H1, HW(H1)* SUM(L,JOBCOR(H1,L)))+ SUM(CM, CMO(CM)) +SUM(L,CMI(L)))))** (ETARA(H))
            #                              * ( SUM(G, TP(H,G) / CPI(H) )/ SUM(G, TP(H,G) / CPI0(H) )) ** ETAPT(H)
            #                              *  ((SUM(GI, PIT0(GI,H)* HH0(H))+ SUM(G, TAUH(G,H)*HH0(H)))/(SUM(GI, PIT(GI,H)* HH(H))+ SUM(G, TAUH(G,H)*HH(H))))**(ETAPIT(H));
            print('LSEQ1(H)')
            line1 = ExprM(vars, m=HW0.loc[H] / HH0.loc[H])
            LSEQ1line2pre = FD.loc(L, Z).sum(1)
            line2 = (((RA.loc(L) / ExprM(vars, m=RA0.loc[L])).sum(L) / 24) / (CPI.loc(H) / ExprM(vars, m=CPI0.loc[H])) \
                     * (LSEQ1line2pre.sum(0) / (
                            (HW.loc(H1) * ExprM(vars, m=JOBCOR.loc[H1, L].sum(1))).sum(H1) + CMO.loc(CM).sum(CM) + CMI.loc(
                        L).sum(L))) \
                     + (ExprM(vars, m=EXWGEO.loc[CM].sum(0) * RA0.loc[L].sum(0) / 72) \
                        * (CMO.loc(CM).sum(CM) / (
                                    (HW.loc(H1) * ExprM(vars, m=JOBCOR.loc[H1, L].sum(1))).sum(H1) + CMO.loc(CM).sum(
                                CM) + CMI.loc(L).sum(L))))) \
                    ** ExprM(vars, m=ETARA.loc[H])
            line3 = ((ExprM(vars, m=TP.loc[H, G]) / CPI.loc(H)).sum(G) / (
                    ExprM(vars, m=TP.loc[H, G]) / ExprM(vars, m=CPI0.loc[H])).sum(G)) ** ExprM(vars, m=ETAPT.loc[H])
            line4 = (((ExprM(vars, m=PIT0.loc[GI, H]) * ExprM(vars, m=HH0.loc[H])).sum(GI) + (
                    ExprM(vars, m=TAUH.loc[G, H]) * ExprM(vars, m=HH0.loc[H])).sum(G)) \
                     / ((ExprM(vars, m=PIT.loc[GI, H]) * HH.loc(H)).sum(GI) + (ExprM(vars, m=TAUH.loc[G, H]) * HH.loc(H)).sum(
                        G))) ** ExprM(vars, m=ETAPIT.loc[H])

            LSEQ1 = ((line1 * line2 * line3 * line4) - HW.loc(H) / HH.loc(H))
            LSEQ1.write(count, filename)
            if test_values:
                LSEQ1.test(vars.initialVals)
            # print(LSEQ1)

            #    LSEQ2A('OUTCOM1').. CMO('OUTCOM1')=E= CMO0('OUTCOM1')* (Sum((F11,IG), FD(F11,IG))/sum((F11,IG), FD0(F11,IG)))**(-ECOMO('OUTCOM1')) ;
            print('LSEQ2A')
            line = ExprM(vars, m=CMO0.loc[CM1]) * (
                    FD.loc(F11, IG).sum(IG).sum(F11) / ExprM(vars, m=FD0.loc[F11, IG].sum(1).sum(0))) ** (
                       ExprM(vars, m=(-1) * ECOMO.loc[CM1]))

            LSEQ2A = (line - CMO.loc(CM1))
            LSEQ2A.write(count, filename)
            if test_values:
                LSEQ2A.test(vars.initialVals)
            # print(LSEQ2A)

            #    LSEQ2B('OUTCOM2').. CMO('OUTCOM2')=E= CMO0('OUTCOM2')* (Sum((F21,IG), FD(F21,IG))/sum((F21,IG), FD0(F21,IG)))**(-ECOMO('OUTCOM2'));
            print('LSEQ2B')
            line = ExprM(vars, m=CMO0.loc[CM2]) * (
                    FD.loc(F21, IG).sum(IG).sum(F21) / ExprM(vars, m=FD0.loc[F21, IG].sum(1).sum(0))) ** (
                       ExprM(vars, m=(-1) * ECOMO.loc[CM2]))

            LSEQ2B = (line - CMO.loc(CM2))
            LSEQ2B.write(count, filename)
            if test_values:
                LSEQ2B.test(vars.initialVals)
            # print(LSEQ2B)

            #    LSEQ2C('OUTCOM3').. CMO('OUTCOM3')=E= CMO0('OUTCOM3')* (sum((F31,IG), FD(F31,IG))/sum((F31,IG), FD0(F31,IG)))** (-ECOMO('OUTCOM3'));
            print('LSEQ2C')
            line = ExprM(vars, m=CMO0.loc[CM3]) * (
                    FD.loc(F31, IG).sum(IG).sum(F31) / ExprM(vars, m=FD0.loc[F31, IG].sum(1).sum(0))) ** (
                       ExprM(vars, m=(-1) * ECOMO.loc[CM3]))

            LSEQ2C = (line - CMO.loc(CM3))
            LSEQ2C.write(count, filename)
            if test_values:
                LSEQ2C.test(vars.initialVals)
            # print(LSEQ2C)

            #    LSEQ3(L).. CMI(L)  =E= CMI0(L)* (Sum(FG, FD(L,FG))/Sum(FG, FD0(L,FG)))**(ECOMI(L));
            print('LSEQ3')
            line = ExprM(vars, m=CMI0.loc[L]) * (
                    (FD.loc(L, FG).sum(FG) / ExprM(vars, m=FD0.loc[L, FG].sum(1))) ** (ExprM(vars, m=ECOMI.loc[L])))

            LSEQ3 = (line - CMI.loc(L))
            LSEQ3.write(count, filename)
            if test_values:
                LSEQ3.test(vars.initialVals)
            # print(LSEQ3)

            #  POPEQ(H).. HH(H)         =E= HH0(H) * NRPG(H)
            #                                + MI0(H) * ((YD(H)/HH(H))/(YD0(H)/HH0(H))/(CPI(H)/CPI0(H))) ** (ETAYD(H))
            #                                         *((HN(H)/HH(H))/(HN0(H)/HH0(H))) ** (ETAU(H))
            #                                         *(sum(HSD, CH(HSD,H))/sum(HSD,CH0(HSD,H)))**(1)
            #                                - MO0(H) *((YD0(H)/HH0(H))/(YD(H)/HH(H))/(CPI0(H)/CPI(H))) ** (ETAYD(H))
            #                                         *((HN0(H)/HH0(H))/(HN(H)/HH(H))) ** (ETAU(H))
            #                                         *(sum(HSD, CH0(HSD,H))/sum(HSD,CH(HSD,H)))**(1)  ;

            print('POPEQ(H)')
            line1 = ExprM(vars, m=HH0.loc[H] * NRPG.loc[H])
            line2 = ExprM(vars, m=MI0.loc[H]) * ((YD.loc(H) / HH.loc(H)) / ExprM(vars, m=YD0.loc[H] / HH0.loc[H]) / (
                    CPI.loc(H) / ExprM(vars, m=CPI0.loc[H]))) ** ExprM(vars, m=ETAYD.loc[H])
            line3 = ((HN.loc(H) / HH.loc(H)) / ExprM(vars, m=HN0.loc[H] / HH0.loc[H])) ** ExprM(vars, m=ETAU.loc[H])
            line4 = (CH.loc(HSD, H).sum(HSD) / ExprM(vars, m=CH0.loc[HSD, H].sum(0))) ** (1)
            line5 = ExprM(vars, m=MO0.loc[H]) * (ExprM(vars, m=YD0.loc[H] / HH0.loc[H]) / (YD.loc(H) / HH.loc(H)) / (
                    ExprM(vars, m=CPI0.loc[H]) / CPI.loc(H))) ** ExprM(vars, m=ETAYD.loc[H])
            line6 = (ExprM(vars, m=HN0.loc[H] / HH0.loc[H]) / (HN.loc(H) / HH.loc(H))) ** ExprM(vars, m=ETAU.loc[H])
            line7 = (ExprM(vars, m=CH0.loc[HSD, H].sum(0)) / CH.loc(HSD, H).sum(HSD)) ** (1)

            POPEQ = (line1 + line2 * line3 * line4 - line5 * line6 * line7 - HH.loc(H))
            POPEQ.write(count, filename)
            if test_values:
                POPEQ.test(vars.initialVals)
            # print(POPEQ)

            #  ANEQ(H).. HN(H)          =E= HH(H) - HW(H);
            print('ANEQ(H)')
            line = HH.loc(H) - HW.loc(H)

            ANEQ = (line - HN.loc(H))
            ANEQ.write(count, filename)
            if test_values:
                ANEQ.test(vars.initialVals)
            # print(ANEQ)

            #  YGEQ(GX).. Y(GX)         =E=   SUM(I, TAUV(GX,I) * V(I) * P(I) )
            #                                 + SUM(I, TAUX(GX,I)* CX(I) *PD(I))
            #                                 + SUM((H,I), TAUC(GX,I) * CH(I,H) * P(I) )
            #                                 + SUM(I, TAUN(GX,I) * CN(I) * P(I) )
            #                                 + SUM((GN,I), TAUG(GX,I) * CG(I,GN) * P(I) )
            #                                 + SUM((F,I), TAUFX(GX,F,I) * RA(F) * R(F,I) * TT(F,I)*FD(F,I) )
            #                                 + SUM((F,GN), TAUFX(GX,F,GN) * RA(F) * R(F,GN) * FD(F,GN) )
            #                                 + SUM(F, TAUFH(GX,F) * (Y(F)))
            #                                 + SUM(H, PIT0(GX,H) * Y(H) )
            #                                 + SUM(H, TAUH(GX,H) * HH(H) )
            #                                 + SUM(GX1, IGT(GX,GX1));
            print('YGEQ')
            line1 = (ExprM(vars, m=TAUV.loc[GX, I]) * V.loc(I) * P.loc(I)).sum(I)
            line2 = (ExprM(vars, m=TAUX.loc[GX, I]) * CX.loc(I) * PD.loc(I)).sum(I)

            YGEQline3pre = ExprM(vars, m=pd.DataFrame(index=GX, columns=H).fillna(0.0))  # first just set it to correct size
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

            YGEQ = ((line1 + line2 + line3 + line4 + line5 + line6 + line7 + line8 + line9 + line10 + line11) - Y.loc(GX))
            YGEQ.write(count, filename)
            if test_values:
                YGEQ.test(vars.initialVals)
            # print(YGEQ)

            #    YGEQ2(GT).. Y(GT)        =E= SUM(GX, IGT(GT,GX));
            print('YGEQ2(GT)')
            line = IGT.loc(GT, GX).sum(GX)

            YGEQ2 = (line - Y.loc(GT))
            YGEQ2.write(count, filename)
            if test_values:
                YGEQ2.test(vars.initialVals)
            # print(YGEQ2)

            # YGEQM(GNLM)..  Y(GNLM)   =E= TAXS1(GNLM)*Y('CYGFM');
            print('YGEQM(GNLM)')
            line = ExprM(vars, m=TAXS1.loc[GNLM]) * Y.loc(['CYGFM'])

            YGEQM = (line - Y.loc(GNLM))
            YGEQM.write(count, filename)
            if test_values:
                YGEQM.test(vars.initialVals)
            # print(YGEQM)

            # YGEQO(GNLO)..  Y(GNLO)   =E= TAXS2(GNLO)*Y('CYGFO');
            print('YGEQO(GNLO)')
            line = ExprM(vars, m=TAXS2.loc[GNLO]) * Y.loc(['CYGFO'])

            YGEQO = (line - Y.loc(GNLO))
            YGEQO.write(count, filename)
            if test_values:
                YGEQO.test(vars.initialVals)
            # print(YGEQ1)

            #  GOVFOR(G).. GVFOR(G)     =E= GFOR(G)*Y(G);
            print('GOVFOR(G)')
            line = ExprM(vars, m=GFOR.loc[G]) * Y.loc(G)

            GOVFOR = (line - GVFOR.loc(G))
            GOVFOR.write(count, filename)
            if test_values:
                GOVFOR.test(vars.initialVals)
            # print(GOVFOR)

            #  CGEQ(I,GN).. P(I)*(1 + SUM(GS, TAUG(GS,I))) * CG(I,GN)
            #                         =E= AG(I,GN) * (Y(GN)+ GFOR(GN)*Y(GN));
            print('CGEQ(I,GN)')
            left = P.loc(I) * ExprM(vars, m=1 + TAUG.loc[GS, I].sum(0)) * CG.loc(I, GN)
            right = ExprM(vars, m=AG.loc[I, GN]) * (Y.loc(GN) + ExprM(vars, m=GFOR.loc[GN]) * Y.loc(GN))

            CGEQ = (right - left)
            CGEQ.write(count, filename)
            if test_values:
                CGEQ.test(vars.initialVals)
            # print(CGEQ)

            #  GFEQ(F,GN)..  FD(F,GN) * R(F,GN) * RA(F)*( 1 + SUM(GF, TAUFX(GF,F,GN)))
            #                         =E= AG(F,GN) * (Y(GN)+ GFOR(GN)*Y(GN));
            print('GFEQ(F,GN)')
            left = FD.loc(F, GN) * R.loc(F, GN) * RA.loc(F) * (1 + ExprM(vars, m=TAUFX_SUM.loc[F, GN]))
            right = ExprM(vars, m=AG.loc[F, GN]) * (Y.loc(GN) + ExprM(vars, m=GFOR.loc[GN]) * Y.loc(GN))

            GFEQ = left - right
            GFEQ.write(count, filename)
            if test_values:
                GFEQ.test(vars.initialVals)
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
            if test_values:
                GSEQL.test(vars.initialVals)
            # print(GSEQL)

            #  GSEQ(GX).. S(GX)         =E= (Y(GX) + GFOR(GX)*Y(GX)) - SUM(H, (TP(H,GX)*HH(H))) - SUM(G,IGT(G,GX));
            print('GSEQ(GX)')
            line1 = (Y.loc(GX) + ExprM(vars, m=GFOR.loc[GX]) * Y.loc(GX))
            line2 = (ExprM(vars, m=TP.loc[H, GX]) * HH.loc(H)).sum(H)
            line3 = IGT.loc(G, GX).sum(G)

            GSEQ = ((line1 - ~line2 - ~line3) - S.loc(GX))
            GSEQ.write(count, filename)
            if test_values:
                GSEQ.test(vars.initialVals)
            # print(GSEQ)

            #  TDEQ(G,GX)$(IGTD(G,GX) EQ 1).. IGT(G,GX)
            #                         =E= TAXS(G,GX)*(Y(GX) + GVFOR(GX)- SUM(H, (TP(H,GX)*HH(H))));
            print('TDEQ(G,GX)$(IGTD(G,GX) EQ 1)')
            line = ExprM(vars, m=TAXS.loc[G, GX]) * (
                    Y.loc(GX) + GVFOR.loc(GX) - ~(ExprM(vars, m=TP.loc[H, GX]) * HH.loc(H)).sum(H))

            TDEQ = line - IGT.loc(G, GX)
            TDEQ.setCondition(IGTD.loc[G, GX], 'EQ', 1)
            TDEQ.write(count, filename)
            if test_values:
                TDEQ.test(vars.initialVals)
            # print(TDEQ)

            #  SPIEQ.. SPI              =E= SUM(H, Y(H)) + SUM((H,G), TP(H,G)*HH(H)) + SUM(H, PRIVRET(H)*HH(H));
            print('SPIEQ')
            line = Y.loc(H).sum(H) + (ExprM(vars, m=TP.loc[H, G]) * HH.loc(H)).sum() + (
                    ExprM(vars, m=PRIVRET.loc[H]) * HH.loc(H)).sum(H)

            SPIEQ = (line - SPI)
            SPIEQ.write(count, filename)
            if test_values:
                SPIEQ.test(vars.initialVals)
            # print(SPIEQ)

            # LMEQ1(L).. SUM(H, HW(H)* JOBCOR(H, L))+CMI(L) =E= SUM(Z, FD(L ,Z) ) ;
            print('LMEQ1(L)')
            left = (ExprM(vars, m=JOBCOR.loc[H, L]) * HW.loc(H)).sum(H) + CMI.loc(L)
            right = FD.loc(L, Z).sum(Z)

            LMEQ1 = (right - left)
            LMEQ1.write(count, filename)
            if test_values:
                LMEQ1.test(vars.initialVals)
            # print(LMEQ1)

            #  KMEQ(K,IG).. KS(K,IG)    =E= TT(K,IG)*FD(K,IG);
            print('KMEQ(K,IG)')
            KMEQ = ((ExprM(vars, m=TT.loc[K, IG]) * FD.loc(K, IG)) - KS.loc(K, IG))
            KMEQ.write(count, filename)
            if test_values:
                KMEQ.test(vars.initialVals)
            # print(KMEQ)

            #  GMEQ(I).. DS(I)          =E= DD(I) + CX(I) - M(I);
            print('GMEQ(I)')
            GMEQ = (DD.loc(I) + CX.loc(I) - M.loc(I) - DS.loc(I))
            GMEQ.write(count, filename)
            if test_values:
                GMEQ.test(vars.initialVals)
            # print(GMEQ)

            #  DDEQ(I).. DD(I)          =E= V(I) + SUM(H, CH(I,H) ) + SUM(G, CG(I,G) ) + CN(I);
            print('DDEQ(I)')
            DDEQ = (V.loc(I) + CH.loc(I, H).sum(H) + CG.loc(I, G).sum(G) + CN.loc(I) - DD.loc(I))
            DDEQ.write(count, filename)
            if test_values:
                DDEQ.test(vars.initialVals)
            # print(DDEQ)

            # -------------------------------------------------------------------------------------------------------------
            # MODEL CLOSURE
            # -------------------------------------------------------------------------------------------------------------

            # FIX INTER GOVERNMENTAL TRANSFERS TO ZERO IF NOT IN ORIGINAL SAM
            # IGT.FX(G,GX)$(NOT IGT0(G,GX))=0;
            print('IGT.FX(G,GX)$(NOT IGT0(G,GX))=0')
            FX1 = IGT.loc(G, GX)
            FX1.setCondition(IGT0.loc[G, GX], 'EQ', 0)
            FX1.write(count, filename)
            # print(FX1)

            # FIX EXOGENOUS INTERGOVERNMENTAL TRANSFERS
            # IGT.FX(G,GX)$(IGTD(G,GX) EQ 2)=IGT0(G,GX);
            print('IGT.FX(G,GX)$(IGTD(G,GX) EQ 2)=IGT0(G,GX)')
            FX2 = IGT.loc(G, GX) - ExprM(vars, m=IGT0.loc[G, GX])
            FX2.setCondition(IGTD.loc[G, GX], 'EQ', 2)
            FX2.write(count, filename)
            # print(FX2)

            # FIX INTER SECTORAL WAGE DIFFERENTIALS
            # R.FX(L,Z) = R0(L,Z);
            print('R.FX(L,Z)=R0(L,Z)')
            FX3 = R.loc(L, Z) - ExprM(vars, m=R0.loc[L, Z])
            FX3.write(count, filename)
            # print(FX3)

            # FIX ECONOMY WIDE SCALAR
            # RA.FX(K) = RA0(K);
            print('RA.FX(K)=RA0(K)')
            FX4 = RA.loc(K) - ExprM(vars, m=RA0.loc[K])
            FX4.write(count, filename)
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
            opt = SolverFactory(solver, solver_io=solver_io)

            if opt is None:
                print("")
                print("ERROR: Unable to create solver plugin for %s " \
                      "using the %s interface" % (solver, solver_io))
                print("")
                exit(1)

            # Create the model
            model = ConcreteModel()
            set_variable(cons_filename)
            set_equation(cons_filename)

            # read the model
            exec(open(cons_filename).read())

            # Declare all suffixes
            # Ipopt bound multipliers (obtained from solution)
            model.ipopt_zL_out = Suffix(direction=Suffix.IMPORT)
            model.ipopt_zU_out = Suffix(direction=Suffix.IMPORT)

            # Ipopt bound multipliers (sent to solver)
            model.ipopt_zL_in = Suffix(direction=Suffix.EXPORT)
            model.ipopt_zU_in = Suffix(direction=Suffix.EXPORT)

            # Obtain dual solutions from first solve and send to warm start
            model.dual = Suffix(direction=Suffix.IMPORT_EXPORT)

            ### Set Ipopt options for warm-start
            # The current values on the ipopt_zU_out and ipopt_zL_out suffixes will be used as
            # initial conditions for the bound multipliers to solve the new problem
            model.ipopt_zL_in.update(model.ipopt_zL_out)
            model.ipopt_zU_in.update(model.ipopt_zU_out)
            opt.options['warm_start_init_point'] = 'yes'
            opt.options['warm_start_bound_push'] = 1e-6
            opt.options['warm_start_mult_bound_push'] = 1e-6
            opt.options['mu_init'] = 1e-6

            ### Send the model and suffix information to ipopt and collect the solution
            # The solver plugin will scan the model for all active suffixes
            # valid for importing, which it will store into the results object

            results = opt.solve(model, keepfiles=keepfiles, tee=stream_solver)

            x = [None for i in range(vars.nvars)]

            with open(temp_file_name, 'w') as f:
                for i in range(vars.nvars):
                    f.write('x[' + str(i) + ']=value(model.x' + str(i) + ')\n')

            exec(open(temp_file_name).read())

            soln.append(x[:])

            return None


        '''
        Calibrate the model 
        '''
        soln = []
        # filename = os.path.join(filePath, "ipopt_cons.py")
        filename = 'ipopt_cons.py'
        # tmp = os.path.join(filePath, "tmp.py")
        tmp = 'tmp.py'
        print("Calibration: ")
        run_solver(filename, tmp)

        '''
        Simulation code below:
        In each simulation:
        
        1. Apply simulation code (for instance PI(I) = 1.02).
        2. Rewrite all equations
        3. Solve the new model with the result from last run as initial guess.
        
        '''

        ############ begin shock by using tables

        # iNum = 1 # dynamic model itterations

        sims = pd.read_csv(os.path.join(filePath, 'SIMS 500.csv'), index_col=0)
        iNum = 1
        # iNum = len(sims.columns)
        KS00 = KS0.copy()

        for num in range(iNum):
            # print("Simulation: ", num+1)
            KS0.loc[K, I] = KS00.loc[K, I].mul(sims.iloc[:, num])
            run_solver(filename, tmp)

        # create output
        CG0 = vars.get('CG', x=soln[0])
        CH0 = vars.get('CH', x=soln[0])
        CMI0 = vars.get('CMI', x=soln[0])
        CMO0 = vars.get('CMO', x=soln[0])
        CN0 = vars.get('CN', x=soln[0])
        CPI0 = vars.get('CPI', x=soln[0])
        CX0 = vars.get('CX', x=soln[0])
        D0 = vars.get('D', x=soln[0])
        DD0 = vars.get('DD', x=soln[0])
        DS0 = vars.get('DS', x=soln[0])
        FD0 = vars.get('FD', x=soln[0])
        IGT0 = vars.get('IGT', x=soln[0])
        KS0 = vars.get('KS', x=soln[0])
        #LAS0 = vars.get('LAS', x=soln[0])
        HH0 = vars.get('HH', x=soln[0])
        HN0 = vars.get('HN', x=soln[0])
        HW0 = vars.get('HW', x=soln[0])
        M0 = vars.get('M', x=soln[0])
        N0 = vars.get('N', x=soln[0])
        NKI0 = vars.get('NKI', x=soln[0])
        #LNFOR0 = vars.get('LNFOR', x=soln[0])
        KPFOR0 = vars.get('KPFOR', x=soln[0])
        GVFOR0 = vars.get('GVFOR', x=soln[0])
        P0 = vars.get('P', x=soln[0])
        PD0 = vars.get('PD', x=soln[0])
        PVA0 = vars.get('PVA', x=soln[0])
        RA0 = vars.get('RA', x=soln[0])
        R0 = vars.get('R', x=soln[0])
        S0 = vars.get('S', x=soln[0])
        SPI0 = vars.get('SPI', x=soln[0])
        V0 = vars.get('V', x=soln[0])
        Y0 = vars.get('Y', x=soln[0])
        YD0 = vars.get('YD', x=soln[0])

        emplist = []
        dsrlist = []
        dsclist = []
        hhinclist = []
        miglist = []
        simlist = []

        for i in range(iNum):
            CGL = vars.get('CG', x=soln[i+1])
            CHL = vars.get('CH', x=soln[i+1])
            CMIL = vars.get('CMI', x=soln[i+1])
            CMOL = vars.get('CMO', x=soln[i+1])
            CNL = vars.get('CN', x=soln[i+1])
            CPIL = vars.get('CPI', x=soln[i+1])
            CXL = vars.get('CX', x=soln[i+1])
            DL = vars.get('D', x=soln[i+1])
            DDL = vars.get('DD', x=soln[i+1])
            DSL = vars.get('DS', x=soln[i+1])
            FDL = vars.get('FD', x=soln[i+1])
            IGTL = vars.get('IGT', x=soln[i+1])
            KSL = vars.get('KS', x=soln[i+1])
            #LASL = vars.get('LAS', x=soln[i+1])
            HHL = vars.get('HH', x=soln[i+1])
            HNL = vars.get('HN', x=soln[i+1])
            HWL = vars.get('HW', x=soln[i+1])
            ML = vars.get('M', x=soln[i+1])
            NL = vars.get('N', x=soln[i+1])
            NKIL = vars.get('NKI', x=soln[i+1])
            #LNFORL = vars.get('LNFOR', x=soln[i+1])
            KPFORL = vars.get('KPFOR', x=soln[i+1])
            GVFORL = vars.get('GVFOR', x=soln[i+1])
            PL = vars.get('P', x=soln[i+1])
            PDL = vars.get('PD', x=soln[i+1])
            PVAL = vars.get('PVA', x=soln[i+1])
            RAL = vars.get('RA', x=soln[i+1])
            RL = vars.get('R', x=soln[i+1])
            SL = vars.get('S', x=soln[i+1])
            SPIL = vars.get('SPI', x=soln[i+1])
            VL = vars.get('V', x=soln[i+1])
            YL = vars.get('Y', x=soln[i+1])
            YDL = vars.get('YD', x=soln[i+1])

            DFCG = CGL - CG0
            DFFD = FDL - FD0
            DK = KSL - KS0
            DY = (YL/CPIL) - Y0
            DDS = DSL - DS0
            DDD = DDL - DD0
            DCX = CXL - CX0
            DCH = CHL - CH0
            DR = RL - R0
            DCMI = CMIL - CMI0
            DCMO = CMOL - CMO0
            DM = ML - M0
            DV = VL - V0
            DN = NL - N0

            s_name = 'Simulation ' + str(i+1)

            emp = DFFD[DFFD.index.isin(['L1A', 'L2A', 'L3A', 'L1B', 'L2B', 'L3B', 'L1C', 'L2C', 'L3C', \
                                        'L1D', 'L2D', 'L3D', 'L1E', 'L2E', 'L3E', 'L1F', 'L2F', 'L3F', \
                                        'L1G', 'L2G', 'L3G', 'L1H', 'L2H', 'L3H'])].sum().sum()
            dsr = DDS[DDS.index.isin(['HS1A', 'HS1B', 'HS1C', 'HS1D', 'HS1E', 'HS1F', 'HS1G', 'HS1H', \
                                      'HS2A', 'HS2B', 'HS2C', 'HS2D', 'HS2E', 'HS2F', 'HS2G', 'HS2H', \
                                      'HS3A', 'HS3B', 'HS3C', 'HS3D', 'HS3E', 'HS3F', 'HS3G', 'HS3H'])].sum()
            dsc = DDS[DDS.index.isin(['GOODSA', 'TRADEA', 'OTHERA', 'GOODSB', 'TRADEB', 'OTHERB', 'GOODSC', 'TRADEC', 'OTHERC', 'GOODSD', 'TRADED', 'OTHERD', \
                                      'GOODSE', 'TRADEE', 'OTHERE', 'GOODSF', 'TRADEF', 'OTHERF', 'GOODSG', 'TRADEG', 'OTHERG', 'GOODSH', 'TRADEH', 'OTHERH'])].sum()
            hhinc = DY[DY.index.isin(['HH1A', 'HH2A', 'HH3A', 'HH4A', 'HH5A', 'HH1B', 'HH2B', 'HH3B', 'HH4B', 'HH5B', 'HH1C', 'HH2C', 'HH3C', 'HH4C', 'HH5C', \
                                      'HH1D', 'HH2D', 'HH3D', 'HH4D', 'HH5D', 'HH1E', 'HH2E', 'HH3E', 'HH4E', 'HH5E', 'HH1F', 'HH2F', 'HH3F', 'HH4F', 'HH5F', \
                                      'HH1G', 'HH2G', 'HH3G', 'HH4G', 'HH5G', 'HH1H', 'HH2H', 'HH3H', 'HH4H', 'HH5H'])].sum()
            hhdiff = HHL-HH0
            mig = hhdiff.sum()

            emplist.append(emp)
            dsrlist.append(dsr)
            dsclist.append(dsc)
            hhinclist.append(hhinc)
            miglist.append(mig)
            simlist.append(s_name)

        cols = {'dsc': dsclist, 'dsr': dsrlist, 'mig': miglist, 'emp': emplist, 'hhinc': hhinclist}

        df = pd.DataFrame.from_dict(cols)
        df.to_csv('simulation_outputs.csv')
        print("simulation_outpus.csv has been created.")


if __name__ == '__main__':
    is_cd = False
    test_values = False
    main_calc(is_cd, test_values)