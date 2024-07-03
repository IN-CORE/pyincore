from pyincore import IncoreClient, FragilityService, MappingSet
from pyincore.analyses.roaddamage import RoadDamage
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    # EQ Road Dataset - Seaside roads
    road_dataset_id = "5ee7af50772cf80008577ae3"

    hazard_type = "tsunami"
    # hazard_type = "earthquake"
    liq_geology_dataset_id = None

    if hazard_type == "earthquake":
        # Seaside Earthquake
        hazard_id = "5ba8f379ec2309043520906f"

        # Earthquake mapping
        mapping_id = "5d545b0bb9219c0689f1f3f4"

        fragility_key = "pgd"
        liquefaction = False
    elif hazard_type == "tsunami":
        # Seaside Tsunami
        hazard_id = "5bc9eaf7f7b08533c7e610e1"

        # Tsunami Mapping for Seaside
        mapping_id = "5ee7b2c9c54361000148de37"

        fragility_key = "Non-Retrofit inundationDepth Fragility ID Code"
        liquefaction = False
    else:
        raise ValueError(
            "Earthquake and tsunami are the only testable hazards with road damage currently"
        )

    uncertainty = False

    # Run road damage
    road_dmg = RoadDamage(client)
    road_dmg.load_remote_input_dataset("roads", road_dataset_id)

    # Load fragility mapping
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    road_dmg.set_input_dataset("dfr3_mapping_set", mapping_set)

    road_dmg.set_parameter("result_name", "seaside_road_dmg_" + hazard_type)
    road_dmg.set_parameter("hazard_type", hazard_type)
    road_dmg.set_parameter("hazard_id", hazard_id)
    if fragility_key is not None:
        road_dmg.set_parameter("fragility_key", fragility_key)
    road_dmg.set_parameter("num_cpu", 1)
    road_dmg.set_parameter("use_liquefaction", liquefaction)
    if liquefaction and liq_geology_dataset_id is not None:
        road_dmg.set_parameter(
            "liquefaction_geology_dataset_id", liq_geology_dataset_id
        )
    road_dmg.set_parameter("use_hazard_uncertainty", uncertainty)

    # Run Analysis
    road_dmg.run_analysis()

    ######################################################################
    # test galveston hurricane road failure

    # road inventory for Galveston island
    road_dataset_id = "664e5812efdc9f1ed5dc2f7f"
    # road damage by hurricane inundation mapping
    mapping_id = "60ba583b1f2b7d4a916faf03"
    # Galveston Deterministic Hurricane - Kriging inundationDuration
    hazard_type = "hurricane"
    hazard_id = "5f10837c01d3241d77729a4f"

    # Create road damage
    hurr_road_dmg = RoadDamage(client)
    # Load input datasets
    hurr_road_dmg.load_remote_input_dataset("roads", road_dataset_id)
    # Load fragility mapping
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    hurr_road_dmg.set_input_dataset("dfr3_mapping_set", mapping_set)
    # Specify the result name
    result_name = "galveston_hurricane_road_result"
    # Set analysis parameters
    hurr_road_dmg.set_parameter("result_name", result_name)
    hurr_road_dmg.set_parameter("hazard_type", hazard_type)
    hurr_road_dmg.set_parameter(
        "fragility_key", "Non-Retrofit inundationDepth Fragility ID Code"
    )
    hurr_road_dmg.set_parameter("hazard_id", hazard_id)
    hurr_road_dmg.set_parameter("num_cpu", 4)

    # Run road damage by hurricane inundation analysis
    hurr_road_dmg.run_analysis()


if __name__ == "__main__":
    run_with_base_class()
