"""
# After running a model, use solution dictionaries to replicate GAMS
# results with DataFrames
#
# NOTE:
# solution variables stored in "vars" and "soln" objects should
# be the primary source for model evaluation.
# This swas only created to assist those unfamiliar with python objects
"""

from seaside.OutputFunctions import baseValue, newValue, getDiff

#CG0
cg0 = baseValue(vars, soln,  'CG')
cgL = newValue(vars, soln, 'CG', iNum)

#CH0
ch0 = baseValue(vars, soln,  'CH')
chL = newValue(vars, soln, 'CH', iNum)

#CMI0
#cmi0 = baseValue(vars, soln,  'CMI')
#cmiL = newValue(vars, soln,  'CMI', iNum)

#CMO0
#cmo0 = baseValue(vars, soln, 'CMO')
#cmoL = newValue(vars, soln,  'CMO', iNum)

#CN0
cn0 = baseValue(vars, soln, 'CN')
cnL = newValue(vars, soln,  'CN', iNum)

#CPI0
cpi0 = baseValue(vars, soln, 'CPI')
cpiL = newValue(vars, soln,  'CPI', iNum)

#CX0
cx0 = baseValue(vars, soln, 'CX')
cxL = newValue(vars, soln,  'CX', iNum)

#D0
d0 = baseValue(vars, soln, 'D')
dL = newValue(vars, soln,  'D', iNum)

#DD0
dd0 = baseValue(vars, soln, 'DD')
ddL = newValue(vars, soln,  'DD', iNum)

#DS0
ds0 = baseValue(vars, soln, 'DS')
dsL = newValue(vars, soln,  'DS', iNum)

#FD
fd0 = baseValue(vars, soln, 'FD')
fdL = newValue(vars, soln, 'FD', iNum)

#IGT
igt0 = baseValue(vars, soln, 'IGT')
igtL = newValue(vars, soln, 'IGT', iNum)

#KS
ks0 = baseValue(vars, soln, 'KS')
ksL = newValue(vars, soln, 'KS', iNum)

#LAS
las0 = baseValue(vars, soln, 'LAS')
lasL = newValue(vars, soln, 'LAS', iNum)

#HH
hh0 = baseValue(vars, soln, 'HH')
hhL = newValue(vars, soln, 'HH', iNum)

#HN
hn0 = baseValue(vars, soln, 'HN')
hnL = newValue(vars, soln, 'HN', iNum)

#HW
hw0 = baseValue(vars, soln, 'HW')
hwL = newValue(vars, soln, 'HW', iNum)

#M
m0 = baseValue(vars, soln, 'M')
mL = newValue(vars, soln, 'M', iNum)

#N
n0 = baseValue(vars, soln, 'N')
nL = newValue(vars, soln, 'N', iNum)

#NKI
nki0 = baseValue(vars, soln, 'NKI')
nkiL = newValue(vars, soln, 'NKI', iNum)

#LNFOR
lnfor0 = baseValue(vars, soln, 'LNFOR')
lnforL = newValue(vars, soln, 'LNFOR', iNum)

#KPFOR
kpfor0 = baseValue(vars, soln, 'KPFOR')
kpforL = newValue(vars, soln, 'KPFOR', iNum)

#GVFOR
gvfor0 = baseValue(vars, soln, 'GVFOR')
gvforL = newValue(vars, soln, 'GVFOR', iNum)

#P
p0 = baseValue(vars, soln, 'P')
pL = newValue(vars, soln, 'P', iNum)

#PD
pd0 = baseValue(vars, soln, 'PD')
pdL = newValue(vars, soln, 'PD', iNum)

#PVA
pva0 = baseValue(vars, soln, 'PVA')
pvaL = newValue(vars, soln, 'PVA', iNum)

#RA
ra0 = baseValue(vars, soln, 'RA')
raL = newValue(vars, soln, 'RA', iNum)

#R
r0 = baseValue(vars, soln, 'R')
rL = newValue(vars, soln, 'R', iNum)

#S
s0 = baseValue(vars, soln, 'S')
sL = newValue(vars, soln, 'S', iNum)

#SPI
spi0 = baseValue(vars, soln, 'SPI')
spiL = newValue(vars, soln, 'SPI', iNum)


#V
v0 = baseValue(vars, soln, 'V')
vL = newValue(vars, soln, 'V', iNum)

#Y
y0 = baseValue(vars, soln, 'Y')
yL = newValue(vars, soln, 'Y', iNum)

#Yd
yd0 = baseValue(vars, soln, 'YD')
ydL = newValue(vars, soln, 'YD', iNum)

# DIFFERENCES

