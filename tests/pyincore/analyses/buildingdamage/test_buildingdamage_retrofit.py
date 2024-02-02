import os

from pyincore import IncoreClient, MappingSet, Tornado, Dataset, HazardService, Flood
from pyincore.analyses.buildingdamage import BuildingDamage
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient()
    dev_client = IncoreClient(pyglobals.INCORE_API_DEV_URL)
    hazardsvc = HazardService(client)
    dev_hazardsvc = HazardService(dev_client)

    # ##############################
    # # dfr3 mapping
    # tornado_fragility_mapping_set = MappingSet.from_json_file(os.path.join(pyglobals.TEST_DATA_DIR,
    #                                                                        "retrofit/tornado_retrofit_mapping.json"))
    #
    # # Building Damage
    # # Create building damage
    # tornado_bldg_dmg = BuildingDamage(client)
    #
    # # Load input dataset
    # bldg_dataset_id = "5dbc8478b9219c06dd242c0d"  # joplin building v6 prod
    # tornado_bldg_dmg.load_remote_input_dataset("buildings", bldg_dataset_id)
    # retrofit_strategy_plan = Dataset.from_file(os.path.join(pyglobals.TEST_DATA_DIR,
    #                                                         "retrofit/tornado_retrofit_plan.csv"),
    #                                            data_type="incore:retrofitStrategy")
    # tornado_bldg_dmg.set_input_dataset("retrofit_strategy", retrofit_strategy_plan)
    #
    # tornado = Tornado.from_hazard_service("608c5b17150b5e17064030df", hazardsvc)
    # tornado_bldg_dmg.set_input_hazard("hazard", tornado)
    #
    # # Load fragility mapping
    # tornado_bldg_dmg.set_input_dataset("dfr3_mapping_set", tornado_fragility_mapping_set)
    #
    # # Set hazard
    # tornado_bldg_dmg.set_input_hazard("hazard", tornado)
    #
    # # Set analysis parameters
    result_folder = "retrofit"
    # if not os.path.exists(result_folder):
    #     os.mkdir(result_folder)
    # result_name = os.path.join(result_folder, "joplin_tornado_commerical_bldg_dmg_w_retrofit")
    # tornado_bldg_dmg.set_parameter("result_name", result_name)
    # tornado_bldg_dmg.set_parameter("num_cpu", 8)
    # tornado_bldg_dmg.run_analysis()

    ##############################
    # lumberton flood
    flood = Flood.from_hazard_service("5f4d02e99f43ee0dde768406", dev_hazardsvc)

    flood_fragility_mapping_set = MappingSet.from_json_file(os.path.join(pyglobals.TEST_DATA_DIR,
                                                                         "retrofit/flood_retrofit_mapping.json"))
    # lumberton building inventory v7
    bldg_dataset_id = "603010f7b1db9c28aef53214"  # 40 building subset
    # bldg_dataset_id = "603010a4b1db9c28aef5319f"  # 21k full building

    flood_bldg_dmg = BuildingDamage(dev_client)
    flood_bldg_dmg.load_remote_input_dataset("buildings", bldg_dataset_id)

    # lumberton building mapping (with equation)
    flood_bldg_dmg.set_input_dataset("dfr3_mapping_set", flood_fragility_mapping_set)
    flood_bldg_dmg.set_parameter("fragility_key", "Lumberton Flood Building Fragility ID Code")

    flood_bldg_dmg.set_input_hazard("hazard", flood)

    retrofit_strategy_plan = Dataset.from_file(os.path.join(pyglobals.TEST_DATA_DIR,
                                                            "retrofit/flood_retrofit_plan.csv"),
                                               data_type="incore:retrofitStrategy")
    flood_bldg_dmg.set_input_dataset("retrofit_strategy", retrofit_strategy_plan)

    result_name = "lumberton_flood_dmg_result_w_retrofit"
    flood_bldg_dmg.set_parameter("result_name", os.path.join(result_folder, result_name))
    flood_bldg_dmg.set_parameter("num_cpu", 8)
    flood_bldg_dmg.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
