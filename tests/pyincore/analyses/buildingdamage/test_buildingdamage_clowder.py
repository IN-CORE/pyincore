from pyincore import IncoreClient, FragilityService, MappingSet, ClowderClient, Dataset, ClowderDataService
from pyincore.analyses.buildingdamage import BuildingDamage
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    # Memphis Earthquake damage
    # New madrid earthquake using Atkinson Boore 1995
    hazard_type = "earthquake"
    hazard_id = "5b902cb273c3371e1236b36b"

    # Building dataset clowder id
    clowder_client = ClowderClient(service_url="https://clowder.ncsa.illinois.edu/clowder/",
                                   token_file_name=".clowderapikey")
    # clowder_client.clear_cache()
    datasvc_clowder = ClowderDataService(clowder_client)
    buildings = Dataset.from_clowder_service("63755d06e4b0a2eb0196b5cb", datasvc_clowder)

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
    bldg_dmg.set_parameter("use_liquefaction", False)

    # Run Analysis
    bldg_dmg.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
