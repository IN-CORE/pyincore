import os

from pyincore import IncoreClient, FragilityService, MappingSet, Hurricane, Tornado, HazardService
from pyincore.models.hazard.localearthquake import LocalEarthquake
from pyincore.analyses.buildingdamage import BuildingDamage
import pyincore.globals as pyglobals


def run_with_base_class():
    # payload = [
    #     {
    #         "demands": ["PGA"],
    #         "units": ["g"],
    #         "loc": "35.84,-89.90",
    #     },
    # ]
    #
    # metadata = {
    #     "name": "Memphis EQ Model",
    #     "description": "Memphis model based hazard",
    #     "eqType": "model",
    #     "attenuations": {
    #         "BooreStewartSeyhanAtkinson2014": "1.0"
    #     },
    #     "eqParameters": {
    #         "srcLatitude": "35.927",
    #         "srcLongitude": "-89.919",
    #         "magnitude": "7.9",
    #         "depth": "10.0",
    #         "eventType": "interface",
    #         "dipAngle": "83",
    #         "coseismicRuptureDepth": "0.0",
    #         "faultTypeMap": {
    #             "BooreStewartSeyhanAtkinson2014": "Strike-Slip"
    #         }
    #     },
    #     "visualizationParameters": {
    #         "demandType": "PGA",
    #         "demandUnits": "g",
    #         "minX": "-90.3099",
    #         "minY": "34.9942",
    #         "maxX": "-89.6231",
    #         "maxY": "35.4129",
    #         "numPoints": "1025",
    #         "amplifyHazard": "true"
    #     }
    # }

    payload = [
        {
            "demands": ["0.24 SA"],
            "units": ["g"],
            "loc": "35.29444,-90.05",
        },
    ]

    metadata = {
        "name": "Memphis EQ Model",
        "description": "Memphis model based hazard",
        "eqType": "model",
        "attenuations": {
            "ChiouYoungs2014": "1.0"
        },
        "eqParameters": {
            "srcLatitude": "35.927",
            "srcLongitude": "-89.919",
            "magnitude": "7.9",
            "depth": "10.0",
            "eventType": "interface",
            "dipAngle": "60",
            "coseismicRuptureDepth": "3.0",
            "faultTypeMap": {
                "ChiouYoungs2014": "Strike-Slip"
            }
        },
        "visualizationParameters": {
            "demandType": "PGA",
            "demandUnits": "g",
            "minX": "-90.3099",
            "minY": "34.9942",
            "maxX": "-89.6231",
            "maxY": "35.4129",
            "numPoints": "1025",
            "amplifyHazard": "true"
        }
    }

    local_eq = LocalEarthquake(metadata, )
    local_eq.read_hazard_values(payload)
    # local_eq.read_hazard_values_pypsha(payload)
    # client = IncoreClient(pyglobals.INCORE_API_DEV_URL)
    #
    # # try local hurricane
    # # test with local hurricane
    # hurricane = Hurricane.from_json_file(
    #     os.path.join(pyglobals.TEST_DATA_DIR, "hurricane-dataset.json")
    # )
    # hurricane.hazardDatasets[0].from_file(
    #     os.path.join(pyglobals.TEST_DATA_DIR, "Wave_Raster.tif"),
    #     data_type="ncsa:probabilisticHurricaneRaster",
    # )
    # # Optional: set threshold to determine exposure or not
    # hurricane.hazardDatasets[0].set_threshold(threshold_value=0.3, threshold_unit="m")
    #
    # hurricane.hazardDatasets[1].from_file(
    #     os.path.join(pyglobals.TEST_DATA_DIR, "Surge_Raster.tif"),
    #     data_type="ncsa:probabilisticHurricaneRaster",
    # )
    # # Optional: set threshold to determine exposure or not
    # hurricane.hazardDatasets[0].set_threshold(threshold_value=0.3, threshold_unit="m")
    #
    # hurricane.hazardDatasets[2].from_file(
    #     os.path.join(pyglobals.TEST_DATA_DIR, "Inundation_Raster.tif"),
    #     data_type="ncsa:probabilisticHurricaneRaster",
    # )
    # # Optional: set threshold to determine exposure or not
    # hurricane.hazardDatasets[2].set_threshold(threshold_value=1, threshold_unit="hr")
    #
    # # Galveston building dataset 602eba8bb1db9c28aef01358
    # bldg_dataset_id = "602eba8bb1db9c28aef01358"  # 19k buildings with age_group
    #
    # bldg_dmg = BuildingDamage(client)
    # bldg_dmg.load_remote_input_dataset("buildings", bldg_dataset_id)
    #
    # # Hurricane building mapping (with equation)
    # mapping_id = "602c381a1d85547cdc9f0675"
    # fragility_service = FragilityService(client)
    # mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    # bldg_dmg.set_input_dataset("dfr3_mapping_set", mapping_set)
    # bldg_dmg.set_parameter(
    #     "fragility_key", "Hurricane SurgeLevel and WaveHeight Fragility ID Code"
    # )
    #
    # bldg_dmg.set_input_hazard("hazard", hurricane)
    #
    # result_folder = "local_hazard"
    # if not os.path.exists(result_folder):
    #     os.mkdir(result_folder)
    # result_name = os.path.join(result_folder, "galveston_local_hurr_dmg_result")
    # bldg_dmg.set_parameter("result_name", result_name)
    # bldg_dmg.set_parameter("num_cpu", 4)
    # bldg_dmg.run_analysis()
    #
    # ###########################
    # # local tornado
    # tornado = Tornado.from_json_file(
    #     os.path.join(pyglobals.TEST_DATA_DIR, "tornado_dataset.json")
    # )
    #
    # # attach dataset from local file
    # tornado.hazardDatasets[0].from_file(
    #     (os.path.join(pyglobals.TEST_DATA_DIR, "joplin_tornado/joplin_path_wgs84.shp")),
    #     data_type="incore:tornadoWindfield",
    # )
    #
    # bldg_dataset_id = "5df7d0de425e0b00092d0082"
    #
    # bldg_dmg = BuildingDamage(client)
    # bldg_dmg.load_remote_input_dataset("buildings", bldg_dataset_id)
    #
    # mapping_id = "5e8e3a21eaa8b80001f04f1c"
    # fragility_service = FragilityService(client)
    # mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    # bldg_dmg.set_input_dataset("dfr3_mapping_set", mapping_set)
    #
    # bldg_dmg.set_input_hazard("hazard", tornado)
    #
    # result_folder = "local_hazard"
    # if not os.path.exists(result_folder):
    #     os.mkdir(result_folder)
    # result_name = os.path.join(result_folder, "joplin_tornado_bldg_dmg")
    # bldg_dmg.set_parameter("result_name", result_name)
    # bldg_dmg.set_parameter("num_cpu", 4)
    # bldg_dmg.run_analysis()

    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)
    hazardsvc = HazardService(client)

    ##########################################################
    # Memphis Earthquake damage
    # New madrid earthquake using Atkinson Boore 1995
    # eq = Earthquake.from_hazard_service("5b902cb273c3371e1236b36b", hazardsvc)

    # Geology dataset
    # liq_geology_dataset_id = "5a284f53c7d30d13bc08249c"

    # Building dataset
    # 5a284f0bc7d30d13bc081a28  5kb
    # 5bcf2fcbf242fe047ce79dad 300kb
    # 5a284f37c7d30d13bc08219c 20mb
    bldg_dataset_id = "5a284f0bc7d30d13bc081a28"

    bldg_dmg = BuildingDamage(client)
    bldg_dmg.load_remote_input_dataset("buildings", bldg_dataset_id)

    # Earthquake mapping
    mapping_id = "5b47b350337d4a3629076f2c"
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    bldg_dmg.set_input_dataset("dfr3_mapping_set", mapping_set)

    bldg_dmg.set_input_hazard("hazard", local_eq)

    result_name = "memphis_eq_bldg_dmg_result"
    bldg_dmg.set_parameter("result_name", result_name)
    bldg_dmg.set_parameter("num_cpu", 1)
    bldg_dmg.set_parameter("use_liquefaction", False)
    # bldg_dmg.set_parameter("liquefaction_geology_dataset_id", liq_geology_dataset_id)

    # Run Analysis
    bldg_dmg.run_analysis()


if __name__ == "__main__":
    run_with_base_class()
