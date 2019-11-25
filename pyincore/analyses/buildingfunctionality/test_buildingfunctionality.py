from pyincore import IncoreClient
from pyincore.analyses.buildingfunctionality.buildingfunctionality import BuildingFunctionality

import time


def run_with_base_class():
    client = IncoreClient()
    bldg_func = BuildingFunctionality(client)
    bldg_func.load_remote_input_dataset("building_damage_mcs_samples", "5dcc8a02b9219ca5e4068ce9")
    bldg_func.load_remote_input_dataset("substations_damage_mcs_samples", "5dcc8f44b9219ca5e4078b82")
    bldg_func.load_remote_input_dataset("poles_damage_mcs_samples", "5dcc8f94b9219ca5e4088a1c")

    bldg_func.load_remote_input_dataset("interdependency_dictionary", "5dcf4a34b9219ca5e4118312")

    bldg_func.set_parameter("result_name", "Joplin_mcs_functionality_probability")
    bldg_func.set_parameter("num_samples", 10000)

    start_time = time.time()
    bldg_func.run_analysis()
    print("--- %s seconds ---" % (time.time() - start_time))


if __name__ == '__main__':
    run_with_base_class()
