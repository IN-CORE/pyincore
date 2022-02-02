# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


"""
Water Facility Restoration
"""

import numpy as np

from pyincore import BaseAnalysis, RestorationService
from pyincore.models.restorationcurveset import RestorationCurveSet


class WaterFacilityRestoration(BaseAnalysis):
    """Computes water facility restoration for an earthquake, tsunami, tornado, or hurricane exposure.

    """

    def __init__(self, incore_client):
        self.restorationsvc = RestorationService(incore_client)
        super(WaterFacilityRestoration, self).__init__(incore_client)

    def run(self):
        """Performs Water facility restoration analysis by using the parameters from the spec
        and creates an output dataset in csv format

        Returns:
            bool: True if successful, False otherwise
        """
        mapping_set = self.get_input_dataset("dfr3_mapping_set")

        restoration_key = self.get_parameter("restoration_key")
        if restoration_key is None:
            restoration_key = "Restoration ID Code"

        end_time = self.get_parameter("end_time")
        if end_time is None:
            end_time = 365.0

        time_interval = self.get_parameter("time_interval")
        if time_interval is None:
            time_interval = 1

        pf_interval = self.get_parameter("pf_interval")
        if pf_interval is None:
            pf_interval = 0.05

        (pf_results, time_results) = self.waterfacility_restoration(mapping_set, restoration_key, end_time,
                                                                    time_interval, pf_interval)

        self.set_result_csv_data("pf_results", time_results, name="percentage_of_functionality_" +
                                                                  self.get_parameter("result_name"))
        self.set_result_csv_data("time_results", pf_results, name="reptime_" + self.get_parameter("result_name"))

        return True

    def waterfacility_restoration(self, mapping_set, restoration_key, end_time, time_interval,
                                  pf_interval):

        """Gets applicable restoration curve set and calculates restoration time and functionality

        Args:
            mapping_set (class): Restoration Mapping Set
            restoration_key (str): Restoration Key to determine which curve to use. E.g. Restoration ID Code
            end_time (float): User specified end repair time
            time_interval (float): Increment interval of repair time. Default to 1 (1 day)
            pf_interval (float): Increment interval of percentage of functionality. Default 0.1 (10%)

        Returns:
            time_results (list): Given Percentage of functionality, the change of repair time
            pf_results (list): Given Repair time, change of the percentage of functionality
        """

        time_results = []
        pf_results = []

        for mapping in mapping_set.mappings:
            # parse rules to get inventory class. e.g. treatment plan, tank, pump etc
            if isinstance(mapping.rules, list):
                inventory_class = RestorationService.extract_inventory_class_legacy(mapping.rules)
            elif isinstance(mapping.rules, dict):
                inventory_class = RestorationService.extract_inventory_class(mapping.rules)
            else:
                raise ValueError("Unsupported mapping rules!")

            # get restoration curves
            # if it's string:id; then need to fetch it from remote and cast to restorationcurveset object
            restoration_curve_set = mapping.entry[restoration_key]
            if isinstance(restoration_curve_set, str):
                restoration_curve_set = RestorationCurveSet(self.restorationsvc.get_dfr3_set(restoration_curve_set))

            # given time calculate pf
            time = np.arange(0, end_time + time_interval, time_interval)
            for t in time:
                pf_results.append({
                    "inventory_class": inventory_class,
                    "time": t,
                    **restoration_curve_set.calculate_restoration_rates(time=t)
                })

            # given pf calculate time
            pf = np.arange(0, 1 + pf_interval, pf_interval)
            for p in pf:
                new_dict = {}
                t_res = restoration_curve_set.calculate_inverse_restoration_rates(time=p)
                for key, value in t_res.items():
                    new_dict.update({"time_" + key: value})
                time_results.append({
                    "inventory_class": inventory_class,
                    "percentage_of_functionality": p,
                    **new_dict
                })

        return pf_results, time_results

    def get_spec(self):
        return {
            'name': 'water-facility-restoration',
            'description': 'water facility restoration analysis',
            'input_parameters': [
                {
                    'id': 'restoration_key',
                    'required': False,
                    'description': 'restoration key to use in mapping dataset',
                    'type': str
                },
                {
                    'id': 'result_name',
                    'required': True,
                    'description': 'result dataset name',
                    'type': str
                },
                {
                    'id': 'end_time',
                    'required': False,
                    'description': 'end time in days. Default to 365.',
                    'type': float
                },
                {
                    'id': 'time_interval',
                    'required': False,
                    'description': 'incremental interval for time in days. Default to 1',
                    'type': float
                },
                {
                    'id': 'pf_interval',
                    'required': False,
                    'description': 'incremental interval for percentage of functionality. Default to 0.05',
                    'type': float
                }
            ],
            'input_datasets': [
                {
                    'id': 'dfr3_mapping_set',
                    'required': True,
                    'description': 'DFR3 Mapping Set Object',
                    'type': ['incore:dfr3MappingSet'],
                }
            ],
            'output_datasets': [
                {
                    'id': 'pf_results',
                    'parent_type': '',
                    'description': 'A csv file recording functionality change with time for each class and limit '
                                   'state.',
                    'type': 'incore:waterFacilityRestorationFunc'
                },
                {
                    'id': 'time_results',
                    'parent_type': '',
                    'description': 'A csv file recording repair time at certain functionality recovery for each class '
                                   'and limit state.',
                    'type': 'incore:waterFacilityRestorationTime'
                },
            ]
        }