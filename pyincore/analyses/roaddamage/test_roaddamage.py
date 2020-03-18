from pyincore import IncoreClient
from pyincore.analyses.roaddamage import RoadDamage
from pyincore.analyses.roaddamage import RoadDamageOld


def run_with_base_class():
    client = IncoreClient()

    # EQ Road Dataset - Seaside roads
    road_dataset_id = "5d25118eb9219c0692cd7527"

    hazard_type = "earthquake"
    liq_geology_dataset_id = None

    if hazard_type == 'earthquake':
        # Seaside Earthquake
        hazard_id = "5ba8f379ec2309043520906f"

        # Earthquake mapping
        mapping_id = "5d545b0bb9219c0689f1f3f4"

        fragility_key = "pgd"
        liquefaction = False
    elif hazard_type == 'tsunami':
        # Seaside Tsunami
        hazard_id = "5d27b986b9219c3c55ad37d0"

        # Tsunami Mapping for Seaside
        mapping_id = "5d274fd8b9219c3c553c71ff"

        fragility_key = "Non-Retrofit inundationDepth Fragility ID Code"
        liquefaction = False
    else:
        raise ValueError("Earthquake and tsunami are the only testable hazards with road damage currently")

    uncertainty = False

    # Run Seaside earthquake road damage
    road_dmg = RoadDamage(client)
    road_dmg_old = RoadDamageOld(client)
    road_dmg.load_remote_input_dataset("roads", road_dataset_id)
    road_dmg_old.load_remote_input_dataset("roads", road_dataset_id)

    road_dmg.set_parameter("result_name", "seaside_road_dmg_" + hazard_type)
    road_dmg_old.set_parameter("result_name", "seaside_road_dmg_" + hazard_type + "_old")
    road_dmg.set_parameter("mapping_id", mapping_id)
    road_dmg_old.set_parameter("mapping_id", mapping_id)
    road_dmg.set_parameter("hazard_type", hazard_type)
    road_dmg_old.set_parameter("hazard_type", hazard_type)
    road_dmg.set_parameter("hazard_id", hazard_id)
    road_dmg_old.set_parameter("hazard_id", hazard_id)
    if fragility_key is not None:
        road_dmg.set_parameter("fragility_key", fragility_key)
        road_dmg_old.set_parameter("fragility_key", fragility_key)
    road_dmg.set_parameter("num_cpu", 1)
    road_dmg_old.set_parameter("num_cpu", 1)
    road_dmg.set_parameter("use_liquefaction", liquefaction)
    road_dmg_old.set_parameter("use_liquefaction", liquefaction)
    if liquefaction and liq_geology_dataset_id is not None:
        road_dmg.set_parameter("liquefaction_geology_dataset_id", liq_geology_dataset_id)
        road_dmg_old.set_parameter("liquefaction_geology_dataset_id", liq_geology_dataset_id)
    road_dmg.set_parameter("use_hazard_uncertainty", uncertainty)
    road_dmg_old.set_parameter("use_hazard_uncertainty", uncertainty)

    # Run Analysis
    road_dmg.run_analysis()
    road_dmg_old.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
