# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


"""
Water Service Availability
"""

from typing import List
from pyincore import BaseAnalysis
import pandas as pd


class WaterServiceAvailability(BaseAnalysis):
    """Computes flood water service availability.

    """

    def __init__(self, incore_client):
        super(WaterServiceAvailability, self).__init__(incore_client)

    def run(self):
        """Performs Water facility restoration analysis by using the parameters from the spec
        and creates an output dataset in csv format

        Returns:
            bool: True if successful, False otherwise
        """

        service_availability = self.calculate_service_availability(stage_time_series,
                                                                   demand_post_hazard,
                                                                   demand_normal)

        self.set_result_csv_data("service_availability", service_availability,
                                 name="service_availability" + self.get_parameter("result_name"))

        return True

    def calculate_service_availability(self, stage_time_series, demand_post_hazard, demand_normal):
        # Initialize a pandas dataframe with time (hour) as index, node names as column names
        service_availability = pd.DataFrame(columns = demand_post_hazard.columns, index = stage_time_series)
        # Iterate over rows of the dataframe
        for index, row in service_availability.iterrows():
            # Iterate over columns
            for c in service_availability.columns:
                # If the junction has no demand
                if demand_normal.loc[index * 3600, c] < 1e-5:
                    row[c] = 0
                else:
                    row[c] = demand_post_hazard.loc[index * 3600, c] / demand_normal.loc[index * 3600, c]
        return service_availability

    def get_spec(self):
        return {
            'name': 'water-facility-restoration',
            'description': 'water facility restoration analysis',
            'input_parameters': [
                {
                    'id': 'result_name',
                    'required': True,
                    'description': 'result dataset name',
                    'type': str
                },
                {
                    'id': 'stage1_start_hr',
                    'required': True,
                    'description': 'Stage 1 start hour',
                    'type': int
                },
                {
                    'id': 'stage1_end_hr',
                    'required': True,
                    'description': 'Stage 1 end hour',
                    'type': int
                },
                {
                    'id': 'stage2_start_hr',
                    'required': True,
                    'description': 'Stage 2 start hour',
                    'type': int
                },
                {
                    'id': 'stage2_start_hr',
                    'required': True,
                    'description': 'Stage 2 start hour',
                    'type': int
                },
                {
                    'id': 'pf_interval',
                    'required': False,
                    'description': 'incremental interval for percentage of functionality. Default to 0.05',
                    'type': float
                },
                {
                    'id': 'discretized_days',
                    'required': False,
                    'description': 'Discretized days to compute functionality',
                    'type': List[int]
                }

            ],
            'input_datasets': [
                {
                    'id': 'water_facilities',
                    'required': True,
                    'description': 'Water Facility Inventory',
                    'type': ['ergo:waterFacilityTopo'],
                },
                {
                    'id': 'dfr3_mapping_set',
                    'required': True,
                    'description': 'DFR3 Mapping Set Object',
                    'type': ['incore:dfr3MappingSet'],
                },
                {

                    'id': 'damage',
                    'required': True,
                    'description': 'damage result that has damage intervals in it',
                    'type': ['ergo:waterFacilityDamageVer6']
                }
            ],
            'output_datasets': [
                {
                    'id': "inventory_restoration_map",
                    'parent_type': '',
                    'description': 'A csv file recording the mapping relationship between GUID and restoration id '
                                   'applicable.',
                    'type': 'incore:inventoryRestorationMap'
                },
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
                {
                    'id': 'func_results',
                    'parent_type': '',
                    'description': 'A csv file recording discretized functionality over time',
                    'type': 'incore:waterFacilityDiscretizedRestorationFunc'
                }
            ]
        }
