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
    """Computes non-structural structural building damage for a hazard.

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

        results = []
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

        results = self.building_damage_concurrent_future(self.building_damage_analysis_bulk_input,
                                                         num_workers,
                                                         inventory_args)

        self.set_result_csv_data("result", results, name=self.get_parameter("result_name"))

        return True

    def building_damage_concurrent_future(self, function_name, num_workers, *args):
        """Utilizes concurrent.future module.

        Args:
            function_name (function): The function to be parallelized.
            num_workers (int): Maximum number workers in parallelization.
            *args: All the arguments in order to pass into parameter function_name.

        Returns:
            list: A list of ordered dictionaries with building damage values and other data/metadata.

        """
        output = []
        with concurrent.futures.ProcessPoolExecutor(max_workers=num_workers) as executor:
            for ret in executor.map(function_name, *args):
                output.extend(ret)

        return output

    def building_damage_analysis_bulk_input(self, buildings):
        """Run analysis for multiple buildings.

        Args:
            buildings (list): Multiple buildings from input inventory set.

        Returns:
            list: A list of ordered dictionaries with building damage values and other data/metadata.

        """
        result = []
        fragility_sets_as = self.fragilitysvc.match_inventory(self.get_parameter("mapping_id"),
                                                              buildings,
                                                              self.get_parameter("fragility_key_as"))
        fragility_sets_ds = self.fragilitysvc.match_inventory(self.get_parameter("mapping_id"),
                                                              buildings,
                                                              self.get_parameter("fragility_key_ds"))

        for building in buildings:
            fragility_set_as = None
            fragility_set_ds = None

            if building["id"] in fragility_sets_as \
                    and building["id"] in fragility_sets_ds:
                fragility_set_as = fragility_sets_as[building["id"]]
                fragility_set_ds = fragility_sets_ds[building["id"]]

            result.append(self.building_damage_analysis(building,
                                                        fragility_set_as,
                                                        fragility_set_ds))

        return result

    def building_damage_analysis(self, building, fragility_set_as, fragility_set_ds):
        """Calculates bridge damage results for a single building.

        Args:
            building (obj): A JSON-mapping of a geometric object from the inventory: current building.
            fragility_set_as (obj): A JSON description of acceleration-sensitive (AS) fragility
                assigned to the building.
            fragility_set_ds (obj): A JSON description of drift-sensitive (DS) fragility
                assigned to the building.

        Returns:
            OrderedDict: A dictionary with building damage values and other data/metadata.

        """
        building_results = collections.OrderedDict()
        dmg_probability_as = collections.OrderedDict()
        dmg_probability_ds = collections.OrderedDict()
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
            hazard_demand_type_as = NonStructBuildingUtil.get_hazard_demand_type(building,
                                                                     fragility_set_as,
                                                                     'earthquake')
            demand_units_as = fragility_set_as.demand_units
            location = GeoUtil.get_location(building)

            point = str(location.y) + "," + str(location.x)

            hazard_val_as = self.hazardsvc.get_earthquake_hazard_values(
                hazard_dataset_id, hazard_demand_type_as,
                demand_units_as,
                points=[point])[0]['hazardValue']

            dmg_probability_as = AnalysisUtil.calculate_limit_state(fragility_set_as,
                                                                 hazard_val_as)
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

        dmg_interval_as = AnalysisUtil.calculate_damage_interval(dmg_probability_as)

        # Drift-Sensitive Fragility ID Code
        if fragility_set_ds is not None:
            hazard_demand_type_ds = NonStructBuildingUtil.get_hazard_demand_type(building,
                                                                                 fragility_set_ds,
                                                                                 'earthquake')
            demand_units_ds = fragility_set_ds.demand_units
            location = GeoUtil.get_location(building)

            point = str(location.y) + "," + str(location.x)

            hazard_val_ds = self.hazardsvc.get_earthquake_hazard_values(
                hazard_dataset_id, hazard_demand_type_ds,
                demand_units_ds, points=[point])[0]['hazardValue']

            dmg_probability_ds = AnalysisUtil.calculate_limit_state(fragility_set_ds,
                                                                    hazard_val_ds)

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
                dmg_probability_ds = NonStructBuildingUtil.adjust_damage_for_liquefaction(
                    dmg_probability_ds,
                    liqufaction_dmg)

            # TODO this value needs to come from the hazard service
            # adjust dmg probability for hazard uncertainty
            if use_hazard_uncertainty:
                raise ValueError('Uncertainty has not yet been implemented!')
        else:
            dmg_probability_ds['immocc'] = 0.0
            dmg_probability_ds['lifesfty'] = 0.0
            dmg_probability_ds['collprev'] = 0.0

        dmg_interval_ds = AnalysisUtil.calculate_damage_interval(dmg_probability_ds)

        # put results in dictionary
        building_results['guid'] = building['properties']['guid']
        building_results['immocc_as'] = dmg_probability_as['immocc']
        building_results['lifsfty_as'] = dmg_probability_as['lifesfty']
        building_results['collpre_as'] = dmg_probability_as['collprev']
        building_results['insig_as'] = dmg_interval_as['insignific']
        building_results['mod_as'] = dmg_interval_as['moderate']
        building_results['heavy_as'] = dmg_interval_as['heavy']
        building_results['comp_as'] = dmg_interval_as['complete']
        building_results['immocc_ds'] = dmg_probability_ds['immocc']
        building_results['lifsfty_ds'] = dmg_probability_ds['lifesfty']
        building_results['collpre_ds'] = dmg_probability_ds['collprev']
        building_results['insig_ds'] = dmg_interval_ds['insignific']
        building_results['mod_ds'] = dmg_interval_ds['moderate']
        building_results['heavy_ds'] = dmg_interval_ds['heavy']
        building_results['comp_ds'] = dmg_interval_ds['complete']
        building_results["hzrdtyp_as"] = hazard_demand_type_as
        building_results["hzrdval_as"] = hazard_val_as
        building_results["hzrdtyp_ds"] = hazard_demand_type_ds
        building_results["hzrdval_ds"] = hazard_val_ds

        return building_results

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
                    'id': 'mapping_id',
                    'required': True,
                    'description': 'Fragility mapping dataset',
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
                }
            ],
            'output_datasets': [
                {
                    'id': 'result',
                    'parent_type': 'buildings',
                    'description': 'CSV file of building non-structural damage',
                    'type': 'ergo:nsBuildingInventoryDamage'
                }
            ]
        }
