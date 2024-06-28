# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import json
from pyincore.models.mapping import Mapping


class MappingSet:
    """class for dfr3 mapping.

    Args:
        metadata (dict): mapping metadata.

    """

    def __init__(self, metadata):
        self.id = metadata["id"] if "id" in metadata else ""
        self.name = metadata["name"] if "name" in metadata else ""
        self.hazard_type = metadata["hazardType"] if "hazardType" in metadata else ""
        self.inventory_type = (
            metadata["inventoryType"] if "inventoryType" in metadata else ""
        )
        if "mappingEntryKeys" in metadata and metadata["mappingEntryKeys"] is not None:
            self.mappingEntryKeys = metadata["mappingEntryKeys"]
        else:
            self.mappingEntryKeys = []

        self.data_type = (
            metadata["dataType"] if "dataType" in metadata else "incore:dfr3MappingSet"
        )

        mappings = []
        for m in metadata["mappings"]:
            if isinstance(m, Mapping):
                mappings.append(m)
            else:
                # enforce convert dictionary to mapping entry object
                mappings.append(Mapping(m["entry"], m["rules"]))
        self.mappings = mappings

        self.mapping_type = metadata["mappingType"]

    @classmethod
    def from_json_str(cls, json_str):
        """Get dfr3 mapping from json string.

        Args:
            json_str (str): JSON of the Dataset.

        Returns:
            obj: dfr3 mapping from JSON.

        """

        return cls(json.loads(json_str))

    @classmethod
    def from_json_file(cls, file_path, data_type="incore:dfr3MappingSet"):
        """Get dfr3 mapping from the file.

        Args:
            file_path (str): json file path that holds the definition of a dfr3 curve.
            data_type (str): mapping dataset type

        Returns:
            obj: dfr3 mapping from file.

        """
        with open(file_path, "r") as f:
            metadata = json.load(f)
            metadata["dataType"] = data_type

            instance = cls(metadata)

        return instance
