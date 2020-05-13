# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import math

from pyincore.dfr3curve import DFR3Curve


class ParametricFragilityCurve(DFR3Curve):

    def __init__(self, curve_parameters):
        # TODO: not sure if i need to define a class of parameters with "name", "unit", "coefficient" and
        #  "interceptTermDefault" as fixed fields; is it going to be over complicated?
        self.parameters = curve_parameters['parameters']
        self.curve_type = curve_parameters['curveType']

        super(ParametricFragilityCurve, self).__init__(curve_parameters)

    def calculate_limit_state_probability(self, hazard, period: float = 0.0, std_dev: float = 0.0,  **kwargs):
        """

        Args:
            hazard: intercept terms. Unit: g
            **kwargs: interception terms
        Returns: pf (DS) = exp(X*theta')/(1+exp(X*theta'));
        example: pf(DS) = EXP(1 * A0 + log(PGA) * A1 + A2*X2 + ...) / (1 + EXP(1 *A0 + log(PGA) * A1 + ...))
        """
        probability = float(0.0)

        if self.curve_type.lower() == "logit":
            cumulate_term = 0 # X*theta'

            for parameter_set in self.parameters:
                name = parameter_set["name"].lower()
                coefficient = parameter_set["coefficient"]
                default = parameter_set["interceptTermDefault"]
                if name == "demand":
                    cumulate_term += math.log(hazard) * coefficient
                else:
                    if name not in kwargs.keys():
                        cumulate_term += default *coefficient
                    else:
                        cumulate_term += kwargs[name] * coefficient

            probability = math.exp(cumulate_term) / (1 + math.exp(cumulate_term))
        else:
            raise ValueError("Other parametric functions than Logit has not been implemented yet!")

        return probability