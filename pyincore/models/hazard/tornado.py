# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
from pyincore import HazardService, Dataset
from pyincore.models.hazard.hazard import Hazard
from pyincore.models.hazard.hazarddataset import TornadoDataset
from pyincore.models.units import Units

from shapely.geometry import Point
import random
import time


class Tornado(Hazard):
    """
    "tornadoType": "dataset",
    "id": "xxx",
    "name": "pytest - Joplin Tornado",
    "description": "Joplin tornado hazard",
    "creator": "xxx",
    "threshold": null,
    "thresholdUnit": "mph",
    "spaces": [
        "xxx"
    ],
    "date": "2020-08-14T16:22:32+0000",
    "hazardDatasets":[]
    """

    def __init__(
        self,
        metadata,
        ef_rating_field="ef_rating",
        ef_wind_speed=(65, 86, 111, 136, 166, 200),
        max_wind_speed=250.0,
    ):
        super().__init__(metadata)
        self.tornado_type = metadata["tornadoType"] if "tornadoType" in metadata else ""
        self.hazardDatasets = []
        if "hazardDatasets" in metadata:
            for hazardDataset in metadata["hazardDatasets"]:
                self.hazardDatasets.append(TornadoDataset(hazardDataset))
        self.hazard_type = "tornado"
        self.EF_RATING_FIELD = ef_rating_field
        self.EF_WIND_SPEED = ef_wind_speed
        self.MAX_WIND_SPEED = max_wind_speed
        self.tornado_parameters = (
            metadata["TornadoParameters"] if "TornadoParameters" in metadata else {}
        )

    @classmethod
    def from_hazard_service(cls, id: str, hazard_service: HazardService):
        """Get Hazard from hazard service, get metadata as well.

        Args:
            id (str): ID of the Hazard.
            hazard_service (obj): Hazard service.

        Returns:
            obj: Hazard from Data service.

        """
        metadata = hazard_service.get_tornado_hazard_metadata(id)
        instance = cls(metadata)
        return instance

    def read_hazard_values(
        self, payload: list, hazard_service=None, seed=None, **kwargs
    ):
        """Retrieve bulk earthquake hazard values either from the Hazard service or read it from local Dataset

        Args:
            payload (list):
            seed: (None or int): Seed value for random values.
            hazard_service (obj): Hazard service.
            kwargs (dict): Keyword arguments.
        Returns:
            obj: Hazard values.

        """
        if self.id and self.id != "" and hazard_service is not None:
            return hazard_service.post_tornado_hazard_values(
                self.id, payload, seed=seed, **kwargs
            )
        else:
            if self.tornado_type == "dataset":
                return self.calculate_wind_speed_uniform_random_dist(payload, seed)
            else:
                raise ValueError(
                    'Local Tornado type "'
                    + self.tornado_type
                    + '" is not supported yet.'
                )

    def calculate_wind_speed_uniform_random_dist(self, payload, seed=-1):
        """Read local hazard values from shapefile dataset

        Args:
            payload (list):
            seed: (None or int): Seed value for random values.
        Returns:
            obj: Hazard values.

        """

        response = []

        # match demand types with shapefile file
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

                    # find matching raster file (Dataset) to read value from
                    if req_demand_type.lower() == hazard_dataset.demand_type.lower():
                        hazard_df = (
                            hazard_dataset.dataset.get_dataframe_from_shapefile()
                        )
                        ef_box = -1
                        x = float(req["loc"].split(",")[1])
                        y = float(req["loc"].split(",")[0])
                        location = Point(x, y)

                        for _, feature in hazard_df.iterrows():
                            polygon = feature["geometry"]
                            if location.within(polygon):
                                ef_rating = feature[self.EF_RATING_FIELD]
                                ef_box = Tornado.get_ef_rating(ef_rating)
                                break

                        if ef_box < 0:
                            raw_wind_speed = None
                        elif ef_box == 5:  # EF5
                            bottom_speed = self.EF_WIND_SPEED[ef_box]
                            top_speed = self.MAX_WIND_SPEED
                            random.seed(self.get_random_seed(location, seed))
                            raw_wind_speed = random.uniform(bottom_speed, top_speed)
                        else:
                            bottom_speed = self.EF_WIND_SPEED[ef_box]
                            top_speed = self.EF_WIND_SPEED[ef_box + 1]
                            random.seed(self.get_random_seed(location, seed))
                            raw_wind_speed = random.uniform(bottom_speed, top_speed)

                        if raw_wind_speed is None:
                            converted_wind_speed = raw_wind_speed
                        else:
                            # some basic unit conversion
                            converted_wind_speed = Units.convert_hazard(
                                raw_wind_speed,
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
                                if converted_wind_speed < converted_threshold_value:
                                    converted_wind_speed = None

                        hazard_values.append(converted_wind_speed)
                        match = True
                        break

                if not match:
                    hazard_values.append(-9999.2)  # invalid demand type

            req.update({"hazardValues": hazard_values})
            response.append(req)

        return response

    def get_random_seed(self, location, seed=-1):
        # Get seed from the model and override if no value specified
        if (
            (seed is None or seed == -1)
            and self.tornado_parameters is not {}
            and "randomSeed" in self.tornado_parameters
        ):
            seed = self.tornado_parameters["randomSeed"]

        # If no seed value provided OR model seed value was never set by the user, use current system time
        if seed is None or seed == -1:
            seed = int(time.time() * 1000)  # Current system time in milliseconds

        # Use 4 decimal places for getting unique seed values from lat/long
        try:
            seed = seed + int(abs((location.x + location.y) * 10000))
        except OverflowError:
            print(
                "Seed + abs((location.x + location.y) * 10000) exceeds max value, capping at Maximum value"
            )
            seed = float("inf")  # Cap at positive infinity for maximum value

        return seed

    @staticmethod
    def get_ef_rating(ef_rating):
        ef_rating_map = {
            "EF0": 0,
            "EF1": 1,
            "EF2": 2,
            "EF3": 3,
            "EF4": 4,
            "EF5": 5,
        }
        return ef_rating_map.get(ef_rating, -1)
