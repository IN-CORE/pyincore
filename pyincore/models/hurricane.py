# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
from pyincore import HazardService, Dataset
from pyincore.models.hazard import Hazard
from pyincore.models.hazardDataset import HurricaneDataset
from pyincore.models.units import Units


class Hurricane(Hazard):

    def __init__(self, metadata):
        super().__init__(metadata)
        self.hazardDatasets = []
        for hazardDataset in metadata["hazardDatasets"]:
            self.hazardDatasets.append(HurricaneDataset(hazardDataset))
        self.hazard_type = "hurricane"

    @classmethod
    def from_hazard_service(cls, id: str, hazard_service: HazardService):
        """Get Hazard from hazard service, get metadata as well.

        Args:
            id (str): ID of the Hazard.
            hazard_service (obj): Hazard service.

        Returns:
            obj: Hazard from Data service.

        """
        metadata = hazard_service.get_hurricane_metadata(id)
        instance = cls(metadata)
        return instance

    def read_hazard_values(self, payload: list, hazard_service=None, timeout=(30, 600), **kwargs):
        """ Retrieve bulk hurricane hazard values either from the Hazard service or read it from local Dataset

        Args:
            payload (list):
            hazard_service (obj): Hazard service.
            timeout (tuple): Timeout for the request.
            kwargs (dict): Keyword arguments.
        Returns:
            obj: Hazard values.

        """
        if self.id and self.id != "" and hazard_service is not None:
            return hazard_service.post_hurricane_hazard_values(self.id, payload, timeout, **kwargs)
        else:
            return self.read_local_raster_hazard_values(payload)

    def read_local_raster_hazard_values(self, payload: list):
        """ Read local hazard values from raster dataset

        Args:
            payload (list):
        Returns:
            obj: Hazard values.

        """

        response = []

        # match demand types with raster file
        for req in payload:
            hazard_values = []
            for index, demand_type in enumerate(req["demands"]):
                for hazard_dataset in self.hazardDatasets:
                    if hazard_dataset.dataset is None or not isinstance(hazard_dataset.dataset, Dataset):
                        raise Exception("Hazard dataset is not properly attached to the hazard object.")

                    # find matching raster file (Dataset) to read value from
                    if demand_type.lower() == hazard_dataset.demand_type.lower():
                        raw_raster_value = hazard_dataset.dataset.get_raster_value(
                            x=float(req["loc"].split(",")[1]),
                            y=float(req["loc"].split(",")[0]))

                        # some basic unit conversion
                        converted_raster_value = Units.convert_hazard(raw_raster_value,
                                                                      original_demand_units=hazard_dataset.demand_units,
                                                                      requested_demand_units=req["units"][index])

                        # compare with threshold (optional)
                        threshold_value = hazard_dataset.threshold_value
                        threshold_unit = hazard_dataset.threshold_unit
                        if threshold_value is not None:
                            converted_threshold_value = Units.convert_hazard(threshold_value,
                                                                             original_demand_units=threshold_unit,
                                                                             requested_demand_units=req["units"][index])
                            if converted_raster_value < converted_threshold_value:
                                converted_raster_value = None

                        hazard_values.append(converted_raster_value)

            req.update({"hazardValues": hazard_values})
            response.append(req)

        return response
