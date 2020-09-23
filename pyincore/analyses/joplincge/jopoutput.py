"""
# After running a model, use solution dictionaries to replicate GAMS
# results with DataFrames
#
# NOTE:
# solution variables stored in "vars" and "soln" objects should
# be the primary source for model evaluation.
# This swas only created to assist those unfamiliar with python objects
"""

from pyincore.analyses.joplincge.outputfunctions import base_value, new_value, get_diff

#CG0
cg0 = base_value(vars, soln, 'CG')
cgL = new_value(vars, soln, 'CG', iNum)

#CH0
ch0 = base_value(vars, soln, 'CH')
chL = new_value(vars, soln, 'CH', iNum)

#CMI0
cmi0 = base_value(vars, soln, 'CMI')
cmiL = new_value(vars, soln, 'CMI', iNum)

#CMO0
cmo0 = base_value(vars, soln, 'CMO')
cmoL = new_value(vars, soln, 'CMO', iNum)

#CN0
cn0 = base_value(vars, soln, 'CN')
cnL = new_value(vars, soln, 'CN', iNum)

#CPI0
cpi0 = base_value(vars, soln, 'CPI')
cpiL = new_value(vars, soln, 'CPI', iNum)

#CX0
cx0 = base_value(vars, soln, 'CX')
cxL = new_value(vars, soln, 'CX', iNum)

#D0
d0 = base_value(vars, soln, 'D')
dL = new_value(vars, soln, 'D', iNum)

#DD0
dd0 = base_value(vars, soln, 'DD')
ddL = new_value(vars, soln, 'DD', iNum)

#DS0
ds0 = base_value(vars, soln, 'DS')
dsL = new_value(vars, soln, 'DS', iNum)

#FD
fd0 = base_value(vars, soln, 'FD')
fdL = new_value(vars, soln, 'FD', iNum)

#IGT
igt0 = base_value(vars, soln, 'IGT')
igtL = new_value(vars, soln, 'IGT', iNum)

#KS
ks0 = base_value(vars, soln, 'KS')
ksL = new_value(vars, soln, 'KS', iNum)

#LAS
las0 = base_value(vars, soln, 'LAS')
lasL = new_value(vars, soln, 'LAS', iNum)

#HH
hh0 = base_value(vars, soln, 'HH')
hhL = new_value(vars, soln, 'HH', iNum)

#HN
hn0 = base_value(vars, soln, 'HN')
hnL = new_value(vars, soln, 'HN', iNum)

#HW
hw0 = base_value(vars, soln, 'HW')
hwL = new_value(vars, soln, 'HW', iNum)

#M
m0 = base_value(vars, soln, 'M')
mL = new_value(vars, soln, 'M', iNum)

#N
n0 = base_value(vars, soln, 'N')
nL = new_value(vars, soln, 'N', iNum)

#NKI
nki0 = base_value(vars, soln, 'NKI')
nkiL = new_value(vars, soln, 'NKI', iNum)

#LNFOR
lnfor0 = base_value(vars, soln, 'LNFOR')
lnforL = new_value(vars, soln, 'LNFOR', iNum)

#KPFOR
kpfor0 = base_value(vars, soln, 'KPFOR')
kpforL = new_value(vars, soln, 'KPFOR', iNum)

#GVFOR
gvfor0 = base_value(vars, soln, 'GVFOR')
gvforL = new_value(vars, soln, 'GVFOR', iNum)

#P
p0 = base_value(vars, soln, 'P')
pL = new_value(vars, soln, 'P', iNum)

#PD
pd0 = base_value(vars, soln, 'PD')
pdL = new_value(vars, soln, 'PD', iNum)

#PVA
pva0 = base_value(vars, soln, 'PVA')
pvaL = new_value(vars, soln, 'PVA', iNum)

#RA
ra0 = base_value(vars, soln, 'RA')
raL = new_value(vars, soln, 'RA', iNum)

#R
r0 = base_value(vars, soln, 'R')
rL = new_value(vars, soln, 'R', iNum)

#S
s0 = base_value(vars, soln, 'S')
sL = new_value(vars, soln, 'S', iNum)

#SPI
spi0 = base_value(vars, soln, 'SPI')
spiL = new_value(vars, soln, 'SPI', iNum)


#V
v0 = base_value(vars, soln, 'V')
vL = new_value(vars, soln, 'V', iNum)

#Y
y0 = base_value(vars, soln, 'Y')
yL = new_value(vars, soln, 'Y', iNum)

#Yd
yd0 = base_value(vars, soln, 'YD')
ydL = new_value(vars, soln, 'YD', iNum)

# DIFFERENCES

if iNum >= 0:
    #DFCG.L(I,G)      = CG.L(I,G)-CG0(I,G);
    dfcg = get_diff(vars, soln, 'CG', iNum)

    #DFFD.L(F,Z)      = FD.L(F,Z)-FD0(F,Z);
    dffd = get_diff(vars, soln, 'FD', iNum)

    #DK.L(K,Z)        = FD.L(K,Z)-FD0(K,Z);
    dk = get_diff(vars, soln, 'KS', iNum)

    #DY.L(Z)          = Y.L(Z)-Y0(Z);
    dy = get_diff(vars, soln, 'Y', iNum)

    #DDS.L(I)         = DS.L(I)-DS0(I);
    dds = get_diff(vars, soln, 'DS', iNum)

    #DDD.L(I)         = DD.L(I) - DD0(I);
    ddd = get_diff(vars, soln, 'DD', iNum)

     #DCX.L(I)         = CX.L(I) -CX0(I);
    dcx = get_diff(vars, soln, 'CX', iNum)

    #DCH.L(I,H)       = CH.L(I,H) - CH0(I,H);
    dch = get_diff(vars, soln, 'CH', iNum)

    #DRR.L(F,Z)       = R.L(F,Z)-R0(F,Z);
    dr = get_diff(vars, soln, 'R', iNum)

    #DCMI.L(L)        = CMI.L(L) - CMI0(L);
    dcmi = get_diff(vars, soln, 'CMI', iNum)

    #DCMO.L(CM)       = CMO.L(CM) - CMO0(CM);
    dcm = get_diff(vars, soln, 'CMO', iNum)
