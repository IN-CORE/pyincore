from pyincore import IncoreClient
from pyincore.analyses.buildingfunctionality.buildingfunctionality import BuildingFunctionality
from pyincore.dataset import Dataset

import time


def run_with_base_class():
    client = IncoreClient()
    bldg_func = BuildingFunctionality(client)

    # load datasets locally
    building_damage_mcs_samples = Dataset.from_file("/Users/diegoac2/Downloads/Joplin_mcs_buildings_samples.csv",
                                                    "ergo:buildingDamage")
    bldg_func.set_input_dataset("building_damage_mcs_samples", building_damage_mcs_samples)

    substations_damage_mcs_samples = Dataset.from_file("/Users/diegoac2/Downloads/Joplin_mcs_substations_samples.csv",
                                                       "incore:substationsDamage")
    bldg_func.set_input_dataset("substations_damage_mcs_samples", substations_damage_mcs_samples)

    poles_damage_mcs_samples = Dataset.from_file("/Users/diegoac2/Downloads/Joplin_mcs_poles_samples.csv",
                                                 "incore:polesDamage")
    bldg_func.set_input_dataset("poles_damage_mcs_samples", poles_damage_mcs_samples)

    bldg_func.load_remote_input_dataset("interdependency_dictionary", "5dcf4a34b9219ca5e4118312")

    bldg_func.set_parameter("result_name", "Joplin_mcs_functionality_probability")
    bldg_func.set_parameter("num_samples", 10000)

    start_time = time.time()
    bldg_func.run_analysis()
    print("--- %s seconds ---" % (time.time() - start_time))


if __name__ == '__main__':
    run_with_base_class()
