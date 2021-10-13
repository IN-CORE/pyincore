# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import math

from scipy.stats import norm


# TODO: This will be deprecated when repair curves are migrated to expression based format.
class StandardRepairCurve:
    """A class to represent standard Repair curve."""

    def __init__(self, curve_parameters):
        self.description = curve_parameters['description']
        self.alpha = curve_parameters['alpha']
        self.beta = curve_parameters['beta']
        self.alpha_type = curve_parameters['alphaType']
        self.curve_type = curve_parameters['curveType']

    def calculate_limit_state_probability(self, hazard, period: float = 0.0, std_dev: float = 0.0, **kwargs):
        """Computes limit state probabilities.

            Args:
                hazard (float): A hazard value to compute probability for.
                period (float): A building period default to 0.
                std_dev (float): A standard deviation.
                **kwargs: Keyword arguments.

            Returns:
                float: A limit state probability.

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

