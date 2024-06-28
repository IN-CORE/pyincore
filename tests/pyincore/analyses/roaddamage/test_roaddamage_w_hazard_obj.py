from pyincore import (
    IncoreClient,
    FragilityService,
    MappingSet,
    HazardService,
    Earthquake,
    Tsunami,
    Hurricane,
)
from pyincore.analyses.roaddamage import RoadDamage
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    # EQ Road Dataset - Seaside roads
    road_dataset_id = "5ee7af50772cf80008577ae3"

    hazard_service = HazardService(client)
    liq_geology_dataset_id = None

    earthquake = Earthquake.from_hazard_service(
        "5ba8f379ec2309043520906f", hazard_service
    )
    tsunami = Tsunami.from_hazard_service("5bc9eaf7f7b08533c7e610e1", hazard_service)

    # Earthquake mapping
    eq_mapping_id = "5d545b0bb9219c0689f1f3f4"

    eq_fragility_key = "pgd"
    liquefaction = False

    # Tsunami Mapping for Seaside
    tsu_mapping_id = "5ee7b2c9c54361000148de37"

    tsu_fragility_key = "Non-Retrofit inundationDepth Fragility ID Code"

    uncertainty = False

    ######################################################################
    # Run Earthquake road damage
    eq_road_dmg = RoadDamage(client)
    eq_road_dmg.load_remote_input_dataset("roads", road_dataset_id)

    # Load fragility mapping
    fragility_service = FragilityService(client)
    eq_mapping_set = MappingSet(fragility_service.get_mapping(eq_mapping_id))
    eq_road_dmg.set_input_dataset("dfr3_mapping_set", eq_mapping_set)
    eq_road_dmg.set_input_hazard("hazard", earthquake)
    eq_road_dmg.set_parameter("result_name", "seaside_road_dmg_earthquake_w_hazard_obj")
    if eq_fragility_key is not None:
        eq_road_dmg.set_parameter("fragility_key", eq_fragility_key)
    eq_road_dmg.set_parameter("num_cpu", 1)
    eq_road_dmg.set_parameter("use_liquefaction", liquefaction)
    if liquefaction and liq_geology_dataset_id is not None:
        eq_road_dmg.set_parameter(
            "liquefaction_geology_dataset_id", liq_geology_dataset_id
        )
    eq_road_dmg.set_parameter("use_hazard_uncertainty", uncertainty)

    # Run Analysis
    eq_road_dmg.run_analysis()

    ######################################################################
    # Run Tsunami road damage
    tsu_road_dmg = RoadDamage(client)
    tsu_road_dmg.load_remote_input_dataset("roads", road_dataset_id)

    # Load fragility mapping
    fragility_service = FragilityService(client)
    tsu_mapping_set = MappingSet(fragility_service.get_mapping(tsu_mapping_id))
    tsu_road_dmg.set_input_dataset("dfr3_mapping_set", tsu_mapping_set)
    tsu_road_dmg.set_input_hazard("hazard", tsunami)
    tsu_road_dmg.set_parameter("result_name", "seaside_road_dmg_tsunami_w_hazard_obj")
    if tsu_fragility_key is not None:
        tsu_road_dmg.set_parameter("fragility_key", tsu_fragility_key)
    tsu_road_dmg.set_parameter("num_cpu", 1)
    tsu_road_dmg.set_parameter("use_liquefaction", False)
    tsu_road_dmg.set_parameter("use_hazard_uncertainty", uncertainty)

    # Run Analysis
    tsu_road_dmg.run_analysis()

    ######################################################################
    # test galveston hurricane road failure

    # road inventory for Galveston island
    road_dataset_id = "664e5812efdc9f1ed5dc2f7f"
    # road damage by hurricane inundation mapping
    mapping_id = "60ba583b1f2b7d4a916faf03"
    # Galveston Deterministic Hurricane - Kriging inundationDuration
    hurricane = Hurricane.from_hazard_service(
        "5f10837c01d3241d77729a4f", hazard_service
    )

    # Create road damage
    hurr_road_dmg = RoadDamage(client)
    # Load input datasets
    hurr_road_dmg.load_remote_input_dataset("roads", road_dataset_id)
    # Load fragility mapping
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    hurr_road_dmg.set_input_dataset("dfr3_mapping_set", mapping_set)
    hurr_road_dmg.set_input_hazard("hazard", hurricane)
    # Specify the result name
    result_name = "galveston_hurricane_road_result_w_hazard_obj"
    # Set analysis parameters
    hurr_road_dmg.set_parameter("result_name", result_name)
    hurr_road_dmg.set_parameter(
        "fragility_key", "Non-Retrofit inundationDepth Fragility ID Code"
    )
    hurr_road_dmg.set_parameter("num_cpu", 4)

    # Run road damage by hurricane inundation analysis
    hurr_road_dmg.run_analysis()


if __name__ == "__main__":
    run_with_base_class()
