from pyincore import (
    IncoreClient,
    FragilityService,
    MappingSet,
    Earthquake,
    HazardService,
    Tsunami,
    Hurricane,
)
from pyincore.analyses.epfdamage import EpfDamage
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    # ## Memphis EPF Damage with Earthquake ##
    hazard_service = HazardService(client)
    earthquake = Earthquake.from_hazard_service(
        "5b902cb273c3371e1236b36b", hazard_service
    )

    epf_dataset_id = "6189c103d5b02930aa3efc35"
    # mapping_id = "61980b11e32da63f4b9d86f4"
    mapping_id = "61980cf5e32da63f4b9d86f5"  # PGA and PGD

    use_liquefaction = True
    use_hazard_uncertainty = False
    liquefaction_geology_dataset_id = "5a284f53c7d30d13bc08249c"

    # Run epf damage
    epf_dmg_eq_memphis = EpfDamage(client)
    epf_dmg_eq_memphis.load_remote_input_dataset("epfs", epf_dataset_id)

    # Load fragility mapping
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    epf_dmg_eq_memphis.set_input_dataset("dfr3_mapping_set", mapping_set)

    epf_dmg_eq_memphis.set_input_hazard("hazard", earthquake)

    epf_dmg_eq_memphis.set_parameter(
        "result_name", "memphis_eq_epf_dmg_result_w_hazard_obj"
    )
    epf_dmg_eq_memphis.set_parameter("use_liquefaction", use_liquefaction)
    epf_dmg_eq_memphis.set_parameter("use_hazard_uncertainty", use_hazard_uncertainty)
    epf_dmg_eq_memphis.set_parameter(
        "liquefaction_geology_dataset_id", liquefaction_geology_dataset_id
    )
    epf_dmg_eq_memphis.set_parameter("num_cpu", 1)
    # Run Analysis
    epf_dmg_eq_memphis.run_analysis()

    # ##  Seaside EPF Damage with Earthquake ##
    hazard_type_eq = "earthquake"
    hazard_id_eq = "5eebcbb08f80fe3899ad6039"
    epf_dataset_id = "5eebcaa17a00803abc85ec11"
    # Earthquake mapping
    mapping_id = "5eebcc13e7226233ce4ef0d7"  # only PGA

    # Run epf damage
    epf_dmg_eq = EpfDamage(client)
    epf_dmg_eq.load_remote_input_dataset("epfs", epf_dataset_id)

    # Load fragility mapping
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    epf_dmg_eq.set_input_dataset("dfr3_mapping_set", mapping_set)
    epf_dmg_eq.set_parameter("result_name", "seaside_eq_epf_dmg_result")
    epf_dmg_eq.set_parameter("hazard_type", hazard_type_eq)
    epf_dmg_eq.set_parameter("hazard_id", hazard_id_eq)
    epf_dmg_eq.set_parameter("num_cpu", 1)
    epf_dmg_eq.run_analysis()

    # ## Seaside Tsunami EPF Damage ##
    tsunami = Tsunami.from_hazard_service("5bc9eaf7f7b08533c7e610e1", hazard_service)

    epf_dataset_id = "5eebcaa17a00803abc85ec11"

    # Tsunami mapping
    mapping_id = "605bf9e1618178207f6475c6"

    # Run epf damage
    epf_dmg_tsu_re = EpfDamage(client)
    epf_dmg_tsu_re.load_remote_input_dataset("epfs", epf_dataset_id)
    epf_dmg_eq = EpfDamage(client)
    epf_dmg_eq.load_remote_input_dataset("epfs", epf_dataset_id)

    # Load fragility mapping
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    epf_dmg_tsu_re.set_input_dataset("dfr3_mapping_set", mapping_set)

    epf_dmg_tsu_re.set_input_hazard("hazard", tsunami)

    epf_dmg_tsu_re.set_parameter(
        "fragility_key", "Non-Retrofit inundationDepth Fragility ID Code"
    )
    epf_dmg_tsu_re.set_parameter(
        "result_name", "seaside_tsunami_epf_dmg_result_w_hazard_obj"
    )
    epf_dmg_tsu_re.set_parameter("num_cpu", 1)

    epf_dmg_tsu_re.set_input_dataset("dfr3_mapping_set", mapping_set)
    # Run Analysis
    epf_dmg_tsu_re.run_analysis()

    #############################################################################
    # Galveston EPF damage
    # Run epf damage
    hurricane = Hurricane.from_hazard_service(
        "5fa472033c1f0c73fe81461a", hazard_service
    )
    epf_dmg_hurricane_galveston = EpfDamage(client)
    epf_dmg_hurricane_galveston.load_remote_input_dataset(
        "epfs", "62fd437b18e50067942b679a"
    )

    # Load fragility mapping
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping("62fac92ecef2881193f22613"))
    epf_dmg_hurricane_galveston.set_input_dataset("dfr3_mapping_set", mapping_set)
    epf_dmg_hurricane_galveston.set_input_hazard("hazard", hurricane)
    epf_dmg_hurricane_galveston.set_parameter(
        "result_name", "galveston_hurricane_epf_damage_w_hazard_obj"
    )
    epf_dmg_hurricane_galveston.set_parameter(
        "fragility_key", "Non-Retrofit Fragility ID Code"
    )
    epf_dmg_hurricane_galveston.set_parameter("num_cpu", 8)
    # Run Analysis
    epf_dmg_hurricane_galveston.run_analysis()


if __name__ == "__main__":
    run_with_base_class()
