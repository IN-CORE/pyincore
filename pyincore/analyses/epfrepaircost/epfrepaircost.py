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


class EpfRepairCost(BaseAnalysis):
    """Computes electric power facility repair cost.

    Args:
        incore_client (IncoreClient): Service authentication.

    """

    def __init__(self, incore_client):
        super(EpfRepairCost, self).__init__(incore_client)

    def run(self):
        """Executes electric power facility repair cost analysis."""

        epf_df = self.get_input_dataset("epfs").get_dataframe_from_shapefile()
        epf_damage_df = self.get_input_dataset("epf_damage").get_dataframe_from_csv()

        # join damage result with original inventory
        epf_set = epf_df.merge(epf_damage_df, on='guid').tolist()

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

        repair_cost = self.epf_repair_cost_concurrent_future(self.epf_repair_cost_bulk_input, num_workers,
                                                             inventory_args)
        self.set_result_csv_data("result", repair_cost, name=self.get_parameter("result_name") + "_repair_cost")

        return True

    def epf_repair_cost_concurrent_future(self, function_name, num_workers, *args):
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

    def epf_repair_cost_bulk_input(self, epfs):
        """Run analysis for multiple epfs.

        Args:
            epfs (list): Multiple epfs from input inventory set.
            hazard_type (str): A type of hazard exposure (earthquake, tsunami, tornado, or hurricane).
            hazard_dataset_id (str): An id of the hazard exposure.

        Returns:
            list: A list of ordered dictionaries with epf damage values and other data/metadata.

        """

        # Setting Local Variables
        for epf in epfs:
            node_type = epf['utilfcltyc']
            node_id = int(epf['nodenwid'])

            reptime_func_node = nodes_reptime_func[nodes_reptime_func['Type'] == node_type]
            dr_data = nodes_damge_ratio[nodes_damge_ratio['Type'] == node_type]
            rep_time = 0
            repair_cost = 0
            if not reptime_func_node.empty:
                if index == 0:
                    node_name = '(' + str(node_id) + ',' + str(net_names["Water"]) + ')'
                else:
                    node_name = '(' + str(node_id) + ',' + str(net_names["Power"]) + ')'
                ds = dmg_sce_data[dmg_sce_data['name'] == node_name].iloc[0][sample_num + 1]
                rep_time = reptime_func_node.iloc[0]['ds_' + ds + '_mean']  # we can use the 100% instead of mean
                dr = dr_data.iloc[0]['dr_' + ds + '_be']
                repair_cost = v[1]['q_ds_3'] * dr
            node_data.loc[v[0], 'p_time'] = rep_time if rep_time > 0 else 0
            node_data.loc[v[0], 'p_budget'] = repair_cost
            node_data.loc[v[0], 'q'] = repair_cost

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
                    'type': ['incore:epf',
                             'ergo:epf',
                             'incore:epfVer2'
                             ],
                },
                {
                    'id': 'damage',
                    'required': True,
                    'description': 'damage result that has damage intervals in it',
                    'type': ['incore:epfDamage',
                             'incore:epfDamageVer2',
                             'incore:epfDamageVer3']
                },
                {
                    'id': 'dmg_ratios',
                    'required': True,
                    'description': 'Damage Ratios table',
                    'type': ['incore:epfDamageRatios']
                },
            ],
            'output_datasets': [
                {
                    'id': 'result',
                    'parent_type': 'epfs',
                    'description': 'A csv file with repair cost for each electric power facility',
                    'type': 'incore:epfRepairCost'
                }
            ]
        }