if iNum >= 0:
    #DFCG.L(I,G)      = CG.L(I,G)-CG0(I,G);
    DFCG = getDiff(vars, soln, 'CG', iNum)

    #DFFD.L(F,Z)      = FD.L(F,Z)-FD0(F,Z);
    DFFD = getDiff(vars, soln, 'FD', iNum)

    #DK.L(K,Z)        = FD.L(K,Z)-FD0(K,Z);
    DK = getDiff(vars, soln, 'KS', iNum)

    #DY.L(Z)          = Y.L(Z)-Y0(Z);
    DY = getDiff(vars, soln, 'Y', iNum)

    #DDS.L(I)         = DS.L(I)-DS0(I);
    DDS = getDiff(vars, soln, 'DS', iNum)

    #DDD.L(I)         = DD.L(I) - DD0(I);
    DDD = getDiff(vars, soln, 'DD', iNum)

     #DCX.L(I)         = CX.L(I) -CX0(I);
    DCX = getDiff(vars, soln, 'CX', iNum)

    #DCH.L(I,H)       = CH.L(I,H) - CH0(I,H);
    DCH = getDiff(vars, soln, 'CH', iNum)

    #DRR.L(F,Z)       = R.L(F,Z)-R0(F,Z);
    DR = getDiff(vars, soln, 'R', iNum)

    #DCMI.L(L)        = CMI.L(L) - CMI0(L);
    #dcmi = getDiff(vars, soln, 'CMI', iNum)

    #DCMO.L(CM)       = CMO.L(CM) - CMO0(CM);
    #dcm = getDiff(vars, soln, 'CMO', iNum)

def make_table():

    total_employment_original = FD0.loc[L,I].sum(0).sum(0)
    total_employment_change = vars.get('FD', x=soln[-1]).loc[L,I].sum(0).sum(0) - total_employment_original
    total_employment_percentage = total_employment_change/total_employment_original

    domestic_supply_original = DS0.sum(0)
    domestic_supply_change = vars.get('DS', x=soln[-1]).sum(0) - domestic_supply_original
    domestic_supply_percentage = domestic_supply_change/domestic_supply_original
    
    DY = vars.get('Y', x=soln[-1]) - Y0
    DY.loc[H] = pd.Series(vars.get('Y', x=soln[-1]).loc[H]/vars.get('CPI', x=soln[-1]).loc[H] - Y0.loc[H])

    HH1_change = DY['HH1']
    HH1_percentage = HH1_change/Y0.loc['HH1']

    HH2_change = DY['HH2']
    HH2_percentage = HH2_change/Y0.loc['HH2']

    HH3_change = DY.loc['HH3']
    HH3_percentage = HH3_change/Y0.loc['HH3']

    HH4_change = DY.loc['HH4']
    HH4_percentage = HH4_change/Y0.loc['HH4']

    HH5_change = DY.loc['HH5']
    HH5_percentage = HH5_change/Y0.loc['HH5']

    HH_total_change = HH1_change + HH2_change + HH3_change + HH4_change + HH5_change
    HH_total_original = Y0.loc[H].sum(0)
    HH_total_percentage = HH_total_change/HH_total_original 

    LOCTAX_original = Y0.loc['LOCTAX']
    LOCTAX_change = DY.loc['LOCTAX']
    LOCTAX_percentage = LOCTAX_change/LOCTAX_original

    PROPTX_original = Y0.loc['PROPTX']
    PROPTX_change = DY.loc['PROPTX']
    PROPTX_percentage = PROPTX_change/PROPTX_original

    ACCTAX_original = Y0.loc['ACCTAX']
    ACCTAX_change = DY.loc['ACCTAX']
    ACCTAX_percentage = ACCTAX_change/ACCTAX_original

    TAX_total_change = LOCTAX_change + PROPTX_change + ACCTAX_change
    TAX_total_original = LOCTAX_original + PROPTX_original + ACCTAX_original
    TAX_total_percentage = TAX_total_change/TAX_total_original

    table = pd.DataFrame({'Seaside': ['Total Employment', 'Domestic Supply(mil of $)', 
                        'Real Household Income(mil of $)', 'HH1', 'HH2', 'HH3', 'HH4', 'HH5', 'Total',
                        'Local Tax Revenue(mil of $)', 'LOCTAX', 'PROPTX', 'ACCTAX', 'Total'],
             'Amount of Change': ['{:.2f}'.format(total_employment_change), '{:.2f}'.format(domestic_supply_change), '',
                                  '{:.2f}'.format(HH1_change), '{:.2f}'.format(HH2_change), '{:.2f}'.format(HH3_change), '{:.2f}'.format(HH4_change), '{:.2f}'.format(HH5_change), '{:.2f}'.format(HH_total_change), '',
                                  '{:.2f}'.format(LOCTAX_change), '{:.2f}'.format(PROPTX_change), '{:.2f}'.format(ACCTAX_change), '{:.2f}'.format(TAX_total_change)],
             'Percent Change': ['{:.2f}%'.format(total_employment_percentage*100), '{:.2f}%'.format(domestic_supply_percentage*100), '',
                                  '{:.2f}%'.format(HH1_percentage*100), '{:.2f}%'.format(HH2_percentage*100), '{:.2f}%'.format(HH3_percentage*100), '{:.2f}%'.format(HH4_percentage*100), '{:.2f}%'.format(HH5_percentage*100), '{:.2f}%'.format(HH_total_percentage*100), '',
                                  '{:.2f}%'.format(LOCTAX_percentage*100), '{:.2f}%'.format(PROPTX_percentage*100), '{:.2f}%'.format(ACCTAX_percentage*100), '{:.2f}%'.format(TAX_total_percentage*100)]
             })

    table.to_csv(index=False, path_or_buf = 'output.csv')

