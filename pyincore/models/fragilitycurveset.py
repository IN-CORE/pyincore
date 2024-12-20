# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import json

from pyincore.models.dfr3curve import DFR3Curve
from pyincore.utils.analysisutil import AnalysisUtil


class FragilityCurveSet:
    """A class for fragility curves.

    Args:
        metadata (dict): fragility curve metadata.

    Raises:
        ValueError: Raised if there are unsupported number of fragility curves
        or if missing a key curve field.

    """

    def __init__(self, metadata):
        self.id = metadata["id"] if "id" in metadata else ""
        self.description = metadata["description"] if "description" in metadata else ""
        self.authors = ", ".join(metadata["authors"]) if "authors" in metadata else ""
        self.paper_reference = (
            str(metadata["paperReference"]) if "paperReference" in metadata else ""
        )
        self.creator = metadata["creator"] if "creator" in metadata else ""
        self.demand_types = metadata["demandTypes"]
        self.demand_units = metadata["demandUnits"]
        self.result_type = metadata["resultType"]
        self.result_unit = metadata["resultUnit"] if "resultUnit" in metadata else ""
        self.hazard_type = metadata["hazardType"]
        self.inventory_type = metadata["inventoryType"]
        self.curve_parameters = {}
        self.fragility_curves = []

        if "curveParameters" in metadata.keys():
            self.curve_parameters = metadata["curveParameters"]

        if "fragilityCurves" in metadata.keys():
            for fragility_curve in metadata["fragilityCurves"]:
                self.fragility_curves.append(DFR3Curve(fragility_curve))
        else:
            raise ValueError(
                "Cannot create dfr3 curve object. Missing key field: fragilityCurves."
            )

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

    def calculate_limit_state(
        self, hazard_values: dict = {}, inventory_type: str = "building", **kwargs
    ):
        """WIP computation of limit state probabilities accounting for custom expressions.

        Args:
            hazard_values (dict): A dictionary with hazard values to compute probability.
            inventory_type (str): An inventory type.
            **kwargs: Keyword arguments.

        Returns:
            OrderedDict: Limit state probabilities.

        """
        output = FragilityCurveSet._initialize_limit_states(inventory_type)
        limit_state = list(output.keys())
        index = 0

        if len(self.fragility_curves) <= 4:
            for fragility_curve in self.fragility_curves:
                probability = fragility_curve.solve_curve_expression(
                    hazard_values, self.curve_parameters, **kwargs
                )
                output[limit_state[index]] = AnalysisUtil.update_precision(
                    probability
                )  # round to default digits
                index += 1
        else:
            raise ValueError(
                "We can only handle fragility curves with less than 4 limit states."
            )

        return output

    def calculate_damage_interval(
        self, damage, hazard_type="earthquake", inventory_type: str = "building"
    ):
        """

        Args:
            damage (list): A list of limit states.
            hazard_type (str): A string describing the hazard being evaluated.
            inventory_type (str): A string describing the type of element being evaluated.

        Returns:
            list: LS-to-DS mapping

        """
        # Organize conceptually per LS-to-DS mapping , then by event, then by structure and by count
        # This may help keep track of scientific requirements also.

        ls_ds_dspatcher = {
            # 1 LS to 4 DS
            ("hurricane", "building", 1): FragilityCurveSet._1ls_to_4ds,
            ("hurricane", "electric_facility", 1): FragilityCurveSet._1ls_to_4ds,
            # 1 LS to 5 DS
            ("hurricane", "road", 1): FragilityCurveSet._1ls_to_5ds,
            ("hurricane", "bridge", 1): FragilityCurveSet._1ls_to_5ds,
            # 3 LS to 4 DS
            ("earthquake", "building", 3): FragilityCurveSet._3ls_to_4ds,
            ("earthquake+tsunami", "building", 3): FragilityCurveSet._3ls_to_4ds,
            ("tornado", "building", 3): FragilityCurveSet._3ls_to_4ds,
            ("hurricane", "building", 3): FragilityCurveSet._3ls_to_4ds,
            ("flood", "building", 3): FragilityCurveSet._3ls_to_4ds,
            ("tsunami", "building", 3): FragilityCurveSet._3ls_to_4ds,
            # 4 LS to 5 DS
            ("earthquake", "bridge", 4): FragilityCurveSet._4ls_to_5ds,
            ("earthquake", "pipeline", 4): FragilityCurveSet._4ls_to_5ds,
            ("earthquake", "road", 4): FragilityCurveSet._4ls_to_5ds,
            ("earthquake", "water_facility", 4): FragilityCurveSet._4ls_to_5ds,
            ("earthquake", "electric_facility", 4): FragilityCurveSet._4ls_to_5ds,
            ("earthquake", "gas_facility", 4): FragilityCurveSet._4ls_to_5ds,
            ("tornado", "bridge", 4): FragilityCurveSet._4ls_to_5ds,
            ("tornado", "electric_facility", 4): FragilityCurveSet._4ls_to_5ds,
            ("flood", "bridge", 4): FragilityCurveSet._4ls_to_5ds,
            ("tsunami", "bridge", 4): FragilityCurveSet._4ls_to_5ds,
            ("tsunami", "pipeline", 4): FragilityCurveSet._4ls_to_5ds,
            ("tsunami", "road", 4): FragilityCurveSet._4ls_to_5ds,
            ("tsunami", "water_facility", 4): FragilityCurveSet._4ls_to_5ds,
            ("tsunami", "electric_facility", 4): FragilityCurveSet._4ls_to_5ds,
            ("hurricane", "bridge", 4): FragilityCurveSet._4ls_to_5ds,
        }

        if (
            not (hazard_type, inventory_type, len(self.fragility_curves))
            in ls_ds_dspatcher.keys()
        ):
            raise ValueError(
                inventory_type
                + " "
                + hazard_type
                + " damage analysis do not support "
                + str(len(self.fragility_curves))
                + " limit state"
            )

        return ls_ds_dspatcher[
            (hazard_type, inventory_type, len(self.fragility_curves))
        ](damage)

    def construct_expression_args_from_inventory(self, inventory_unit: dict):
        """

        Args:
            inventory_unit (dict): An inventory set.

        Returns:
            dict: Function parameters.

        """
        kwargs_dict = {}
        for parameters in self.curve_parameters:
            if parameters["name"] == "age_group" and (
                "age_group" not in inventory_unit["properties"]
                or inventory_unit["properties"]["age_group"] == ""
            ):
                if (
                    "year_built" in inventory_unit["properties"].keys()
                    and inventory_unit["properties"]["year_built"] is not None
                ):
                    try:
                        yr_built = int(inventory_unit["properties"]["year_built"])
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

                    kwargs_dict["age_group"] = age_group

            if (
                parameters["name"] in inventory_unit["properties"]
                and inventory_unit["properties"][parameters["name"]] is not None
                and inventory_unit["properties"][parameters["name"]] != ""
            ):
                kwargs_dict[parameters["name"]] = inventory_unit["properties"][
                    parameters["name"]
                ]
        return kwargs_dict

    @staticmethod
    def _3ls_to_4ds(limit_states):
        """

        Args:
            limit_states (dict): Limit states.

        Returns:
            dict: Damage states.

        """
        limit_states = AnalysisUtil.float_dict_to_decimal(limit_states)
        damage_states = AnalysisUtil.float_dict_to_decimal(
            {"DS_0": 0.0, "DS_1": 0.0, "DS_2": 0.0, "DS_3": 0.0}
        )

        small_overlap = FragilityCurveSet.is_there_small_overlap(limit_states)

        if small_overlap:
            ds_overlap = FragilityCurveSet.adjust_for_small_overlap(
                small_overlap, limit_states, damage_states
            )

            damage_states["DS_0"] = ds_overlap[0]
            damage_states["DS_1"] = ds_overlap[1]
            damage_states["DS_2"] = ds_overlap[2]
            damage_states["DS_3"] = ds_overlap[3]

        else:
            damage_states["DS_0"] = 1 - limit_states["LS_0"]
            damage_states["DS_1"] = limit_states["LS_0"] - limit_states["LS_1"]
            damage_states["DS_2"] = limit_states["LS_1"] - limit_states["LS_2"]
            damage_states["DS_3"] = limit_states["LS_2"]

        return damage_states

    @staticmethod
    def _4ls_to_5ds(limit_states):
        """

        Args:
            limit_states (dict): Limit states.

        Returns:
            dict: Damage states.

        """
        limit_states = AnalysisUtil.float_dict_to_decimal(limit_states)
        damage_states = AnalysisUtil.float_dict_to_decimal(
            {"DS_0": 0.0, "DS_1": 0.0, "DS_2": 0.0, "DS_3": 0.0, "DS_4": 0.0}
        )

        small_overlap = FragilityCurveSet.is_there_small_overlap(limit_states)

        if small_overlap:
            ds_overlap = FragilityCurveSet.adjust_for_small_overlap(
                small_overlap, limit_states, damage_states
            )

            damage_states["DS_0"] = ds_overlap[0]
            damage_states["DS_1"] = ds_overlap[1]
            damage_states["DS_2"] = ds_overlap[2]
            damage_states["DS_3"] = ds_overlap[3]
            damage_states["DS_4"] = ds_overlap[4]

        else:
            damage_states["DS_0"] = 1 - limit_states["LS_0"]
            damage_states["DS_1"] = limit_states["LS_0"] - limit_states["LS_1"]
            damage_states["DS_2"] = limit_states["LS_1"] - limit_states["LS_2"]
            damage_states["DS_3"] = limit_states["LS_2"] - limit_states["LS_3"]
            damage_states["DS_4"] = limit_states["LS_3"]

        return damage_states

    @staticmethod
    def _1ls_to_4ds(limit_states):
        """

        Args:
            limit_states (dict): Limit states.

        Returns:
            dict: Damage states.

        """
        limit_states = AnalysisUtil.float_dict_to_decimal(limit_states)
        damage_states = dict()
        damage_states["DS_0"] = 1 - limit_states["LS_0"]
        damage_states["DS_1"] = 0
        damage_states["DS_2"] = 0
        damage_states["DS_3"] = limit_states["LS_0"]

        return damage_states

    @staticmethod
    def _1ls_to_5ds(limit_states):
        """

        Args:
            limit_states (dict): Limit states.

        Returns:
            dict: Damage states.

        """
        limit_states = AnalysisUtil.float_dict_to_decimal(limit_states)
        damage_states = dict()
        damage_states["DS_0"] = 1 - limit_states["LS_0"]
        damage_states["DS_1"] = 0
        damage_states["DS_2"] = 0
        damage_states["DS_3"] = 0
        damage_states["DS_4"] = limit_states["LS_0"]

        return damage_states

    @staticmethod
    def is_there_small_overlap(limit_states):
        small_overlap = []
        keys = list(limit_states)
        for ls_index in range(len(limit_states)):
            for tmp_index in range(ls_index + 1, len(limit_states)):
                if limit_states[keys[ls_index]] < limit_states[keys[tmp_index]]:
                    # if previous limit state is less than the next, there's an overlap
                    small_overlap.append(ls_index)
                    break

        return small_overlap

    @staticmethod
    def adjust_for_small_overlap(small_overlap, limit_states, damage_states):
        """

        Args:
            small_overlap (obj): Overlap.
            limit_states (dict): Limit states.
            damage_states (dict): Damage states.

        Returns:
            list: Damage states overlap.

        """
        ls_overlap = list(limit_states.values())
        ds_overlap = [0.0] * len(damage_states)
        for index in range(len(damage_states)):
            ds_index = index
            # If the limit state is overlapped, find the next non-overlapping limit state
            if index in small_overlap:
                for tmp_index in range(index + 1, len(ls_overlap)):
                    if tmp_index not in small_overlap:
                        ds_index = tmp_index

            if index == 0:
                # Compute DS_0
                ds_overlap[index] = 1 - ls_overlap[ds_index]
            elif index == len(damage_states) - 1:
                # Compute last DS
                ds_overlap[index] = ls_overlap[index - 1]
            else:
                # If one of the limit state curves between the first and last are overlapped, they've been
                # eliminated and will be 0. If not, then compute the interval
                current_ls = index - 1
                if current_ls not in small_overlap:
                    ds_overlap[index] = ls_overlap[index - 1] - ls_overlap[ds_index]

        return ds_overlap

    @staticmethod
    def _initialize_limit_states(inventory_type):
        """

        Args:
            inventory_type (str): Inventory type..

        Returns:
            dict: Limit states..

        """
        if inventory_type == "building":
            output = {"LS_0": 0.0, "LS_1": 0.0, "LS_2": 0.0}
        elif inventory_type == "pipeline":
            output = {"LS_0": 0.0, "LS_1": 0.0, "LS_2": 0.0, "LS_3": 0.0}
        elif inventory_type == "bridge":
            output = {"LS_0": 0.0, "LS_1": 0.0, "LS_2": 0.0, "LS_3": 0.0}
        elif inventory_type == "electric_facility":
            output = {"LS_0": 0.0, "LS_1": 0.0, "LS_2": 0.0, "LS_3": 0.0}
        elif inventory_type == "road":
            output = {"LS_0": 0.0, "LS_1": 0.0, "LS_2": 0.0, "LS_3": 0.0}
        elif inventory_type == "water_facility":
            output = {"LS_0": 0.0, "LS_1": 0.0, "LS_2": 0.0, "LS_3": 0.0}
        elif inventory_type == "gas_facility":
            output = {"LS_0": 0.0, "LS_1": 0.0, "LS_2": 0.0, "LS_3": 0.0}
        elif inventory_type == "Transmission Towers":
            output = {"LS_0": 0.0}
        elif inventory_type == "Distribution Poles":
            output = {"LS_0": 0.0}
        else:
            output = {"LS_0": 0.0, "LS_1": 0.0, "LS_2": 0.0}

        return output
