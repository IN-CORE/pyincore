from pyincore import IncoreClient, FragilityService, MappingSet
from pyincore.analyses.buildingdamage import BuildingDamage

if __name__ == "__main__":
    client = IncoreClient()
    # Create building damage
    bldg_dmg = BuildingDamage(client)

    # Load input dataset
    bldg_dmg.load_remote_input_dataset("buildings", "656f6e5f70bd6e5ce90aac95")

    # Load fragility mapping
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping("5b47b2d9337d4a36187c7563"))
    bldg_dmg.set_input_dataset('dfr3_mapping_set', mapping_set)

    # Specify the result name
    result_name = "los_angeles_bldg_dmg_result"

    # Set analysis parameters
    bldg_dmg.set_parameter("result_name", result_name)
    bldg_dmg.set_parameter("hazard_type", "earthquake")
    bldg_dmg.set_parameter("hazard_id", "656f5d67b57f7b0a431faa15")
    bldg_dmg.set_parameter("num_cpu", 10)

    # Run building damage analysis
    bldg_dmg.run_analysis()
