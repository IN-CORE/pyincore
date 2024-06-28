# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
from pyincore import HazardService
from pyincore.models.hazard.hazard import Hazard
from pyincore.models.hazard.hazarddataset import EarthquakeDataset


class Earthquake(Hazard):
    def __init__(self, metadata):
        super().__init__(metadata)
        self.hazardDatasets = []
        if "hazardDatasets" in metadata:
            for hazardDataset in metadata["hazardDatasets"]:
                self.hazardDatasets.append(EarthquakeDataset(hazardDataset))
        self.hazard_type = "earthquake"

    @classmethod
    def from_hazard_service(cls, id: str, hazard_service: HazardService):
        """Get Hazard from hazard service, get metadata as well.

        Args:
            id (str): ID of the Hazard.
            hazard_service (obj): Hazard service.

        Returns:
            obj: Hazard from Data service.

        """
        metadata = hazard_service.get_earthquake_hazard_metadata(id)
        instance = cls(metadata)
        return instance

    def read_hazard_values(self, payload: list, hazard_service=None, **kwargs):
        """Retrieve bulk earthquake hazard values either from the Hazard service or read it from local Dataset

        Args:
            payload (list):
            hazard_service (obj): Hazard service.
            kwargs (dict): Keyword arguments.
        Returns:
            obj: Hazard values.

        """
        if self.id and self.id != "" and hazard_service is not None:
            return hazard_service.post_earthquake_hazard_values(
                self.id, payload, **kwargs
            )
        else:
            return self.read_local_raster_hazard_values(payload)
