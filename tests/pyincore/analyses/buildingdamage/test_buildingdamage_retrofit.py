import os

from pyincore import IncoreClient, MappingSet, Tornado, Dataset, HazardService
from pyincore.analyses.buildingdamage import BuildingDamage
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient()
    hazardsvc = HazardService(client)

    # dfr3 mapping
    fragility_mapping_set = MappingSet.from_json_file(os.path.join(pyglobals.TEST_DATA_DIR,
                                                                              "retrofit/tornado_retrofit_mapping.json"))

    # Building Damage
    # Create building damage
    bldg_dmg = BuildingDamage(client)

    # Load input dataset
    bldg_dataset_id = "5dbc8478b9219c06dd242c0d"  # joplin building v6 prod
    bldg_dmg.load_remote_input_dataset("buildings", bldg_dataset_id)
    retrofit_strategy_plan1 = Dataset.from_file(os.path.join(pyglobals.TEST_DATA_DIR,
                                                             "retrofit/tornado_retrofit_mapping.csv"),
                                                data_type="incore:retrofitStrategy")
    bldg_dmg.set_input_dataset("retrofit_strategy", retrofit_strategy_plan1)

    tornado = Tornado.from_hazard_service("608c5b17150b5e17064030df", hazardsvc)
    bldg_dmg.set_input_hazard("hazard", tornado)

    # Load fragility mapping
    bldg_dmg.set_input_dataset("dfr3_mapping_set", fragility_mapping_set)

    # Set hazard
    bldg_dmg.set_input_hazard("hazard", tornado)

    # Set analysis parameters
    result_folder = "retrofit"
    if not os.path.exists(result_folder):
        os.mkdir(result_folder)
    result_name = os.path.join(result_folder, "joplin_tornado_commerical_bldg_dmg_retrofitted")
    bldg_dmg.set_parameter("result_name", result_name)
    bldg_dmg.set_parameter("num_cpu", 2)
    bldg_dmg.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
