# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
import math

from scipy.stats import norm

from pyincore.dfr3curve import DFR3Curve


class PeriodBuildingFragilityCurve(DFR3Curve):

    def __init__(self, curve_parameters):
        self.period_eqn_type = curve_parameters['periodEqnType']
        self.period_param1 = curve_parameters['periodParam1']
        self.period_param2 = curve_parameters['periodParam2']
        self.period_param0 = curve_parameters['periodParam0']
        self.fs_param0 = curve_parameters['fsParam0']
        self.fs_param1 = curve_parameters['fsParam1']
        self.fs_param2 = curve_parameters['fsParam2']
        self.fs_param3 = curve_parameters['fsParam3']
        self.fs_param4 = curve_parameters['fsParam4']
        self.fs_param5 = curve_parameters['fsParam5']

        super(PeriodBuildingFragilityCurve, self).__init__(curve_parameters)

    def calculate_limit_state_probability(self, hazard, period: float = 0.0):
        """
            Computes limit state probabilities.
            Args:
                hazard: hazard value to compute probability for
                period: period of the structure, if applicable

            Returns: limit state probability

        """

        probability = float(0.0)

        if hazard > 0.0:
            # If no period is provided, assumption is 0 since the user should check their
            # data for missing parameters (e.g. number of building stories).
            probability = PeriodBuildingFragilityCurve.compute_period_building_fragility_value(
                hazard, period, self.fs_param0, self.fs_param1, self.fs_param2, self.fs_param3, self.fs_param4,
                self.fs_param5)

        return probability

    @staticmethod
    def compute_period_building_fragility_value(hazard, period, a11_param, a12_param, a13_param, a14_param,
                                                a21_param, a22_param):

        # Assumption from Ergo BuildingLowPeriodSolver
        cutoff_period = 0.87

        probability = 0.0
        if period < cutoff_period:
            multiplier = cutoff_period - period
            surface_eq = (math.log(
                hazard) - cutoff_period * a12_param + a11_param) / (
                                 a13_param + a14_param * cutoff_period)
            probability = norm.cdf(surface_eq + multiplier * (
                    math.log(hazard) - a21_param) / a22_param)
        else:
            probability = norm.cdf(
                (math.log(hazard) - (a11_param + a12_param * period)) / (
                        a13_param + a14_param * period))

        return probability
