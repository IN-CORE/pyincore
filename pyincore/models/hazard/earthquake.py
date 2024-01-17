# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
import re

from pyincore import HazardService, Units
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
        """ Retrieve bulk earthquake hazard values either from the Hazard service or read it from local Dataset

        Args:
            payload (list):
            hazard_service (obj): Hazard service.
            kwargs (dict): Keyword arguments.
        Returns:
            obj: Hazard values.

        """
        if self.id and self.id != "" and hazard_service is not None:
            return hazard_service.post_earthquake_hazard_values(self.id, payload, **kwargs)
        else:
            return self.get_ground_motion_at_site(hazard_value, site, period, demand_type, demand_units,
                                                  amplify_hazard=None, site_class_fc=None)

    def get_ground_motion_at_site(self, hazard_value, site, period, demand_type, demand_units,
                                  amplify_hazard=None,
                                  site_class_fc=None):
        if demand_units is None:
            raise ValueError("Missing demand units cannot be None")

        if amplify_hazard and site_class_fc is not None:
            # TODO logic to amplify hazard
            raise ValueError("Amplify hazard is not supported yet.")

        if demand_type.lower() == "sd":
            supported = self._supports_hazard(period, demand_type, True)
            if not supported:
                result = self.compute_ground_motion_at_site(hazard_value, period, "sa", demand_units)
                updated_hazard_value = None
                if result is not None:
                    updated_hazard_value = Units.convert_eq_hazard(result["hazard_value"], result["units"],
                                                                   float(result["period"]), "sa", demand_units, "sd")
                return {"hazard_value": updated_hazard_value, "period": result["period"], "units": "sd",
                        "demand": demand_units}
            else:
                return self.compute_ground_motion_at_site(hazard_value, period, demand_type.lower(), demand_units)
        elif demand_type.lower() == "pgv":
            supported = self._supports_hazard(period, demand_type, True)
            if not supported:
                supported = self._supports_hazard("1.0", "Sa", True)
                if not supported:
                    raise ValueError(
                        f"{demand_type} is not supported and cannot be converted given the defined earthquake")
                result = self.compute_ground_motion_at_site(site, "1.0", "Sa", None)
                updated_hazard_value = None
                if result["hazard_value"] is not None:
                    updated_hazard_value = Units.convert_eq_hazard(result["hazard_value"], "g", 1.0, "sa",
                                                                   demand_units, "pgv")
                return {"hazard_value": updated_hazard_value, "period": "0.0", "units": "pgv",
                        "demand": demand_units}
        else:
            supported = self._supports_hazard(period, demand_type, False)
            if not supported:
                print(f"{demand_type} is not supported by the defined earthquake.")
                return None

        return self.compute_ground_motion_at_site(hazard_value, period, demand_type.lower(), demand_units)

    def compute_ground_motion_at_site(self, hazard_value, period, demand, demand_units):
        hazard_dataset = Earthquake._find_hazard(self.hazardDatasets, demand, period, False)
        closest_hazard_period = str(hazard_dataset.period)

        if hazard_value is not None:
            converted_hazard_val = Units.convert_eq_hazard(hazard_value, hazard_dataset.demand_units,
                                                           float(period), hazard_dataset.demand_type,
                                                           demand_units, demand)
            return {
                "hazard_value": converted_hazard_val,
                "period": closest_hazard_period,
                "units": demand_units,
                "demand": demand
            }

        return None

    @staticmethod
    def _find_hazard(hazard_datasets, demand_hazard, period, exact_only=False):
        demand_hazard_motion = Earthquake._strip_period(demand_hazard)
        matches = []

        for dataset in hazard_datasets:
            if dataset.demand_type.lower() == demand_hazard_motion.lower():
                matches.append(dataset)

        if not matches:
            for dataset in hazard_datasets:
                raster_period = dataset.period
                conversions = Earthquake._find_hazard_conversion_types(dataset.demand_type, raster_period)
                if demand_hazard_motion.lower() in map(str.lower, conversions):
                    if dataset not in matches:
                        matches.append(dataset)

        if exact_only:
            for raster_dataset in matches:
                raster_period = raster_dataset.period
                if abs(raster_period - period) < 0.001:
                    return raster_dataset
            return None

        if not matches:
            print("Did not find appropriate hazard or a conversion")
            print("Fragility curve requires hazard type: " + demand_hazard)
            print("Here are the hazard types we have: ")
            for dataset in hazard_datasets:
                print(dataset.demand_type)
            return None
        elif len(matches) == 1:
            return matches[0]
        else:
            return_val = matches[0]
            period_diff = abs(period - return_val.period)

            for i in range(1, len(matches)):
                tmp = abs(period - matches[i].period)
                if tmp < period_diff:
                    period_diff = tmp
                    return_val = matches[i]

            return return_val

    @staticmethod
    def _strip_period(demand_type):
        demand_type = re.sub(r'[0-9]*', '', demand_type)
        demand_type = re.sub(r'\.*', '', demand_type)
        demand_type = re.sub(r'sec', '', demand_type)
        demand_type = demand_type.replace(' ', '')
        if demand_type == '':
            demand_type = 'Sa'

        return demand_type

    @staticmethod
    def _find_hazard_conversion_types(demand_type, period):
        if demand_type.lower() == "pga":
            return ["pga", "pgd"]
        elif demand_type.lower() == "sa":
            if period == 1.0:
                return ["sa", "sd", "sv", "pgv"]
            else:
                return ["sa", "sd", "sv"]
        else:
            return [demand_type]

    def _supports_hazard(self, period, demand_type, exact_only):
        can_output_hazard = True
        hazard_dataset = Earthquake._find_hazard(self.hazardDatasets, demand_type, period, exact_only)
        if hazard_dataset is None:
            can_output_hazard = False

        return can_output_hazard

