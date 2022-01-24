# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import json
from pyincore.models.dfr3curve import DFR3Curve


class RestorationCurveSet:
    """class for restoration curves.

    Args:
        metadata (dict): restoration curve metadata.

    Raises:
        ValueError: Raised if there are unsupported number of restoration curves
        or if missing a key curve field.
    """

    def __init__(self, metadata):
        self.id = metadata["id"] if "id" in metadata else ""
        self.description = metadata['description'] if "description" in metadata else ""
        self.authors = ", ".join(metadata['authors']) if "authors" in metadata else ""
        self.paper_reference = str(metadata["paperReference"]) if "paperReference" in metadata else ""
        self.creator = metadata["creator"] if "creator" in metadata else ""
        self.time_units = metadata["timeUnits"]
        self.result_type = metadata["resultType"]
        self.result_unit = metadata["resultUnit"] if "resultUnit" in metadata else ""
        self.hazard_type = metadata['hazardType']
        self.inventory_type = metadata['inventoryType']
        self.restoration_curves = []

        if 'curveParameters' in metadata.keys():
            self.curve_parameters = metadata["curveParameters"]

        if 'restorationCurves' in metadata.keys():
            for restoration_curve in metadata["restorationCurves"]:
                self.restoration_curves.append(DFR3Curve(restoration_curve))
        else:
            raise ValueError("Cannot create dfr3 curve object. Missing key field: restorationCurves.")

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

    def calculate_restoration_rates(self, **kwargs):
        """Computation of restoration rates.

        Args:
            **kwargs: Keyword arguments.

        Returns:
            OrderedDict: Limit state specific restoration rates.

        """

        output = {}

        if len(self.restoration_curves) <= 5:
            for restoration_curve in self.restoration_curves:
                eval_value = restoration_curve.solve_curve_expression(hazard_values={},
                                                                      curve_parameters=self.curve_parameters, **kwargs)
                output[restoration_curve.return_type['description']] = eval_value
        else:
            raise ValueError("We can only handle restoration curves with less than 5 damage states.")

        return output

    def calculate_inverse_restoration_rates(self, **kwargs):
        """Computation of inverse restoration rates example, inverse of cdf, that is, ppf.

        Args:
            **kwargs: Keyword arguments.

        Returns:
            OrderedDict: Limit state specific restoration rates.

        """

        output = {}
        if len(self.restoration_curves) <= 5:
            for restoration_curve in self.restoration_curves:
                eval_value = restoration_curve.solve_curve_for_inverse(hazard_values={},
                                                                       curve_parameters=self.curve_parameters, **kwargs)
                output[restoration_curve.return_type['description']] = eval_value
        else:
            raise ValueError("We can only handle restoration curves with less than 5 damage states.")

        return output
