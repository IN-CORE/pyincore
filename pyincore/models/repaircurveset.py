# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import json
from pyincore.models.standardfragilitycurve import StandardFragilityCurve


class RepairCurveSet:
    """class for repair curves.

    Args:
        metadata (dict): repair curve metadata.

    Raises:
        ValueError: Raised if there are unsupported number of repair curves
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
        self.repair_curves = []

        if 'repairCurves' in metadata.keys():
            for repair_curve in metadata["repairCurves"]:
                if repair_curve['className'] == 'StandardRepairCurve':
                    # Using StandardFragilityCurve for now instead of creating a StandardRepairCurve because it will be
                    # deprecated and repair curves will be using the expression based format the in near future.
                    self.repair_curves.append(StandardFragilityCurve(repair_curve))
                else:
                    # TODO make a custom repair curve class that accept other formats
                    self.repair_curves.append(repair_curve)
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


