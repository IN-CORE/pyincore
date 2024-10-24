import os

from pyincore import IncoreClient, FragilityService, MappingSet
from pyincore.analyses.buildingstructuraldamage.buildingstructuraldamage import (
    BuildingStructuralDamage,
)
import pyincore.globals as pyglobals


def run_with_base_class():
    result_folder = "legacy"
    if not os.path.exists(result_folder):
        os.mkdir(result_folder)

    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    # Memphis Earthquake damage
    # New madrid earthquake using Atkinson Boore 1995
    hazard_type = "earthquake"
    hazard_id = "5b902cb273c3371e1236b36b"

    # Geology dataset
    liq_geology_dataset_id = "5a284f53c7d30d13bc08249c"

    # Building dataset
    # 5a284f0bc7d30d13bc081a28  5kb
    # 5bcf2fcbf242fe047ce79dad 300kb
    # 5a284f37c7d30d13bc08219c 20mb
    bldg_dataset_id = "5a284f0bc7d30d13bc081a28"

    bldg_dmg = BuildingStructuralDamage(client)
    bldg_dmg.load_remote_input_dataset("buildings", bldg_dataset_id)

    # Earthquake mapping
    mapping_id = "5b47b350337d4a3629076f2c"
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    bldg_dmg.set_input_dataset("dfr3_mapping_set", mapping_set)

    result_name = os.path.join(result_folder, "memphis_eq_bldg_dmg_result")
    bldg_dmg.set_parameter("result_name", result_name)
    bldg_dmg.set_parameter("hazard_type", hazard_type)
    bldg_dmg.set_parameter("hazard_id", hazard_id)
    bldg_dmg.set_parameter("num_cpu", 4)
    bldg_dmg.set_parameter("use_liquefaction", True)
    bldg_dmg.set_parameter("liquefaction_geology_dataset_id", liq_geology_dataset_id)

    # Run Analysis
    bldg_dmg.run_analysis()

    # TSUNAMI

    hazard_type = "tsunami"
    hazard_id = "5bc9e25ef7b08533c7e610dc"

    # Seaside building dataset
    bldg_dataset_id = "5bcf2fcbf242fe047ce79dad"

    # Run seaside tsunami building damage
    bldg_dmg = BuildingStructuralDamage(client)
    bldg_dmg.load_remote_input_dataset("buildings", bldg_dataset_id)

    # Tsunami mapping
    mapping_id = "5b48fb1f337d4a478e7bd54d"
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    bldg_dmg.set_input_dataset("dfr3_mapping_set", mapping_set)

    result_name = os.path.join(result_folder, "seaside_tsunami_dmg_result")
    bldg_dmg.set_parameter("result_name", result_name)
    bldg_dmg.set_parameter("hazard_type", hazard_type)
    bldg_dmg.set_parameter("hazard_id", hazard_id)
    bldg_dmg.set_parameter("num_cpu", 4)
    bldg_dmg.run_analysis()

    # Hurricane

    hazard_type = "hurricane"
    hazard_id = "5f11e50cc6491311a814584c"

    # Galveston building dataset 602eba8bb1db9c28aef01358
    bldg_dataset_id = "602eba8bb1db9c28aef01358"  # 19k buildings with age_group
    # bldg_dataset_id = "602d61d0b1db9c28aeedea03"  # 40 buildings without age_group

    bldg_dmg = BuildingStructuralDamage(client)
    bldg_dmg.load_remote_input_dataset("buildings", bldg_dataset_id)

    # Hurricane building mapping (with equation)
    mapping_id = "602c381a1d85547cdc9f0675"
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    bldg_dmg.set_input_dataset("dfr3_mapping_set", mapping_set)
    bldg_dmg.set_parameter(
        "fragility_key", "Hurricane SurgeLevel and WaveHeight Fragility ID Code"
    )

    result_name = os.path.join(result_folder, "galveston_hurr_dmg_result")
    bldg_dmg.set_parameter("result_name", result_name)
    bldg_dmg.set_parameter("hazard_type", hazard_type)
    bldg_dmg.set_parameter("hazard_id", hazard_id)
    bldg_dmg.set_parameter("num_cpu", 4)
    bldg_dmg.run_analysis()

    # joplin tornado with retrofit strategy
    bldg_dataset_id = "5df7d0de425e0b00092d0082"  # joplin building v6
    retrofit_strategy_id = "660ab8f8ce705a7e54748557"  # plan 1

    bldg_dmg = BuildingStructuralDamage(client)
    bldg_dmg.load_remote_input_dataset("buildings", bldg_dataset_id)
    bldg_dmg.load_remote_input_dataset("retrofit_strategy", retrofit_strategy_id)

    mapping_id = "5e8e3a21eaa8b80001f04f1c"  # 19 archetype with retrofit
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    bldg_dmg.set_input_dataset("dfr3_mapping_set", mapping_set)

    hazard_type = "tornado"
    hazard_id = "5dfa32bbc0601200080893fb"
    result_name = os.path.join(result_folder, "joplin_tornado_dmg_result_w_retrofit")
    bldg_dmg.set_parameter("result_name", result_name)
    bldg_dmg.set_parameter("hazard_type", hazard_type)
    bldg_dmg.set_parameter("hazard_id", hazard_id)
    bldg_dmg.set_parameter("num_cpu", 4)
    bldg_dmg.set_parameter("seed", 1000)
    bldg_dmg.run_analysis()


if __name__ == "__main__":
    run_with_base_class()
