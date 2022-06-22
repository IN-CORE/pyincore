# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import concurrent.futures
from itertools import repeat

from pyincore import AnalysisUtil, GeoUtil
from pyincore import BaseAnalysis, HazardService, FragilityService
from pyincore.models.dfr3curve import DFR3Curve


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

        if use_hazard_uncertainty:
            raise ValueError("Uncertainty is not implemented yet.")

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
                                                                         repeat(hazard_dataset_id))

        self.set_result_csv_data("result", ds_results, name=self.get_parameter("result_name"))
        self.set_result_json_data("metadata", damage_results,
                                  name=self.get_parameter("result_name") + "_additional_info")

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

    def epf_damage_analysis_bulk_input(self, epfs, hazard_type, hazard_dataset_id):
        """Run analysis for multiple epfs.

        Args:
            epfs (list): Multiple epfs from input inventory set.
            hazard_type (str): A type of hazard exposure (earthquake, tsunami, tornado, or hurricane).
            hazard_dataset_id (str): An id of the hazard exposure.

        Returns:
            list: A list of ordered dictionaries with epf damage values and other data/metadata.

        """

        use_liquefaction = False
        liquefaction_available = False

        fragility_key = self.get_parameter("fragility_key")

        fragility_set = self.fragilitysvc.match_inventory(self.get_input_dataset("dfr3_mapping_set"), epfs,
                                                          fragility_key)

        if hazard_type == "earthquake":
            liquefaction_fragility_key = self.get_parameter("liquefaction_fragility_key")
            if self.get_parameter("use_liquefaction") is True:
                if liquefaction_fragility_key is None:
                    liquefaction_fragility_key = self.DEFAULT_LIQ_FRAGILITY_KEY

                use_liquefaction = self.get_parameter("use_liquefaction")

                # Obtain the geology dataset
                geology_dataset_id = self.get_parameter("liquefaction_geology_dataset_id")

                if geology_dataset_id is not None:
                    fragility_sets_liq = self.fragilitysvc.match_inventory(
                        self.get_input_dataset("dfr3_mapping_set"), epfs, liquefaction_fragility_key)

                    if fragility_sets_liq is not None:
                        liquefaction_available = True

        values_payload = []
        values_payload_liq = []
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

                if liquefaction_available and epf["id"] in fragility_sets_liq:
                    fragility_set_liq = fragility_sets_liq[epf["id"]]
                    demands_liq = fragility_set_liq.demand_types
                    units_liq = fragility_set_liq.demand_units
                    value_liq = {
                        "demands": demands_liq,
                        "units": units_liq,
                        "loc": loc
                    }
                    values_payload_liq.append(value_liq)
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

        liquefaction_resp = None
        if liquefaction_available:
            liquefaction_resp = self.hazardsvc.post_liquefaction_values(hazard_dataset_id,
                                                                        geology_dataset_id,
                                                                        values_payload_liq)

        ds_results = []
        damage_results = []

        i = 0
        for epf in mapped_epfs:
            ds_result = dict()
            damage_result = dict()
            selected_fragility_set = fragility_set[epf["id"]]

            if isinstance(selected_fragility_set.fragility_curves[0], DFR3Curve):
                hazard_val = AnalysisUtil.update_precision_of_lists(hazard_vals[i]["hazardValues"])
                input_demand_types = hazard_vals[i]["demands"]
                input_demand_units = hazard_vals[i]["units"]

                hval_dict = dict()
                j = 0
                for d in selected_fragility_set.demand_types:
                    hval_dict[d] = hazard_val[j]
                    j += 1

                epf_args = selected_fragility_set.construct_expression_args_from_inventory(epf)
                limit_states = selected_fragility_set.calculate_limit_state(hval_dict,
                                                                            inventory_type='electric_facility',
                                                                            **epf_args)

                if liquefaction_resp is not None:
                    fragility_set_liq = fragility_sets_liq[epf["id"]]

                    if isinstance(fragility_set_liq.fragility_curves[0], DFR3Curve):
                        liq_hazard_vals = AnalysisUtil.update_precision_of_lists(liquefaction_resp[i]["pgdValues"])
                        liq_demand_types = liquefaction_resp[i]["demands"]
                        liq_demand_units = liquefaction_resp[i]["units"]
                        liquefaction_prob = liquefaction_resp[i]['liqProbability']

                        hval_dict_liq = dict()

                        for j, d in enumerate(fragility_set_liq.demand_types):
                            hval_dict_liq[d] = liq_hazard_vals[j]

                        facility_liq_args = fragility_set_liq.construct_expression_args_from_inventory(epf)
                        pgd_limit_states = \
                            fragility_set_liq.calculate_limit_state(
                                hval_dict_liq, inventory_type="electric_facility",
                                **facility_liq_args)
                    else:
                        raise ValueError("One of the fragilities is in deprecated format. "
                                         "This should not happen If you are seeing this please report the issue.")

                    limit_states = AnalysisUtil.adjust_limit_states_for_pgd(limit_states, pgd_limit_states)

                dmg_interval = selected_fragility_set.calculate_damage_interval(
                    limit_states, hazard_type=hazard_type, inventory_type='electric_facility')
            else:
                raise ValueError("One of the fragilities is in deprecated format. This should not happen. If you are "
                                 "seeing this please report the issue.")

            ds_result["guid"] = epf["properties"]["guid"]
            ds_result.update(limit_states)
            ds_result.update(dmg_interval)
            ds_result['haz_expose'] = AnalysisUtil.get_exposure_from_hazard_values(hazard_val, hazard_type)

            damage_result['guid'] = epf['properties']['guid']
            damage_result['fragility_id'] = selected_fragility_set.id
            damage_result["demandtypes"] = input_demand_types
            damage_result["demandunits"] = input_demand_units
            damage_result["hazardtype"] = hazard_type
            damage_result["hazardvals"] = hazard_val

            if hazard_type == "earthquake" and use_liquefaction is True:
                if liquefaction_available:
                    damage_result['liq_fragility_id'] = fragility_sets_liq[epf["id"]].id
                    damage_result['liqdemandtypes'] = liq_demand_types
                    damage_result['liqdemandunits'] = liq_demand_units
                    damage_result['liqhazval'] = liq_hazard_vals
                    damage_result['liqprobability'] = liquefaction_prob
                else:
                    damage_result['liq_fragility_id'] = None
                    damage_result['liqdemandtypes'] = None
                    damage_result['liqdemandunits'] = None
                    damage_result['liqhazval'] = None
                    damage_result['liqprobability'] = None

            ds_results.append(ds_result)
            damage_results.append(damage_result)

            i += 1

        #############################################################

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
            damage_result['hazardval'] = None
            if hazard_type == "earthquake" and use_liquefaction is True:
                damage_result['liq_fragility_id'] = None
                damage_result['liqdemandtypes'] = None
                damage_result['liqdemandunits'] = None
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
                    'id': 'liquefaction_fragility_key',
                    'required': False,
                    'description': 'Fragility key to use in liquefaction mapping dataset',
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
                    'type': 'incore:epfDamageVer3'
                },
                {
                    'id': 'metadata',
                    'parent_type': 'epfs',
                    'description': 'additional metadata in json file about applied hazard value and '
                                   'fragility',
                    'type': 'incore:epfDamageSupplement'
                }
            ]
        }
