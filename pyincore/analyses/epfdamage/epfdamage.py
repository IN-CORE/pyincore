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
import traceback


class EpfDamage(BaseAnalysis):
    """Computes electric power facility structural damage for an earthquake hazard.

    Args:
        incore_client (IncoreClient): Service authentication.

    """
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
                                                    inventory_args, repeat(hazard_type), repeat(hazard_dataset_id),
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

    def epf_damage_analysis_bulk_input(self, epfs, hazard_type, hazard_dataset_id, fragility_key,
                                       use_hazard_uncertainty, use_liquefaction):
        """Run analysis for multiple epfs.

        Args:
            epfs (list): Multiple epfs from input inventory set.
            hazard_type (str): A tyoe of hazard exposure (earthquake etc.).
            hazard_dataset_id (str): An id of the hazard exposure.
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

        #fragility_sets = self.fragilitysvc.map_fragilities(mapping_id, epfs, "Non-Retrofit Fragility ID Code")

        # TODO there is a chance the fragility key is pgd, we should either update our mappings or add support here
        # fragility_sets_liq = self.fragilitysvc.map_fragilities(mapping_id, epfs, "Liquefaction-Fragility-Key")
        #for epf in epfs:
        #    if epf["id"] in fragility_sets.keys():
        #        liq_fragility_set = None
                # Check if mapping contains liquefaction fragility
        #        if epf_dataset_id is not None and epf["id"] in fragility_sets_liq:
        #            liq_fragility_set = fragility_sets_liq[epf["id"]]
        #
        #        result.append(self.epf_damage_analysis(epf, fragility_sets[epf["id"]], liq_fragility_set,
        #                                               hazardsvc, hazard_dataset_id, epf_dataset_id))

        for epf in epfs:
            fragility_set = None
            if epf["id"] in fragility_sets:
                fragility_set = fragility_sets[epf["id"]]

            result.append(self.epf_damage_analysis(epf, fragility_set, hazard_type, hazard_dataset_id,
                                                   fragility_key, use_hazard_uncertainty, use_liquefaction))

        return result

    def epf_damage_analysis(self, facility, fragility_set, hazard_type, hazard_dataset_id, fragility_key,
                            use_hazard_uncertainty, use_liquefaction):
        """Calculates epf damage results for a single epf.

        Args:
            facility (obj): A JSON mapping of a geometric object from the inventory: current Electric Power facility.
            fragility_set (obj): A JSON description of fragility assigned to the epf.
            hazard_type (str): A tyoe of hazard exposure (earthquake etc.).
            hazard_dataset_id (str): An id of the hazard exposure.
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
        dmg_probability = [0.0, 0.0, 0.0, 0.0]
        dmg_interval = [0.0, 0.0, 0.0, 0.0, 0.0]

        try:
            if fragility_set is not None:
                location = GeoUtil.get_location(facility)
                demand_type = EpfUtil.get_hazard_demand_type(fragility_set, hazard_type)
                # demand_type = fragility_set['demandType']
                demand_units = fragility_set['demandUnits']

                #fragility_key = self.get_parameter("fragility_key")
                local_fragility_set = fragility_set[fragility_key]
                if hazard_type == 'earthquake':
                    # TODO include liquefaction and hazard uncertainty
                    hazard_demand_type = EpfUtil.get_hazard_demand_type(local_fragility_set, hazard_type)
                    demand_units = local_fragility_set['demandUnits']

                    demand_type = local_fragility_set['demandType']

                    if hazard_demand_type != demand_type:
                        print("Mismatch in hazard type.")
                        # exit(1)

                    # Start here, need to add the hazard dataset id to the analysis parameter list
                    hazard_resp = self.hazardsvc.get_earthquake_hazard_values(hazard_dataset_id, demand_type,
                                                                              demand_units,
                                                                              [location.y, location.x])
                    hazard_val = hazard_resp[0]['hazardValue']

                    dmg_probability = AnalysisUtil.calculate_damage_json2(fragility_set, hazard_val)
                    dmg_interval = AnalysisUtil.calculate_damage_interval(dmg_probability)

                    # use ground liquifacition to modify damage interval, not implemented
                    if use_liquefaction:
                        liq_hazard_type = ""
                        liq_hazard_val = 0.0
                        liquefaction_prob = 0.0

                        geology_dataset_id = ""
                        pgd_demand_units = ""
                        fragility_set_liq = None
                        if fragility_set_liq is not None and geology_dataset_id is not None:
                            liq_fragility_curve = fragility_set_liq['fragilityCurves'][0]
                            liq_hazard_type = fragility_set_liq['demandType']
                            pgd_demand_units = fragility_set_liq['demandUnits']

                            # Get PGD hazard value from hazard service
                            location_str = str(location.y) + "," + str(location.x)

                            liquefaction = self.hazardsvc.get_liquefaction_values(hazard_dataset_id, geology_dataset_id,
                                                                              pgd_demand_units, [location_str])
                            liq_hazard_val = liquefaction[0]['pgd']
                            liquefaction_prob = liquefaction[0]['liqProbability']

                            liq_fragility_vars = {'x': liq_hazard_val, 'y': liquefaction_prob}
                            pgd_repairs = AnalysisUtil.compute_custom_limit_state_probability(fragility_set_liq,
                                                                                              liq_fragility_vars)

                    # use hazard uncertainty, not implemented
                    if use_hazard_uncertainty:
                        pass

                else:
                    print("Missing hazard type.")
            else:
                print("Missing fragility set.")

            epf_results['guid'] = facility['properties']['guid']
            epf_results["hazardtype"] = demand_type
            epf_results["hazardval"] = hazard_val
            epf_results["nodenwid"] = facility["properties"]["nodenwid"]
            epf_results["fltytype"] = facility["properties"]["fltytype"]
            epf_results["strctype"] = facility["properties"]["strctype"]
            epf_results["utilfcltyc"] = facility["properties"]["utilfcltyc"]
            epf_results["flow"] = facility["properties"]["flow"]
            epf_results["indpnode"] = facility["properties"]["indpnode"]

            # epf_results.update(dmg_probability)
            epf_results["ls-slight"] = dmg_probability[0]
            epf_results["ls-moderat"] = dmg_probability[1]
            epf_results["ls-extensi"] = dmg_probability[2]
            epf_results["ls-complet"] = dmg_probability[3]
            # epf_results.update(dmg_interval)
            epf_results["none"] = dmg_interval[0]
            epf_results["slight-mod"] = dmg_interval[1]
            epf_results["mod-extens"] = dmg_interval[2]
            epf_results["ext-comple"] = dmg_interval[3]
            epf_results["complete"] = dmg_interval[4]

        except Exception as ex:
            # This prints the type, value and stacktrace of error being handled.
            traceback.print_exc()
            print()
            # raise e

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
                    'type': ['ergo:epfs'],
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
