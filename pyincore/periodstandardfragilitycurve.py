# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
# and is available at https://www.mozilla.org/en-US/MPL/2.0/\]=
import math

from scipy.stats import norm

from pyincore.dfr3curve import DFR3Curve


class PeriodStandardFragilityCurve(DFR3Curve):

    def __init__(self, curve_parameters):
        self.alpha = curve_parameters['alpha']
        self.beta = curve_parameters['beta']
        self.alpha_type = curve_parameters['alphaType']
        self.curve_type = curve_parameters['curveType']
        self.period_param2 = curve_parameters['periodParam2']
        self.period_param1 = curve_parameters['periodParam1']
        self.period_param0 = curve_parameters['periodParam0']
        self.period_eqn_type = curve_parameters['periodEqnType']

        super(PeriodStandardFragilityCurve, self).__init__(curve_parameters)

    def get_building_period(self, num_stories):
        """Get building period from the fragility curve.

        Args:
            num_stories (int): Number of building stories.

        Returns:
            float: Building period.

        """
        period = 0.0
        period_equation_type = self.period_eqn_type
        if period_equation_type == 1:
            period = self.period_param0
        elif period_equation_type == 2:
            period = self.period_param0 * num_stories
        elif period_equation_type == 3:
            period = self.period_param1 * math.pow(
                self.period_param0 * num_stories,
                self.period_param2)

        return period

    def calculate_limit_state_probability(self, hazard, period: float = 0.0, std_dev: float = 0.0, **kwargs):
        """
            Computes limit state probabilities.
            Args:
                hazard: hazard value to compute probability for
                std_dev: standard deviation

            Returns: limit state probability

        """
        probability = float(0.0)

        if hazard > 0.0:
            alpha = float(self.alpha)
            beta = math.sqrt(math.pow(self.beta, 2) + math.pow(std_dev, 2))

            if self.alpha_type == 'median':
                sp = (math.log(hazard) - math.log(alpha)) / beta
                probability = norm.cdf(sp)
            elif self.alpha_type == "lambda":
                x = (math.log(hazard) - alpha) / beta
                probability = norm.cdf(x)

        return probability

    def adjust_fragility_for_liquefaction(self, liquefaction: str):
        """Adjusts fragility curve object by input parameter liquefaction.

        Args:
            liquefaction (str): Liquefaction type.

        Returns:
        """
        liquefaction_unified = str(liquefaction).upper()
        if liquefaction_unified == "U":
            multiplier = 0.85
        elif liquefaction_unified == "Y":
            multiplier = 0.65
        else:
            multiplier = 1.0

        self.alpha = self.alpha * multiplier
        self.beta = self.beta
