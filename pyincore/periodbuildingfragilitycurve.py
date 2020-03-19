# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from pyincore.dfr3curve import DFR3Curve


class PeriodBuildingFragilityCurve(DFR3Curve):

    def __init__(self, curve_parameters):
        self.periodEqnType = curve_parameters['periodEqnType']
        self.periodParam1 = curve_parameters['periodParam1']
        self.periodParam2 = curve_parameters['periodParam2']
        self.periodParam0 = curve_parameters['periodParam0']
        self.fsParam0 = curve_parameters['fsParam0']
        self.fsParam1 = curve_parameters['fsParam1']
        self.fsParam2 = curve_parameters['fsParam2']
        self.fsParam3 = curve_parameters['fsParam3']
        self.fsParam4 = curve_parameters['fsParam4']
        self.fsParam5 = curve_parameters['fsParam5']

        super(PeriodBuildingFragilityCurve, self).__init__(curve_parameters)

    def compute_limit_state(self):
        pass

    def plot(self):
        pass
    