from pyincore import (
    IncoreClient,
    FragilityService,
    MappingSet,
    HazardService,
    Earthquake,
    Hurricane,
)
from pyincore.analyses.bridgedamage import BridgeDamage
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    # New madrid earthquake using Atkinson Boore 1995
    hazard_service = HazardService(client)
    eq = Earthquake.from_hazard_service("5b902cb273c3371e1236b36b", hazard_service)

    # NBSR bridges
    bridge_dataset_id = "5a284f2dc7d30d13bc082040"

    # Default Bridge Fragility Mapping on incore-service
    mapping_id = "5b47bcce337d4a37755e0cb2"

    # Use liquefaction (LIQ) column of bridges to modify fragility curve
    use_liquefaction = True

    # Geology dataset
    liq_geology_dataset_id = "5a284f53c7d30d13bc08249c"

    # Create bridge damage
    bridge_dmg = BridgeDamage(client)

    # Load input datasets
    bridge_dmg.load_remote_input_dataset("bridges", bridge_dataset_id)

    # Load fragility mapping
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    bridge_dmg.set_input_dataset("dfr3_mapping_set", mapping_set)

    bridge_dmg.set_input_hazard("hazard", eq)

    # Set analysis parameters
    # bridge_dmg.set_parameter("result_name", "bridge_result")
    bridge_dmg.set_parameter("result_name", "bridge_result_w_liquefaction")
    bridge_dmg.set_parameter("num_cpu", 4)
    bridge_dmg.set_parameter("use_liquefaction", use_liquefaction)
    bridge_dmg.set_parameter("liquefaction_geology_dataset_id", liq_geology_dataset_id)

    # Run bridge damage analysis
    bridge_dmg.run_analysis()

    ###################################################################
    # south carolina eq damage
    eq = Earthquake.from_hazard_service("5ee9309bc9f1b70008fdbd26", hazard_service)

    # south carolina bridges
    bridge_dataset_id = "5ee92f884210b80008f9377e"

    # Default Bridge Fragility Mapping on incore-service
    mapping_id = "5b47bcce337d4a37755e0cb2"

    # Create bridge damage
    bridge_dmg = BridgeDamage(client)

    # Load input datasets
    bridge_dmg.load_remote_input_dataset("bridges", bridge_dataset_id)

    # Load fragility mapping
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    bridge_dmg.set_input_dataset("dfr3_mapping_set", mapping_set)

    bridge_dmg.set_input_hazard("hazard", eq)
    # Set analysis parameters
    bridge_dmg.set_parameter("result_name", "bridge_result_south_carolina")
    bridge_dmg.set_parameter("use_liquefaction", False)
    bridge_dmg.set_parameter("num_cpu", 1)

    # Run bridge damage analysis
    bridge_dmg.run_analysis()

    ###################################################################
    # test Galveston Bridge Damage
    hurricane = Hurricane.from_hazard_service(
        "5f11e50cc6491311a814584c", hazard_service
    )

    # Galveston bridge
    bridge_dataset_id = "6062058ac57ada48e48c31e3"

    # Galveston hurricane bridge mapping
    refactored_mapping_id = "6062254b618178207f66226c"

    # Create bridge damage
    bridge_dmg = BridgeDamage(client)

    # Load input datasets
    bridge_dmg.load_remote_input_dataset("bridges", bridge_dataset_id)

    # Load fragility mapping
    fragility_service = FragilityService(client)
    refactored_mapping_set = MappingSet(
        fragility_service.get_mapping(refactored_mapping_id)
    )
    bridge_dmg.set_input_dataset("dfr3_mapping_set", refactored_mapping_set)

    bridge_dmg.set_input_hazard("hazard", hurricane)

    # Set analysis parameters
    bridge_dmg.set_parameter(
        "fragility_key", "Hurricane SurgeLevel and WaveHeight Fragility ID Code"
    )
    bridge_dmg.set_parameter("result_name", "galveston_bridge_dmg_result")
    bridge_dmg.set_parameter("num_cpu", 4)

    # Run bridge damage analysis
    bridge_dmg.run_analysis()


if __name__ == "__main__":
    run_with_base_class()
