# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import collections
import concurrent.futures
from itertools import repeat

from pyincore import AnalysisUtil, GeoUtil
from pyincore import BaseAnalysis, HazardService, FragilityService
from pyincore.models.fragilitycurverefactored import FragilityCurveRefactored


class EpfDamage(BaseAnalysis):
    """Computes electric power facility structural damage for an earthquake, tsunami, tornado, and hurricane hazards.

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

        (ds_results, damage_results) = self.epf_damage_concurrent_future(self.epf_damage_analysis_bulk_input,
                                                                         num_workers,
                                                                         inventory_args, repeat(hazard_type),
                                                                         repeat(hazard_dataset_id),
                                                                         repeat(use_hazard_uncertainty),
                                                                         repeat(use_liquefaction),
                                                                         repeat(liq_geology_dataset_id))

        self.set_result_csv_data("result", ds_results, name=self.get_parameter("result_name"))
        self.set_result_json_data("metadata", damage_results, name=self.get_parameter("result_name") +
                                                                   "_additional_info")

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

        output_ds = []
        output_dmg = []
        with concurrent.futures.ProcessPoolExecutor(max_workers=num_workers) as executor:
            for ret1, ret2 in executor.map(function_name, *args):
                output_ds.extend(ret1)
                output_dmg.extend(ret2)

        return output_ds, output_dmg

    def epf_damage_analysis_bulk_input(self, epfs, hazard_type, hazard_dataset_id,
                                       use_hazard_uncertainty, use_liquefaction, liq_geology_dataset_id):
        """Run analysis for multiple epfs.

        Args:
            epfs (list): Multiple epfs from input inventory set.
            hazard_type (str): A type of hazard exposure (earthquake, tsunami, tornado, or hurricane).
            hazard_dataset_id (str): An id of the hazard exposure.
            use_hazard_uncertainty (bool):  Hazard uncertainty. True for using uncertainty when computing damage,
                False otherwise.
            use_liquefaction (bool): Liquefaction. True for using liquefaction information to modify the damage,
                False otherwise.
            liq_geology_dataset_id (str): geology_dataset_id (str): A dataset id for geology dataset for liquefaction.

        Returns:
            list: A list of ordered dictionaries with epf damage values and other data/metadata.

        """
        fragility_key = self.get_parameter("fragility_key")

        fragility_set = self.fragilitysvc.match_inventory(self.get_input_dataset("dfr3_mapping_set"), epfs,
                                                          fragility_key)

        values_payload = []
        unmapped_epfs = []
        mapped_epfs = []
        for epf in epfs:
            epf_id = epf["id"]
            if epf_id in fragility_set:
                location = GeoUtil.get_location(epf)
                loc = str(location.y) + "," + str(location.x)
                demands = fragility_set[epf_id].demand_types
                units = fragility_set[epf_id].demand_units
                value = {
                    "demands": demands,
                    "units": units,
                    "loc": loc
                }
                values_payload.append(value)
                mapped_epfs.append(epf)
            else:
                unmapped_epfs.append(epf)

        if hazard_type == 'earthquake':
            hazard_vals = self.hazardsvc.post_earthquake_hazard_values(hazard_dataset_id, values_payload)
        elif hazard_type == 'tornado':
            hazard_vals = self.hazardsvc.post_tornado_hazard_values(hazard_dataset_id, values_payload)
        elif hazard_type == 'hurricane':
            # TODO: implement hurricane
            raise ValueError('Hurricane hazard has not yet been implemented!')
        elif hazard_type == 'tsunami':
            hazard_vals = self.hazardsvc.post_tsunami_hazard_values(hazard_dataset_id, values_payload)
        else:
            raise ValueError("Missing hazard type.")

        ds_results = []
        damage_results = []

        i = 0
        for epf in mapped_epfs:
            ds_result = dict()
            damage_result = dict()
            selected_fragility_set = fragility_set[epf["id"]]

            if isinstance(selected_fragility_set.fragility_curves[0], FragilityCurveRefactored):
                hazard_val = AnalysisUtil.update_precision_of_lists(hazard_vals[i]["hazardValues"])
                input_demand_types = hazard_vals[i]["demands"]
                input_demand_units = hazard_vals[i]["units"]

                hval_dict = dict()
                j = 0
                for d in hazard_vals[i]["demands"]:
                    hval_dict[d] = hazard_vals[i]["hazardValues"][j]
                    j += 1

                epf_args = selected_fragility_set.construct_expression_args_from_inventory(epf)
                limit_states = selected_fragility_set.calculate_limit_state_refactored(hval_dict, **epf_args)
            else:
                hazard_val = AnalysisUtil.update_precision(hazard_vals[i]["hazardValues"][0])
                # Sometimes the geotiffs give large negative values for out of bounds instead of 0
                if hazard_val <= 0.0:
                    hazard_val = 0.0

                std_dev = 0.0
                if use_hazard_uncertainty:
                    raise ValueError("Uncertainty Not Implemented!")

                input_demand_types = hazard_vals[i]["demands"][0]
                input_demand_units = hazard_vals[i]["units"][0]
                limit_states = selected_fragility_set.calculate_limit_state(hazard_val, std_dev=std_dev)

            dmg_interval = AnalysisUtil.calculate_damage_interval(limit_states)

            ds_result["guid"] = epf["properties"]["guid"]
            ds_result.update(limit_states)
            ds_result.update(dmg_interval)

            damage_result['guid'] = epf['properties']['guid']
            damage_result['fragility_id'] = selected_fragility_set.id
            damage_result["demandtypes"] = input_demand_types
            damage_result["demandunits"] = input_demand_units
            damage_result["hazardtype"] = hazard_type
            damage_result["hazardval"] = hazard_val

            ds_results.append(ds_result)
            damage_results.append(damage_result)

            i += 1

        #############################################################
        # when there is liquefaction, limit state need to be modified
        if hazard_type == 'earthquake' and use_liquefaction and liq_geology_dataset_id is not None:
            liq_fragility_key = self.get_parameter("liquefaction_fragility_key")
            if liq_fragility_key is None:
                liq_fragility_key = self.DEFAULT_LIQ_FRAGILITY_KEY
            liq_fragility_set = self.fragilitysvc.match_inventory(self.get_input_dataset("dfr3_mapping_set"),
                                                                  epfs, liq_fragility_key)

            liq_values_payload = []
            for epf in epfs:
                epf_id = epf["id"]
                if epf_id in liq_fragility_set:
                    location = GeoUtil.get_location(epf)
                    liq_loc = str(location.y) + "," + str(location.x)
                    liq_demands = liq_fragility_set[epf_id].demand_types
                    liq_units = liq_fragility_set[epf_id].demand_units
                    value = {
                        "demands": liq_demands,
                        "units": liq_units,
                        "loc": liq_loc
                    }
                    liq_values_payload.append(value)

            liquefaction_vals = self.hazardsvc.post_liquefaction_values(hazard_dataset_id,
                                                                        geology_dataset_id=liq_geology_dataset_id,
                                                                        payload=liq_values_payload)

            i = 0
            for liq_epf in epfs:
                liq_epf_id = liq_epf["id"]
                liq_input_demand_types = liquefaction_vals[i]["demands"][0]
                liq_hazard_val = AnalysisUtil.update_precision(liquefaction_vals[i][liq_input_demand_types][0])
                std_dev = 0.0
                if use_hazard_uncertainty:
                    raise ValueError("Uncertainty Not Implemented!")

                liquefaction_prob = liquefaction_vals[i]['liqProbability']

                selected_liq_fragility = liq_fragility_set[liq_epf_id]
                pgd_limit_states = selected_liq_fragility.calculate_limit_state(liq_hazard_val, std_dev=std_dev)

                # match id and add liqhaztype, liqhazval, liqprobability field as well as rewrite limit
                # states and dmg_interval
                for ds_result in ds_results:
                    if ds_result['guid'] == liq_epf["properties"]['guid']:
                        if ['ls-slight', 'ls-moderat', 'ls-extensi', 'ls-complet'] in ds_result.keys():
                            limit_states = {"ls-slight": ds_result['ls-slight'],
                                            "ls-moderat": ds_result['ls-moderat'],
                                            "ls-extensi": ds_result['ls-extensi'],
                                            "ls-complet": ds_result['ls-complet']}
                        elif ['LS_0', 'LS_1', 'LS_2'] in ds_result.keys():
                            limit_states = {
                                "LS_0": ds_result["DS_0"],
                                "LS_1": ds_result["DS_1"],
                                "LS_2": ds_result["DS_2"]
                            }
                        else:
                            raise ValueError("Do not support the limit state name")

                        liq_limit_states = AnalysisUtil.adjust_limit_states_for_pgd(limit_states, pgd_limit_states)
                        liq_dmg_interval = AnalysisUtil.calculate_damage_interval(liq_limit_states)

                        ds_result.update(liq_limit_states)
                        ds_result.update(liq_dmg_interval)

                for damage_result in damage_results:
                    if damage_result['guid'] == liq_epf["properties"]['guid']:
                        damage_result['liqhaztype'] = liq_input_demand_types
                        damage_result['liqhazval'] = liq_hazard_val
                        damage_result['liqprobability'] = liquefaction_prob

                i = i + 1

        # unmapped
        for epf in unmapped_epfs:
            ds_result = dict()
            damage_result = dict()
            ds_result['guid'] = epf['properties']['guid']
            damage_result['guid'] = epf['properties']['guid']
            damage_result['fragility_id'] = None
            damage_result["demandtypes"] = None
            damage_result['demandunits'] = None
            damage_result["hazardtype"] = None
            damage_result['hazardval'] = 0.0
            damage_result['liqhaztype'] = None
            damage_result['liqhazval'] = None
            damage_result['liqprobability'] = None

            ds_results.append(ds_result)
            damage_results.append(damage_result)

        return ds_results, damage_results

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
                    'parent_type': 'epfs',
                    'type': 'incore:epfDamageVer2'
                },
                {
                    'id': 'metadata',
                    'parent_type': 'epfs',
                    'description': 'additional metadata in json file about applied hazard value and '
                                   'fragility',
                    'type': 'incore:epfDamageMetadata'
                }
            ]
        }
