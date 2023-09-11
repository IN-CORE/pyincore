# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
from pyincore import HazardService, Dataset
from pyincore.models.hazard import Hazard
from pyincore.models.hazardDataset import TornadoDataset
from pyincore.models.units import Units

from shapely.geometry import Point
import random


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
    "datasetId": "xxx"
    """

    def __init__(self, metadata, ef_rating_field="ef_rating", ef_wind_speed=(65, 86, 111, 136, 166, 200),
                 max_wind_speed=250.0, seed=1234):
        super().__init__(metadata)
        self.tornado_type = metadata["tornadoType"] if "tornadoType" in metadata else ""
        # tornado has very different shape than other hazards
        self.hazardDatasets = [
            TornadoDataset({"threshold": metadata["threshold"],
                            "demandType": "wind",
                            "demandUnits": metadata["thresholdUnit"] if "thresholdUnit" in metadata else "mph",
                            "datasetId": metadata["datasetId"] if "datasetId" in metadata else ""})
        ]
        self.hazard_type = "tornado"
        self.EF_RATING_FIELD = ef_rating_field
        self.EF_WIND_SPEED = ef_wind_speed
        self.MAX_WIND_SPEED = max_wind_speed
        self.SEED = seed

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

    def read_hazard_values(self, payload: list, hazard_service=None, timeout=(30, 600), **kwargs):
        """ Retrieve bulk earthquake hazard values either from the Hazard service or read it from local Dataset

        Args:
            payload (list):
            hazard_service (obj): Hazard service.
            timeout (tuple): Timeout for the request.
            kwargs (dict): Keyword arguments.
        Returns:
            obj: Hazard values.

        """
        if self.id and self.id != "" and hazard_service is not None:
            return hazard_service.post_tornado_hazard_values(self.id, payload, timeout, **kwargs)
        else:
            return self.calculate_wind_speed_uniform_random_dist(payload)

    def calculate_wind_speed_uniform_random_dist(self, payload):
        """ Read local hazard values from shapefile dataset

                Args:
                    payload (list):
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
                    if hazard_dataset.dataset is None or not isinstance(hazard_dataset.dataset, Dataset):
                        raise Exception("Hazard dataset is not properly attached to the hazard object.")

                    # find matching raster file (Dataset) to read value from
                    if req_demand_type.lower() == hazard_dataset.demand_type.lower():
                        hazard_df = hazard_dataset.dataset.get_dataframe_from_shapefile()
                        ef_box = -1
                        x = float(req["loc"].split(",")[0])
                        y = float(req["loc"].split(",")[1])
                        location = Point(x, y)

                        for _, feature in hazard_df.iterrows():
                            polygon = feature['geometry']
                            if location.within(polygon):
                                ef_rating = feature[self.EF_RATING_FIELD]
                                ef_box = Tornado.get_ef_rating(ef_rating)
                                break

                        if ef_box < 0:
                            return None

                        if ef_box == 5:  # EF5
                            bottom_speed = self.EF_WIND_SPEED[ef_box]
                            top_speed = self.MAX_WIND_SPEED
                        else:
                            bottom_speed = self.EF_WIND_SPEED[ef_box]
                            top_speed = self.EF_WIND_SPEED[ef_box + 1]

                        random.seed(self.SEED)
                        raw_wind_speed = random.uniform(bottom_speed, top_speed)

                        if raw_wind_speed is None:
                            converted_wind_speed = raw_wind_speed
                        else:
                            # some basic unit conversion
                            converted_wind_speed = Units.convert_hazard(raw_wind_speed,
                                                                        original_demand_units=hazard_dataset.demand_units,
                                                                        requested_demand_units=req["units"][index])

                            # compare with threshold (optional)
                            threshold_value = hazard_dataset.threshold_value
                            threshold_unit = hazard_dataset.threshold_unit
                            if threshold_value is not None:
                                converted_threshold_value = Units.convert_hazard(threshold_value,
                                                                                 original_demand_units=threshold_unit,
                                                                                 requested_demand_units=req["units"][
                                                                                     index])
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
