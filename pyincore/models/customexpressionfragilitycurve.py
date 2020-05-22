# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
from pyincore import Parser

from pyincore.models.fragilitycurve import FragilityCurve


class CustomExpressionFragilityCurve(FragilityCurve):
    """
    class to represent custom expression fragility curve
    """

    def __init__(self, curve_parameters):
        self.expression = curve_parameters['expression']

        super(CustomExpressionFragilityCurve, self).__init__(curve_parameters)

    def calculate_limit_state_probability(self, hazard, period: float = 0.0, std_dev: float = 0.0, **kwargs):
        raise ValueError("Custom Expression Fragility Curve does not support this limit state calculation method. "
                         "Please use computer_custom_limit_state_probability(variables) instead!")

    def compute_custom_limit_state_probability(self, variables: dict):
        """Computes custom limit state probabilities.
            Args:
                variables: variables to set

            Returns: limit state probability
        """
        expression = self.expression
        parser = Parser()
        probability = parser.parse(expression).evaluate(variables)

        return probability
