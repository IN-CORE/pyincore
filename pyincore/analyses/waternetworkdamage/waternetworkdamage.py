# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import pandas as pd
import concurrent.futures
from itertools import repeat
from collections import OrderedDict

from pyincore.analyses.waternetworkdamage.waternetworkutil import WaterNetworkUtil
from pyincore import HazardService, FragilityService
from pyincore import AnalysisUtil
from pyincore import GeoUtil
from pyincore import BaseAnalysis
from pyincore.dataset import Dataset
from pyincore.networkdataset import NetworkDataset


class WaterNetworkDamage(BaseAnalysis):

    def __init__(self, incore_client):
        self.hazardsvc = HazardService(incore_client)
        self.fragilitysvc = FragilityService(incore_client)

        super(WaterNetworkDamage, self).__init__(incore_client)

    def get_pipe_damage_bulk_input(self, pipes, fragility_sets):
        """run pipeline damage for multiple pipes

        Args:
            pipes: multiple pipes from shapefile
            fragility_sets: fragility set apply to each pipe

        Returns:
            a list of damage state for each pipe

        """
        output = []
        for pipe in pipes:
            result = self.get_pipe_damage(pipe, fragility_sets)
            if result != None:
                output.append(result)

        return output

    def get_pump_damage_bulk_input(self, pumps, fragility_sets):
        """run pump damage for multiple pumps

        Args:
            pumps: multiple pumps from shapefile
            fragility_sets: fragility set apply to each pump

        Returns:
            a list of damage state for each pump

        """
        output = []
        for pump in pumps:
            result = self.get_pump_damage(pump, fragility_sets)
            if result != None:
                output.append(result)

        return output

    def get_tank_damage_bulk_input(self, tanks, fragility_sets):
        """run tank damage for multiple pumps

        Args:
            tanks: multiple tanks from shapefile
            fragility_sets: fragility set apply to each tank

        Returns:
            a list of damage state for each tank

        """
        output = []
        for tank in tanks:
            result = self.get_tank_damage(tank, fragility_sets)
            if result != None:
                output.append(result)

        return output

    def get_pipe_damage(self, pipe, fragility_sets):
        """run pipeline damage for a single pipe

        Args:
            pipe: a pipe
            fragility_sets: fragility set apply to each pipe

        Returns:

        """
        if pipe['properties']['data_type'] == 'pipe' and pipe['id'] in fragility_sets.keys():

            pipe_PEDS = OrderedDict()

            # calculate pipe length, make sure foot convert to m
            pipe_PEDS['pipe_length'] = float(pipe['properties']['length']) * 0.3048

            # get Pipe location
            location = GeoUtil.get_location(pipe)

            point = str(location.y) + "," + str(location.x)

            # get hazard value pgv
            hazard_val = self.hazardsvc.get_earthquake_hazard_values(
                hazard_id=self.get_parameter('earthquake_id'),
                demand_type='pgv',
                demand_units='in/s',
                points=[point])[0]['hazardValue']

            # make sure it converts in/s back to m/s
            pipe_PEDS['id'] = pipe['id']
            pipe_PEDS['hazardtype'] = 'PGV'
            pipe_PEDS['hazardval'] = hazard_val * 0.0254

            # calculate repair rate for pipe
            fragility_vars = {'x': hazard_val}
            rr_pipe = \
                AnalysisUtil.compute_custom_limit_state_probability(fragility_sets[pipe['id']],
                                                                    fragility_vars)
            # 1/1000ft convert to 1/m
            rr_pipe = WaterNetworkUtil.convert_result_unit("repairs/1000ft", rr_pipe)
            pipe_PEDS['mean_repair_rate'] =  rr_pipe * pipe_PEDS['pipe_length']

            return pipe_PEDS

    def get_pump_damage(self, pump, fragility_sets):
        """ rum pump damage for a single pump

        Args:
            pump: a pump
            fragility_sets: fragility set applicable to pump

        Returns:

        """
        if pump['properties']['data_type'] == 'pump' and pump['id'] in fragility_sets.keys():

            pump_PEDS = OrderedDict()

            # calculate pump coordinates and calculate its pga
            location = GeoUtil.get_location(pump)

            point = str(location.y) + "," + str(location.x)

            # calculate pga
            hazard_val = self.hazardsvc.get_earthquake_hazard_values(
                hazard_id=self.get_parameter('earthquake_id'),
                demand_type='pga',
                demand_units='g',
                points=[point])[0]['hazardValue']

            pump_PEDS['id'] = pump['id']
            pump_PEDS['hazardtype'] = fragility_sets[pump['id']]['demandType']
            pump_PEDS['hazardval'] = hazard_val

            # calculate cdf
            dmg_probability = AnalysisUtil.calculate_damage_json2(
                fragility_sets[pump['id']], hazard_val)
            for key, val in dmg_probability.items():
                pump_PEDS[key] = val

            return pump_PEDS

    def get_tank_damage(self, tank, fragility_sets):
        """run tank damage analysis for a single tank

        Args:
            tank: a tank
            fragility_sets: fragility set applicable to tank

        Returns:

        """
        if tank['properties']['data_type'] == 'tank' and tank['id'] in fragility_sets.keys():
            tank_PEDS = OrderedDict()

            # get tank coordinates and calculate its pga
            location = GeoUtil.get_location(tank)

            point = str(location.y) + "," + str(location.x)

            hazard_val = self.hazardsvc.get_earthquake_hazard_values(
                hazard_id=self.get_parameter('earthquake_id'),
                demand_type='pga',
                demand_units='g',
                points=[point])[0]['hazardValue']

            tank_PEDS['id'] = tank['id']
            tank_PEDS['hazardtype'] = fragility_sets[tank['id']]['demandType']
            tank_PEDS['hazardval'] = hazard_val

            # calculate cdf
            dmg_probability = AnalysisUtil.calculate_damage_json2(
                fragility_sets[tank['id']],
                hazard_val)
            for key, val in dmg_probability.items():
                tank_PEDS[key] = val

            return tank_PEDS

    def water_network_damage_concurrent_future(self, function_name, parallelism, *args):
        """Utilizes concurrent.future module.

        Args:
            function_name: the function to be parallelized
            parallelism: number of max workers in parallelization
            *args: all the arguments in order to pass into parameter function_name

        Returns:
            output: list of OrderedDict

        """
        output = []
        with concurrent.futures.ProcessPoolExecutor(max_workers=parallelism) as executor:
            for result in executor.map(function_name, *args):
                output.extend(result)

        return output

    def run(self):
        """
        Executes water network damage analysis
        """

        # Water network dataset
        water_network_set = NetworkDataset(self.get_input_dataset("water_network"))
        water_facilities_set = water_network_set.node.get_inventory_reader()
        water_pipelines_set = water_network_set.link.get_inventory_reader()

        water_pipelines = list(water_pipelines_set)
        for item in water_pipelines:
            item['id'] = item['properties']['id']

        water_facilities = list(water_facilities_set)
        for item in water_facilities:
            item['id'] = item['properties']['id']

        # Get hazard input
        earthquake_id = self.get_parameter("earthquake_id")

        # mapping id
        water_pipeline_mapping_id = self.get_parameter('water_pipeline_mapping_id')
        water_facility_mapping_id = self.get_parameter('water_facility_mapping_id')

        ########################################################################
        # pipeline damage states
        if not self.get_parameter("num_cpu") is None and self.get_parameter("num_cpu") > 0:
            user_defined_cpu = self.get_parameter("num_cpu")
        else:
            user_defined_cpu = 1

        parallelism = AnalysisUtil.determine_parallelism_locally(len(water_pipelines), user_defined_cpu)
        pipes_per_process = int(len(water_pipelines) / parallelism)
        inventory_args = []
        count = 0

        while count < len(water_pipelines):
            inventory_args.append(
                water_pipelines[count:count + pipes_per_process])
            count += pipes_per_process

        water_pipeline_fragility_sets = \
            self.fragilitysvc.map_inventory(water_pipeline_mapping_id,
                                              water_pipelines,
                                              "pgv")

        output = self.water_network_damage_concurrent_future(
            self.get_pipe_damage_bulk_input,
            parallelism,
            inventory_args,
            repeat(water_pipeline_fragility_sets))
        pipe_PEDS = pd.DataFrame(output).set_index('id')
        pipe_PEDS.to_csv('pipeline_dmg.csv')
        pipeline_dmg_dataset = Dataset.from_file('pipeline_dmg.csv', 'csv')
        self.set_output_dataset("pipeline_dmg", pipeline_dmg_dataset)

        ########################################################################
        # facility damage states
        parallelism = AnalysisUtil.determine_parallelism_locally(
            len(water_facilities), user_defined_cpu)
        water_facility_fragility_sets = self.fragilitysvc.map_inventory(
            water_facility_mapping_id, water_facilities, "pga")
        facility_per_process = int(len(water_facilities) / parallelism)
        inventory_args = []
        count = 0

        while count < len(water_facilities):
            inventory_args.append(
                water_facilities[count:count + facility_per_process])
            count += facility_per_process

        # pump damage states
        output = self.water_network_damage_concurrent_future(
            self.get_pump_damage_bulk_input,
            parallelism,
            inventory_args,
            repeat(water_facility_fragility_sets))
        pump_PEDS = pd.DataFrame(output).set_index('id')
        pump_PEDS.to_csv('pump_dmg.csv')
        pump_dmg_dataset = Dataset.from_file('pump_dmg.csv', 'csv')
        self.set_output_dataset("pump_dmg", pump_dmg_dataset)

        # tank damage states
        output = self.water_network_damage_concurrent_future(
            self.get_tank_damage_bulk_input,
            parallelism,
            inventory_args,
            repeat(water_facility_fragility_sets))
        tank_PEDS = pd.DataFrame(output).set_index('id')
        tank_PEDS.to_csv('tank_dmg.csv')
        tank_dmg_dataset = Dataset.from_file('tank_dmg.csv', 'csv')
        self.set_output_dataset("tank_dmg", tank_dmg_dataset)

        return True

    def get_spec(self):
        return {
            'name': 'water-network-damage',
            'description': 'water network damage analysis',
            'input_parameters': [
                {
                    'id': 'water_facility_mapping_id',
                    'required': True,
                    'description': 'water facility fragility mapping dataset',
                    'type': str
                },
                {
                    'id': 'water_pipeline_mapping_id',
                    'required': True,
                    'description': 'water pipeline fragility mapping dataset',
                    'type': str
                },
                {
                    'id': 'earthquake_id',
                    'required': True,
                    'description': 'earthquake ID',
                    'type': str
                },
                {
                    'id': 'num_cpu',
                    'required': False,
                    'description': 'If using parallel execution, the number of cpus to request',
                    'type': int
                },
            ],
            'input_datasets': [
                {
                    'id': 'water_network',
                    'required': True,
                    'description':'',
                    'type': ['incore:waternetwork']
                },
            ],
            'output_datasets': [
                {
                    'id': 'pipeline_dmg',
                    'type': 'ergo:pipelineDamage'
                },
                {
                    'id': 'tank_dmg',
                    'type': 'ergo:pumpDamage'
                },
                {
                    'id': 'pump_dmg',
                    'type': 'ergo:lifelineWaterTankInventoryDamage'
                }
            ]
        }
