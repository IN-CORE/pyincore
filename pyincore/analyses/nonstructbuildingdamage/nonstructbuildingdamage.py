# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import concurrent.futures

from pyincore import AnalysisUtil, GeoUtil
from pyincore import BaseAnalysis, HazardService, FragilityService
from pyincore.analyses.nonstructbuildingdamage.nonstructbuildingutil import \
    NonStructBuildingUtil
from pyincore.models.dfr3curve import DFR3Curve


class NonStructBuildingDamage(BaseAnalysis):
    """Computes non-structural structural building damage for an earthquake hazard.

    Args:
        incore_client (IncoreClient): Service authentication.

    """

    def __init__(self, incore_client):
        self.hazardsvc = HazardService(incore_client)
        self.fragilitysvc = FragilityService(incore_client)

        super(NonStructBuildingDamage, self).__init__(incore_client)

    def run(self):
        """Executes building damage analysis."""
        # Building dataset
        building_set = self.get_input_dataset("buildings").get_inventory_reader()

        # set Default Fragility key
        fragility_key_as = self.get_parameter("fragility_key_as")
        if fragility_key_as is None:
            self.set_parameter("fragility_key_as", NonStructBuildingUtil.DEFAULT_FRAGILITY_KEY_AS)

        fragility_key_ds = self.get_parameter("fragility_key_ds")
        if fragility_key_ds is None:
            self.set_parameter("fragility_key_ds", NonStructBuildingUtil.DEFAULT_FRAGILITY_KEY_DS)

        # Set Default Hazard Uncertainty
        use_hazard_uncertainty = self.get_parameter("use_hazard_uncertainty")
        if use_hazard_uncertainty is None:
            self.set_parameter("use_hazard_uncertainty", False)

        # Set Default Liquefaction
        use_liquefaction = self.get_parameter("use_liquefaction")
        if use_liquefaction is None:
            self.set_parameter("use_liquefaction", False)

        user_defined_cpu = 1

        if not self.get_parameter("num_cpu") is None and self.get_parameter("num_cpu") > 0:
            user_defined_cpu = self.get_parameter("num_cpu")

        num_workers = AnalysisUtil.determine_parallelism_locally(self, len(building_set), user_defined_cpu)

        avg_bulk_input_size = int(len(building_set) / num_workers)
        inventory_args = []
        count = 0
        inventory_list = list(building_set)

        while count < len(inventory_list):
            inventory_args.append(inventory_list[count:count + avg_bulk_input_size])
            count += avg_bulk_input_size

        (ds_results, damage_results) = self.building_damage_concurrent_future(self.building_damage_analysis_bulk_input,
                                                                              num_workers,
                                                                              inventory_args)

        self.set_result_csv_data("result", ds_results, name=self.get_parameter("result_name"))
        self.set_result_json_data("damage_result",
                                  damage_results,
                                  name=self.get_parameter("result_name") + "_additional_info")
        return True

    def building_damage_concurrent_future(self, function_name, num_workers, *args):
        """Utilizes concurrent.future module.

        Args:
            function_name (function): The function to be parallelized.
            num_workers (int): Maximum number workers in parallelization.
            *args: All the arguments in order to pass into parameter function_name.

        Returns:
            dict: An ordered dictionary with building damage values.
            dict: An ordered dictionary with building data/metadata.

        """
        output_ds = []
        output_dmg = []
        with concurrent.futures.ProcessPoolExecutor(max_workers=num_workers) as executor:
            for ret1, ret2 in executor.map(function_name, *args):
                output_ds.extend(ret1)
                output_dmg.extend(ret2)

        return output_ds, output_dmg

    def building_damage_analysis_bulk_input(self, buildings):
        """Run analysis for multiple buildings.

        Args:
            buildings (list): Multiple buildings from input inventory set.

        Returns:
            dict: An ordered dictionary with building damage values.
            dict: An ordered dictionary with building data/metadata.

        """
        # read static parameters from object self
        hazard_type = self.get_parameter("hazard_type")
        hazard_dataset_id = self.get_parameter("hazard_id")
        liq_geology_dataset_id = self.get_parameter("liq_geology_dataset_id")
        use_liquefaction = self.get_parameter("use_liquefaction")
        use_hazard_uncertainty = self.get_parameter("use_hazard_uncertainty")

        building_results = []
        damage_results = []
        fragility_sets_as = self.fragilitysvc.match_inventory(self.get_input_dataset("dfr3_mapping_set"), buildings,
                                                              self.get_parameter("fragility_key_as"))
        fragility_sets_ds = self.fragilitysvc.match_inventory(self.get_input_dataset("dfr3_mapping_set"), buildings,
                                                              self.get_parameter("fragility_key_ds"))
        values_payload_as = []
        values_payload_ds = []
        values_payload_liq = []
        mapped_buildings = []
        unmapped_buildings = []
        for building in buildings:
            if building["id"] in fragility_sets_as and building["id"] in fragility_sets_ds:
                fragility_set_as = fragility_sets_as[building["id"]]
                fragility_set_ds = fragility_sets_ds[building["id"]]
                location = GeoUtil.get_location(building)
                loc = str(location.y) + "," + str(location.x)

                # Acceleration-Sensitive
                demands_as = AnalysisUtil.get_hazard_demand_types(building, fragility_set_as, hazard_type)
                units_as = fragility_set_as.demand_units
                value_as = {
                    "demands": demands_as,
                    "units": units_as,
                    "loc": loc
                }
                values_payload_as.append(value_as)

                # Drift-Sensitive
                demands_ds = AnalysisUtil.get_hazard_demand_types(building, fragility_set_ds, hazard_type)
                units_ds = fragility_set_ds.demand_units
                value_ds = {
                    "demands": demands_ds,
                    "units": units_ds,
                    "loc": loc
                }
                values_payload_ds.append(value_ds)

                # liquefaction
                if use_liquefaction:
                    value_liq = {
                        "demands": ["pgd"],  # implied...
                        "units": ["in"],
                        "loc": loc
                    }
                    values_payload_liq.append(value_liq)

                mapped_buildings.append(building)
            else:
                unmapped_buildings.append(building)

        del buildings

        # get hazard values and liquefaction
        if hazard_type == 'earthquake':
            hazard_resp_as = self.hazardsvc.post_earthquake_hazard_values(hazard_dataset_id, values_payload_as)
            hazard_resp_ds = self.hazardsvc.post_earthquake_hazard_values(hazard_dataset_id, values_payload_ds)

            # adjust dmg probability for liquefaction
            if use_liquefaction:
                if liq_geology_dataset_id is not None:
                    liquefaction_resp = self.hazardsvc.post_liquefaction_values(hazard_dataset_id,
                                                                                liq_geology_dataset_id,
                                                                                values_payload_liq)
                else:
                    raise ValueError('Hazard does not support liquefaction! Check to make sure you defined the '
                                     'liquefaction portion of your scenario earthquake.')
        else:
            raise ValueError("The provided hazard type is not supported yet by this analysis")

        # calculate LS and DS
        for i, building in enumerate(mapped_buildings):
            dmg_probability_as = {"LS_0": None, "LS_1": None, "LS_2": None}
            dmg_interval_as = {"DS_0": None, "DS_1": None, "DS_2": None, "DS_3": None}
            dmg_probability_ds = {"LS_0": None, "LS_1": None, "LS_2": None}
            dmg_interval_ds = {"DS_0": None, "DS_1": None, "DS_2": None, "DS_3": None}
            fragility_set_as = fragility_sets_as[building["id"]]
            fragility_set_ds = fragility_sets_ds[building["id"]]

            # TODO this value needs to come from the hazard service
            # adjust dmg probability for hazard uncertainty
            if use_hazard_uncertainty:
                raise ValueError('Uncertainty has not yet been implemented!')

            ###############
            # AS
            if isinstance(fragility_set_as.fragility_curves[0], DFR3Curve):
                hazard_vals_as = AnalysisUtil.update_precision_of_lists(hazard_resp_as[i]["hazardValues"])
                demand_types_as = hazard_resp_as[i]["demands"]
                demand_units_as = hazard_resp_as[i]["units"]
                hval_dict_as = dict()
                for j, d in enumerate(fragility_set_as.demand_types):
                    hval_dict_as[d] = hazard_vals_as[j]
                if not AnalysisUtil.do_hazard_values_have_errors(hazard_resp_as[i]["hazardValues"]):
                    building_args = fragility_set_as.construct_expression_args_from_inventory(building)
                    dmg_probability_as = fragility_set_as. \
                        calculate_limit_state(hval_dict_as, inventory_type="building",
                                              **building_args)
                    # adjust dmg probability for liquefaction
                    if use_liquefaction:
                        if liq_geology_dataset_id is not None:
                            liquefaction_dmg = AnalysisUtil.update_precision_of_lists(liquefaction_resp[i][
                                                                                          "groundFailureProb"])
                            dmg_probability_as = AnalysisUtil.update_precision_of_dicts(
                                NonStructBuildingUtil.adjust_damage_for_liquefaction(dmg_probability_as,
                                                                                     liquefaction_dmg))
                    dmg_interval_as = fragility_set_ds.calculate_damage_interval(dmg_probability_as,
                                                                                 hazard_type=hazard_type,
                                                                                 inventory_type="building")
            else:
                raise ValueError("One of the fragilities is in deprecated format. This should not happen. If you are "
                                 "seeing this please report the issue.")

            ###############
            # DS
            if isinstance(fragility_set_ds.fragility_curves[0], DFR3Curve):
                hazard_vals_ds = AnalysisUtil.update_precision_of_lists(hazard_resp_ds[i]["hazardValues"])
                demand_types_ds = hazard_resp_ds[i]["demands"]
                demand_units_ds = hazard_resp_ds[i]["units"]
                hval_dict_ds = dict()
                for j, d in enumerate(fragility_set_ds.demand_types):
                    hval_dict_ds[d] = hazard_vals_ds[j]

                if not AnalysisUtil.do_hazard_values_have_errors(hazard_resp_ds[i]["hazardValues"]):
                    building_args = fragility_set_ds.construct_expression_args_from_inventory(building)
                    dmg_probability_ds = fragility_set_ds. \
                        calculate_limit_state(hval_dict_ds, inventory_type="building",
                                              **building_args)
                    # adjust dmg probability for liquefaction
                    if use_liquefaction:
                        if liq_geology_dataset_id is not None:
                            liquefaction_dmg = AnalysisUtil.update_precision_of_lists(
                                liquefaction_resp[i]["groundFailureProb"])
                            dmg_probability_ds = AnalysisUtil.update_precision_of_dicts(
                                NonStructBuildingUtil.adjust_damage_for_liquefaction(dmg_probability_ds,
                                                                                     liquefaction_dmg))
                    dmg_interval_ds = fragility_set_ds.calculate_damage_interval(dmg_probability_ds,
                                                                                 hazard_type=hazard_type,
                                                                                 inventory_type="building")
            else:
                raise ValueError("One of the fragilities is in deprecated format. This should not happen. If you are "
                                 "seeing this please report the issue.")

            # put results in dictionary
            # AS denotes acceleration-sensitive fragility assigned to the building.
            # DS denotes drift-sensitive fragility assigned to the building.
            building_result = dict()
            building_result['guid'] = building['properties']['guid']
            building_result['AS_LS_0'] = dmg_probability_as['LS_0']
            building_result['AS_LS_1'] = dmg_probability_as['LS_1']
            building_result['AS_LS_2'] = dmg_probability_as['LS_2']
            building_result['AS_DS_0'] = dmg_interval_as['DS_0']
            building_result['AS_DS_1'] = dmg_interval_as['DS_1']
            building_result['AS_DS_2'] = dmg_interval_as['DS_2']
            building_result['AS_DS_3'] = dmg_interval_as['DS_3']
            building_result['DS_LS_0'] = dmg_probability_ds['LS_0']
            building_result['DS_LS_1'] = dmg_probability_ds['LS_1']
            building_result['DS_LS_2'] = dmg_probability_ds['LS_2']
            building_result['DS_DS_0'] = dmg_interval_ds['DS_0']
            building_result['DS_DS_1'] = dmg_interval_ds['DS_1']
            building_result['DS_DS_2'] = dmg_interval_ds['DS_2']
            building_result['DS_DS_3'] = dmg_interval_ds['DS_3']
            building_result['hazard_exposure_as'] = AnalysisUtil.get_exposure_from_hazard_values(hazard_vals_as,
                                                                                                 hazard_type)
            building_result['hazard_exposure_ds'] = AnalysisUtil.get_exposure_from_hazard_values(hazard_vals_ds,
                                                                                                 hazard_type)

            # put damage results in dictionary
            damage_result = dict()
            damage_result['guid'] = building['properties']['guid']
            damage_result['fragility_id_as'] = fragility_set_as.id
            damage_result['demandtypes_as'] = demand_types_as
            damage_result['demandunits_as'] = demand_units_as
            damage_result['fragility_id_ds'] = fragility_set_ds.id
            damage_result['demandtypes_ds'] = demand_types_ds
            damage_result['demandunits_ds'] = demand_units_ds
            damage_result['hazardtype'] = hazard_type
            damage_result['hazardvals_as'] = hazard_vals_as
            damage_result['hazardvals_ds'] = hazard_vals_ds

            building_results.append(building_result)
            damage_results.append(damage_result)

        for building in unmapped_buildings:
            building_result = dict()
            building_result['guid'] = building['properties']['guid']

            damage_result = dict()
            damage_result['guid'] = building['properties']['guid']
            damage_result['fragility_id_as'] = None
            damage_result['demandtypes_as'] = None
            damage_result['demandunits_as'] = None
            damage_result['fragility_id_ds'] = None
            damage_result['demandtypes_ds'] = None
            damage_result['demandunits_ds'] = None
            damage_result['hazardtype'] = None
            damage_result['hazardvals_as'] = None
            damage_result['hazardvals_ds'] = None

            building_results.append(building_result)
            damage_results.append(damage_result)

        return building_results, damage_results

    def get_spec(self):
        """Get specifications of the building damage analysis.

        Returns:
            obj: A JSON object of specifications of the building damage analysis.

        """
        return {
            'name': 'building-damage',
            'description': 'building damage analysis',
            'input_parameters': [
                {
                    'id': 'result_name',
                    'required': True,
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
                    'id': 'fragility_key_as',
                    'required': False,
                    'description': 'Acceleration-Sensitive Fragility key to use in mapping dataset',
                    'type': str
                },
                {
                    'id': 'fragility_key_ds',
                    'required': False,
                    'description': 'Drift-Sensitive Fragility key to use in mapping dataset',
                    'type': str
                },
                {
                    'id': 'use_liquefaction',
                    'required': False,
                    'description': 'Use liquefaction',
                    'type': bool
                },
                {
                    'id': 'liq_geology_dataset_id',
                    'required': False,
                    'description': 'liquefaction geology dataset id, \
                        if use liquefaction, you have to provide this id',
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
                    'id': 'buildings',
                    'required': True,
                    'description': 'building Inventory',
                    'type': ['ergo:buildingInventoryVer4'],
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
                    'parent_type': 'buildings',
                    'description': 'CSV file of damage states for building non-structural damage',
                    'type': 'ergo:nsBuildingInventoryDamageVer3'
                },
                {
                    'id': 'damage_result',
                    'parent_type': 'buildings',
                    'description': 'Json file with information about applied hazard value and fragility',
                    'type': 'incore:nsBuildingInventoryDamageSupplement'
                }
            ]
        }
