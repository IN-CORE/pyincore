# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
import math

from scipy.stats import norm

from pyincore.models.fragilitycurve import FragilityCurve


class ConditionalStandardFragilityCurve(FragilityCurve):
    """
    class to represent conditional standard fragility curve
    """

    def __init__(self, curve_parameters):
        self.alpha = curve_parameters['alpha']
        self.beta = curve_parameters['beta']
        self.alpha_type = curve_parameters['alphaType']
        self.curve_type = curve_parameters['curveType']
        self.rules = curve_parameters['rules']

        super(ConditionalStandardFragilityCurve, self).__init__(curve_parameters)

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
            index = ConditionalStandardFragilityCurve._fragility_curve_rules_match(self.rules, hazard)
            if index:
                alpha = float(self.alpha[index])
                beta = math.sqrt(math.pow(self.beta[index], 2) + math.pow(std_dev, 2))

                if self.alpha_type == 'median':
                    sp = (math.log(hazard) - math.log(alpha)) / beta
                    probability = norm.cdf(sp)
                elif self.alpha_type == "lambda":
                    x = (math.log(hazard) - alpha) / beta
                    probability = norm.cdf(x)
            else:
                raise ValueError("No matching rule has been found in this conditonal standard fragility curve. "
                                 "Please verify it's the right curve to use.")

        return probability

    @staticmethod
    def _fragility_curve_rules_match(rules, value):
        """
        given value and rules; decide which index to use
        Args:
            rules: index: ["rule1", "rule2"...]
            value: value to be evaluated against

        Returns:
            index (which used to decide which pair of alpha and beta to use)
        """

        # add more operators if needed
        known_operators = {
            "EQ": "==",
            "EQUALS": "==",
            "NEQUALS": "!=",
            "GT": ">",
            "GE": ">=",
            "LT": "<",
            "LE": "<=",
        }

        # if rules is [[]] meaning it matches without any condition
        for index, rule in rules.items():
            # TODO: for now assuming only one rule; in the future need to consider if it's a range
            # TODO: eg. demand GT 3, demand LT 4
            # TODO: for now default it's always using the hazard value as the rule_key

            # the format of a rule is always: rule_key + rule_operator + rule_value
            elements = rule[0].split(" ", 2)

            rule_operator = elements[1]
            if rule_operator not in known_operators.keys():
                raise ValueError(rule_operator + " Unknown. Cannot parse the rules of this mapping!")

            rule_value = elements[2]

            matched = eval(str(value) + known_operators[rule_operator] + rule_value)
            if matched:
                return int(index)

        return None
