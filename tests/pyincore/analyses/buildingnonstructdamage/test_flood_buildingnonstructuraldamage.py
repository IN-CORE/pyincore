from pyincore import IncoreClient, FragilityService, MappingSet, Flood, HazardService
from pyincore.analyses.buildingnonstructuraldamage import BuildingNonStructDamage
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)
    hazardsvc = HazardService(client)

    # lumberton flood
    flood = Flood.from_hazard_service("5f4d02e99f43ee0dde768406", hazardsvc)

    # lumberton building inventory v7
    # bldg_dataset_id = "603010f7b1db9c28aef53214"  # 40 building subset
    bldg_dataset_id = "603010a4b1db9c28aef5319f"  # 21k full building

    # lumberton building mapping (with equation)
    mapping_id = "602f3cf981bd2c09ad8f4f9d"
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))

    non_structural_building_dmg_flood = BuildingNonStructDamage(client)
    non_structural_building_dmg_flood.load_remote_input_dataset("buildings", bldg_dataset_id)
    non_structural_building_dmg_flood.set_input_dataset('dfr3_mapping_set', mapping_set)
    non_structural_building_dmg_flood.set_parameter("result_name", "non_structural_building_dmg_result_flood")
    non_structural_building_dmg_flood.set_input_hazard("hazard", flood)
    non_structural_building_dmg_flood.set_parameter("num_cpu", 4)
    non_structural_building_dmg_flood.set_parameter("fragility_key", "Lumberton Flood Building Fragility ID Code")
    non_structural_building_dmg_flood.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
