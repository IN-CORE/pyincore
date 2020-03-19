# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import json

from pyincore.standardfragilitycurve import StandardFragilityCurve
from pyincore.periodbuildingfragilitycurve import PeriodBuildingFragilityCurve
from pyincore.periodstandardfragilitycurve import PeriodStandardFragilityCurve
from pyincore.customexpressionfragilitycurve import CustomExpressionFragilityCurve

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
            # based on what type of fragility_curve it is, instantiate different fragility curve object
            for fragility_curve in metadata["fragilityCurves"]:
                if fragility_curve['className'] == 'StandardFragilityCurve':
                    self.fragility_curves.append(StandardFragilityCurve(fragility_curve))
                elif fragility_curve['className'] == 'PeriodBuildingFragilityCurve':
                    self.fragility_curves.append(PeriodBuildingFragilityCurve(fragility_curve))
                elif fragility_curve['className'] == 'PeriodStandardFragilityCurve':
                    self.fragility_curves.append(PeriodStandardFragilityCurve(fragility_curve))
                elif fragility_curve['className'] == 'CustomExpressionFragilityCurve':
                    self.fragility_curves.append(CustomExpressionFragilityCurve(fragility_curve))
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
    def from_dict(cls, metadata):
        return cls(metadata)

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