make_table()

'''
def make_table():

    total_employment_original = FD0.loc[L,I].sum(0).sum(0)
    total_employment_change = vars.get('FD', x=soln[-1]).loc[F,I].sum(0).sum(0) - total_employment_original
    total_employment_percentage = total_employment_change/total_employment_original

    domestic_supply_original = DS0.sum(0)
    domestic_supply_change = vars.get('DS', x=soln[-1]).sum(0) - domestic_supply_original
    domestic_supply_percentage = domestic_supply_change/domestic_supply_original

    HH_after = vars.get('HH', x=soln[-1])

    HH1_original = HH0.loc['HH1']
    HH1_after = HH_after.loc['HH1']
    HH1_change = HH1_after - HH1_original
    HH1_percentage = HH1_change/HH1_original

    HH2_original = HH0.loc['HH2']
    HH2_after = HH_after.loc['HH2']
    HH2_change = HH2_after - HH2_original
    HH2_percentage = HH2_change/HH2_original

    HH3_original = HH0.loc['HH3']
    HH3_after = HH_after.loc['HH3']
    HH3_change = HH3_after - HH3_original
    HH3_percentage = HH3_change/HH3_original

    HH4_original = HH0.loc['HH4']
    HH4_after = HH_after.loc['HH4']
    HH4_change = HH4_after - HH4_original
    HH4_percentage = HH4_change/HH4_original

    HH5_original = HH0.loc['HH5']
    HH5_after = HH_after.loc['HH5']
    HH5_change = HH5_after - HH5_original
    HH5_percentage = HH5_change/HH5_original

    HH_total_change = HH1_change + HH2_change + HH3_change + HH4_change + HH5_change
    HH_total_original = HH1_original + HH2_original + HH3_original + HH4_original + HH5_original
    HH_total_percentage = HH_total_change/HH_total_original

    Y_after = vars.get('Y', x=soln[-1]) 

    LOCTAX_original = Y0.loc['LOCTAX']
    LOCTAX_after = Y_after.loc['LOCTAX']
    LOCTAX_change = LOCTAX_after - LOCTAX_original
    LOCTAX_percentage = LOCTAX_change/LOCTAX_original

    PROPTX_original = Y0.loc['PROPTX']
    PROPTX_after = Y_after.loc['PROPTX']
    PROPTX_change = PROPTX_after - PROPTX_original
    PROPTX_percentage = PROPTX_change/PROPTX_original

    ACCTAX_original = Y0.loc['ACCTAX']
    ACCTAX_after = Y_after.loc['ACCTAX']
    ACCTAX_change = ACCTAX_after - ACCTAX_original
    ACCTAX_percentage = ACCTAX_change/ACCTAX_original

    TAX_total_change = LOCTAX_change + PROPTX_change + ACCTAX_change
    TAX_total_original = LOCTAX_original + PROPTX_original + ACCTAX_original
    TAX_total_percentage = TAX_total_change/TAX_total_original

    table = pd.DataFrame({'Seaside': ['Total Employment', 'Domestic Supply(mil of $)', 
                        'Real Household Income(mil of $)', 'HH1', 'HH2', 'HH3', 'HH4', 'HH5', 'Total',
                        'Local Tax Revenue(mil of $)', 'LOCTAX', 'PROPTX', 'ACCTAX', 'Total'],
             'Amount of Change': ['{:.2f}'.format(total_employment_change), '{:.2f}'.format(domestic_supply_change), '',
                                  '{:.2f}'.format(HH1_change), '{:.2f}'.format(HH2_change), '{:.2f}'.format(HH3_change), '{:.2f}'.format(HH4_change), '{:.2f}'.format(HH5_change), '{:.2f}'.format(HH_total_change), '',
                                  '{:.2f}'.format(LOCTAX_change), '{:.2f}'.format(PROPTX_change), '{:.2f}'.format(ACCTAX_change), '{:.2f}'.format(TAX_total_change)],
             'Percent Change': ['{:.2f}%'.format(total_employment_percentage*100), '{:.2f}%'.format(domestic_supply_percentage*100), '',
                                  '{:.2f}%'.format(HH1_percentage*100), '{:.2f}%'.format(HH2_percentage*100), '{:.2f}%'.format(HH3_percentage*100), '{:.2f}%'.format(HH4_percentage*100), '{:.2f}%'.format(HH5_percentage*100), '{:.2f}%'.format(HH_total_percentage*100), '',
                                  '{:.2f}%'.format(LOCTAX_percentage*100), '{:.2f}%'.format(PROPTX_percentage*100), '{:.2f}%'.format(ACCTAX_percentage*100), '{:.2f}%'.format(TAX_total_percentage*100)]
             })

    table.to_csv(index=False,path_or_buf = 'output.csv')
'''