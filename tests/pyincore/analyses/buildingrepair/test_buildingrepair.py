# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from pyincore import IncoreClient, RepairService, MappingSet
from pyincore.analyses.buildingrepair.buildingrepair import BuildingRepair
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    # Joplin
    buildings = "5df7d0de425e0b00092d0082"  # joplin ergo:buildingInventoryVer6 28k buildings

    # sample_damage_states = "6112d9ccca3e973ce144b4d9"  # 500 samples 28k buildings - MCS output format
    sample_damage_states = "60f883c059a8cc52bab4dd77"  # 10 samples 28k buildings - MCS output format

    building_repair = BuildingRepair(client)
    building_repair.load_remote_input_dataset("buildings", buildings)

    mapping_id = "60edfa3efc0f3a7af53a21b5"
    repair_service = RepairService(client)
    mapping_set = MappingSet(repair_service.get_mapping(mapping_id))
    building_repair.set_input_dataset('dfr3_mapping_set', mapping_set)

    building_repair.load_remote_input_dataset("sample_damage_states", sample_damage_states)

    building_repair.set_parameter("result_name", "joplin_repair_time")
    building_repair.set_parameter("seed", 1238)

    building_repair.run_analysis()

    return True


if __name__ == '__main__':
    run_with_base_class()
