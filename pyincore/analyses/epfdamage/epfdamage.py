# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import collections
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

        fragility_set = dict()
        fragility_set = self.fragilitysvc.match_inventory(mapping_id, epfs, fragility_key)
        epf_results = []

        # Converting list of epfs into a dictionary for ease of reference
        list_epfs = epfs
        epfs = dict()
        for epf in list_epfs:
            epfs[epf["id"]] = epf
        list_epfs = None  # Clear as it's not needed anymore

        processed_epf = []
        grouped_epfs = AnalysisUtil.group_by_demand_type(epfs, fragility_set)
        for demand, grouped_epf_items in grouped_epfs.items():
            input_demand_type = demand[0]
            input_demand_units = demand[1]

            # For every group of unique demand and demand unit, call the end-point once
            epf_chunks = list(AnalysisUtil.chunks(grouped_epf_items, 50))
            for epf_chunk in epf_chunks:
                points = []
                for epf_id in epf_chunk:
                    location = GeoUtil.get_location(epfs[epf_id])
                    points.append(str(location.y) + "," + str(location.x))

                if hazard_type == 'earthquake':
                    hazard_vals = self.hazardsvc.get_earthquake_hazard_values(hazard_dataset_id, input_demand_type,
                                                                              input_demand_units,
                                                                              points)
                elif hazard_type == 'tornado':
                    hazard_vals = self.hazardsvc.get_tornado_hazard_values(hazard_dataset_id, input_demand_units,
                                                                          points)
                elif hazard_type == 'hurricane':
                    # TODO: implement hurricane
                    raise ValueError('Hurricane hazard has not yet been implemented!')

                elif hazard_type == 'tsunami':
                    hazard_vals = self.hazardsvc.get_tsunami_hazard_values(hazard_dataset_id,
                                                                          input_demand_type,
                                                                          input_demand_units,
                                                                          points)
                else:
                    raise ValueError("Missing hazard type.")

                # Parse the batch hazard value results and map them back to the building and fragility.
                # This is a potential pitfall as we are relying on the order of the returned results
                i = 0
                for epf_id in epf_chunk:
                    epf_result = collections.OrderedDict()
                    epf = epfs[epf_id]
                    hazard_val = hazard_vals[i]['hazardValue']

                    std_dev = 0.0
                    if use_hazard_uncertainty:
                        std_dev = random.random()

                    selected_fragility_set = fragility_set[epf_id]
                    limit_states = AnalysisUtil.calculate_limit_state(selected_fragility_set, hazard_val, std_dev=std_dev)
                    dmg_interval = AnalysisUtil.calculate_damage_interval(limit_states)

                    epf_result['guid'] = epf['properties']['guid']
                    epf_result.update(limit_states)
                    epf_result.update(dmg_interval)
                    epf_result['demandtype'] = input_demand_type
                    epf_result['demandunits'] = input_demand_units
                    epf_result['hazardtype'] = hazard_type
                    epf_result['hazardval'] = hazard_val

                    epf_results.append(epf_result)
                    processed_epf.append(epf_id)
                    i = i + 1

        # when there is liquefaction, limit state need to be modified
        if hazard_type == 'earthquake' and use_liquefaction and liq_geology_dataset_id is not None:
            liq_fragility_key = self.get_parameter("liquefaction_fragility_key")
            if liq_fragility_key is None:
                liq_fragility_key = self.DEFAULT_LIQ_FRAGILITY_KEY
            liq_fragility_set = self.fragilitysvc.match_inventory(mapping_id, epfs, liq_fragility_key)
            grouped_liq_epfs = AnalysisUtil.group_by_demand_type(epfs, liq_fragility_set)

            for liq_demand, grouped_liq_epf_items in grouped_liq_epfs.items():
                liq_input_demand_type = liq_demand[0]
                liq_input_demand_units = liq_demand[1]

                # For every group of unique demand and demand unit, call the end-point once
                liq_epf_chunks = list(AnalysisUtil.chunks(grouped_liq_epf_items, 50))
                for liq_epf_chunk in liq_epf_chunks:
                    points = []
                    for liq_epf_id in liq_epf_chunk:
                        location = GeoUtil.get_location(epfs[liq_epf_id])
                        points.append(str(location.y) + "," + str(location.x))
                    liquefaction_vals = self.hazardsvc.get_liquefaction_values(hazard_dataset_id,
                                                                          liq_geology_dataset_id,
                                                                          liq_input_demand_units, points)

                    # Parse the batch hazard value results and map them back to the building and fragility.
                    # This is a potential pitfall as we are relying on the order of the returned results
                    i = 0
                    for liq_epf_id in liq_epf_chunk:
                        liq_hazard_val = liquefaction_vals[i][liq_input_demand_type]

                        std_dev = 0.0
                        if use_hazard_uncertainty:
                            std_dev = random.random()

                        liquefaction_prob = liquefaction_vals[i]['liqProbability']

                        selected_liq_fragility = liq_fragility_set[liq_epf_id]
                        pgd_limit_states = AnalysisUtil.calculate_limit_state(selected_liq_fragility, liq_hazard_val, std_dev=std_dev)

                        # match id and add liqhaztype, liqhazval, liqprobability field as well as rewrite limit
                        # statess and dmg_interval
                        for epf_result in epf_results:
                            if epf_result['guid'] == epfs[liq_epf_id]['guid']:
                                limit_states = None # todo retreive that limit state from epf result record
                                liq_limit_states = AnalysisUtil.adjust_limit_states_for_pgd(limit_states,
                                                                                         pgd_limit_states)
                                liq_dmg_interval = AnalysisUtil.calculate_damage_interval(liq_limit_states)
                                epf_result.update(liq_limit_states)
                                epf_result.update(liq_dmg_interval)
                                epf_result['liqhaztype'] = liq_input_demand_type
                                epf_result['liqhazval'] = liq_hazard_val
                                epf_result['liqprobability'] = liquefaction_prob
                        i = i + 1

        unmapped_limit_states = {"ls-slight": 0.0, "ls-moderat": 0.0, "ls-extensi": 0.0, "ls-complet": 0.0}
        unmapped_dmg_intervals = AnalysisUtil.calculate_damage_interval(unmapped_limit_states)
        for epf_id, epf in epfs.items():
            if epf_id not in processed_epf:
                unmapped_epf_result = collections.OrderedDict()
                unmapped_epf_result['guid'] = epf['properties']['guid']
                unmapped_epf_result.update(unmapped_limit_states)
                unmapped_epf_result.update(unmapped_dmg_intervals)
                unmapped_epf_result["demandtype"] = "None"
                unmapped_epf_result['demandunits'] = "None"
                unmapped_epf_result["hazardtype"] = "None"
                unmapped_epf_result['hazardval'] = 0.0
                unmapped_epf_result['liqhaztype'] = "NA"
                unmapped_epf_result['liqhazval'] = "NA"
                unmapped_epf_result['liqprobability'] = "NA"
                epf_results.append(unmapped_epf_result)

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
