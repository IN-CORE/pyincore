from pyincore import IncoreClient, FragilityService, MappingSet
from pyincore.analyses.roaddamage import RoadDamage
from pyincore.globals import INCORE_TEST_URL


def run_with_base_class():
    client = IncoreClient(INCORE_TEST_URL)

    # EQ Road Dataset - Seaside roads
    road_dataset_id = "5ee7af50772cf80008577ae3"

    hazard_type = "tsunami"
    liq_geology_dataset_id = None

    if hazard_type == 'earthquake':
        # Seaside Earthquake
        hazard_id = "5ba8f379ec2309043520906f"

        # Earthquake mapping
        mapping_id = "5ee7b145c54361000148dcc5"

        fragility_key = "pgd"
        liquefaction = False
    elif hazard_type == 'tsunami':
        # Seaside Tsunami
        hazard_id = "5bc9eaf7f7b08533c7e610e1"

        # Tsunami Mapping for Seaside
        mapping_id = "5ee7b2c9c54361000148de37"

        fragility_key = "Non-Retrofit inundationDepth Fragility ID Code"
        liquefaction = False
    else:
        raise ValueError("Earthquake and tsunami are the only testable hazards with road damage currently")

    uncertainty = False

    # Run Seaside earthquake road damage
    road_dmg = RoadDamage(client)
    road_dmg.load_remote_input_dataset("roads", road_dataset_id)

    # Load fragility mapping
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    road_dmg.set_input_dataset('dfr3_mapping_set', mapping_set)

    road_dmg.set_parameter("result_name", "seaside_road_dmg_" + hazard_type)
    road_dmg.set_parameter("hazard_type", hazard_type)
    road_dmg.set_parameter("hazard_id", hazard_id)
    if fragility_key is not None:
        road_dmg.set_parameter("fragility_key", fragility_key)
    road_dmg.set_parameter("num_cpu", 1)
    road_dmg.set_parameter("use_liquefaction", liquefaction)
    if liquefaction and liq_geology_dataset_id is not None:
        road_dmg.set_parameter("liquefaction_geology_dataset_id", liq_geology_dataset_id)
    road_dmg.set_parameter("use_hazard_uncertainty", uncertainty)

    # Run Analysis
    road_dmg.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
