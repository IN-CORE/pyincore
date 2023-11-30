import os

from pyincore import IncoreClient, FragilityCurveSet, MappingSet, Tornado, GeoUtil, Dataset, Mapping, FragilityService
from pyincore.analyses.buildingdamage import BuildingDamage
import pyincore.globals as pyglobals
import pandas as pd
import geopandas as gpd


def run_with_base_class():
    client = IncoreClient(offline=True)
    # client = IncoreClient(pyglobals.INCORE_API_DEV_URL)
    # client.clear_cache()

    # building
    buildings = Dataset.from_file(os.path.join(pyglobals.TEST_DATA_DIR,
                                               "building/joplin_commercial_bldg_v6_sample.shp"),
                                  data_type="ergo:buildingInventoryVer6")

    # tornado
    tornado = Tornado.from_json_file(os.path.join(pyglobals.TEST_DATA_DIR, "tornado_dataset.json"))
    tornado.hazardDatasets[0].from_file((os.path.join(pyglobals.TEST_DATA_DIR, "joplin_tornado/joplin_path_wgs84.shp")),
                                        data_type="incore:tornadoWindfield")
    # dfr3
    fragility_archetype_6 = FragilityCurveSet.from_json_file(os.path.join(pyglobals.TEST_DATA_DIR,
                                                                          "fragility_curves/fragility_archetype_6.json"))
    fragility_archetype_7 = FragilityCurveSet.from_json_file(os.path.join(pyglobals.TEST_DATA_DIR,
                                                                          "fragility_curves/fragility_archetype_7.json"))

    fragility_entry_archetype_6 = {"Non-Retrofit Fragility ID Code": fragility_archetype_6}
    fragility_rules_archetype_6 = {"OR": ["int archetype EQUALS 6"]}
    fragility_mapping_archetype_6 = Mapping(fragility_entry_archetype_6, fragility_rules_archetype_6)
    fragility_entry_archetype_7 = {"Non-Retrofit Fragility ID Code": fragility_archetype_7}
    fragility_rules_archetype_7 = {"OR": ["int archetype EQUALS 7"]}
    fragility_mapping_archetype_7 = Mapping(fragility_entry_archetype_7, fragility_rules_archetype_7)

    fragility_mapping_set_definition = {
        "id": "N/A",
        "name": "local joplin tornado fragility mapping object",
        "hazardType": "tornado",
        "inventoryType": "building",
        'mappings': [
            fragility_mapping_archetype_6,
            fragility_mapping_archetype_7,
        ],
        "mappingType": "fragility"
    }

    fragility_mapping_set = MappingSet(fragility_mapping_set_definition)

    # Building Damage
    # Create building damage
    bldg_dmg = BuildingDamage(client)

    # Load input dataset
    bldg_dmg.set_input_dataset("buildings", buildings)

    # Load fragility mapping
    fragility_service = FragilityService(client)
    bldg_dmg.set_input_dataset("dfr3_mapping_set", fragility_mapping_set)

    # Set hazard
    bldg_dmg.set_input_hazard("hazard", tornado)

    # Set analysis parameters
    result_folder = "offline"
    # result_folder = "online"
    if not os.path.exists(result_folder):
        os.mkdir(result_folder)
    result_name = os.path.join(result_folder, "joplin_tornado_commerical_bldg_dmg")
    bldg_dmg.set_parameter("result_name", result_name)
    bldg_dmg.set_parameter("num_cpu", 2)
    bldg_dmg.run_analysis()

    if __name__ == '__main__':
        run_with_base_class()
