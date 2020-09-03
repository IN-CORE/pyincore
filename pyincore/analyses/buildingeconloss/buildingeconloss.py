# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import collections
import concurrent.futures
import traceback

from pyincore import BaseAnalysis, AnalysisUtil
from pyincore.analyses.buildingeconloss.buildingeconutil import BuildingEconUtil


class BuildingEconLoss(BaseAnalysis):
    """Building Economic Loss Analysis calculates the building loss based on
    mean damage and various multipliers such as inflation.

    Args:
        incore_client (IncoreClient): Service authentication.

    """
    def __init__(self, incore_client):
        self.occ_damage_mult = None
        self.inflation_table = None
        self.default_inflation_factor = 0.0

        super(BuildingEconLoss, self).__init__(incore_client)

    def run(self):
        """Executes building economic damage analysis."""
        bldg_dmg_set = self.get_input_dataset("building_dmg").get_inventory_reader()

        occ_damage_mult = self.get_input_dataset("building_occupancy").get_inventory_reader()
        self.occ_damage_mult = list(occ_damage_mult)
        # inflation table
        inflation_table = self.get_input_dataset("consumer_price_index").get_inventory_reader()
        self.inflation_table = list(inflation_table)

        user_defined_cpu = 1
        if not self.get_parameter("num_cpu") is None and self.get_parameter("num_cpu") > 0:
            user_defined_cpu = self.get_parameter("num_cpu")

        num_workers = AnalysisUtil.determine_parallelism_locally(self, len(bldg_dmg_set), user_defined_cpu)

        avg_bulk_input_size = int(len(bldg_dmg_set) / num_workers)
        inventory_args = []
        count = 0
        inventory_list = list(bldg_dmg_set)
        while count < len(inventory_list):
            inventory_args.append(inventory_list[count:count + avg_bulk_input_size])
            count += avg_bulk_input_size

        results = self.bldg_econ_dmg_concurrent_future(self.bldg_econ_loss_bulk_input, num_workers, inventory_args)

        self.set_result_csv_data("result", results, name=self.get_parameter("result_name"))

        return True

    def bldg_econ_dmg_concurrent_future(self, function_name, parallelism, *args):
        """Utilizes concurrent.future module.

        Args:
            function_name (function): The function to be parallelized.
            parallelism (int): Number of workers in parallelization.
            *args: All the arguments in order to pass into parameter function_name.

        Returns:
            list: A list of ordered dictionaries with building damage values and other data/metadata.

        """
        output = []
        with concurrent.futures.ProcessPoolExecutor(max_workers=parallelism) as executor:
            for ret in executor.map(function_name, *args):
                output.extend(ret)

        return output

    def bldg_econ_loss_bulk_input(self, buildings):
        """Run analysis for multiple buildings.

        Args:
            buildings (list): Multiple buildings from input inventory set.

        Returns:
            list: A list of ordered dictionaries with building damage values and other data/metadata.

        """
        result = []
        for building in buildings:
            result.append(self.bldg_econ_loss(building))

        return result

    def bldg_econ_loss(self, building):
        """Calculates building economic damage results for a single building.

        Args:
            building (obj): A JSON mapping of a geometric object from the inventory: current building.

        Returns:
            OrderedDict: A dictionary with building economic damage values and other data/metadata.

        """
        str_loss = 0.0
        str_loss_dev = 0.0
        try:
            bldg_results = collections.OrderedDict()

            mean_damage = float(building["properties"]["meandamage"])
            mean_damage_dev = float(building["properties"]["mdamagedev"])

            bldg = building["properties"]
            bldg_results["guid"] = building["properties"]["guid"]
            # bldg_results["parid"] = building["properties"]["parid"]
            # bldg_results["struct_typ"] = building["properties"]["struct_typ"]
            # bldg_results["year_built"] = building["properties"]["year_built"]
            # bldg_results["no_stories"] = building["properties"]["no_stories"]
            # bldg_results["occ_type"] = building["properties"]["occ_type"]
            # bldg_results["cont_val"] = building["properties"]["cont_val"]
            # bldg_results["efacility"] = building["properties"]["efacility"]
            # bldg_results["dwell_unit"] = building["properties"]["dwell_unit"]
            # bldg_results["sq_foot"] = building["properties"]["sq_foot"]
            # bldg_results["str_typ2"] = building["properties"]["str_typ2"]
            # bldg_results["par_id"] = building["properties"]["par_id"]
            # bldg_results["lat"] = building["properties"]["lat"]
            # bldg_results["long"] = building["properties"]["long"]
            # bldg_results["occ_detail"] = building["properties"]["occ_detail"]
            # bldg_results["tot_appr"] = building["properties"]["tot_appr"]
            # bldg_results["tract"] = building["properties"]["tract"]
            # bldg_results["ct_lat"] = building["properties"]["ct_lat"]
            # bldg_results["ct_lon"] = building["properties"]["ct_lon"]
            # bldg_results["immocc"] = building["properties"]["immocc"]
            # bldg_results["lifesfty"] = building["properties"]["lifesfty"]
            # bldg_results["collprev"] = building["properties"]["collprev"]
            # bldg_results["insignific"] = building["properties"]["insignific"]
            # bldg_results["moderate"] = building["properties"]["moderate"]
            # bldg_results["heavy"] = building["properties"]["heavy"]
            # bldg_results["complete"] = building["properties"]["complete"]
            # bldg_results["meandamage"] = building["properties"]["meandamage"]
            # bldg_results["mdamagedev"] = building["properties"]["mdamagedev"]
            # bldg_results["oldcode"] = building["properties"]["oldcode"]
            # bldg_results["newcode"] = building["properties"]["newcode"]
            # bldg_results["hazardtype"] = building["properties"]["hazardtype"]
            # bldg_results["hazardval"] = building["properties"]["hazardval"]
            # bldg_results["cost"] = building["properties"]["cost"]
            # bldg_results["period"] = building["properties"]["period"]

            if "appr_bldg" in bldg:
                appr_val = float(building["properties"]["appr_bldg"])
                bldg_results["appr_bldg"] = str(appr_val)

                inflation_mult = BuildingEconUtil.get_inflation_mult(self.default_inflation_factor,
                                                                     self.inflation_table)
                # It was determined after some email exchange with Steve French that if the user does not supply
                # non-structural damage we should compute str_loss from the entire appraised value
                str_loss = BuildingEconUtil.get_econ_loss(1.0, mean_damage, appr_val, inflation_mult)
                str_loss_dev = BuildingEconUtil.get_econ_std_loss(1.0, mean_damage_dev, appr_val, inflation_mult)

            bldg_results["strloss"] = "{:.2f}".format(str_loss)
            bldg_results["strlossdev"] = "{:.2f}".format(str_loss_dev)

            return bldg_results

        except Exception as e:
            # This prints the type, value and stacktrace of error being handled.
            traceback.print_exc()
            raise e

    def get_spec(self):
        """Get specifications of the building damage analysis.

        Returns:
            obj: A JSON object of specifications of the building damage analysis.

        """
        return {
            'name': 'building-economy-damage',
            'description': 'building economy damage analysis',
            'input_parameters': [
                {
                    'id': 'result_name',
                    'required': True,
                    'description': 'result dataset name',
                    'type': str
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
                    'id': 'building_dmg',
                    'required': True,
                    'description': 'Building damage results CSV file',
                    'type': ['ergo:buildingDamageVer4', 'ergo:buildingInventory', 'ergo:buildingDamage']
                },
                {
                    'id': 'building_occupancy',
                    'required': True,
                    'description': 'Building occupancy, use, efacility and multipliers',
                    'type': ['incore:buildingOccupancyMultiplier']
                },
                {
                    'id': 'consumer_price_index',
                    'required': False,
                    'description': 'US Consumer Price Index 1913-2020, CSV file',
                    'type': ['incore:consumerPriceIndexUS']
                }
            ],
            'output_datasets': [
                {
                    'id': 'result',
                    'parent_type': 'buildings',
                    'description': 'CSV file of building economy damages',
                    'type': 'ergo:buildingEconomicLoss'
                }
            ]
        }
