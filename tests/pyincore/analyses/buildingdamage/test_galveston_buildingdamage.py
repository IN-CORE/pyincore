from pyincore import IncoreClient, FragilityService, MappingSet
from pyincore.analyses.buildingdamage import BuildingDamage
import pyincore.globals as pyglobals
from pyincore import Dataset


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)
    buildings = Dataset.from_file("/Users/cwang138/Documents/INCORE-2.0/Galveston/galveston_bldgs",
                                  "ergo:buildingInventoryVer7")

    bldg_dmg = BuildingDamage(client)
    bldg_dmg.set_input_dataset("buildings", buildings)

    hazard_type = "hurricane"
    hazard_id = "5fa472033c1f0c73fe81461a"

    # hurricane wind
    wind_mapping_id = "62fef3a6cef2881193f2261d"
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(wind_mapping_id))
    bldg_dmg.set_input_dataset('dfr3_mapping_set', mapping_set)

    bldg_dmg.set_parameter("result_name", "galveston_hurricane_wind_bldg_dmg")
    bldg_dmg.set_parameter("hazard_type", hazard_type)
    bldg_dmg.set_parameter("hazard_id", hazard_id)
    bldg_dmg.set_parameter("num_cpu", 8)
    bldg_dmg.set_parameter("use_liquefaction", True)

    # Run Analysis
    bldg_dmg.run_analysis()

    # hurricane flood
    flood_mapping_id = "62fefd688a30d30dac57bbd7"
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(wind_mapping_id))
    bldg_dmg.set_input_dataset('dfr3_mapping_set', mapping_set)

    bldg_dmg.set_parameter("result_name", "galveston_hurricane_flood_bldg_dmg")
    bldg_dmg.set_parameter("hazard_type", hazard_type)
    bldg_dmg.set_parameter("hazard_id", hazard_id)
    bldg_dmg.set_parameter("num_cpu", 8)
    bldg_dmg.set_parameter("use_liquefaction", True)

    # Run Analysis
    bldg_dmg.run_analysis()

    # hurricane surge-wave
    sw_mapping_id = "6303e51bd76c6d0e1f6be080"
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(wind_mapping_id))
    bldg_dmg.set_input_dataset('dfr3_mapping_set', mapping_set)

    bldg_dmg.set_parameter("result_name", "galveston_hurricane_sw_bldg_dmg")
    bldg_dmg.set_parameter("hazard_type", hazard_type)
    bldg_dmg.set_parameter("hazard_id", hazard_id)
    bldg_dmg.set_parameter("num_cpu", 8)
    bldg_dmg.set_parameter("use_liquefaction", True)

    # Run Analysis
    bldg_dmg.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
