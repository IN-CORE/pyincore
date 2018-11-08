"""pyincore.analyses.epfdamage.epfdamage

Copyright (c) 2017 University of Illinois and others.  All rights reserved.
This program and the accompanying materials are made available under the
terms of the BSD-3-Clause which accompanies this distribution,
and is available at https://opensource.org/licenses/BSD-3-Clause

"""
import collections
import concurrent.futures
from pyincore import BaseAnalysis, HazardService, FragilityService
from pyincore import AnalysisUtil, GeoUtil
from pyincore.analyses.epfdamage.epfutil import EpfUtil
from itertools import repeat


class EpfDamage(BaseAnalysis):
    """Computes electric power facility structural damage for an earthquake hazard.

    Args:
        incore_client (incoreClient): Service authentication.

    """
    def __init__(self, incore_client):
        self.hazardsvc = HazardService(incore_client)
        self.fragilitysvc = FragilityService(incore_client)

        super(EpfDamage, self).__init__(incore_client)

    def run(self):
        """Executes electric power facility damage analysis."""
        epf_set = self.get_input_dataset("epfs").get_inventory_reader()

        dmg_ratio_csv = self.get_input_dataset("dmg_ratios").get_csv_reader()
        dmg_ratio_tbl = EpfUtil.get_damage_ratio_rows(dmg_ratio_csv)

        # Get Fragility key
        fragility_key = self.get_parameter("fragility_key")
        if fragility_key is None:
            fragility_key = EpfUtil.DEFAULT_FRAGILITY_KEY

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

        results = []
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
                                                       inventory_args, repeat(hazard_dataset_id), repeat(dmg_ratio_tbl),
                                                       repeat(fragility_key), repeat(use_hazard_uncertainty),
                                                       repeat(use_liquefaction))

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

    def epf_damage_analysis_bulk_input(self, epfs, hazard_dataset_id, dmg_ratio_tbl, fragility_key,
                                          use_hazard_uncertainty, use_liquefaction):
        """Run analysis for multiple epfs.

        Args:
            epfs (list): Multiple epfs from input inventory set.
            hazard_dataset_id (str): An id of the hazard exposure.
            dmg_ratio_tbl (obj): A damage ratio table, including weights to compute mean damage.
            fragility_key (str): Fragility key describing the type of fragility.
            use_hazard_uncertainty (bool):  Hazard uncertainty. True for using uncertainty when computing damage,
                False otherwise.
            use_liquefaction (bool): Liquefaction. True for using liquefaction information to modify the damage,
                False otherwise.

        Returns:
            list: A list of ordered dictionaries with epf damage values and other data/metadata.

        """
        result = []
        fragility_sets = self.fragilitysvc.map_fragilities(self.get_parameter("mapping_id"), epfs, fragility_key)
        for epf in epfs:
            fragility_set = None
            if epf["id"] in fragility_sets:
                fragility_set = fragility_sets[epf["id"]]

            result.append(self.epf_damage_analysis(epf, fragility_set, hazard_dataset_id, dmg_ratio_tbl,
                                                      fragility_key, use_hazard_uncertainty, use_liquefaction))

        return result

    def epf_damage_analysis(self, epf, fragility_set, hazard_dataset_id, dmg_ratio_tbl, fragility_key,
                               use_hazard_uncertainty, use_liquefaction):
        """Calculates epf damage results for a single epf.

        Args:
            epf (obj): A JSON mapping of a geometric object from the inventory: current epf.
            fragility_set (obj): A JSON description of fragility assigned to the epf.
            hazard_dataset_id (str): A hazard dataset to use.
            dmg_ratio_tbl (obj): A table of damage ratios for mean damage.
            fragility_key (str): A fragility key to use for mapping epfs to fragilities.
            use_hazard_uncertainty (bool):  Hazard uncertainty. True for using uncertainty in damage analysis,
                False otherwise.
            use_liquefaction (bool): Liquefaction. True for using liquefaction information to modify the damage,
                False otherwise.

        Returns:
            OrderedDict: A dictionary with epf damage values and other data/metadata.

        """
        epf_results = collections.OrderedDict()

        hazard_val = 0.0
        demand_type = "Unknown"
        exceedence_probability = [0.0, 0.0, 0.0, 0.0]
        dmg_intervals = [0.0, 0.0, 0.0, 0.0, 0.0]
        mean_damage = 0.0
        expected_damage = "Unknown"
        retrofit_type = "Non-Retrofit"
        retrofit_cost = 0.0

        if fragility_set is not None:
            location = GeoUtil.get_location(epf)
            demand_type = fragility_set['demandType']
            demand_units = fragility_set['demandUnits']
            # Start here, need to add the hazard dataset id to the analysis parameter list
            hazard_resp = self.hazardsvc.get_earthquake_hazard_values(hazard_dataset_id, demand_type, demand_units,
                                                                     [location.y, location.x])
            hazard_val = hazard_resp[0]['hazardValue']
            hazard_std_dev = 0.0

            # if use_hazard_uncertainty:
            # TODO this value needs to come from the hazard service
            # hazard_std_dev = ...

            exceedence_probability = EpfUtil.get_probability_of_exceedence(epf, fragility_set, hazard_val,
                                                                              hazard_std_dev, use_liquefaction)

            dmg_intervals = EpfUtil.get_damage_state_intervals(exceedence_probability)
            mean_damage = EpfUtil.get_mean_damage(dmg_intervals, 1, epf, dmg_ratio_tbl)
            expected_damage = EpfUtil.get_expected_damage(mean_damage, dmg_ratio_tbl)
            retrofit_cost = EpfUtil.get_retrofit_cost(fragility_key)
            retrofit_type = EpfUtil.get_retrofit_type(fragility_key)

        epf_results['guid'] = epf['properties']['guid']
        epf_results["ls-slight"] = exceedence_probability[0]
        epf_results["ls-moderat"] = exceedence_probability[1]
        epf_results["ls-extensi"] = exceedence_probability[2]
        epf_results["ls-complet"] = exceedence_probability[3]
        epf_results["none"] = dmg_intervals[0]
        epf_results["slight-mod"] = dmg_intervals[1]
        epf_results["mod-extens"] = dmg_intervals[2]
        epf_results["ext-comple"] = dmg_intervals[3]
        epf_results["complete"] = dmg_intervals[4]
        epf_results["meandamage"] = mean_damage
        epf_results["expectval"] = expected_damage
        epf_results["retrofit"] = retrofit_type
        epf_results["retro_cost"] = retrofit_cost
        epf_results["hazardtype"] = demand_type
        epf_results["hazardval"] = hazard_val

        return epf_results

    def get_spec(self):
        """Get specifications of the epf damage analysis.

        Returns:
            obj: A JSON object of specifications of the epf damage analysis.

        """
        return {
            'name': 'epf-damage',
            'description': 'electric power facility damage analysis',
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
                    'id': 'epfs',
                    'required': True,
                    'description': 'Electric Power Facility Inventory',
                    'type': ['ergo:epfs'],
                },
                {
                    'id': 'dmg_ratios',
                    'required': True,
                    'description': 'Electric Power Facility Damage Ratios',
                    'type': ['ergo:epfDamageRatios'],
                },

            ],
            'output_datasets': [
                {
                    'id': 'result',
                    'parent_type': 'epfs',
                    'type': 'epf-damage'
                }
            ]
        }
