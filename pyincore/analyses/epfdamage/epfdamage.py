# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import concurrent.futures
import random
from itertools import repeat

from pyincore import AnalysisUtil, GeoUtil
from pyincore import BaseAnalysis, HazardService, FragilityService


class EpfDamage(BaseAnalysis):
    """Computes electric power facility structural damage for an earthquake hazard.

    Args:
        incore_client (IncoreClient): Service authentication.

    """

    DEFAULT_LIQ_FRAGILITY_KEY = "pgd"
    DEFAULT_FRAGILITY_KEY = "pga"

    def __init__(self, incore_client):
        self.hazardsvc = HazardService(incore_client)
        self.fragilitysvc = FragilityService(incore_client)

        super(EpfDamage, self).__init__(incore_client)

    def run(self):
        """Executes electric power facility damage analysis."""
        epf_set = self.get_input_dataset("epfs").get_inventory_reader()

        # Get Fragility key
        fragility_key = self.get_parameter("fragility_key")
        if fragility_key is None:
            fragility_key = self.DEFAULT_FRAGILITY_KEY
            self.set_parameter("fragility_key", fragility_key)

        # Get hazard input
        hazard_dataset_id = self.get_parameter("hazard_id")

        # Hazard type, note this is here for future use if additional hazards are supported by this analysis
        hazard_type = self.get_parameter("hazard_type")

        # Hazard Uncertainty
        use_hazard_uncertainty = False
        if self.get_parameter("use_hazard_uncertainty") is not None:
            use_hazard_uncertainty = self.get_parameter("use_hazard_uncertainty")

        # Liquefaction
        use_liquefaction = False
        if self.get_parameter("use_liquefaction") is not None:
            use_liquefaction = self.get_parameter("use_liquefaction")
        liq_geology_dataset_id = self.get_parameter("liquefaction_geology_dataset_id")

        user_defined_cpu = 1

        if not self.get_parameter("num_cpu") is None and self.get_parameter("num_cpu") > 0:
            user_defined_cpu = self.get_parameter("num_cpu")

        num_workers = AnalysisUtil.determine_parallelism_locally(self, len(epf_set), user_defined_cpu)

        avg_bulk_input_size = int(len(epf_set) / num_workers)
        inventory_args = []
        count = 0
        inventory_list = list(epf_set)
        while count < len(inventory_list):
            inventory_args.append(inventory_list[count:count + avg_bulk_input_size])
            count += avg_bulk_input_size

        results = self.epf_damage_concurrent_future(self.epf_damage_analysis_bulk_input, num_workers,
                                                    inventory_args, repeat(hazard_type), repeat(hazard_dataset_id),
                                                    repeat(use_hazard_uncertainty),
                                                    repeat(use_liquefaction), repeat(liq_geology_dataset_id))

        self.set_result_csv_data("result", results, name=self.get_parameter("result_name"))

        return True

    def epf_damage_concurrent_future(self, function_name, num_workers, *args):
        """Utilizes concurrent.future module.

        Args:
            function_name (function): The function to be parallelized.
            num_workers (int): Maximum number workers in parallelization.
            *args: All the arguments in order to pass into parameter function_name.

        Returns:
            list: A list of ordered dictionaries with epf damage values and other data/metadata.

        """

        output = []
        with concurrent.futures.ProcessPoolExecutor(max_workers=num_workers) as executor:
            for ret in executor.map(function_name, *args):
                output.extend(ret)

        return output

    def epf_damage_analysis_bulk_input(self, epfs, hazard_type, hazard_dataset_id,
                                       use_hazard_uncertainty, use_liquefaction, liq_geology_dataset_id):
        """Run analysis for multiple epfs.

        Args:
            epfs (list): Multiple epfs from input inventory set.
            hazard_type (str): A tyoe of hazard exposure (earthquake etc.).
            hazard_dataset_id (str): An id of the hazard exposure.
            use_hazard_uncertainty (bool):  Hazard uncertainty. True for using uncertainty when computing damage,
                False otherwise.
            use_liquefaction (bool): Liquefaction. True for using liquefaction information to modify the damage,
                False otherwise.
            liq_geology_dataset_id (str): geology_dataset_id (str): A dataset id for geology dataset for liquefaction.

        Returns:
            list: A list of ordered dictionaries with epf damage values and other data/metadata.

        """
        result = []

        fragility_key = self.get_parameter("fragility_key")
        mapping_id = self.get_parameter("mapping_id")

        fragility_sets = dict()
        fragility_sets[fragility_key] = self.fragilitysvc.match_inventory(mapping_id, epfs,
                                                                        fragility_key)

        liq_fragility_set = []
        if use_liquefaction and liq_geology_dataset_id is not None:
            liq_fragility_key = self.get_parameter("liquefaction_fragility_key")
            if liq_fragility_key is None:
                liq_fragility_key = self.DEFAULT_LIQ_FRAGILITY_KEY
            liq_fragility_set = self.fragilitysvc.match_inventory(mapping_id, epfs, liq_fragility_key)

        # TODO there is a chance the fragility key is pgd, we should either update our mappings or add support here
        liq_fragility = None

        for epf in epfs:
            fragility_set = dict()
            if epf["id"] in fragility_sets[fragility_key]:
                fragility_set = fragility_sets[fragility_key][epf["id"]]
                if liq_geology_dataset_id is not None and epf["id"] in liq_fragility_set:
                    liq_fragility = liq_fragility_set[epf["id"]]

            result.append(self.epf_damage_analysis(epf, fragility_set, liq_fragility, hazard_type, hazard_dataset_id,
                                                   liq_geology_dataset_id, use_hazard_uncertainty))

        return result

    def epf_damage_analysis(self, facility, fragility_set, liq_fragility, hazard_type, hazard_dataset_id,
                            liq_geology_dataset_id, use_hazard_uncertainty):
        """Calculates epf damage results for a single epf.

        Args:
            facility (obj): A JSON mapping of a geometric object from the inventory: current Electric Power facility.
            fragility_set (obj): A JSON description of fragility assigned to the epf.
            liq_fragility(obj): A JSON description of liquefaction fragility mapped to the facility.
            hazard_type (str): A type of hazard exposure (earthquake etc.).
            hazard_dataset_id (str): An id of the hazard exposure.
            liq_geology_dataset_id(str): Geology dataset id from data service to use for liquefaction calculation,
                if applicable
            use_hazard_uncertainty(bool): Whether to use hazard standard deviation values for uncertainty

        Returns:
            OrderedDict: A dictionary with epf damage values and other data/metadata.

        """
        demand_type = "Unknown"
        hazard_val = 0.0
        limit_states = {"ls-slight": 0.0, "ls-moderat": 0.0,
                        "ls-extensi": 0.0, "ls-complet": 0.0}

        if fragility_set is not None:
            location = GeoUtil.get_location(facility)
            demand_type = fragility_set['demandType']
            point = str(location.y) + "," + str(location.x)
            demand_units = fragility_set['demandUnits']

            liq_hazard_val = "NA"
            liquefaction_prob = "NA"
            liq_hazard_type = "NA"

            std_dev = 0.0
            if use_hazard_uncertainty:
                std_dev = random.random()

            if hazard_type == 'earthquake':
                hazard_resp = self.hazardsvc.get_earthquake_hazard_values(hazard_dataset_id, demand_type,
                                                                          demand_units,
                                                                          [point])
                hazard_val = hazard_resp[0]['hazardValue']
                limit_states = AnalysisUtil.calculate_limit_state(
                    fragility_set, hazard_val, std_dev=std_dev)

                # use ground liquefaction to modify damage interval
                if liq_fragility is not None and liq_geology_dataset_id:
                    liq_hazard_type = liq_fragility['demandType']
                    pgd_demand_units = liq_fragility['demandUnits']
                    point = str(location.y) + "," + str(location.x)
                    liquefaction = self.hazardsvc.get_liquefaction_values(hazard_dataset_id, liq_geology_dataset_id,
                                                                          pgd_demand_units, [point])
                    liq_hazard_val = liquefaction[0][liq_hazard_type]
                    liquefaction_prob = liquefaction[0]['liqProbability']
                    pgd_limit_states = AnalysisUtil.calculate_limit_state(
                        liq_fragility, liq_hazard_val, std_dev=std_dev)
                    limit_states = AnalysisUtil.adjust_limit_states_for_pgd(limit_states, pgd_limit_states)

            elif hazard_type == 'tornado':
                hazard_val = self.hazardsvc.get_tornado_hazard_value(hazard_dataset_id, demand_units, location.y,
                                                                     location.x, 0)
                limit_states = AnalysisUtil.calculate_limit_state(
                    fragility_set, hazard_val, std_dev=std_dev)

            elif hazard_type == 'hurricane':
                # TODO: implement hurricane
                raise ValueError('Hurricane hazard has not yet been implemented!')

            elif hazard_type == 'tsunami':
                demand_units = fragility_set["demandUnits"]
                point = str(location.y) + "," + str(location.x)
                hazard_val = self.hazardsvc.get_tsunami_hazard_values(hazard_dataset_id,
                                                                      demand_type,
                                                                      demand_units,
                                                                      [point])[0]["hazardValue"]
                # Sometimes the geotiffs give large negative values for out of bounds instead of 0
                if hazard_val <= 0.0:
                    hazard_val = 0.0
                limit_states = AnalysisUtil.calculate_limit_state(
                    fragility_set, hazard_val, std_dev=std_dev)

            else:
                raise ValueError("Missing hazard type.")

        dmg_interval = AnalysisUtil.calculate_damage_interval(limit_states)

        # Needs py 3.5+
        epf_results = {
            'guid': facility['properties']['guid'],
            'hazardtype': demand_type,
            'hazard_val': hazard_val,
            **limit_states,
            **dmg_interval,
            'liqhaztype': liq_hazard_type,
            'liqhazval': liq_hazard_val,
            'liqprobability': liquefaction_prob
        }
        return epf_results

    def get_spec(self):
        """Get specifications of the epf damage analysis.

        Returns:
            obj: A JSON object of specifications of the epf damage analysis.

        """
        return {
            'name': 'epf-damage',
            'description': 'Electric Power Facility damage analysis.',
            'input_parameters': [
                {
                    'id': 'result_name',
                    'required': True,
                    'description': 'A name of the resulting dataset',
                    'type': str
                },
                {
                    'id': 'mapping_id',
                    'required': True,
                    'description': 'Fragility mapping dataset applicable to the EPF.',
                    'type': str
                },
                {
                    'id': 'hazard_type',
                    'required': True,
                    'description': 'Hazard type (e.g. earthquake).',
                    'type': str
                },
                {
                    'id': 'hazard_id',
                    'required': True,
                    'description': 'Hazard ID which defines the particular hazard (e.g. New madrid earthquake '
                                   'using Atkinson Boore 1995).',
                    'type': str
                },
                {
                    'id': 'fragility_key',
                    'required': False,
                    'description': 'Fragility key to use in mapping dataset ()',
                    'type': str
                },
                {
                    'id': 'use_liquefaction',
                    'required': False,
                    'description': 'Use a ground liquifacition to modify damage interval.',
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
                    'id': 'use_hazard_uncertainty',
                    'required': False,
                    'description': 'Use hazard uncertainty',
                    'type': bool
                },
                {
                    'id': 'num_cpu',
                    'required': False,
                    'description': 'If using parallel execution, the number of cpus to request.',
                    'type': int
                },
            ],
            'input_datasets': [
                {
                    'id': 'epfs',
                    'required': True,
                    'description': 'Electric Power Facility Inventory',
                    'type': ['incore:epf', 'ergo:epf'],
                },

            ],
            'output_datasets': [
                {
                    'id': 'result',
                    'parent_type': 'epfs',
                    'type': 'incore:epfVer1'
                }
            ]
        }
