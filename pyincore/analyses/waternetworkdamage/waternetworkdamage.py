import pandas as pd
import concurrent.futures
from itertools import repeat
from collections import OrderedDict

from pyincore.analyses.waternetworkdamage.waternetworkutil import WaterNetworkUtil
from pyincore import HazardService, FragilityService
from pyincore import AnalysisUtil
from pyincore import InventoryDataset
from pyincore import GeoUtil

class WaterNetworkDamage:

    def __init__(self, client, water_facility_shp, water_pipeline_shp):
        """
        :param client:
        :param water_facility_shp:
        :param water_pipeline_shp:
        """

        self.hazardsvc = HazardService(client)
        self.fragilitysvc = FragilityService(client)

        # get water facility information
        water_facility_set = InventoryDataset(water_facility_shp)
        water_pipeline_set = InventoryDataset(water_pipeline_shp)

        water_facilities= list(water_facility_set.inventory_set)
        # note pipeline shapefile has pump as lines
        water_pipelines = list(water_pipeline_set.inventory_set)

        for item in water_facilities:
            item['id'] = item['properties']['id']
        self.water_facilities = water_facilities

        for item in water_pipelines:
            item['id'] = item['properties']['id']
        self.water_pipelines = water_pipelines

    def get_pipe_damage_bulk_input(self, pipes, fragility_sets, hazard_id):
        output = []
        for pipe in pipes:
            result = self.get_pipe_damage(pipe, fragility_sets, hazard_id)
            if result != None:
                output.append(result)

        return output

    def get_pump_damage_bulk_input(self, pumps, fragility_sets, hazard_id):
        output = []
        for pump in pumps:
            result = self.get_pump_damage(pump, fragility_sets, hazard_id)
            if result != None:
                output.append(result)

        return output

    def get_tank_damage_bulk_input(self, tanks, fragility_sets, hazard_id):
        output = []
        for tank in tanks:
            result = self.get_tank_damage(tank, fragility_sets, hazard_id)
            if result != None:
                output.append(result)

        return output

    def get_pipe_damage(self, pipe, fragility_sets, hazard_id):
        """
        :param pipe:
        :param fragility_sets:
        :param hazard_id:
        :return:
        """
        if pipe['properties']['data_type'] == 'pipe' and pipe['id'] in fragility_sets.keys():

            pipe_PEDS = OrderedDict()

            # calculate pipe length, make sure foot convert to m
            pipe_PEDS['pipe_length'] = float(pipe['properties']['length']) * 0.3048

            # get Pipe location
            location = GeoUtil.get_location(pipe)

            # get hazard value pgv
            hazard_val = self.hazardsvc.get_earthquake_hazard_values(
                hazard_id=hazard_id,
                demand_type='pgv',
                demand_units='in/s',
                points=[location.y,location.x])[0]['hazardValue']

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

    def get_pump_damage(self, pump, fragility_sets, hazard_id):
        """
        :param self:
        :param pump:
        :param fragility_sets:
        :param hazard_id:
        :return:
        """
        if pump['properties']['data_type'] == 'pump' and pump['id'] in fragility_sets.keys():

            pump_PEDS = OrderedDict()

            # calculate pump coordinates and calculate its pga
            location = GeoUtil.get_location(pump)

            # calulate pga
            hazard_val = self.hazardsvc.get_earthquake_hazard_values(
                hazard_id=hazard_id,
                demand_type='pga',
                demand_units='g',
                points=[location.y,location.x])[0]['hazardValue']

            pump_PEDS['id'] = pump['id']
            pump_PEDS['hazardtype'] = fragility_sets[pump['id']]['demandType']
            pump_PEDS['hazardval'] = hazard_val

            # calculate cdf
            dmg_probability = AnalysisUtil.calculate_damage_json2(
                fragility_sets[pump['id']], hazard_val)
            for key, val in dmg_probability.items():
                pump_PEDS[key] = val

            return pump_PEDS

    def get_tank_damage(self, tank, fragility_sets, hazard_id):
        """
        :param self:
        :param tank:
        :param fragility_sets:
        :param hazard_id:
        :return:
        """
        if tank['properties']['data_type'] == 'tank' and tank['id'] in fragility_sets.keys():
            tank_PEDS = OrderedDict()

            # get tank coordinates and calculate its pga
            location = GeoUtil.get_location(tank)
            hazard_val = self.hazardsvc.get_earthquake_hazard_values(
                hazard_id=hazard_id,
                demand_type='pga',
                demand_units='g',
                points=[location.y,location.x])[0]['hazardValue']

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
        """
        :param self:
        :param function_name:
        :param parallelism:
        :param args:
        :return:
        """
        output = []
        with concurrent.futures.ProcessPoolExecutor(max_workers=parallelism) as executor:
            for result in executor.map(function_name, *args):
                output.extend(result)

        return output

    def water_netowork_damage(self, water_facility_mapping_id, water_pipeline_mapping_id,
                   hazard_id, num_threads=0):
        """
        :param self:
        :param water_facility_mapping_id:
        :param water_pipeline_mapping_id:
        :param hazard_id:
        :param simulation_num:
        :param num_threads:
        :param peak_hour:
        :return:
        """

        ########################################################################
        # pipeline damage states
        parallelism = AnalysisUtil.determine_parallelism_locally(len(self.water_pipelines), num_threads)
        pipes_per_process = int(len(self.water_pipelines) / parallelism)
        inventory_args = []
        count = 0

        while count < len(self.water_pipelines):
            inventory_args.append(
                self.water_pipelines[count:count + pipes_per_process])
            count += pipes_per_process

        water_pipeline_fragility_sets = \
            self.fragilitysvc.map_fragilities(water_pipeline_mapping_id,
                                              self.water_pipelines,
                                              "pgv")

        output = self.water_network_damage_concurrent_future(
            self.get_pipe_damage_bulk_input,
            parallelism,
            inventory_args,
            repeat(water_pipeline_fragility_sets),
            repeat(hazard_id))
        pipe_PEDS = pd.DataFrame(output).set_index('id')
        pipe_PEDS.to_csv('pipeline_dmg.csv')
        print('pipeline_dmg.csv')

        ########################################################################
        # facility damage states
        parallelism = AnalysisUtil.determine_parallelism_locally(len(self.water_facilities), num_threads)
        water_facility_fragility_sets = self.fragilitysvc.map_fragilities(water_facility_mapping_id, self.water_facilities, "pga")
        facility_per_process = int(len(self.water_facilities) / parallelism)
        inventory_args = []
        count = 0

        while count < len(self.water_facilities):
            inventory_args.append(
                self.water_facilities[count:count + facility_per_process])
            count += facility_per_process

        # pump damage states
        output = self.water_network_damage_concurrent_future(
            self.get_pump_damage_bulk_input,
            parallelism,
            inventory_args,
            repeat(water_facility_fragility_sets),
            repeat(hazard_id))
        pump_PEDS = pd.DataFrame(output).set_index('id')
        pump_PEDS.to_csv('pump_dmg.csv')
        print('pump_dmg.csv')

        # tank damage states
        output = self.water_network_damage_concurrent_future(
            self.get_tank_damage_bulk_input,
            parallelism,
            inventory_args,
            repeat(water_facility_fragility_sets),
            repeat(hazard_id))
        tank_PEDS = pd.DataFrame(output).set_index('id')
        tank_PEDS.to_csv('tank_dmg.csv')
        print('tank_dmg.csv')

        return None