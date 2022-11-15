"""
functions for output validation

# NOTE:
This is a hack to create dataframes that resemble matrix results
returned in GAMS
"""

import pandas as pd


# Return initial values function
def base_value(vars, eqName):
    if vars.get_info(eqName)['size'] == 1:
        basevalues = vars.initialVals[vars.get_index(eqName)]

    else:
        rows = vars.get_info(eqName)['rows']
        rws = []
        if vars.get_info(eqName)['size'] == vars.get_info(eqName)['nrows']:
            for rr in rows:
                number = vars.initialVals[vars.get_index(eqName, row=rr)]
                rws.append(number)
            basevalues = pd.DataFrame(rws, index=rows)

        else:
            cols = vars.get_info(eqName)['cols']
            for rr in rows:
                clms = []
                for cc in cols:
                    number = vars.initialVals[vars.get_index(eqName, row=rr, col=cc)]
                    clms.append(number)
                rws.append(clms)
            basevalues = pd.DataFrame(rws, index=rows, columns=cols)

    return basevalues


# Get the new values function
def new_value(vars, soln, eqName, ittr):
    #    for scalar
    if vars.get_info(eqName)['size'] == 1:
        newvalue = soln[ittr][vars.get_index(eqName)]

    else:
        rows = vars.get_info(eqName)['rows']
        rws = []
        #       vectors
        if vars.get_info(eqName)['size'] == vars.get_info(eqName)['nrows']:
            for rr in rows:
                number = soln[ittr][vars.get_index(eqName, row=rr)]
                rws.append(number)
            newvalue = pd.DataFrame(rws, index=rows)
        #       data frames
        else:
            cols = []
            for rr in rows:
                cols = vars.get_info(eqName)['cols']
                clms = []
                for cc in cols:
                    number = soln[ittr][vars.get_index(eqName, row=rr, col=cc)]
                    clms.append(number)
                rws.append(clms)
            newvalue = pd.DataFrame(rws, index=rows, columns=cols)

    return newvalue


# Get differences function
def get_diff(vars, soln, eqName, ittr):
    difference = new_value(vars, soln, eqName, ittr) - base_value(vars, eqName)
    return difference
