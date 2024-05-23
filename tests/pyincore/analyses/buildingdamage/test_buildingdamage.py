from pyincore import IncoreClient, FragilityService, MappingSet, Earthquake, HazardService, Tsunami, Hurricane, \
    Tornado
from pyincore.analyses.buildingdamage import BuildingDamage
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)
    hazardsvc = HazardService(client)

    ##########################################################
    # Memphis Earthquake damage
    # New madrid earthquake using Atkinson Boore 1995
    eq = Earthquake.from_hazard_service("5b902cb273c3371e1236b36b", hazardsvc)

    # Geology dataset
    liq_geology_dataset_id = "5a284f53c7d30d13bc08249c"

    # Building dataset
    # 5a284f0bc7d30d13bc081a28  5kb
    # 5bcf2fcbf242fe047ce79dad 300kb
    # 5a284f37c7d30d13bc08219c 20mb
    bldg_dataset_id = "5a284f0bc7d30d13bc081a28"

    bldg_dmg = BuildingDamage(client)
    bldg_dmg.load_remote_input_dataset("buildings", bldg_dataset_id)

    # Earthquake mapping
    mapping_id = "5b47b350337d4a3629076f2c"
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    bldg_dmg.set_input_dataset('dfr3_mapping_set', mapping_set)

    bldg_dmg.set_input_hazard("hazard", eq)

    result_name = "memphis_eq_bldg_dmg_result"
    bldg_dmg.set_parameter("result_name", result_name)
    bldg_dmg.set_parameter("num_cpu", 4)
    bldg_dmg.set_parameter("use_liquefaction", True)
    bldg_dmg.set_parameter("liquefaction_geology_dataset_id", liq_geology_dataset_id)

    # Run Analysis
    bldg_dmg.run_analysis()

    ##########################################################
    # TSUNAMI
    tsunami = Tsunami.from_hazard_service("5bc9e25ef7b08533c7e610dc", hazardsvc)

    # Seaside building dataset
    bldg_dataset_id = "5bcf2fcbf242fe047ce79dad"

    # Run seaside tsunami building damage
    bldg_dmg = BuildingDamage(client)
    bldg_dmg.load_remote_input_dataset("buildings", bldg_dataset_id)

    # Tsunami mapping
    mapping_id = "5b48fb1f337d4a478e7bd54d"
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    bldg_dmg.set_input_dataset('dfr3_mapping_set', mapping_set)
    bldg_dmg.set_input_hazard("hazard", tsunami)
    result_name = "seaside_tsunami_dmg_result"
    bldg_dmg.set_parameter("result_name", result_name)
    bldg_dmg.set_parameter("num_cpu", 4)
    bldg_dmg.run_analysis()

    ##########################################################
    # Hurricane
    hurricane = Hurricane.from_hazard_service("5f11e50cc6491311a814584c", hazardsvc)

    # Galveston building dataset 602eba8bb1db9c28aef01358
    bldg_dataset_id = "602eba8bb1db9c28aef01358"  # 19k buildings with age_group
    # bldg_dataset_id = "602d61d0b1db9c28aeedea03"  # 40 buildings without age_group

    bldg_dmg = BuildingDamage(client)
    bldg_dmg.load_remote_input_dataset("buildings", bldg_dataset_id)

    # Hurricane building mapping (with equation)
    mapping_id = "602c381a1d85547cdc9f0675"
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    bldg_dmg.set_input_dataset('dfr3_mapping_set', mapping_set)
    bldg_dmg.set_parameter("fragility_key", "Hurricane SurgeLevel and WaveHeight Fragility ID Code")

    bldg_dmg.set_input_hazard("hazard", hurricane)

    result_name = "galveston_hurr_dmg_result"
    bldg_dmg.set_parameter("result_name", result_name)
    bldg_dmg.set_parameter("num_cpu", 4)
    bldg_dmg.run_analysis()

    ##########################################################
    # joplin tornado without strategy
    bldg_dataset_id = "5df7d0de425e0b00092d0082"  # joplin building v6

    bldg_dmg = BuildingDamage(client)
    bldg_dmg.load_remote_input_dataset("buildings", bldg_dataset_id)

    mapping_id = "5e8e3a21eaa8b80001f04f1c"  # 19 archetype mapping
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    bldg_dmg.set_input_dataset('dfr3_mapping_set', mapping_set)
    bldg_dmg.set_parameter("fragility_key", "Fragility ID Code")

    tornado = Tornado.from_hazard_service("5dfa32bbc0601200080893fb", hazardsvc)
    bldg_dmg.set_input_hazard("hazard", tornado)

    result_name = "joplin_tornado_dmg_result"
    bldg_dmg.set_parameter("result_name", result_name)
    bldg_dmg.set_parameter("num_cpu", 4)
    bldg_dmg.set_parameter("seed", 1000)
    bldg_dmg.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
