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

        # Get Fragility key
        restoration_key = self.get_parameter("restoration_key")
        if restoration_key is None:
            restoration_key = "Restoration ID Code"

        # Hazard type of the exposure
        hazard_type = self.get_parameter("hazard_type")

        end_time = self.get_parameter("end_time")
        if end_time is None:
            end_time = 365.0

        time_interval = self.get_parameter("time_interval")
        if time_interval is None:
            time_interval = 1  # 1 day

        pf_interval = self.get_parameter("pf_interval")
        if pf_interval is None:
            pf_interval = 0.1  # 0.1

        (pf_results, time_results) = self.waterfacility_restoration(mapping_set, restoration_key, hazard_type, end_time,
                                                                    time_interval, pf_interval)

        self.set_result_csv_data("pf_results", time_results, name="percentage_of_functionality_" +
                                                                  self.get_parameter("result_name"))
        self.set_result_csv_data("time_results", pf_results, name="reptime_" + self.get_parameter("result_name"))

        return True

    def waterfacility_restoration(self, mapping_set, restoration_key, hazard_type, end_time, time_interval, pf_interval):

        """Gets applicable restoration and calculates restoration time and functionality

        Args:
            mapping_set (class):
            restoration_key (str):
            hazard_type (str): A hazard type of the hazard exposure (earthquake, tsunami, tornado, or hurricane).
            end_time (float):
            time_interval (float):
            pf_interval (float):

        Returns:

        """

        time_results = []
        pf_results = []

        # Obtain the restoration set

        '''
            {
              "entry": {
                "Restoration ID Code": "xxxx"
              },
              "rules": [
                [
                  "java.lang.String utilfcltyc EQUALS 'PWT2'",
                  # "java.lang.String utilfcltyc EQUALS 'PPP2'",
                ]
              ]
            },
        '''
        for mapping in mapping_set.mappings:
            # TODO parse rules to get inventory class. e.g. treatment plan, tank, pump etc
            inventory_class = "parse rules to get type"
            restoration_curve_set = mapping.entry[restoration_key]
            # if it's string:id; then need to fetch it from remote and cast to restorationcurveset object
            if isinstance(restoration_curve_set, str):
                restoration_curve_set = RestorationCurveSet(self.restorationsvc.get_dfr3_set(restoration_curve_set))

            time = np.arange(0, end_time, time_interval)
            for t in time:
                pf_results.append({
                    "inventory_class": inventory_class,
                    "time": t,
                    **restoration_curve_set.calculate_restoration_rates(time=t)
                })

            pf = np.arange(0, 1, pf_interval, )
            for p in pf:
                time_results.append({
                    "inventory_class": inventory_class,
                    "percentage_of_functionality": p,
                    **restoration_curve_set.calculate_inverse_restoration_rates(time=p)
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
                    'id': 'hazard_type',
                    'required': True,
                    'description': 'hazard type',
                    'type': str
                },
                {
                    'id': 'end_time',
                    'required': False,
                    'description': 'end time. Default to 365.',
                    'type': float
                },
                {
                    'id': 'time_interval',
                    'required': False,
                    'description': 'incremental interval for time. Default to 1',
                    'type': float
                },
                {
                    'id': 'pf_interval',
                    'required': False,
                    'description': 'incremental interval for percentage of functionality. Default to 0.1',
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
                    'description': 'A csv file recording repair time at certain funcionality recovery for each class '
                                   'and limit state.',
                    'type': 'incore:waterFacilityRestorationTime'
                },
            ]
        }
