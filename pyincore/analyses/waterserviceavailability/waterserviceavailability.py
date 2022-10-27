# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


"""
Water Service Availability
"""

from typing import List
from pyincore import BaseAnalysis
import pandas as pd
import networkx as nx
import numpy as np

from pyincore.analyses.waterserviceavailability import WaterServiceAvailabilityUtil


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

        supply = self.get_parameter("supply_rate")
        stage_time_series = self.get_parameter("stage_time_series")

        Stage2_time_series = np.linspace(stage2_start, stage2_end, stage2_end - stage2_start + 1)
        house_junction = self.get_input_dataset("house_junction").get_json_reader()
        building_junction = self.get_input_dataset("building_junction").get_json_reader()


        service_availability_stage1 = self.calculate_service_availability(stage_time_series, demand_post_hazard,
                                                                          demand_normal)

        service_availability_stage2 = self.infer_service_availability(supply, stage_time_series,
                                                                      wdn_post_hazard, results_post_hazard,
                                                                      results_normal)
        # combine two stages
        service_availability = pd.concat([service_availability_stage1, service_availability_stage2])

        household_service_availability = WaterServiceAvailabilityUtil.map_to_household_service_availability(
            house_junction, service_availability)
        self.set_result_csv_data("household_service_availability", household_service_availability,
                                 name="household_service_availability" + self.get_parameter("result_name"),
                                 source="dataframe")

        building_service_availability = WaterServiceAvailabilityUtil.map_to_building_service_availability(
            building_junction, service_availability)
        self.set_result_csv_data("building_service_availability", building_service_availability,
                                 name="building_service_availability" + self.get_parameter("result_name"),
                                 source="dataframe")

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

    # Infer if a node has water service
    def infer_service_availability(self, supply, stage_time_series, wdn_post_hazard, results_post_hazard,
                                   results_normal):
        stage_start = stage_time_series[0]
        # Get the directed network at the stage_start, use this network as the base network for inference
        flow_post_hazard = results_post_hazard.link['flowrate']
        dgraph_stage_start = WaterServiceAvailabilityUtil.hourly_dgraph(wdn_post_hazard, flow_post_hazard, stage_start)
        # Initialize a pandas dataframe with time (hour) as index, node names as column names
        demand_normal = results_normal.node['demand']
        service_availability = pd.DataFrame(columns=demand_normal.columns, index=stage_time_series)
        # All the downstream nodes of the source (water treatment plant)
        downstreams = list(nx.bfs_successors(dgraph_stage_start, source=wdn_post_hazard.reservoir_name_list[0]))
        n = len(downstreams)
        # Iterate over rows of the dataframe
        for index, row in service_availability.iterrows():
            # Sepcify the available partial supply at this index time instant
            total_supply = supply
            # Store nodes with service
            node_service = []
            end_indicator = 0
            for i in range(n):
                (up, down) = downstreams[i]
                # Check if the downstream node has water service
                if end_indicator < 1:
                    for dn in down:
                        # Only focus on node that has demand
                        if demand_normal.loc[index * 3600, dn] > 1e-5:
                            total_supply -= demand_normal.loc[index * 3600, dn]
                            # If there is left supply
                            if total_supply > 0:
                                # node dn has water service
                                node_service.append(dn)
                            else:
                                end_indicator = 1
                                break
                else:
                    break
            # Iterate over columns
            for c in service_availability.columns:
                # If this node has water service
                if c in node_service:
                    row[c] = 1
                else:
                    row[c] = 0
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
                    'id': 'supply_rate',
                    'required': True,
                    'description': 'Average supply flow rates, 50% of normal average flow rates from the water '
                                   'treatment plant',
                    'type': float
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
                    'id': 'house_junction',
                    'required': True,
                    'description': 'House junction',
                    'type': ['incore:houseJunction'],
                },
                {
                    'id': 'building_junction',
                    'required': True,
                    'description': 'building junction',
                    'type': ['incore:bldgJunction'],
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
