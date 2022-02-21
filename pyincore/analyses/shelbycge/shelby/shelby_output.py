"""
# After running a model, use solution dictionaries to replicate GAMS
# results with DataFrames
#
# NOTE:
# solution variables stored in "vars" and "soln" objects should
# be the primary source for model evaluation.
# This swas only created to assist those unfamiliar with python objects
"""

#from jopSmall.OutputFunctions import baseValue, newValue, getDiff
import pandas as pd
    
#CG0
CG0 = vars.get('CG', x=soln[0])

#CH0
CH0 = vars.get('CH', x=soln[0])

#CMI0
CMI0 = vars.get('CMI', x=soln[0])

#CMO0
CMO0 = vars.get('CMO', x=soln[0])

#CN0
CN0 = vars.get('CN', x=soln[0])

#CPI0
CPI0 = vars.get('CPI', x=soln[0])

#CX0
CX0 = vars.get('CX', x=soln[0])

#D0
D0 = vars.get('D', x=soln[0])

#DD0
DD0 = vars.get('DD', x=soln[0])

#DS0
DS0 = vars.get('DS', x=soln[0])

#FD
FD0 = vars.get('FD', x=soln[0])

#IGT
IGT0 = vars.get('IGT', x=soln[0])

#KS
KS0 = vars.get('KS', x=soln[0])

#LAS
#LAS0 = vars.get('LAS', x=soln[0])

#HH
HH0 = vars.get('HH', x=soln[0])

#HN
HN0 = vars.get('HN', x=soln[0])

#HW
HW0 = vars.get('HW', x=soln[0])

#M
M0 = vars.get('M', x=soln[0])

#N
N0 = vars.get('N', x=soln[0])

#NKI
NKI0 = vars.get('NKI', x=soln[0])

#LNFOR
#LNFOR0 = vars.get('LNFOR', x=soln[0])

#KPFOR
KPFOR0 = vars.get('KPFOR', x=soln[0])

#GVFOR
GVFOR0 = vars.get('GVFOR', x=soln[0])

#P
P0 = vars.get('P', x=soln[0])

#PD
PD0 = vars.get('PD', x=soln[0])

#PVA
PVA0 = vars.get('PVA', x=soln[0])

#RA
RA0 = vars.get('RA', x=soln[0])

#R
R0 = vars.get('R', x=soln[0])

#S
S0 = vars.get('S', x=soln[0])

#SPI
SPI0 = vars.get('SPI', x=soln[0])

#V
V0 = vars.get('V', x=soln[0])

#Y
Y0 = vars.get('Y', x=soln[0])

#Yd
YD0 = vars.get('YD', x=soln[0])

# DIFFERENCES
writer = pd.ExcelWriter('test.xlsx',engine='xlsxwriter')   
workbook=writer.book

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
    
    
    emp = DFFD[DFFD.index.isin(['L1A', 'L2A', 'L3A', 'L1B', 'L2B', 'L3B', 'L1C', 'L2C', 'L3C',
                                'L1D', 'L2D', 'L3D', 'L1E', 'L2E', 'L3E', 'L1F', 'L2F', 'L3F',
                                'L1G', 'L2G', 'L3G', 'L1H', 'L2H', 'L3H'])].sum().sum()
    dsr = DDS[DDS.index.isin(['HS1A', 'HS1B', 'HS1C', 'HS1D', 'HS1E', 'HS1F', 'HS1G', 'HS1H',
                              'HS2A', 'HS2B', 'HS2C', 'HS2D', 'HS2E', 'HS2F', 'HS2G', 'HS2H',
                              'HS3A', 'HS3B', 'HS3C', 'HS3D', 'HS3E', 'HS3F', 'HS3G', 'HS3H'])].sum()
    dsc = DDS[DDS.index.isin(['GOODSA', 'TRADEA', 'OTHERA', 'GOODSB', 'TRADEB', 'OTHERB', 'GOODSC', 'TRADEC', 'OTHERC', 'GOODSD', 'TRADED', 'OTHERD',
                              'GOODSE', 'TRADEE', 'OTHERE', 'GOODSF', 'TRADEF', 'OTHERF', 'GOODSG', 'TRADEG', 'OTHERG', 'GOODSH', 'TRADEH', 'OTHERH'])].sum()
    hhinc = DY[DY.index.isin(['HH1A', 'HH2A', 'HH3A', 'HH4A', 'HH5A', 'HH1B', 'HH2B', 'HH3B', 'HH4B', 'HH5B', 'HH1C', 'HH2C', 'HH3C', 'HH4C', 'HH5C',
                              'HH1D', 'HH2D', 'HH3D', 'HH4D', 'HH5D', 'HH1E', 'HH2E', 'HH3E', 'HH4E', 'HH5E', 'HH1F', 'HH2F', 'HH3F', 'HH4F', 'HH5F',
                              'HH1G', 'HH2G', 'HH3G', 'HH4G', 'HH5G', 'HH1H', 'HH2H', 'HH3H', 'HH4H', 'HH5H'])].sum()
    hhdiff = HHL-HH0
    mig = hhdiff.sum()
    
    emplist.append(emp)
    dsrlist.append(dsr)
    dsclist.append(dsc)
    hhinclist.append(hhinc)
    miglist.append(mig)
    simlist.append(s_name)
    


cols = {'dsc' : dsclist,
        'dsr' : dsrlist,
        'mig' : miglist,
        'emp' : emplist,
        'hhinc' : hhinclist}

df = pd.DataFrame.from_dict(cols)
df.to_csv('simulation_outputs.csv')
