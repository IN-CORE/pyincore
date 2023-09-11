# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import json
import warnings

warnings.filterwarnings("ignore", "", UserWarning)


class Hazard:
    """Hazard.

    Args:
        metadata (dict): Hazard metadata.

    """

    def __init__(self, metadata):

        self.id = metadata["id"] if "id" in metadata else ""
        self.name = metadata['name'] if "name" in metadata else ""
        self.description = metadata['description'] if "description" in metadata else ""
        self.date = metadata['date'] if "date" in metadata else ""
        self.creator = metadata["creator"] if "creator" in metadata else ""
        self.spaces = metadata["spaces"] if "spaces" in metadata else []
        self.hazard_type = metadata["hazard_type"] if "hazard_type" in metadata else ""

    @classmethod
    def from_json_str(cls, json_str):
        """Create hazard object from json string.

        Args:
            json_str (str): JSON of the Dataset.

        Returns:
            obj: Hazard

        """
        return cls(json.loads(json_str))

    @classmethod
    def from_json_file(cls, file_path):
        """Get hazard from the file.

        Args:
            file_path (str): json file path that holds the definition of a hazard.

        Returns:
            obj: Hazard

        """
        with open(file_path, "r") as f:
            instance = cls(json.load(f))

        return instance
