from pyincore import IncoreClient, FragilityService, MappingSet
from pyincore.analyses.buildingnonstructuraldamage import (
    BuildingNonStructDamage,
    BuildingNonStructUtil,
)
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    # Memphis 7.9 AB-95
    hazard_type = "earthquake"
    hazard_id = "5b902cb273c3371e1236b36b"

    # Shelby County Essential Facilities
    building_dataset_id = "5a284f42c7d30d13bc0821ba"

    # Default Building Fragility Mapping v1.0
    mapping_id = "5b47b350337d4a3629076f2c"
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))

    # use liquefaction (slow)
    # Shelby County Liquefaction Susceptibility
    use_liquefaction = True
    liq_geology_dataset_id = "5a284f55c7d30d13bc0824ba"

    # Acceleration sensitive
    non_structural_building_dmg_as = BuildingNonStructDamage(client)
    non_structural_building_dmg_as.load_remote_input_dataset(
        "buildings", building_dataset_id
    )
    non_structural_building_dmg_as.set_input_dataset("dfr3_mapping_set", mapping_set)
    non_structural_building_dmg_as.set_parameter(
        "result_name", "non_structural_building_dmg_result_as"
    )
    non_structural_building_dmg_as.set_parameter("hazard_type", hazard_type)
    non_structural_building_dmg_as.set_parameter("hazard_id", hazard_id)
    non_structural_building_dmg_as.set_parameter("num_cpu", 4)
    non_structural_building_dmg_as.set_parameter(
        "fragility_key", BuildingNonStructUtil.DEFAULT_FRAGILITY_KEY_AS
    )
    non_structural_building_dmg_as.set_parameter("use_liquefaction", use_liquefaction)
    non_structural_building_dmg_as.set_parameter(
        "liq_geology_dataset_id", liq_geology_dataset_id
    )
    non_structural_building_dmg_as.run_analysis()

    # Drift sensitive
    non_structural_building_dmg_ds = BuildingNonStructDamage(client)
    non_structural_building_dmg_ds.load_remote_input_dataset(
        "buildings", building_dataset_id
    )
    non_structural_building_dmg_ds.set_input_dataset("dfr3_mapping_set", mapping_set)
    non_structural_building_dmg_ds.set_parameter(
        "result_name", "non_structural_building_dmg_result_ds"
    )
    non_structural_building_dmg_ds.set_parameter("hazard_type", hazard_type)
    non_structural_building_dmg_ds.set_parameter("hazard_id", hazard_id)
    non_structural_building_dmg_ds.set_parameter("num_cpu", 4)
    non_structural_building_dmg_ds.set_parameter(
        "fragility_key", BuildingNonStructUtil.DEFAULT_FRAGILITY_KEY_DS
    )
    non_structural_building_dmg_ds.set_parameter("use_liquefaction", use_liquefaction)
    non_structural_building_dmg_ds.set_parameter(
        "liq_geology_dataset_id", liq_geology_dataset_id
    )
    non_structural_building_dmg_ds.run_analysis()


if __name__ == "__main__":
    run_with_base_class()
