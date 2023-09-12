import os

from pyincore import IncoreClient, FragilityService, MappingSet, Hurricane
from pyincore.analyses.bridgedamage import BridgeDamage
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    # Galveston bridge
    bridge_dataset_id = "6062058ac57ada48e48c31e3"

    # Galveston hurricane bridge mapping
    refactored_mapping_id = "6062254b618178207f66226c"

    # Create bridge damage
    bridge_dmg = BridgeDamage(client)

    # Load input datasets
    bridge_dmg.load_remote_input_dataset("bridges", bridge_dataset_id)

    # Load fragility mapping
    fragility_service = FragilityService(client)
    refactored_mapping_set = MappingSet(fragility_service.get_mapping(refactored_mapping_id))
    bridge_dmg.set_input_dataset('dfr3_mapping_set', refactored_mapping_set)

    # try local hurricane
    # test with local hurricane
    hurricane = Hurricane.from_json_file(os.path.join(pyglobals.TEST_DATA_DIR, "hurricane-dataset.json"))
    hurricane.hazardDatasets[0].from_file(os.path.join(pyglobals.TEST_DATA_DIR, "Wave_Raster.tif"),
                                          data_type="ncsa:probabilisticHurricaneRaster")
    # Optional: set threshold to determine exposure or not
    hurricane.hazardDatasets[0].set_threshold(threshold_value=0.3, threshold_unit="m")

    hurricane.hazardDatasets[1].from_file(os.path.join(pyglobals.TEST_DATA_DIR, "Surge_Raster.tif"),
                                          data_type="ncsa:probabilisticHurricaneRaster")
    # Optional: set threshold to determine exposure or not
    hurricane.hazardDatasets[0].set_threshold(threshold_value=0.3, threshold_unit="m")

    hurricane.hazardDatasets[2].from_file(os.path.join(pyglobals.TEST_DATA_DIR, "Inundation_Raster.tif"),
                                          data_type="ncsa:probabilisticHurricaneRaster")
    # Optional: set threshold to determine exposure or not
    hurricane.hazardDatasets[2].set_threshold(threshold_value=1, threshold_unit="hr")

    bridge_dmg.set_input_hazard("hazard", hurricane)

    # Set analysis parameters
    bridge_dmg.set_parameter("fragility_key", "Hurricane SurgeLevel and WaveHeight Fragility ID Code")
    bridge_dmg.set_parameter("result_name", "galveston_bridge_dmg_result_local_hazard")

    bridge_dmg.set_parameter("num_cpu", 4)

    # Run bridge damage analysis
    bridge_dmg.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
