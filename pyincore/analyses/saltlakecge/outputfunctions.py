# Copyright (c) 2021 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
from pyincore.analyses.saltlakecge.equationlib import *
import pandas as pd
import numpy as np


# Return initial values function
def baseValue(vars, soln, eqName):
    if vars.getInfo(eqName)['size'] == 1:
        basevalues = vars.initialVals[vars.getIndex(eqName)]

    else:
        rows = vars.getInfo(eqName)['rows']
        rws = []
        if vars.getInfo(eqName)['size'] == vars.getInfo(eqName)['nrows']:
            for rr in rows:
                number = vars.initialVals[vars.getIndex(eqName, row=rr)]
                rws.append(number)
            basevalues = pd.DataFrame(rws, index=rows)

        else:
            cols = vars.getInfo(eqName)['cols']
            for rr in rows:
                clms = []
                for cc in cols:
                    number = vars.initialVals[vars.getIndex(eqName, row=rr, col=cc)]
                    clms.append(number)
                rws.append(clms)
            basevalues = pd.DataFrame(rws, index=rows, columns=cols)

    return basevalues


# Get the new values function
def newValue(vars, soln, eqName, ittr):
    #    for scalar
    if vars.getInfo(eqName)['size'] == 1:
        newvalue = soln[ittr][vars.getIndex(eqName)]

    else:
        rows = vars.getInfo(eqName)['rows']
        rws = []
        #       vectors
        if vars.getInfo(eqName)['size'] == vars.getInfo(eqName)['nrows']:
            for rr in rows:
                number = soln[ittr][vars.getIndex(eqName, row=rr)]
                rws.append(number)
            newvalue = pd.DataFrame(rws, index=rows)
        #       data frames
        else:
            for rr in rows:
                cols = vars.getInfo(eqName)['cols']
                clms = []
                for cc in cols:
                    number = soln[ittr][vars.getIndex(eqName, row=rr, col=cc)]
                    clms.append(number)
                rws.append(clms)
            newvalue = pd.DataFrame(rws, index=rows, columns=cols)

    return newvalue


# Get differences function
def getDiff(vars, soln, eqName, ittr):
    difference = newValue(vars, soln, eqName, ittr) - baseValue(vars, soln, eqName)
    return difference
