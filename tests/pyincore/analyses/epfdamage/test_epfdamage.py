from pyincore import IncoreClient, FragilityService, MappingSet
from pyincore.analyses.epfdamage import EpfDamage
from pyincore.globals import INCORE_TEST_URL


def run_with_base_class():
    client = IncoreClient(INCORE_TEST_URL)

    hazard_type = "earthquake"

    hazard_id = "5eebcbb08f80fe3899ad6039"

    epf_dataset_id = "5eebcaa17a00803abc85ec11"

    # Earthquake mapping
    mapping_id = "5eebcc13e7226233ce4ef0d7"

    # Run epf damage
    epf_dmg = EpfDamage(client)

    epf_dmg.load_remote_input_dataset("epfs", epf_dataset_id)

    # Load fragility mapping
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    epf_dmg.set_input_dataset('dfr3_mapping_set', mapping_set)

    epf_dmg.set_parameter("result_name", "earthquake_epf_dmg_result")
    epf_dmg.set_parameter("hazard_type", hazard_type)
    epf_dmg.set_parameter("hazard_id", hazard_id)
    epf_dmg.set_parameter("num_cpu", 1)

    # Run Analysis
    epf_dmg.run_analysis()

    hazard_type = "tsunami"

    hazard_id = "5bc9eaf7f7b08533c7e610e1"

    epf_dataset_id = "5eebcaa17a00803abc85ec11"

    # Tsunami mapping
    mapping_id = "5eebce11e7226233ce4ef305"

    # Run epf damage
    epf_dmg = EpfDamage(client)
    epf_dmg.load_remote_input_dataset("epfs", epf_dataset_id)

    # Load fragility mapping
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    epf_dmg.set_input_dataset('dfr3_mapping_set', mapping_set)

    epf_dmg.set_parameter("fragility_key", "Non-Retrofit inundationDepth Fragility ID Code")
    epf_dmg.set_parameter("result_name", "tsunami_epf_dmg_result")
    epf_dmg.set_parameter("hazard_type", hazard_type)
    epf_dmg.set_parameter("hazard_id", hazard_id)
    epf_dmg.set_parameter("num_cpu", 1)

    # Run Analysis
    epf_dmg.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
