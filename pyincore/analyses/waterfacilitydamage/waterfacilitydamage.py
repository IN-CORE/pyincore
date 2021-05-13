# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


"""
Water Facility Damage
"""

import collections
import concurrent.futures
import random
from itertools import repeat

from pyincore import BaseAnalysis, HazardService, FragilityService, GeoUtil, \
    AnalysisUtil


class WaterFacilityDamage(BaseAnalysis):
    """Computes water facility damage for an earthquake tsunami, tornado, or hurricane exposure.

    """

    DEFAULT_EQ_FRAGILITY_KEY = "pga"
    DEFAULT_TSU_FRAGILITY_KEY = "Non-Retrofit inundationDepth Fragility ID Code"
    DEFAULT_LIQ_FRAGILITY_KEY = "pgd"

    def __init__(self, incore_client):
        # Create Hazard and Fragility service
        self.hazardsvc = HazardService(incore_client)
        self.fragilitysvc = FragilityService(incore_client)

        super(WaterFacilityDamage, self).__init__(incore_client)

    def run(self):
        """Performs Water facility damage analysis by using the parameters from the spec
        and creates an output dataset in csv format

        Returns:
            bool: True if successful, False otherwise
        """
        # Facility dataset
        inventory_set = self.get_input_dataset(
            "water_facilities").get_inventory_reader()

        # Get hazard input
        hazard_dataset_id = self.get_parameter("hazard_id")

        # Hazard type of the exposure
        hazard_type = self.get_parameter("hazard_type")

        user_defined_cpu = 1

        if not self.get_parameter("num_cpu") is None and self.get_parameter(
                "num_cpu") > 0:
            user_defined_cpu = self.get_parameter("num_cpu")

        num_workers = AnalysisUtil.determine_parallelism_locally(self,
                                                                 len(inventory_set),
                                                                 user_defined_cpu)

        avg_bulk_input_size = int(len(inventory_set) / num_workers)
        inventory_args = []
        count = 0
        inventory_list = list(inventory_set)
        while count < len(inventory_list):
            inventory_args.append(
                inventory_list[count:count + avg_bulk_input_size])
            count += avg_bulk_input_size

        (ds_results, damage_results) = self.waterfacility_damage_concurrent_execution(
            self.waterfacilityset_damage_analysis, num_workers,
            inventory_args, repeat(hazard_type), repeat(hazard_dataset_id))

        self.set_result_csv_data("result", ds_results, name=self.get_parameter("result_name"))
        self.set_result_json_data("metadata",
                                  damage_results,
                                  name=self.get_parameter("result_name") + "_additional_info")

        return True

    def waterfacility_damage_concurrent_execution(self, function_name,
                                                  parallel_processes,
                                                  *args):
        """Utilizes concurrent.future module.

            Args:
                function_name (function): The function to be parallelized.
                parallel_processes (int): Number of workers in parallelization.
                *args: All the arguments in order to pass into parameter function_name.

            Returns:
                list: A list of ordered dictionaries with water facility damage values
                list: A list of ordered dictionaries with other water facility data/metadata


        """
        output_ds = []
        output_dmg = []

        with concurrent.futures.ProcessPoolExecutor(max_workers=parallel_processes) as executor:
            for ret1, ret2 in executor.map(function_name, *args):
                output_ds.extend(ret1)
                output_dmg.extend(ret2)

        return output_ds, output_dmg

    def waterfacilityset_damage_analysis(self, facilities, hazard_type,
                                         hazard_dataset_id):
        """Gets applicable fragilities and calculates damage

        Args:
            facilities (list): Multiple water facilities from input inventory set.
            hazard_type (str): A hazard type of the hazard exposure (earthquake, tsunami, tornado, or hurricane).
            hazard_dataset_id (str): An id of the hazard exposure.

        Returns:
            list: A list of ordered dictionaries with water facility damage values
            list: A list of ordered dictionaries with other water facility data/metadata
        """
        ds_results = []
        damage_results = []

        liq_fragility = None
        use_liquefaction = self.get_parameter("use_liquefaction")
        liq_geology_dataset_id = self.get_parameter(
            "liquefaction_geology_dataset_id")
        uncertainty = self.get_parameter("use_hazard_uncertainty")
        fragility_key = self.get_parameter("fragility_key")

        if hazard_type == 'earthquake':
            if fragility_key is None:
                fragility_key = self.DEFAULT_EQ_FRAGILITY_KEY

            pga_fragility_set = self.fragilitysvc.match_inventory(self.get_input_dataset("dfr3_mapping_set"),
                                                                  facilities, fragility_key)

            liq_fragility_set = []

            if use_liquefaction and liq_geology_dataset_id is not None:
                liq_fragility_key = self.get_parameter(
                    "liquefaction_fragility_key")
                if liq_fragility_key is None:
                    liq_fragility_key = self.DEFAULT_LIQ_FRAGILITY_KEY
                liq_fragility_set = self.fragilitysvc.match_inventory(self.get_input_dataset(
                    "dfr3_mapping_set"), facilities, liq_fragility_key)

            for facility in facilities:
                fragility = pga_fragility_set[facility["id"]]
                if facility["id"] in liq_fragility_set:
                    liq_fragility = liq_fragility_set[facility["id"]]

                ds_result, damage_result = self.waterfacility_damage_analysis(facility, fragility,
                                                                              liq_fragility,
                                                                              hazard_type,
                                                                              hazard_dataset_id,
                                                                              liq_geology_dataset_id,
                                                                              uncertainty)
                ds_results.append(ds_result)
                damage_results.append(damage_result)

        elif hazard_type == 'tsunami':
            if fragility_key is None:
                fragility_key = self.DEFAULT_TSU_FRAGILITY_KEY

            inundation_fragility_set = self.fragilitysvc.match_inventory(
                self.get_input_dataset("dfr3_mapping_set"), facilities, fragility_key)

            for facility in facilities:
                fragility = inundation_fragility_set[facility["id"]]

                ds_result, damage_result = self.waterfacility_damage_analysis(facility, fragility, [],
                                                       facility["id"],
                                                       hazard_type,
                                                       hazard_dataset_id, "",
                                                       False)

                ds_results.append(ds_result)
                damage_results.append(damage_result)

        else:
            raise ValueError(
                "Hazard type other than Earthquake and Tsunami are not currently supported.")

        return ds_results, damage_results

    def waterfacility_damage_analysis(self, facility, fragility, liq_fragility,
                                      hazard_type, hazard_dataset_id,
                                      liq_geology_dataset_id, uncertainty):
        """Computes damage analysis for a single facility

        Args:
            facility (obj): A JSON mapping of a facility based on mapping attributes
            fragility (obj): A JSON description of fragility mapped to the building.
            liq_fragility (obj): A JSON description of liquefaction fragility mapped to the building.
            hazard_type (str): A string that indicates the hazard type
            hazard_dataset_id (str): Hazard id from the hazard service
            liq_geology_dataset_id (str): Geology dataset id from data service to use for liquefaction calculation, if
                applicable
            uncertainty (bool): Whether to use hazard standard deviation values for uncertainty

        Returns:
            OrderedDict: ordered dictionary with water facility damage values
            OrderedDict: ordered dictionary with other water facility data/metadata.
        """
        hazard_std_dev = 0
        if uncertainty:
            hazard_std_dev = random.random()

        hazard_demand_type = fragility.demand_types[0]
        demand_unit = fragility.demand_units[0]
        liq_hazard_type = None
        liq_hazard_val = None
        liquefaction_prob = None
        location = GeoUtil.get_location(facility)

        point = str(location.y) + "," + str(location.x)

        if hazard_type == "earthquake":
            hazard_val_set = self.hazardsvc.get_earthquake_hazard_values(
                hazard_dataset_id, hazard_demand_type,
                demand_unit, [point])
        elif hazard_type == "tsunami":
            hazard_val_set = self.hazardsvc.get_tsunami_hazard_values(
                hazard_dataset_id, hazard_demand_type, demand_unit, [point])
        else:
            raise ValueError(
                "Hazard type other than Earthquake and Tsunami are not currently supported.")
        hazard_val = hazard_val_set[0]['hazardValue']
        if hazard_val < 0:
            hazard_val = 0

        limit_states = fragility.calculate_limit_state_w_conversion(hazard_val,
                                                                    std_dev=hazard_std_dev,
                                                                    inventory_type="water_facility")

        pgd_demand_unit = None

        if liq_fragility is not None and liq_geology_dataset_id:
            liq_hazard_type = liq_fragility.demand_types[0]
            pgd_demand_unit = liq_fragility.demand_units[0]
            point = str(location.y) + "," + str(location.x)

            liquefaction = self.hazardsvc.get_liquefaction_values(
                hazard_dataset_id, liq_geology_dataset_id,
                pgd_demand_unit, [point])
            liq_hazard_val = liquefaction[0][liq_hazard_type]
            liquefaction_prob = liquefaction[0]['liqProbability']
            pgd_limit_states = liq_fragility.calculate_limit_state_w_conversion(liq_hazard_val,
                                                                                std_dev=hazard_std_dev,
                                                                                inventory_type="water_facility")

            limit_states = AnalysisUtil.adjust_limit_states_for_pgd(
                limit_states, pgd_limit_states)

        dmg_intervals = fragility.calculate_damage_interval(limit_states,
                                                            hazard_type=hazard_type,
                                                            inventory_type="water_facility")

        result = collections.OrderedDict()
        result['guid'] = facility['properties']['guid']
        result = {**limit_states, **dmg_intervals}  # Needs py 3.5+
        metadata = collections.OrderedDict()
        metadata['guid'] = facility['properties']['guid']
        metadata['hazardtype'] = hazard_type
        metadata['hazardval'] = hazard_val
        metadata['demandtypes'] = hazard_demand_type
        metadata['demandunits'] = demand_unit
        metadata['liqhaztype'] = liq_hazard_type
        metadata['liqhazval'] = liq_hazard_val
        metadata['liqprobability'] = liquefaction_prob

        return result, metadata

    def get_spec(self):
        return {
            'name': 'water-facility-damage',
            'description': 'water facility damage analysis',
            'input_parameters': [
                {
                    'id': 'result_name',
                    'required': False,
                    'description': 'result dataset name',
                    'type': str
                },
                {
                    'id': 'hazard_type',
                    'required': True,
                    'description': 'Hazard Type (e.g. earthquake)',
                    'type': str
                },
                {
                    'id': 'hazard_id',
                    'required': True,
                    'description': 'Hazard ID',
                    'type': str
                },
                {
                    'id': 'fragility_key',
                    'required': False,
                    'description': 'Fragility key to use in mapping dataset',
                    'type': str
                },
                {
                    'id': 'use_liquefaction',
                    'required': False,
                    'description': 'Use liquefaction',
                    'type': bool
                },

                {
                    'id': 'liquefaction_geology_dataset_id',
                    'required': False,
                    'description': 'Liquefaction geology/susceptibility dataset id. '
                                   'If not provided, liquefaction will be ignored',
                    'type': str
                },
                {
                    'id': 'liquefaction_fragility_key',
                    'required': False,
                    'description': 'Fragility key to use in liquefaction mapping dataset',
                    'type': str
                },
                {
                    'id': 'use_hazard_uncertainty',
                    'required': False,
                    'description': 'Use hazard uncertainty',
                    'type': bool
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
                }
            ],
            'output_datasets': [
                {
                    'id': 'result',
                    'parent_type': 'water_facilities',
                    'description': 'A csv file with limit state probabilities and damage states '
                                   'for each water facility',
                    'type': 'ergo:waterFacilityDamageVer5'
                },
                {
                    'id': 'metadata',
                    'parent_type': 'water_facilities',
                    'description': 'additional metadata in json file about applied hazard value and '
                                   'fragility',
                    'type': 'incore:waterFacilityDamageSupplement'
                }
            ]
        }
