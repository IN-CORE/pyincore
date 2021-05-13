# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import collections
import concurrent.futures

from pyincore import AnalysisUtil, GeoUtil
from pyincore import BaseAnalysis, HazardService, FragilityService
from pyincore.analyses.nonstructbuildingdamage.nonstructbuildingutil import \
    NonStructBuildingUtil


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
        building_results = []
        damage_results = []
        fragility_sets_as = self.fragilitysvc.match_inventory(self.get_input_dataset("dfr3_mapping_set"), buildings,
                                                              self.get_parameter("fragility_key_as"))
        fragility_sets_ds = self.fragilitysvc.match_inventory(self.get_input_dataset("dfr3_mapping_set"), buildings,
                                                              self.get_parameter("fragility_key_ds"))

        for building in buildings:
            fragility_set_as = None
            fragility_set_ds = None

            if building["id"] in fragility_sets_as and building["id"] in fragility_sets_ds:
                fragility_set_as = fragility_sets_as[building["id"]]
                fragility_set_ds = fragility_sets_ds[building["id"]]

            (building_result, damage_result) = self.building_damage_analysis(building,
                                                                             fragility_set_as,
                                                                             fragility_set_ds)
            building_results.append(building_result)
            damage_results.append(damage_result)

        return building_results, damage_results

    def building_damage_analysis(self, building, fragility_set_as, fragility_set_ds):
        """Calculates bridge damage results for a single building.

        Args:
            building (obj): A JSON-mapping of a geometric object from the inventory: current building.
            fragility_set_as (obj): A JSON description of acceleration-sensitive (AS) fragility
                assigned to the building.
            fragility_set_ds (obj): A JSON description of drift-sensitive (DS) fragility
                assigned to the building.

        Returns:
            dict: An ordered dictionary with building damage values.
            dict: An ordered dictionary with building data/metadata.

        """
        building_result = collections.OrderedDict()
        dmg_probability_as = collections.OrderedDict()
        dmg_probability_ds = collections.OrderedDict()
        damage_result = collections.OrderedDict()
        hazard_demand_type_as = None
        hazard_demand_type_ds = None
        hazard_val_as = 0.0
        hazard_val_ds = 0.0

        # read static parameters from object self
        hazard_dataset_id = self.get_parameter("hazard_id")
        liq_geology_dataset_id = self.get_parameter("liq_geology_dataset_id")
        use_liquefaction = self.get_parameter("use_liquefaction")
        use_hazard_uncertainty = self.get_parameter("use_hazard_uncertainty")

        # Acceleration-Sensitive Fragility ID Code
        if fragility_set_as is not None:
            fragility_id_as = fragility_set_as.id

            hazard_demand_type_as = AnalysisUtil.get_hazard_demand_type(building, fragility_set_as, 'earthquake')
            demand_unit_as = fragility_set_as.demand_units[0]
            location = GeoUtil.get_location(building)

            point = str(location.y) + "," + str(location.x)

            hazard_val_as = self.hazardsvc.get_earthquake_hazard_values(
                hazard_dataset_id, hazard_demand_type_as,
                demand_unit_as,
                points=[point])[0]['hazardValue']

            dmg_probability_as = fragility_set_as.calculate_limit_state(hazard_val_as)
            # adjust dmg probability for liquefaction
            if use_liquefaction:
                if liq_geology_dataset_id is not None:
                    liqufaction_dmg = self.hazardsvc.get_liquefaction_values(
                        hazard_dataset_id, liq_geology_dataset_id,
                        'in',
                        points=[point])[0][
                        'groundFailureProb']
                else:
                    raise ValueError('Hazard does not support liquefaction! \
                                     Check to make sure you defined the liquefaction\
                                     portion of your scenario earthquake.')
                dmg_probability_as = NonStructBuildingUtil.adjust_damage_for_liquefaction(dmg_probability_as,
                                                                                          liqufaction_dmg)

            # TODO this value needs to come from the hazard service
            # adjust dmg probability for hazard uncertainty
            if use_hazard_uncertainty:
                raise ValueError('Uncertainty has not yet been implemented!')
        else:
            dmg_probability_as['immocc'] = 0.0
            dmg_probability_as['lifesfty'] = 0.0
            dmg_probability_as['collprev'] = 0.0
            demand_unit_as = None
            fragility_id_as = None

        dmg_interval_as = AnalysisUtil.calculate_damage_interval(dmg_probability_as)

        # Drift-Sensitive Fragility ID Code
        if fragility_set_ds is not None:
            fragility_id_ds = fragility_set_ds.id

            hazard_demand_type_ds = AnalysisUtil.get_hazard_demand_type(building, fragility_set_ds, 'earthquake')
            demand_unit_ds = fragility_set_ds.demand_units[0]
            location = GeoUtil.get_location(building)

            point = str(location.y) + "," + str(location.x)

            hazard_val_ds = self.hazardsvc.get_earthquake_hazard_values(
                hazard_dataset_id, hazard_demand_type_ds,
                demand_unit_ds, points=[point])[0]['hazardValue']

            dmg_probability_ds = fragility_set_ds.calculate_limit_state(hazard_val_ds)

            # adjust hazard value for liquefaction
            if use_liquefaction:
                if liq_geology_dataset_id is not None:
                    liqufaction_dmg = self.hazardsvc.get_liquefaction_values(
                        hazard_dataset_id, liq_geology_dataset_id,
                        'in',
                        points=[point])[0][
                        'groundFailureProb']
                else:
                    raise ValueError('Hazard does not support liquefaction! \
                                                 Check to make sure you defined the liquefaction\
                                                 portion of your scenario earthquake.')
                dmg_probability_ds = NonStructBuildingUtil.adjust_damage_for_liquefaction(dmg_probability_ds,
                                                                                          liqufaction_dmg)

            # TODO this value needs to come from the hazard service
            # adjust dmg probability for hazard uncertainty
            if use_hazard_uncertainty:
                raise ValueError('Uncertainty has not yet been implemented!')
        else:
            dmg_probability_ds['immocc'] = 0.0
            dmg_probability_ds['lifesfty'] = 0.0
            dmg_probability_ds['collprev'] = 0.0
            demand_unit_ds = None
            fragility_id_ds = None


        dmg_interval_ds = AnalysisUtil.calculate_damage_interval(dmg_probability_ds)

        # put results in dictionary
        # AS denotes acceleration-sensitive fragility assigned to the building.
        # DS denotes drift-sensitive fragility assigned to the building.
        building_result['guid'] = building['properties']['guid']
        building_result['AS_LS_0'] = dmg_probability_as['immocc']
        building_result['AS_LS_1'] = dmg_probability_as['lifesfty']
        building_result['AS_LS_2'] = dmg_probability_as['collprev']
        building_result['AS_DS_0'] = dmg_interval_as['insignific']
        building_result['AS_DS_1'] = dmg_interval_as['moderate']
        building_result['AS_DS_2'] = dmg_interval_as['heavy']
        building_result['AS_DS_3'] = dmg_interval_as['complete']
        building_result['DS_LS_0'] = dmg_probability_ds['immocc']
        building_result['DS_LS_1'] = dmg_probability_ds['lifesfty']
        building_result['DS_LS_2'] = dmg_probability_ds['collprev']
        building_result['DS_DS_0'] = dmg_interval_ds['insignific']
        building_result['DS_DS_1'] = dmg_interval_ds['moderate']
        building_result['DS_DS_2'] = dmg_interval_ds['heavy']
        building_result['DS_DS_3'] = dmg_interval_ds['complete']

        # put damage results in dictionary
        damage_result['guid'] = building['properties']['guid']
        damage_result['fragility_id_ds'] = fragility_id_ds
        damage_result['demandtype_ds'] = hazard_demand_type_ds
        damage_result['demandunits_ds'] = demand_unit_ds
        damage_result['fragility_id_as'] = fragility_id_as
        damage_result['demandtype_as'] = hazard_demand_type_as
        damage_result['demandunits_as'] = demand_unit_as
        damage_result['hazardtype'] = self.get_parameter("hazard_type")
        damage_result['hazardval_ds'] = hazard_val_ds
        damage_result['hazardval_as'] = hazard_val_as

        return building_result, damage_result

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
                    'description': 'AS Fragility key to use in mapping dataset',
                    'type': str
                },
                {
                    'id': 'fragility_key_ds',
                    'required': False,
                    'description': 'DS Fragility key to use in mapping dataset',
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
                    'type': 'ergo:nsBuildingInventoryDamageVer2'
                },
                {
                    'id': 'damage_result',
                    'parent_type': 'buildings',
                    'description': 'Json file with information about applied hazard value and fragility',
                    'type': 'incore:nsBuildingInventoryDamageSupplement'
                }
            ]
        }
