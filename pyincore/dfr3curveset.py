# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import collections
import json

from pyincore.dfr3curve import DFR3Curve
from pyincore.customexpressionfragilitycurve import CustomExpressionFragilityCurve
from pyincore.periodbuildingfragilitycurve import PeriodBuildingFragilityCurve
from pyincore.periodstandardfragilitycurve import PeriodStandardFragilityCurve
from pyincore.standardfragilitycurve import StandardFragilityCurve
from pyincore.conditionalstandardfragilitycurve import ConditionalStandardFragilityCurve
from pyincore.parametricfragilitycurve import ParametricFragilityCurve


class DFR3CurveSet:
    """class for dfr3 curves.

    Args:
        metadata (dict): dfr3 curve metadata.

    """

    def __init__(self, metadata):
        self.id = metadata["id"]
        self.demand_type = metadata["demandType"]
        self.demand_units = metadata["demandUnits"]
        self.result_type = metadata["resultType"]
        self.hazard_type = metadata['hazardType']
        self.inventory_type = metadata['inventoryType']

        self.fragility_curves = []
        if 'fragilityCurves' in metadata.keys():
            for fragility_curve in metadata["fragilityCurves"]:

                # if it's already an df3curve object, directly put it in the list:
                if isinstance(fragility_curve, DFR3Curve):
                    self.fragility_curves.append(fragility_curve)
                # based on what type of fragility_curve it is, instantiate different fragility curve object
                else:
                    if fragility_curve['className'] == 'StandardFragilityCurve':
                        self.fragility_curves.append(StandardFragilityCurve(fragility_curve))
                    elif fragility_curve['className'] == 'PeriodBuildingFragilityCurve':
                        self.fragility_curves.append(PeriodBuildingFragilityCurve(fragility_curve))
                    elif fragility_curve['className'] == 'PeriodStandardFragilityCurve':
                        self.fragility_curves.append(PeriodStandardFragilityCurve(fragility_curve))
                    elif fragility_curve['className'] == 'CustomExpressionFragilityCurve':
                        self.fragility_curves.append(CustomExpressionFragilityCurve(fragility_curve))
                    elif fragility_curve['className'] == 'ConditionalStandardFragilityCurve':
                        self.fragility_curves.append(ConditionalStandardFragilityCurve(fragility_curve))
                    elif fragility_curve['className'] == 'ParametricFragilityCurve':
                        self.fragility_curves.append(ParametricFragilityCurve(fragility_curve))
                    else:
                        # TODO make a custom fragility curve class that accept whatever
                        self.fragility_curves.append(fragility_curve)
        elif 'repairCurves' in metadata.keys():
            self.repairCurves = metadata['repairCurves']
        elif 'restorationCurves' in metadata.keys():
            self.restorationCurves = metadata['restorationCurves']
        else:
            raise ValueError("Cannot create dfr3 curve object. Missing key field.")

    @classmethod
    def from_json_str(cls, json_str):
        """Get dfr3set from json string.

        Args:
            json_str (str): JSON of the Dataset.

        Returns:
            obj: dfr3set from JSON.

        """
        return cls(json.loads(json_str))

    @classmethod
    def from_json_file(cls, file_path):
        """Get dfr3set from the file.

        Args:
            file_path (str): json file path that holds the definition of a dfr3 curve.

        Returns:
            obj: dfr3set from file.

        """
        with open(file_path, "r") as f:
            instance = cls(json.load(f))

        return instance

    def calculate_limit_state(self, hazard, period: float = 0.0, std_dev: float = 0.0):
        """
            Computes limit state probabilities.
            Args:
                hazard: hazard value to compute probability for
                period: period of the structure, if applicable
                std_dev: standard deviation

            Returns: limit state probabilities

        """
        output = collections.OrderedDict()
        index = 0

        if len(self.fragility_curves) == 1:
            limit_state = ['failure']
        elif len(self.fragility_curves) == 3:
            limit_state = ['immocc', 'lifesfty', 'collprev']
        elif len(self.fragility_curves) == 4:
            limit_state = ['ls-slight', 'ls-moderat', 'ls-extensi', 'ls-complet']
        else:
            raise ValueError("We can only handle fragility curves with 1, 3 or 4 limit states!")

        for fragility_curve in self.fragility_curves:
            probability = fragility_curve.calculate_limit_state_probability(hazard, period, std_dev)
            output[limit_state[index]] = probability
            index += 1

        return output
