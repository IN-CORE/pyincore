# Copyright (c) 2020 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
import json
import math
from abc import ABC

from pyincore import globals as pyglobals
from pyincore.utils import evaluateexpression

logger = pyglobals.LOGGER


class FragilityCurve(ABC):
    """A class to represent conditional standard fragility curve."""

    def __init__(self, curve_parameters):
        self.rules = curve_parameters['rules']
        self.return_type = curve_parameters['returnType']

        for rule in self.rules:
            rule["expression"] = rule["expression"].replace("^", "**")
        self.description = curve_parameters['description']

    def calculate_limit_state_probability(self, hazard_values: dict, fragility_curve_parameters: dict, **kwargs):
        """Computes limit state probabilities.

        Args:
            hazard_values (dict): Hazard values.
            fragility_curve_parameters (dict): Fragility curve parameters.
            **kwargs: Keyword arguments.

        Returns:
            float: A limit state probability.

        """
        parameters = {}
        mapped_demand_types = {}
        # For all curve parameters:
        # 1. Figure out if parameter name needs to be mapped (i.e. the name contains forbidden characters)
        # 2. Fetch all parameters listed in the curve from kwargs and if there are not in kwargs, use default values
        # from the curve.
        for parameter in fragility_curve_parameters:
            # if default exists, use default
            if "expression" in parameter and parameter["expression"] is not None:
                parameters[parameter["name"]] = evaluateexpression.evaluate(parameter["expression"], parameters)
            else:
                parameters[parameter["name"]] = None

            # e.g. map point_two_sec_sa to its full name (0.2 Sec Sa)
            if "fullName" in parameter and parameter["fullName"] is not None:
                mapped_demand_types[parameter["fullName"]] = parameter["name"]

            # else overwrite with real values; make sure it handles case sensitivity
            for kwargs_key, kwargs_value in kwargs.items():
                if "fullName" in parameter and parameter["fullName"] is not None:
                    if parameter["fullName"].lower() == kwargs_key.lower():
                        parameters[parameter["name"]] = kwargs_value
                elif parameter["name"].lower() == kwargs_key.lower():
                    parameters[parameter["name"]] = kwargs_value

        probability = 0.0

        # use hazard values if present
        # consider case insensitive situation
        for key, value in hazard_values.items():
            if key in mapped_demand_types:
                key = mapped_demand_types[key]
            for parameter_key in parameters.keys():
                if parameter_key.lower() == key.lower():
                    if value is not None:
                        parameters[parameter_key] = value
                    else:
                        # returning 0 even if a single demand value is None, assumes there is no hazard exposure. TBD
                        return probability

        for rule in self.rules:
            if "condition" not in rule or rule["condition"] is None:
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

        if math.isnan(probability):
            error_msg = "Unable to calculate limit state."
            if self.rules:
                error_msg += " Evaluation failed for expression: \n" + json.dumps(self.rules) + "\n"
                error_msg += "Provided Inputs: \n" + json.dumps(hazard_values) + "\n" + json.dumps(kwargs)

            raise ValueError(error_msg)

        return probability

    def get_building_period(self, fragility_curve_parameters, **kwargs):
        period = 0.0
        num_stories = 1.0
        for parameter in fragility_curve_parameters:
            # if default exists, use default
            if parameter["name"] == "num_stories" and "expression" in parameter and parameter["expression"] is not None:
                num_stories = evaluateexpression.evaluate(parameter["expression"])

            # if exist in building inventory
            for kwargs_key, kwargs_value in kwargs.items():
                if kwargs_key.lower() == "num_stories" and kwargs_value is not None and kwargs_value > 0:
                    num_stories = kwargs_value

            # calculate period
            if parameter["name"] == "period" and "expression" in parameter and parameter["expression"] is not None:
                period = evaluateexpression.evaluate(parameter["expression"], {"num_stories": num_stories})

        return period
