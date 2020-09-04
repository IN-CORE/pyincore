# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import pandas as pd
import collections
import concurrent.futures
import traceback
from itertools import repeat

from pyincore import BaseAnalysis, AnalysisUtil
from pyincore.analyses.buildingeconloss.buildingeconutil import BuildingEconUtil


class BuildingEconLoss(BaseAnalysis):
    """Building Economic Loss Analysis calculates the building loss based on
    mean damage and various multipliers such as inflation.

    Args:
        incore_client (IncoreClient): Service authentication.

    """
    def __init__(self, incore_client):
        self.inflation_table = None
        self.default_inflation_factor = 0.0

        super(BuildingEconLoss, self).__init__(incore_client)

    def run(self):
        """Executes building economic damage analysis."""
        bldg_set = self.get_input_dataset("buildings").get_inventory_reader()

        prop_select = []
        for bldg_item in list(bldg_set):
            guid = bldg_item["properties"]["guid"]
            appr_bldg = bldg_item["properties"]["appr_bldg"]
            prop_select.append([guid, appr_bldg])

        bldg_set_df = pd.DataFrame(prop_select, columns=["guid", "appr_bldg"])
        bldg_dmg_set = self.get_input_dataset("building_mean_dmg").get_csv_reader()
        bldg_dmg_df = pd.DataFrame(list(bldg_dmg_set))

        bldg_dmg_set_df = pd.merge(bldg_set_df, bldg_dmg_df, how='outer', left_on="guid", right_on="guid",
                                   sort=True, copy=True)
        # inflation table
        inflation_table = self.get_input_dataset("consumer_price_index").get_inventory_reader()
        self.inflation_table = list(inflation_table)

        user_defined_cpu = 4
        if not self.get_parameter("num_cpu") is None and self.get_parameter("num_cpu") > 0:
            user_defined_cpu = self.get_parameter("num_cpu")

        row_num = len(bldg_dmg_set_df.index)
        num_workers = AnalysisUtil.determine_parallelism_locally(self, row_num, user_defined_cpu)

        avg_bulk_input_size = row_num / num_workers
        inventory = []
        count = 0
        while count < row_num:
            inventory.append(bldg_dmg_set_df.loc[count:count + avg_bulk_input_size])
            count += avg_bulk_input_size

        results = self.bldg_econ_dmg_concurrent_future(self.bldg_econ_loss_bulk_input, num_workers, inventory)

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

    def bldg_econ_loss_bulk_input(self, bldg_dmg_set):
        """Run analysis for multiple buildings.

        Args:
            bldg_dmg_set (obj): A set of all building damage results.

        Returns:
            list: A list of ordered dictionaries with building damage values and other data/metadata.

        """
        result = []
        for index, bldg in bldg_dmg_set.iterrows():
            result.append(self.bldg_econ_loss(bldg))
        return result

    def bldg_econ_loss(self, bldg):
        """Calculates building economic damage results for a single building.

        Args:
            bldg (obj): An inventory property: current building.

        Returns:
            OrderedDict: A dictionary with building economic damage values and other data/metadata.

        """
        str_loss = 0.0
        str_loss_dev = 0.0
        try:
            bldg_results = collections.OrderedDict()
            mean_damage = float(bldg.loc["meandamage"])
            mean_damage_dev = float(bldg.loc["mdamagedev"])

            bldg_results["guid"] = bldg.loc["guid"]
            if "appr_bldg" in bldg:
                appr_val = float(bldg.loc["appr_bldg"])
                # bldg_results["appr_bldg"] = str(appr_val)

                inflation_mult = BuildingEconUtil.get_inflation_mult(self.default_inflation_factor,
                                                                     self.inflation_table)
                # It was determined after some email exchange with Steve French that if the user does not supply
                # non-structural damage we should compute str_loss from the entire appraised value
                str_loss = BuildingEconUtil.get_econ_loss(1.0, mean_damage, appr_val, inflation_mult)
                str_loss_dev = BuildingEconUtil.get_econ_std_loss(1.0, mean_damage_dev, appr_val, inflation_mult)

            # 7fd16f4d-b201-4c28-9d63-336fc006884f, 72500, 43167.21428, 24144.25773,
            # parid, year_built, occ_type, appr_bldg, guid, lat, long
            # 017053, 1910, RES3, 72500, 7fd16f4d-b201-4c28-9d63-336fc006884f, 35.1373, -89.99892
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
                    'id': 'buildings',
                    'required': True,
                    'description': 'Building Inventory',
                    'type': ['ergo:buildingInventory','ergo:buildingInventoryVer4', 'ergo:buildingInventoryVer5', 'ergo:buildingInventoryVer6'],
                },
                {
                    'id': 'building_mean_dmg',
                    'required': True,
                    'description': 'Building mean damage results CSV file',
                    'type': ['ergo:meanDamage', 'ergo:buildingDamage']
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
