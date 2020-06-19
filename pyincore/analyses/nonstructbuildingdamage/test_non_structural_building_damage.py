
from pyincore import IncoreClient, FragilityService, MappingSet
from pyincore.analyses.nonstructbuildingdamage import NonStructBuildingDamage


def run_with_base_class():
    client = IncoreClient()

    # Memphis 7.9 AB-95
    hazard_type = "earthquake"
    hazard_id = "5b902cb273c3371e1236b36b"

    # Shelby County Essential Facilities
    building_dataset_id = "5a284f42c7d30d13bc0821ba"

    # Default Building Fragility Mapping v1.0
    mapping_id = "5b47b350337d4a3629076f2c"

    non_structural_building_dmg = NonStructBuildingDamage(client)

    # Load input datasets
    non_structural_building_dmg.load_remote_input_dataset("buildings", building_dataset_id)

    # Load fragility mapping
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    non_structural_building_dmg.set_input_dataset('dfr3_mapping_set', mapping_set)

    # Specify the result name
    result_name = "non_structural_building_dmg_result"

    # Set analysis parameters
    non_structural_building_dmg.set_parameter("result_name", result_name)
    non_structural_building_dmg.set_parameter("hazard_type", hazard_type)
    non_structural_building_dmg.set_parameter("hazard_id", hazard_id)
    non_structural_building_dmg.set_parameter("num_cpu", 4)

    # use liquefaction (slow)
    # Shelby County Liquefaction Susceptibility
    use_liquefaction = True
    liq_geology_dataset_id = "5a284f55c7d30d13bc0824ba"

    non_structural_building_dmg.set_parameter("use_liquefaction", use_liquefaction)
    non_structural_building_dmg.set_parameter("liq_geology_dataset_id", liq_geology_dataset_id)

    # Run analysis
    non_structural_building_dmg.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
