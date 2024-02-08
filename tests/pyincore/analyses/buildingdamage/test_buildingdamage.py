from pyincore import IncoreClient, FragilityService, MappingSet, Earthquake, HazardService, Tsunami, Hurricane, Flood, \
    Tornado
from pyincore.analyses.buildingdamage import BuildingDamage
import pyincore.globals as pyglobals
import time


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)
    hazardsvc = HazardService(client)

    time1 = time.time()
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
    time2 = time.time()
    print(f"Memphis Earthquake damage run time: {time2-time1}")

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

    time3 = time.time()
    print(f"Seaside Tsunami damage run time: {time3-time2}")

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

    time4 = time.time()
    print(f"Galveston Hurricane damage run time: {time4 - time3}")

    ##########################################################
    # lumberton flood
    flood = Flood.from_hazard_service("5f4d02e99f43ee0dde768406", hazardsvc)

    # lumberton building inventory v7
    # bldg_dataset_id = "603010f7b1db9c28aef53214"  # 40 building subset
    bldg_dataset_id = "603010a4b1db9c28aef5319f"  # 21k full building

    bldg_dmg = BuildingDamage(client)
    bldg_dmg.load_remote_input_dataset("buildings", bldg_dataset_id)

    # lumberton building mapping (with equation)
    mapping_id = "602f3cf981bd2c09ad8f4f9d"
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    bldg_dmg.set_input_dataset('dfr3_mapping_set', mapping_set)
    bldg_dmg.set_parameter("fragility_key", "Lumberton Flood Building Fragility ID Code")

    bldg_dmg.set_input_hazard("hazard", flood)

    result_name = "lumberton_flood_dmg_result"
    bldg_dmg.set_parameter("result_name", result_name)
    bldg_dmg.set_parameter("num_cpu", 4)
    bldg_dmg.run_analysis()

    time5 = time.time()
    print(f"Lumberton Flood damage run time: {time5 - time4}")

    ##########################################################
    # joplin tornado with retrofit strategy
    bldg_dataset_id = "5df7d0de425e0b00092d0082"  # joplin building v6
    # retrofit_strategy_id = "6091d5a8daa06e14ee96d502"  # plan 1
    # retrofit_strategy_id = "6091d5ffdaa06e14ee96d5ef" # plan 2

    bldg_dmg = BuildingDamage(client)
    bldg_dmg.load_remote_input_dataset("buildings", bldg_dataset_id)
    # bldg_dmg.load_remote_input_dataset("retrofit_strategy", retrofit_strategy_id)

    # lumberton building mapping (with equation)
    mapping_id = "6091d9fbb53ed4646fd276ca"  # 19 archetype with retrofit
    # mapping_id = "60994a1906d63d5ded1d6dcc" # 19 archetype with retrofit new format mapping
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    bldg_dmg.set_input_dataset('dfr3_mapping_set', mapping_set)
    bldg_dmg.set_parameter("fragility_key", "Fragility ID Code")

    tornado = Tornado.from_hazard_service("5dfa32bbc0601200080893fb", hazardsvc)
    bldg_dmg.set_input_hazard("hazard", tornado)

    result_name = "joplin_tornado_dmg_result_w_retrofit"
    bldg_dmg.set_parameter("result_name", result_name)
    bldg_dmg.set_parameter("num_cpu", 4)
    bldg_dmg.set_parameter("seed", 1000)
    bldg_dmg.run_analysis()

    time6 = time.time()
    print(f"Joplin Tornado damage run time: {time6 - time5}")


if __name__ == '__main__':
    run_with_base_class()
