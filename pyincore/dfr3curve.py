# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import json


class DFR3Curve:
    """class for dfr3 curves.

    Args:
        metadata (dict): dfr3 curve metadata.

    """

    def __init__(self, metadata):
        # TODO think if we need id or not?
        self.id = metadata["id"]
        self.demand_type = metadata["demandType"]
        self.demand_units = metadata["demandUnits"]
        self.result_type = metadata["resultType"]
        self.hazard_type = metadata['hazardType']
        self.inventory_type = metadata['inventoryType']

        # TODO need to represent curves better
        if 'fragilityCurves' in metadata.keys():
            self.fragility_curves = metadata["fragilityCurves"]
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
        with open(file_path, "w") as f:
            instance = cls(json.load(f))

        return instance
