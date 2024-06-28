import os

from pyincore import IncoreClient, MappingSet, Tornado, Dataset, HazardService
from pyincore.analyses.buildingstructuraldamage.buildingstructuraldamage import (
    BuildingStructuralDamage,
)
import pyincore.globals as pyglobals
import time


def run_with_base_class():
    client = IncoreClient()
    hazardsvc = HazardService(client)

    # Set analysis parameters
    result_folder = "retrofit"
    if not os.path.exists(result_folder):
        os.mkdir(result_folder)

    start_time = time.time()
    ##############################
    # joplin tornado
    # dfr3 mapping
    tornado_fragility_mapping_set = MappingSet.from_json_file(
        os.path.join(pyglobals.TEST_DATA_DIR, "retrofit/tornado_retrofit_mapping.json")
    )

    # Building Damage
    # Create building damage
    tornado_bldg_dmg = BuildingStructuralDamage(client)

    # Load input dataset
    bldg_dataset_id = "5dbc8478b9219c06dd242c0d"  # joplin building v6 prod
    tornado_bldg_dmg.load_remote_input_dataset("buildings", bldg_dataset_id)
    retrofit_strategy_plan = Dataset.from_file(
        os.path.join(pyglobals.TEST_DATA_DIR, "retrofit/tornado_retrofit_plan.csv"),
        data_type="incore:retrofitStrategy",
    )
    tornado_bldg_dmg.set_input_dataset("retrofit_strategy", retrofit_strategy_plan)

    tornado = Tornado.from_hazard_service("608c5b17150b5e17064030df", hazardsvc)
    tornado_bldg_dmg.set_input_hazard("hazard", tornado)

    # Load fragility mapping
    tornado_bldg_dmg.set_input_dataset(
        "dfr3_mapping_set", tornado_fragility_mapping_set
    )

    # Set hazard
    tornado_bldg_dmg.set_input_hazard("hazard", tornado)

    result_name = os.path.join(
        result_folder, "joplin_tornado_commerical_bldg_dmg_w_retrofit"
    )
    tornado_bldg_dmg.set_parameter("result_name", result_name)
    tornado_bldg_dmg.set_parameter("num_cpu", 8)
    tornado_bldg_dmg.run_analysis()

    end_time_1 = time.time()
    print(
        f"Joplin Tornado Retrofit execution time: {end_time_1 - start_time:.5f} seconds"
    )


if __name__ == "__main__":
    run_with_base_class()
