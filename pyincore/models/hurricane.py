# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
from pyincore import HazardService, DataService
from pyincore.models.hazard import Hazard
from pyincore.models.hazardDataset import HurricaneDataset


class Hurricane(Hazard):

    def __init__(self, metadata, data_service=None):
        super().__init__(metadata)
        self.hazardDatasets = []
        for hazardDataset in metadata["hazardDatasets"]:
            self.hazardDatasets.append(HurricaneDataset(hazardDataset, data_service))

    @classmethod
    def from_hazard_service(cls, id: str, hazard_service: HazardService, data_service: DataService = None):
        """Get Hazard from hazard service, get metadata as well.

        Args:
            id (str): ID of the Hazard.
            hazard_service (obj): Hazard service.
            data_service (obj): Data service.

        Returns:
            obj: Hazard from Data service.

        """
        metadata = hazard_service.get_hurricane_metadata(id)
        instance = cls(metadata, data_service)
        return instance
