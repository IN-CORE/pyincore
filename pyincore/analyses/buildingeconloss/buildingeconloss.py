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


class BuildingEconDamage(BaseAnalysis):
    """Building Economic Loss Analysis calculates the building loss based on
    mean damage and various multipliers such as inflation.

    Args:
        incore_client (IncoreClient): Service authentication.

    """
    def __init__(self, incore_client):
        self.occ_damage_mult = None
        self.inflation_table = None
        self.default_inflation_factor = 0.0

        super(BuildingEconDamage, self).__init__(incore_client)

    def run(self):
        """Executes building economic damage analysis."""
        bldg_dmg_set = self.get_input_dataset("building_dmg").get_inventory_reader()

        occ_damage_mult = self.get_input_dataset("building_occupancy").get_inventory_reader()
        # [{'type': 'Feature', 'id': '1',
        # 'properties': OrderedDict([   ('Occupancy', 'RES1'), ('SD Multiplier', '23.4'),
        #                               ('AS Multiplier', '26.6'), ('DS Multiplier', '50'),
        #                               ('Content Multiplier', '50')]),'geometry': None},
        self.occ_damage_mult = list(occ_damage_mult)
        # inflation table
        inflation_table = self.get_input_dataset("consumer_price_index").get_inventory_reader()
        # [{'type': 'Feature', 'id': '1',
        # 'properties': OrderedDict([   ('Year', '1913'), ('Jan', '9.8'), ('Feb', '9.8'), ('Mar', '9.8'), ('Apr', '9.8'), ('May', '9.7'), ('June', '9.8'), ('July', '9.9'), ('Aug', '9.9'), ('Sep', '10.0'), ('Oct', '10.0'), ('Nov', '10.1'), ('Dec', '10.0'),
        # ('Annual Avg', '9.9'), ('Percent Change Dec-Dec', '–'), ('Percent Change Avg-Avg', '–')]), 'geometry': None},
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
            # print(building["properties"])
            # OrderedDict([('guid', '463b4421-253b-457e-bb5c-3175c1f02c1d'), ('immocc', '0.0004999626218314243'),
            #              ('lifesfty', '1.4383210899030638e-06'), ('collprev', '6.462535621686252e-10'),
            #              ('insignific', '0.9995000373781686'), ('moderate', '0.0004985243007415213'),
            #              ('heavy', '1.4376748363408952e-06'), ('complete', '6.462535621686252e-10'),
            #              ('meandamage', '0.005075562756293972'), ('mdamagedev', '0.004162696692006942'),
            #              ('hazardtype', 'Sa'), ('hazardval', '0.09099999815225601')])

            # parid, struct_typ, year_built, no_stories, occ_type, appr_bldg, cont_val,
            # efacility, dwell_unit, sq_foot, str_typ2, guid, par_id, lat, long,
            # occ_detail, tot_appr, tract, ct_lat, ct_lon, immocc, lifesfty, collprev,
            # insignific, moderate, heavy, complete, meandamage, mdamagedev,
            # oldcode, newcode, hazardtype, hazardval, cost, period

            mean_damage = float(building["properties"]["meandamage"])
            mean_damage_dev = float(building["properties"]["mdamagedev"])
            # print(mean_damage)
            # print(mean_damage_dev)

            bldg = building["properties"]
            if "appr_bldg" in bldg and "year_built" in bldg:
                appr_val = float(building["properties"]["appr_bldg"])
                year_built = building["properties"]["year_built"]

                inflation_mult = BuildingEconUtil.get_inflation_mult(self.default_inflation_factor,
                                                                     self.inflation_table)
                print(inflation_mult)
                # It was determined after some email exchange with Steve French that if the user does not supply
                # non-structural damage we should compute str_loss from the entire appraised value
                str_loss = BuildingEconUtil.get_econ_loss(1.0, mean_damage, appr_val, inflation_mult)
                str_loss_dev = BuildingEconUtil.get_econ_std_loss(1.0, mean_damage_dev, appr_val, inflation_mult)

            bldg_results["guid"] = building["properties"]["guid"]
            bldg_results["loss"] = "{:.2f}".format(str_loss)
            bldg_results["loss_dev"] = "{:.2f}".format(str_loss_dev)
            # 43167.21428, 24144.25773
            # 53226.58677435593, 29770.659295267684
            # 43167.214282397734","24144.257729226276

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
