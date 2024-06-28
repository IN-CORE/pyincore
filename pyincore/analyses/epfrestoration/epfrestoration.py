# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


"""
Electric Power Facility Restoration
"""

import numpy as np

from typing import List
from pyincore import BaseAnalysis, RestorationService, AnalysisUtil
from pyincore.models.restorationcurveset import RestorationCurveSet


class EpfRestoration(BaseAnalysis):
    """Computes electric power facility restoration for an earthquake exposure."""

    def __init__(self, incore_client):
        self.restorationsvc = RestorationService(incore_client)
        super(EpfRestoration, self).__init__(incore_client)

    def run(self):
        """Performs Water facility restoration analysis by using the parameters from the spec
        and creates an output dataset in csv format

        Returns:
            bool: True if successful, False otherwise

        """
        inventory_list = list(self.get_input_dataset("epfs").get_inventory_reader())
        mapping_set = self.get_input_dataset("dfr3_mapping_set")

        restoration_key = self.get_parameter("restoration_key")
        if restoration_key is None:
            restoration_key = "Restoration ID Code"

        end_time = self.get_parameter("end_time")
        if end_time is None:
            end_time = 365.0

        time_interval = self.get_parameter("time_interval")
        if time_interval is None:
            time_interval = 1

        pf_interval = self.get_parameter("pf_interval")
        if pf_interval is None:
            pf_interval = 0.1

        discretized_days = self.get_parameter("discretized_days")
        if discretized_days is None:
            discretized_days = [1, 3, 7, 30, 90]

        damage = self.get_input_dataset("damage").get_csv_reader()
        damage_result = AnalysisUtil.get_csv_table_rows(damage, ignore_first_row=False)

        (
            inventory_restoration_map,
            pf_results,
            time_results,
            func_results,
            repair_times,
        ) = self.electricpowerfacility_restoration(
            inventory_list,
            damage_result,
            mapping_set,
            restoration_key,
            end_time,
            time_interval,
            pf_interval,
            discretized_days,
        )

        self.set_result_csv_data(
            "inventory_restoration_map",
            inventory_restoration_map,
            name="inventory_restoration_map_" + self.get_parameter("result_name"),
        )
        self.set_result_csv_data(
            "pf_results",
            time_results,
            name="percentage_of_functionality_" + self.get_parameter("result_name"),
        )
        self.set_result_csv_data(
            "time_results",
            pf_results,
            name="reptime_" + self.get_parameter("result_name"),
        )
        self.set_result_csv_data(
            "func_results",
            func_results,
            name=self.get_parameter("result_name") + "_discretized_restoration",
        )
        self.set_result_csv_data(
            "repair_times",
            repair_times,
            name="full_reptime_" + self.get_parameter("result_name"),
        )

        return True

    def electricpowerfacility_restoration(
        self,
        inventory_list,
        damage_result,
        mapping_set,
        restoration_key,
        end_time,
        time_interval,
        pf_interval,
        discretized_days,
    ):
        """Gets applicable restoration curve set and calculates restoration time and functionality

        Args:
            inventory_list (list): Multiple EPF facilities from input inventory set.
            damage_result: EPF damage
            mapping_set (class): Restoration Mapping Set
            restoration_key (str): Restoration Key to determine which curve to use. E.g. Restoration ID Code
            end_time (float): User specified end repair time
            time_interval (float): Increment interval of repair time. Default to 1 (1 day)
            pf_interval (float): Increment interval of percentage of functionality. Default 0.1 (10%)
            discretized_days (list): Days to compute discretized restoration (e.g. 1, 3, 7, 30, 90)

        Returns:
            time_results (list): Given Percentage of functionality, the change of repair time
            pf_results (list): Given Repair time, change of the percentage of functionality

        """
        # Obtain the restoration id for each electric facilities
        inventory_restoration_map = []

        # Obtain classification for each electric facility, used to lookup discretized functionality
        inventory_class_map = {}
        restoration_sets = self.restorationsvc.match_inventory(
            self.get_input_dataset("dfr3_mapping_set"), inventory_list, restoration_key
        )
        for inventory in inventory_list:
            if inventory["id"] in restoration_sets.keys():
                restoration_set_id = restoration_sets[inventory["id"]].id
            else:
                restoration_set_id = None

            inventory_restoration_map.append(
                {
                    "guid": inventory["properties"]["guid"],
                    "restoration_id": restoration_set_id,
                }
            )

            restoration_curve_set = restoration_sets[inventory["id"]]

            # For each facility, get the discretized restoration from the continuous curve
            discretized_restoration = AnalysisUtil.get_discretized_restoration(
                restoration_curve_set, discretized_days
            )
            inventory_class_map[
                inventory["properties"]["guid"]
            ] = discretized_restoration

        time_results = []
        pf_results = []
        repair_time = {}

        for mapping in mapping_set.mappings:
            # get restoration curves
            # if it's string:id; then need to fetch it from remote and cast to restorationcurveset object
            restoration_curve_set = mapping.entry[restoration_key]
            if isinstance(restoration_curve_set, str):
                restoration_curve_set = RestorationCurveSet(
                    self.restorationsvc.get_dfr3_set(restoration_curve_set)
                )

            # given time calculate pf
            time = np.arange(0, end_time + time_interval, time_interval)
            for t in time:
                pf_results.append(
                    {
                        "restoration_id": restoration_curve_set.id,
                        "time": t,
                        **restoration_curve_set.calculate_restoration_rates(time=t),
                    }
                )

            # given pf calculate time
            pf = np.arange(0, 1 + pf_interval, pf_interval)
            for p in pf:
                new_dict = {}
                t_res = restoration_curve_set.calculate_inverse_restoration_rates(
                    time=p
                )
                for key, value in t_res.items():
                    new_dict.update({"time_" + key: value})
                time_results.append(
                    {
                        "restoration_id": restoration_curve_set.id,
                        "percentage_of_functionality": p,
                        **new_dict,
                    }
                )

            repair_time[
                restoration_curve_set.id
            ] = restoration_curve_set.calculate_inverse_restoration_rates(time=0.99)

        # Compute discretized restoration
        func_result = []
        for dmg in damage_result:
            guid = dmg["guid"]

            # Dictionary of discretized restoration functionality
            rest_dict = inventory_class_map[guid]

            ds_0, ds_1, ds_2, ds_3, ds_4 = (
                dmg["DS_0"],
                dmg["DS_1"],
                dmg["DS_2"],
                dmg["DS_3"],
                dmg["DS_4"],
            )
            result_dict = {}
            for time in discretized_days:
                key = "day" + str(time)
                # Only compute if we have damage
                if ds_0:
                    functionality = (
                        rest_dict[key][0] * float(ds_0)
                        + rest_dict[key][1] * float(ds_1)
                        + rest_dict[key][2] * float(ds_2)
                        + rest_dict[key][3] * float(ds_3)
                        + rest_dict[key][4] * float(ds_4)
                    )
                    result_dict.update({str(key): functionality})

            func_result.append({"guid": guid, **result_dict})

        repair_times = []
        for inventory in inventory_restoration_map:
            repair_times.append(
                {"guid": inventory["guid"], **repair_time[inventory["restoration_id"]]}
            )

        return (
            inventory_restoration_map,
            pf_results,
            time_results,
            func_result,
            repair_times,
        )

    def get_spec(self):
        return {
            "name": "electric-power-facility-restoration",
            "description": "electric power facility restoration analysis",
            "input_parameters": [
                {
                    "id": "restoration_key",
                    "required": False,
                    "description": "restoration key to use in mapping dataset",
                    "type": str,
                },
                {
                    "id": "result_name",
                    "required": True,
                    "description": "result dataset name",
                    "type": str,
                },
                {
                    "id": "end_time",
                    "required": False,
                    "description": "end time. Default to 365.",
                    "type": float,
                },
                {
                    "id": "time_interval",
                    "required": False,
                    "description": "incremental interval for time in days. Default to 1",
                    "type": float,
                },
                {
                    "id": "pf_interval",
                    "required": False,
                    "description": "incremental interval for percentage of functionality. Default to 0.1",
                    "type": float,
                },
                {
                    "id": "discretized_days",
                    "required": False,
                    "description": "Discretized days to compute functionality",
                    "type": List[int],
                },
            ],
            "input_datasets": [
                {
                    "id": "epfs",
                    "required": True,
                    "description": "Electric Power Facility Inventory",
                    "type": ["incore:epf", "ergo:epf"],
                },
                {
                    "id": "dfr3_mapping_set",
                    "required": True,
                    "description": "DFR3 Mapping Set Object",
                    "type": ["incore:dfr3MappingSet"],
                },
                {
                    "id": "damage",
                    "required": True,
                    "description": "damage result that has damage intervals in it",
                    "type": [
                        "incore:epfDamage",
                        "incore:epfDamageVer2",
                        "incore:epfDamageVer3",
                    ],
                },
            ],
            "output_datasets": [
                {
                    "id": "inventory_restoration_map",
                    "parent_type": "",
                    "description": "A csv file recording the mapping relationship between GUID and restoration id "
                    "applicable.",
                    "type": "incore:inventoryRestorationMap",
                },
                {
                    "id": "pf_results",
                    "parent_type": "",
                    "description": "A csv file recording functionality change with time for each class and limit "
                    "state.",
                    "type": "incore:epfRestorationFunc",
                },
                {
                    "id": "time_results",
                    "parent_type": "",
                    "description": "A csv file recording repair time at certain functionality recovery for each class "
                    "and limit state.",
                    "type": "incore:epfRestorationTime",
                },
                {
                    "id": "func_results",
                    "parent_type": "",
                    "description": "A csv file recording discretized functionality over time",
                    "type": "incore:epfDiscretizedRestorationFunc",
                },
                {
                    "id": "repair_times",
                    "parent_type": "",
                    "description": "A csv file recording repair time at full functionality recovery for each guid "
                    "and limit state.",
                    "type": "incore:epfRepairTime",
                },
            ],
        }
