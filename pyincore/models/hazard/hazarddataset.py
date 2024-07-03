# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
from pyincore import Dataset


class HazardDataset:
    def __init__(self, hazard_datasets_metadata):
        self.hazard_type = (
            hazard_datasets_metadata["hazardType"]
            if "hazardType" in hazard_datasets_metadata
            else ""
        )
        self.demand_type = (
            hazard_datasets_metadata["demandType"]
            if "demandType" in hazard_datasets_metadata
            else ""
        )
        self.demand_units = (
            hazard_datasets_metadata["demandUnits"]
            if "demandUnits" in hazard_datasets_metadata
            else ""
        )
        self.dataset_id = (
            hazard_datasets_metadata["datasetId"]
            if "datasetId" in hazard_datasets_metadata
            else ""
        )
        self.dataset = None

        # default threshold value and unit if exist
        self.threshold_value = (
            hazard_datasets_metadata["threshold"]
            if "threshold" in hazard_datasets_metadata
            else None
        )
        self.threshold_unit = self.demand_units

    def from_file(self, file_path, data_type):
        """Get hurricane dataset from the file."""
        self.dataset = Dataset.from_file(file_path, data_type)

    def set_threshold(self, threshold_value, threshold_unit):
        """
        Set threshold value for the hazard to determine exposure or not
        Args:
            threshold_value: threshold_value
            threshold_unit: threshold_unit
        Returns:

        """
        self.threshold_value = threshold_value
        self.threshold_unit = threshold_unit

    def from_data_service(self, data_service):
        """Get hazard dataset from the data service."""
        self.dataset = Dataset.from_data_service(self.dataset_id, data_service)


class HurricaneDataset(HazardDataset):
    def __init__(self, hazard_datasets_metadata):
        super().__init__(hazard_datasets_metadata)
        self.hurricane_parameters = (
            hazard_datasets_metadata["hurricaneParameters"]
            if "hurricaneParameters" in hazard_datasets_metadata
            else {}
        )


class EarthquakeDataset(HazardDataset):
    def __init__(self, hazard_datasets_metadata):
        super().__init__(hazard_datasets_metadata)
        self.period = (
            hazard_datasets_metadata["period"]
            if "period" in hazard_datasets_metadata
            else 0
        )
        self.recurrence_interval = (
            hazard_datasets_metadata["recurrenceInterval"]
            if "recurrenceInterval" in hazard_datasets_metadata
            else 10000
        )
        self.recurrence_unit = (
            hazard_datasets_metadata["recurrenceUnit"]
            if "recurrenceUnit" in hazard_datasets_metadata
            else "years"
        )
        self.eq_parameters = (
            hazard_datasets_metadata["eqParameters"]
            if "eqParameters" in hazard_datasets_metadata
            else {}
        )


class TsunamiDataset(HazardDataset):
    def __init__(self, hazard_datasets_metadata):
        super().__init__(hazard_datasets_metadata)
        self.recurrence_interval = (
            hazard_datasets_metadata["recurrenceInterval"]
            if "recurrenceInterval" in hazard_datasets_metadata
            else 100
        )
        self.recurrence_unit = (
            hazard_datasets_metadata["recurrenceUnit"]
            if "recurrenceUnit" in hazard_datasets_metadata
            else "years"
        )


# TODO: Tornado dataset has very different shape
class TornadoDataset(HazardDataset):
    def __init__(self, hazard_datasets_metadata):
        super().__init__(hazard_datasets_metadata)


class FloodDataset(HazardDataset):
    def __init__(self, hazard_datasets_metadata):
        super().__init__(hazard_datasets_metadata)
        self.flood_parameters = (
            hazard_datasets_metadata["floodParameters"]
            if "floodParameters" in hazard_datasets_metadata
            else {}
        )
