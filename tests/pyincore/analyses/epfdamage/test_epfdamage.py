import pyincore.globals as pyglobals
from pyincore import IncoreClient, FragilityService, MappingSet
from pyincore.analyses.epfdamage import EpfDamage


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    hazard_type_eq = "earthquake"

    hazard_id_eq = "5eebcbb08f80fe3899ad6039"

    epf_dataset_id = "5eebcaa17a00803abc85ec11"

    # Earthquake mapping
    mapping_id = "5eebcc13e7226233ce4ef0d7"

    # Run epf damage
    epf_dmg_eq = EpfDamage(client)

    epf_dmg_eq.load_remote_input_dataset("epfs", epf_dataset_id)

    # Load fragility mapping
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    epf_dmg_eq.set_input_dataset('dfr3_mapping_set', mapping_set)

    epf_dmg_eq.set_parameter("result_name", "earthquake_epf_dmg_result")
    epf_dmg_eq.set_parameter("hazard_type", hazard_type_eq)
    epf_dmg_eq.set_parameter("hazard_id", hazard_id_eq)
    epf_dmg_eq.set_parameter("num_cpu", 1)

    # Run Analysis
    epf_dmg_eq.run_analysis()

    hazard_type_tsu = "tsunami"
    hazard_id_tsu = "5bc9eaf7f7b08533c7e610e1"

    epf_dataset_id = "5eebcaa17a00803abc85ec11"

    # Tsunami mapping
    mapping_id = "5eebce11e7226233ce4ef305"

    # Run epf damage
    epf_dmg_tsu = EpfDamage(client)
    epf_dmg_tsu.load_remote_input_dataset("epfs", epf_dataset_id)

    # Load fragility mapping
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    epf_dmg_tsu.set_input_dataset('dfr3_mapping_set', mapping_set)

    epf_dmg_tsu.set_parameter("fragility_key", "Non-Retrofit inundationDepth Fragility ID Code")
    epf_dmg_tsu.set_parameter("result_name", "tsunami_epf_dmg_result")
    epf_dmg_tsu.set_parameter("hazard_type", hazard_type_tsu)
    epf_dmg_tsu.set_parameter("hazard_id", hazard_id_tsu)
    epf_dmg_tsu.set_parameter("num_cpu", 1)

    # Run Analysis
    epf_dmg_tsu.run_analysis()

    ##################################
    # test refactored

    # Earthquake mapping
    mapping_id = "605bf99b618178207f64754b"

    # Run epf damage
    epf_dmg_eq_re = EpfDamage(client)

    epf_dmg_eq_re.load_remote_input_dataset("epfs", epf_dataset_id)

    # Load fragility mapping
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    epf_dmg_eq_re.set_input_dataset('dfr3_mapping_set', mapping_set)

    epf_dmg_eq_re.set_parameter("result_name", "refactored_earthquake_epf_dmg_result")
    epf_dmg_eq_re.set_parameter("hazard_type", hazard_type_eq)
    epf_dmg_eq_re.set_parameter("hazard_id", hazard_id_eq)
    epf_dmg_eq_re.set_parameter("num_cpu", 1)

    # Run Analysis
    epf_dmg_eq_re.run_analysis()

    epf_dataset_id = "5eebcaa17a00803abc85ec11"
    # Tsunami mapping
    mapping_id = "605bf9e1618178207f6475c6"

    # Run epf damage
    epf_dmg_tsu_re = EpfDamage(client)
    epf_dmg_tsu_re.load_remote_input_dataset("epfs", epf_dataset_id)

    # Load fragility mapping
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    epf_dmg_tsu_re.set_input_dataset('dfr3_mapping_set', mapping_set)

    epf_dmg_tsu_re.set_parameter("fragility_key", "Non-Retrofit inundationDepth Fragility ID Code")
    epf_dmg_tsu_re.set_parameter("result_name", "refactored_tsunami_epf_dmg_result")
    epf_dmg_tsu_re.set_parameter("hazard_type", hazard_type_tsu)
    epf_dmg_tsu_re.set_parameter("hazard_id", hazard_id_tsu)
    epf_dmg_tsu_re.set_parameter("num_cpu", 1)

    # Run Analysis
    epf_dmg_tsu_re.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
