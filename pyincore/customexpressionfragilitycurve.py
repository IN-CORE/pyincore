# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from pyincore.dfr3curve import DFR3Curve


class CustomExpressionFragilityCurve(DFR3Curve):

    def __init__(self, curve_parameters):
        self.expression = curve_parameters['expression']

        super(CustomExpressionFragilityCurve, self).__init__(curve_parameters)

    def compute_limit_state(self):
        pass

    def plot(self):
        pass
    