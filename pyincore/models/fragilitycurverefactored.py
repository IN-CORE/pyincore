# Copyright (c) 2020 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
from abc import ABC

from pyincore import globals as pyglobals
from pyincore.utils import evaluateexpression
from pyincore.models.fragilitycurve import FragilityCurve

logger = pyglobals.LOGGER


class FragilityCurveRefactored(FragilityCurve, ABC):
    """
    class to represent conditional standard fragility curve
    """

    def __init__(self, curve_parameters):
        self.rules = curve_parameters['rules']
        self.return_type = curve_parameters['returnType']

        for rule in self.rules:
            rule["expression"] = rule["expression"].replace("^", "**")

        super(FragilityCurveRefactored, self).__init__(curve_parameters)

    def calculate_limit_state_probability(self, hazard_values: dict, fragility_curve_parameters: dict, **kwargs):
        """
        Computes limit state probability.
        :param hazard_values: hazard values to compute probability based on demand type
        :param fragility_curve_parameters: set of rules (condition and expression) for each element of the curves
        :key demandType: hazard values the curve uses to compute probability

        :returns: limit state probability
        :rtype: float
        """
        parameters = {}
        mapped_demand_types = {}
        # For all curve parameters:
        # 1. Figure out if parameter name needs to be mapped (i.e. the name contains forbidden characters)
        # 2. Fetch all parameters listed in the curve from kwargs and if there are not in kwargs, use default values
        # from the curve.
        for parameter in fragility_curve_parameters:
            if "key" in parameter:
                mapped_demand_types[parameter["key"]] = parameter["name"]
                if parameter["key"] in kwargs.keys():
                    parameters[parameter["name"]] = kwargs[parameter["key"]]
                else:
                    parameters[parameter["name"]] = None
            elif parameter["name"] in kwargs.keys():
                parameters[parameter["name"]] = kwargs[parameter["name"]]
            elif "expression" in parameter:
                parameters[parameter["name"]] = evaluateexpression.evaluate(parameter["expression"], parameters)
            else:
                parameters[parameter["name"]] = None

        # use hazard values if present
        for key, value in hazard_values.items():
            if key in mapped_demand_types:
                key = mapped_demand_types[key]
            for parameter_key in parameters.keys():
                if parameter_key in key:
                    parameters[parameter_key] = value
        probability = 0.0
        for rule in self.rules:
            if "condition" not in rule:
                probability = evaluateexpression.evaluate(rule["expression"], parameters)
            else:
                conditions_met = []
                for condition in rule["condition"]:
                    if evaluateexpression.evaluate(condition, parameters):
                        conditions_met.append(True)
                    else:
                        conditions_met.append(False)
                        break
                if all(conditions_met):
                    probability = evaluateexpression.evaluate(rule["expression"], parameters)
                    break

        return probability
