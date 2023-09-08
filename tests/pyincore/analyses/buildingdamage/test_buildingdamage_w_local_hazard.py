import os

from pyincore import FragilityService, MappingSet, Hurricane, IncoreClient
from pyincore.analyses.buildingdamage import BuildingDamage
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    # Galveston building dataset 602eba8bb1db9c28aef01358
    bldg_dataset_id = "602eba8bb1db9c28aef01358"  # 19k buildings with age_group

    bldg_dmg = BuildingDamage(client)
    bldg_dmg.load_remote_input_dataset("buildings", bldg_dataset_id)

    # Hurricane building mapping (with equation)
    mapping_id = "602c381a1d85547cdc9f0675"
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    bldg_dmg.set_input_dataset('dfr3_mapping_set', mapping_set)
    bldg_dmg.set_parameter("fragility_key", "Hurricane SurgeLevel and WaveHeight Fragility ID Code")

    # test with local hurricane
    hurricane = Hurricane.from_json_file(os.path.join(pyglobals.TEST_DATA_DIR, "hurricane-dataset.json"))
    hurricane.hazardDatasets[0].from_file((os.path.join(pyglobals.TEST_DATA_DIR, "Wave_Raster.tif")))
    hurricane.hazardDatasets[1].from_file(os.path.join(pyglobals.TEST_DATA_DIR, "Surge_Raster.tif"))
    hurricane.hazardDatasets[2].from_file(os.path.join(pyglobals.TEST_DATA_DIR, "Inundation_Raster.tif"))
    bldg_dmg.set_input_hazard("hazard", hurricane)

    result_name = "galveston_hurr_dmg_result"
    bldg_dmg.set_parameter("result_name", result_name)
    bldg_dmg.set_parameter("num_cpu", 4)
    bldg_dmg.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
