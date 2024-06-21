from pyincore import IncoreClient, FragilityService, MappingSet, HazardService, Earthquake
from pyincore.analyses.nonstructbuildingdamage import NonStructBuildingDamage, NonStructBuildingUtil
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    # Memphis 7.9 AB-95
    hazard_service = HazardService(client)
    earthquake = Earthquake.from_hazard_service("5b902cb273c3371e1236b36b", hazard_service)

    # Shelby County Essential Facilities
    building_dataset_id = "5a284f42c7d30d13bc0821ba"

    # Default Building Fragility Mapping v1.0
    mapping_id = "5b47b350337d4a3629076f2c"
    # Load fragility mapping
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))

    # use liquefaction (slow)
    # Shelby County Liquefaction Susceptibility
    use_liquefaction = True
    liq_geology_dataset_id = "5a284f55c7d30d13bc0824ba"

    # Acceleration sensitive
    non_structural_building_dmg_as = NonStructBuildingDamage(client)
    non_structural_building_dmg_as.load_remote_input_dataset("buildings", building_dataset_id)
    non_structural_building_dmg_as.set_input_dataset('dfr3_mapping_set', mapping_set)
    non_structural_building_dmg_as.set_input_hazard("hazard", earthquake)
    non_structural_building_dmg_as.set_parameter("result_name", "non_structural_building_dmg_result_w_hazard_obj_as")
    non_structural_building_dmg_as.set_parameter("num_cpu", 4)
    non_structural_building_dmg_as.set_parameter("fragility_key", NonStructBuildingUtil.DEFAULT_FRAGILITY_KEY_AS)
    non_structural_building_dmg_as.set_parameter("use_liquefaction", use_liquefaction)
    non_structural_building_dmg_as.set_parameter("liq_geology_dataset_id", liq_geology_dataset_id)
    non_structural_building_dmg_as.run_analysis()

    # Drift sensitive
    non_structural_building_dmg_ds = NonStructBuildingDamage(client)
    non_structural_building_dmg_ds.load_remote_input_dataset("buildings", building_dataset_id)
    non_structural_building_dmg_ds.set_input_dataset('dfr3_mapping_set', mapping_set)
    non_structural_building_dmg_ds.set_parameter("result_name", "non_structural_building_dmg_result_w_hazard_obj_ds")
    non_structural_building_dmg_ds.set_input_hazard("hazard", earthquake)
    non_structural_building_dmg_ds.set_parameter("num_cpu", 4)
    non_structural_building_dmg_ds.set_parameter("fragility_key", NonStructBuildingUtil.DEFAULT_FRAGILITY_KEY_DS)
    non_structural_building_dmg_ds.set_parameter("use_liquefaction", use_liquefaction)
    non_structural_building_dmg_ds.set_parameter("liq_geology_dataset_id", liq_geology_dataset_id)
    non_structural_building_dmg_ds.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
