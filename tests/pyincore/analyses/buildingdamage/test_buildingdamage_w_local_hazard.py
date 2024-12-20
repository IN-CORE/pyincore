import os

from pyincore import IncoreClient, FragilityService, MappingSet, Hurricane, Tornado
from pyincore.analyses.buildingdamage import BuildingDamage
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    # try local hurricane
    # test with local hurricane
    hurricane = Hurricane.from_json_file(
        os.path.join(pyglobals.TEST_DATA_DIR, "hurricane-dataset.json")
    )
    hurricane.hazardDatasets[0].from_file(
        os.path.join(pyglobals.TEST_DATA_DIR, "Wave_Raster.tif"),
        data_type="ncsa:probabilisticHurricaneRaster",
    )
    # Optional: set threshold to determine exposure or not
    hurricane.hazardDatasets[0].set_threshold(threshold_value=0.3, threshold_unit="m")

    hurricane.hazardDatasets[1].from_file(
        os.path.join(pyglobals.TEST_DATA_DIR, "Surge_Raster.tif"),
        data_type="ncsa:probabilisticHurricaneRaster",
    )
    # Optional: set threshold to determine exposure or not
    hurricane.hazardDatasets[0].set_threshold(threshold_value=0.3, threshold_unit="m")

    hurricane.hazardDatasets[2].from_file(
        os.path.join(pyglobals.TEST_DATA_DIR, "Inundation_Raster.tif"),
        data_type="ncsa:probabilisticHurricaneRaster",
    )
    # Optional: set threshold to determine exposure or not
    hurricane.hazardDatasets[2].set_threshold(threshold_value=1, threshold_unit="hr")

    # Galveston building dataset 602eba8bb1db9c28aef01358
    bldg_dataset_id = "602eba8bb1db9c28aef01358"  # 19k buildings with age_group

    bldg_dmg = BuildingDamage(client)
    bldg_dmg.load_remote_input_dataset("buildings", bldg_dataset_id)

    # Hurricane building mapping (with equation)
    mapping_id = "602c381a1d85547cdc9f0675"
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    bldg_dmg.set_input_dataset("dfr3_mapping_set", mapping_set)
    bldg_dmg.set_parameter(
        "fragility_key", "Hurricane SurgeLevel and WaveHeight Fragility ID Code"
    )

    bldg_dmg.set_input_hazard("hazard", hurricane)

    result_folder = "local_hazard"
    if not os.path.exists(result_folder):
        os.mkdir(result_folder)
    result_name = os.path.join(result_folder, "galveston_local_hurr_dmg_result")
    bldg_dmg.set_parameter("result_name", result_name)
    bldg_dmg.set_parameter("num_cpu", 4)
    bldg_dmg.run_analysis()

    ###########################
    # local tornado
    tornado = Tornado.from_json_file(
        os.path.join(pyglobals.TEST_DATA_DIR, "tornado_dataset.json")
    )

    # attach dataset from local file
    tornado.hazardDatasets[0].from_file(
        (os.path.join(pyglobals.TEST_DATA_DIR, "joplin_tornado/joplin_path_wgs84.shp")),
        data_type="incore:tornadoWindfield",
    )

    bldg_dataset_id = "5df7d0de425e0b00092d0082"

    bldg_dmg = BuildingDamage(client)
    bldg_dmg.load_remote_input_dataset("buildings", bldg_dataset_id)

    mapping_id = "5e8e3a21eaa8b80001f04f1c"
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    bldg_dmg.set_input_dataset("dfr3_mapping_set", mapping_set)

    bldg_dmg.set_input_hazard("hazard", tornado)

    result_folder = "local_hazard"
    if not os.path.exists(result_folder):
        os.mkdir(result_folder)
    result_name = os.path.join(result_folder, "joplin_tornado_bldg_dmg")
    bldg_dmg.set_parameter("result_name", result_name)
    bldg_dmg.set_parameter("num_cpu", 4)
    bldg_dmg.run_analysis()


if __name__ == "__main__":
    run_with_base_class()
