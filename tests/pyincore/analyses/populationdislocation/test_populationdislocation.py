# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from pyincore import IncoreClient, FragilityService, MappingSet
from pyincore.analyses.populationdislocation import PopulationDislocation
from pyincore.analyses.buildingdamage.buildingdamage import BuildingDamage
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)
    # client = IncoreClient(pyglobals.INCORE_TEST_URL)

    # # Joplin building damage
    # hazard_type = "tornado"
    # hazard_id = "5dfa32bbc0601200080893fb"
    # bldg_dataset_id = "5df7d0de425e0b00092d0082"
    # # Create a mapping to assign tornado fragilities to 19 building archetypes.
    # mapping_id = "5e8e3a21eaa8b80001f04f1c"
    #
    # # hazard_type = "hurricane"
    # # # Galveston building damage
    # # hazard_id = "5f6ccf67de7b566bb71b202d" # dev and tst
    # # bldg_dataset_id = "6024e935b70815363b8cdd1b" # dev
    # # mapping_id = "602c381a1d85547cdc9f0675" # dev and tst
    #
    # fragility_service = FragilityService(client)  # loading fragility mapping
    # mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    #
    # bldg_dmg = BuildingDamage(client)
    # bldg_dmg.load_remote_input_dataset("buildings", bldg_dataset_id)
    # bldg_dmg.set_input_dataset("dfr3_mapping_set", mapping_set)
    #
    # result_name = "bldg_dmg_result"
    #
    # bldg_dmg.set_parameter("result_name", result_name)
    # bldg_dmg.set_parameter("hazard_type", hazard_type)
    # bldg_dmg.set_parameter("hazard_id", hazard_id)
    # bldg_dmg.set_parameter("num_cpu", 4)
    #
    # bldg_dmg.run_analysis()
    #
    # building_dmg_result = bldg_dmg.get_output_dataset('result')

    # # Joplin population dislocation
    # # incore-tst
    housing_unit_alloc = "5df7c989425e0b00092c5eb4"
    bg_data = "5df7cb0b425e0b00092c9464"  # 2ev2
    value_loss = "60269f81ac5c86149b6aa988"

    # Galveston population dislocation
    # incore-dev
    # housing_unit_alloc = "602d5279b1db9c28aeede1ca"
    bg_data = "5df7cb0b425e0b00092c9464"  # Joplin 2ev2
    value_loss = "602d508fb1db9c28aeedb2a5"

    result_name = "pop-dislocation-results"
    seed = 1111

    pop_dis = PopulationDislocation(client)

    # pop_dis.set_input_dataset("building_dmg", building_dmg_result)
    # building_dmg = "602d96e4b1db9c28aeeebdce" # dev Joplin
    building_dmg = "602d975db1db9c28aeeebe35" # MO test - dev Joplin
    pop_dis.load_remote_input_dataset("building_dmg", building_dmg)
    housing_unit_alloc = "602ea965b1db9c28aeefa5d6" # MO test - dev Joplin

    pop_dis.load_remote_input_dataset("housing_unit_allocation", housing_unit_alloc)
    pop_dis.load_remote_input_dataset("block_group_data", bg_data)
    pop_dis.load_remote_input_dataset("value_poss_param", value_loss)

    # pop_dis.show_gdocstr_docs()

    pop_dis.set_parameter("result_name", result_name)
    pop_dis.set_parameter("seed", seed)
    # pop_dis.set_parameter("iterations", iterations)

    pop_dis.run_analysis()

    return True

if __name__ == '__main__':
    run_with_base_class()





