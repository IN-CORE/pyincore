#!/usr/bin/env python3

from pyincore import IncoreClient, FragilityService, MappingSet
from pyincore.analyses.buildingdamage import BuildingDamage
from pyincore.analyses.joplinempiricalrestoration import JoplinEmpiricalRestoration
import pyincore.globals as pyglobals

def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    # Joplin tornado building damage
    bldg_dataset_id = "5df7d0de425e0b00092d0082"  # joplin building v6

    bldg_dmg = BuildingDamage(client)
    bldg_dmg.load_remote_input_dataset("buildings", bldg_dataset_id)

    mapping_id = "5e8e3a21eaa8b80001f04f1c"  # 19 archetype, non-retrofit
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    bldg_dmg.set_input_dataset("dfr3_mapping_set", mapping_set)
    bldg_dmg.set_parameter("fragility_key", "Non-Retrofit Fragility ID Code")

    # The simulated EF-5 tornado shows geographical locations and the range of wind speed
    # of tornado hazard in Joplin.
    hazard_type = "tornado"
    hazard_id = "5dfa32bbc0601200080893fb"

    result_name = "joplin_tornado_dmg_result"
    bldg_dmg.set_parameter("result_name", result_name)
    bldg_dmg.set_parameter("hazard_type", hazard_type)
    bldg_dmg.set_parameter("hazard_id", hazard_id)
    bldg_dmg.set_parameter("num_cpu", 4)
    bldg_dmg.set_parameter("seed", 1000)
    bldg_dmg.run_analysis()
    # end of Building damage analysis

    # get csv results from Building damage analysis
    building_dmg_result = bldg_dmg.get_output_dataset("ds_result")
    building_dmg_result.get_dataframe_from_csv()

    restoration = JoplinEmpiricalRestoration(client)

    restoration.load_remote_input_dataset("buildings", bldg_dataset_id)
    # restoration.load_remote_input_dataset("building_dmg", building_dmg_result)
    restoration.set_input_dataset("building_dmg", building_dmg_result)

    result_name = "Joplin_empirical_restoration_result"
    restoration.set_parameter("result_name", result_name)
    restoration.set_parameter("target_functionality_level", 0)
    # restoration.set_parameter("seed", 1234)

    # Run Analysis
    restoration.run_analysis()


if __name__ == '__main__':
    run_with_base_class()