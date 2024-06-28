# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import json
import warnings

from pyincore.models.units import Units
from pyincore.dataset import Dataset

warnings.filterwarnings("ignore", "", UserWarning)


class Hazard:
    """Hazard.

    Args:
        metadata (dict): Hazard metadata.

    """

    def __init__(self, metadata):
        self.id = metadata["id"] if "id" in metadata else ""
        self.name = metadata["name"] if "name" in metadata else ""
        self.description = metadata["description"] if "description" in metadata else ""
        self.date = metadata["date"] if "date" in metadata else ""
        self.creator = metadata["creator"] if "creator" in metadata else ""
        self.spaces = metadata["spaces"] if "spaces" in metadata else []
        self.hazard_type = metadata["hazard_type"] if "hazard_type" in metadata else ""
        self.hazardDatasets = []

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

    def read_local_raster_hazard_values(self, payload: list):
        """Read local hazard values from raster dataset

        Args:
            payload (list):
        Returns:
            obj: Hazard values.

        """

        response = []

        # match demand types with raster file
        for req in payload:
            hazard_values = []
            for index, req_demand_type in enumerate(req["demands"]):
                match = False
                for hazard_dataset in self.hazardDatasets:
                    if hazard_dataset.dataset is None or not isinstance(
                        hazard_dataset.dataset, Dataset
                    ):
                        raise Exception(
                            "Hazard dataset is not properly attached to the hazard object."
                        )

                    # TODO Consider how to get the closest period
                    # TODO consider pga, pgv, sd conversions
                    if "sa" in req_demand_type.lower():
                        period = req_demand_type.split(" ")[0]
                    else:
                        period = None

                    # find matching raster file (Dataset) to read value from
                    if (
                        req_demand_type.lower() == hazard_dataset.demand_type.lower()
                        or (
                            hasattr(hazard_dataset, "period")
                            and period == hazard_dataset.period
                        )
                    ):
                        raw_raster_value = hazard_dataset.dataset.get_raster_value(
                            x=float(req["loc"].split(",")[1]),
                            y=float(req["loc"].split(",")[0]),
                        )

                        if raw_raster_value is None:
                            converted_raster_value = raw_raster_value
                        else:
                            # some basic unit conversion
                            converted_raster_value = Units.convert_hazard(
                                raw_raster_value,
                                original_demand_units=hazard_dataset.demand_units,
                                requested_demand_units=req["units"][index],
                            )

                            # compare with threshold (optional)
                            threshold_value = hazard_dataset.threshold_value
                            threshold_unit = hazard_dataset.threshold_unit
                            if threshold_value is not None:
                                converted_threshold_value = Units.convert_hazard(
                                    threshold_value,
                                    original_demand_units=threshold_unit,
                                    requested_demand_units=req["units"][index],
                                )
                                if converted_raster_value < converted_threshold_value:
                                    converted_raster_value = None

                        hazard_values.append(converted_raster_value)
                        match = True
                        break

                if not match:
                    hazard_values.append(-9999.2)  # invalid demand type

            req.update({"hazardValues": hazard_values})
            response.append(req)

        return response
