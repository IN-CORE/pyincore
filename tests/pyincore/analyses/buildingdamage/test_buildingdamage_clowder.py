from pyincore import IncoreClient, FragilityService, MappingSet, ClowderClient, Dataset, ClowderDataService
from pyincore.analyses.buildingdamage import BuildingDamage
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    # Memphis Earthquake damage
    # New madrid earthquake using Atkinson Boore 1995
    hazard_type = "earthquake"
    hazard_id = "5b902cb273c3371e1236b36b"

    # Geology dataset
    liq_geology_dataset_id = "5a284f53c7d30d13bc08249c"

    # Building dataset clowder id
    clowder_client = ClowderClient(service_url="http://localhost:8000/", token_file_name=".clowderapikey")
    datasvc_clowder = ClowderDataService(clowder_client)
    clowder_bldg_dataset_id = "63750d33e4b0e6b66b32f56b"
    buildings = Dataset.from_clowder_service(clowder_bldg_dataset_id, datasvc_clowder)

    bldg_dmg = BuildingDamage(client)

    # Earthquake mapping
    mapping_id = "5b47b350337d4a3629076f2c"
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    bldg_dmg.set_input_dataset('dfr3_mapping_set', mapping_set)

    bldg_dmg.set_input_dataset('buildings', buildings)

    result_name = "clowder_memphis_eq_bldg_dmg_result"
    bldg_dmg.set_parameter("result_name", result_name)
    bldg_dmg.set_parameter("hazard_type", hazard_type)
    bldg_dmg.set_parameter("hazard_id", hazard_id)
    bldg_dmg.set_parameter("num_cpu", 4)
    bldg_dmg.set_parameter("use_liquefaction", True)
    bldg_dmg.set_parameter("liquefaction_geology_dataset_id", liq_geology_dataset_id)

    # Run Analysis
    bldg_dmg.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
