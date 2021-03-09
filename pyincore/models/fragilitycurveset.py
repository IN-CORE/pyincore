# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import collections
from decimal import getcontext, Decimal
import json

from deprecated.sphinx import deprecated

from pyincore.models.customexpressionfragilitycurve import CustomExpressionFragilityCurve
from pyincore.models.fragilitycurve import FragilityCurve
from pyincore.models.periodbuildingfragilitycurve import PeriodBuildingFragilityCurve
from pyincore.models.periodstandardfragilitycurve import PeriodStandardFragilityCurve
from pyincore.models.standardfragilitycurve import StandardFragilityCurve
from pyincore.models.conditionalstandardfragilitycurve import ConditionalStandardFragilityCurve
from pyincore.models.parametricfragilitycurve import ParametricFragilityCurve
from pyincore.models.fragilitycurverefactored import FragilityCurveRefactored
from pyincore.globals import DAMAGE_PRECISION

class FragilityCurveSet:
    """class for fragility curves.

    Args:
        metadata (dict): fragility curve metadata.

    Raises:
        ValueError: Raised if there are unsupported number of fragility curves
        or if missing a key curve field.
    """

    getcontext().prec = DAMAGE_PRECISION

    def __init__(self, metadata):
        self.id = metadata["id"] if "id" in metadata else ""
        self.description = metadata['description'] if "description" in metadata else ""
        self.authors = ", ".join(metadata['authors']) if "authors" in metadata else ""
        self.paper_reference = str(metadata["paperReference"]) if "paperReference" in metadata else ""
        self.creator = metadata["creator"] if "creator" in metadata else ""
        self.demand_types = metadata["demandTypes"]
        self.demand_units = metadata["demandUnits"]
        self.result_type = metadata["resultType"]
        self.result_unit = metadata["resultUnit"] if "resultUnit" in metadata else ""
        self.hazard_type = metadata['hazardType']
        self.inventory_type = metadata['inventoryType']
        self.fragility_curve_parameters = {}
        self.fragility_curves = []

        if 'fragilityCurveParameters' in metadata.keys():
            self.fragility_curve_parameters = metadata["fragilityCurveParameters"]

        if 'fragilityCurves' in metadata.keys():
            for fragility_curve in metadata["fragilityCurves"]:

                # if it's already an df3curve object, directly put it in the list:
                if isinstance(fragility_curve, FragilityCurve):
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
                    elif fragility_curve['className'] == 'FragilityCurveRefactored':
                        self.fragility_curves.append(FragilityCurveRefactored(fragility_curve))
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

    @deprecated(version="0.9.0", reason="calculate_limit_state_w_conversion instead")
    def calculate_limit_state(self, hazard, period: float = 0.0, std_dev: float = 0.0, **kwargs):
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
            probability = fragility_curve.calculate_limit_state_probability(hazard, period, std_dev, **kwargs)
            output[limit_state[index]] = probability
            index += 1

        return output

    def calculate_limit_state_refactored_w_conversion(self, hazard_values: dict = {}, **kwargs):
        """
        WIP computation of limit state probabilities accounting for custom expressions.
        :param std_dev: standard deviation
        :param hazard_values: dictionary with hazard values to compute probability

        Returns: limit state probabilities
        """

        output = collections.OrderedDict([("LS_0", 0.0), ("LS_1", 0.0),("LS_2", 0.0)])
        limit_state = list(output.keys())
        index = 0

        if len(self.fragility_curves) <= 3:
            for fragility_curve in self.fragility_curves:
                probability = fragility_curve.calculate_limit_state_probability(hazard_values,
                                                                                self.fragility_curve_parameters,
                                                                                **kwargs)
                output[limit_state[index]] = probability
                index += 1
        else:
            raise ValueError("We can only handle fragility curves with less than 3 limit states.")

        return output

    @deprecated(version="0.9.0", reason="calculate_custom_limit_state_w_conversion instead")
    def calculate_custom_limit_state(self, variables: dict):
        """
            Computes limit state probabilities.
            Args:

            Returns: limit state probabilities for custom expression fragilities

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
            probability = fragility_curve.compute_custom_limit_state_probability(variables)
            output[limit_state[index]] = probability
            index += 1

        return output

    def calculate_limit_state_w_conversion(self, hazard, period: float = 0.0, std_dev: float = 0.0, **kwargs):
        """
            Computes limit state probabilities.
            Args:
                hazard: hazard value to compute probability for
                period: period of the structure, if applicable
                std_dev: standard deviation

            Returns: limit state probabilities

        """
        output = collections.OrderedDict([("LS_0", 0.0), ("LS_1", 0.0), ("LS_2", 0.0)])
        limit_state = list(output.keys())
        index = 0

        if len(self.fragility_curves) <= 3:
            for fragility_curve in self.fragility_curves:
                probability = fragility_curve.calculate_limit_state_probability(hazard, period, std_dev, **kwargs)
                output[limit_state[index]] = probability
                index += 1
        else:
            raise ValueError("We can only handle fragility curves with less than 3 limit states.")

        return output

    def calculate_custom_limit_state_w_conversion(self, variables: dict):
        """
            Computes limit state probabilities.
            Args:

            Returns: limit state probabilities for custom expression fragilities

        """
        output = collections.OrderedDict([("LS_0", 0.0), ("LS_1", 0.0), ("LS_2", 0.0)])
        limit_state = list(output.keys())
        index = 0

        if len(self.fragility_curves) <= 3:
            for fragility_curve in self.fragility_curves:
                probability = fragility_curve.compute_custom_limit_state_probability(variables)
                output[limit_state[index]] = probability
                index += 1
        else:
            raise ValueError("We can only handle fragility curves with less than 3 limit states.")

        return output

    def calculate_damage_interval(self, damage, hazard_type="earthquake", inventory_type="building"):
        """
        Args:
            damage:
            hazard_type:
            inventory_type:

        Returns:

        """
        # default to 3 limit states -- > 4 damage states
        output = FragilityCurveSet._3ls_to_4ds(damage)

        if hazard_type == "earthquake":
            pass
        elif hazard_type == "tornado":
            pass
        elif hazard_type == "flood":
            pass
        elif hazard_type == "tsunami":
            pass
        elif hazard_type == "hurricane":
            # 1-For two DS buildings, probabilities of zero for DS 1 and DS2 need to be placed in IN-CORE.
            # So, damage state possibilities will be either DS0 or DS3.
            if inventory_type == "building":
                if len(self.fragility_curves) == 1:
                    output = FragilityCurveSet._1ls_to_4ds(damage)
        else:
            pass

        return output

    def construct_expression_args_from_inventory(self, inventory_unit: dict):
        kwargs_dict = {}
        for parameters in self.fragility_curve_parameters:

            if parameters['name'] == "age_group" and ('age_group' not in inventory_unit['properties'] or \
                    inventory_unit['properties']['age_group'] == ""):
                if inventory_unit['properties']['year_built'] is not None:
                    try:
                        yr_built = int(inventory_unit['properties']['year_built'])
                    except ValueError:
                        print("Non integer value found in year_built")
                        raise
                    age_group = 4  # for yr_built >= 2008
                    if yr_built < 1974:
                        age_group = 1
                    elif 1974 <= yr_built < 1987:
                        age_group = 2
                    elif 1987 <= yr_built < 1995:
                        age_group = 3
                    elif 1995 <= yr_built < 2008:
                        age_group = 4

                    kwargs_dict['age_group'] = age_group

            if parameters['name'] in inventory_unit['properties'] and \
                    inventory_unit['properties'][parameters['name']] is not None and \
                    inventory_unit['properties'][parameters['name']] != "":

                kwargs_dict[parameters['name']] = inventory_unit['properties'][parameters['name']]
        return kwargs_dict

    @staticmethod
    def _3ls_to_4ds(damage):
        output = dict()
        output['DS_0'] = 1 - Decimal(damage["LS_0"])
        output['DS_1'] = Decimal(damage["LS_0"]) - Decimal(damage["LS_1"])
        output['DS_2'] = Decimal(damage["LS_1"]) - Decimal(damage["LS_2"])
        output['DS_3'] = Decimal(damage["LS_2"])

        return output

    @staticmethod
    def _1ls_to_4ds(damage):
        output = dict()
        output['DS_0'] = 1 - Decimal(damage["LS_0"])
        output['DS_1'] = 0.0
        output['DS_2'] = 0.0
        output['DS_3'] = Decimal(damage["LS_0"])

        return output
