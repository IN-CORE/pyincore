# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
from pyincore import Dataset


class HazardDataset:
    def __init__(self, hazard_datasets_metadata):
        self.hazard_type = hazard_datasets_metadata["hazardType"] if "hazardType" in hazard_datasets_metadata else ""
        self.demand_type = hazard_datasets_metadata["demandType"] if "demandType" in hazard_datasets_metadata else ""
        self.demand_units = hazard_datasets_metadata["demandUnits"] \
            if "demandUnits" in hazard_datasets_metadata else ""
        self.dataset_id = hazard_datasets_metadata["datasetId"] if "datasetId" in hazard_datasets_metadata else ""
        self.dataset = None


class HurricaneDataset(HazardDataset):
    def __init__(self, hazard_datasets_metadata):
        super().__init__(hazard_datasets_metadata)
        self.threshold = hazard_datasets_metadata["threshold"] if "threshold" in hazard_datasets_metadata else None
        self.hurricane_parameters = hazard_datasets_metadata["hurricaneParameters"] \
            if "hurricaneParameters" in hazard_datasets_metadata else {}

    def from_file(self, file_path, data_type="ncsa:deterministicHurricaneRaster"):
        """Get hurricane dataset from the file."""
        self.dataset = Dataset.from_file(file_path, data_type)

    def from_data_service(self, data_service):
        """Get hurricane dataset from the data service."""
        self.dataset = Dataset.from_data_service(self.dataset_id, data_service)
