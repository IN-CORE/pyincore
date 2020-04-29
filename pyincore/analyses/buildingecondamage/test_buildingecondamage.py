from pyincore import IncoreClient
from pyincore.analyses.buildingecondamage import BuildingEconDamage


def run_with_base_class():
    client = IncoreClient()

    bldg_edmg = BuildingEconDamage(client)
    # Memphis Earthquake damage
    # New madrid earthquake using Atkinson Boore 1995
    hazard_type = "earthquake"
    hazard_id = "5b902cb273c3371e1236b36b"

    # Building dataset
    # 5a284f0bc7d30d13bc081a28  5kb
    # 5bcf2fcbf242fe047ce79dad 300kb
    # 5a284f37c7d30d13bc08219c 20mb
    #bldg_dataset_id = "5a284f0bc7d30d13bc081a28"
    bldg_dataset_id = "5df40388b9219c06cf8b0c80"

    # Earthquake mapping
    mapping_id = "5b47b350337d4a3629076f2c"
    bldg_dmg = BuildingEconDamage(client)
    bldg_dmg.load_remote_input_dataset("buildings", bldg_dataset_id)

    # # load datasets locally
    # building_damage_mcs_samples = Dataset.from_file("./Joplin_mcs_buildings_samples.csv", "incore:buildingDamageMcSamples")
    # bldg_func.set_input_dataset("building_damage_mcs_samples", building_damage_mcs_samples)
    # substations_damage_mcs_samples = Dataset.from_file("./Joplin_mcs_substations_samples.csv","incore:substationsDamageMcSamples")
    # bldg_func.set_input_dataset("substations_damage_mcs_samples", substations_damage_mcs_samples)
    # poles_damage_mcs_samples = Dataset.from_file("./Joplin_mcs_poles_samples.csv", "incore:polesDamageMcSamples")
    # bldg_func.set_input_dataset("poles_damage_mcs_samples", poles_damage_mcs_samples)
    # bldg_func.load_remote_input_dataset("interdependency_dictionary", "5defc8c663a6cc000172b2a9")

    result_name = "memphis_bldg_edmg_result"
    bldg_edmg.set_parameter("result_name", result_name)
    bldg_edmg.set_parameter("mapping_id", mapping_id)
    bldg_edmg.set_parameter("hazard_type", hazard_type)
    bldg_edmg.set_parameter("hazard_id", hazard_id)
    bldg_edmg.set_parameter("num_cpu", 1)

    # Run Analysis
    bldg_edmg.run_analysis()


if __name__ == '__main__':
    import time
    start_time = time.time()

    run_with_base_class()

    end_time = time.time()
    elapsed = end_time - start_time
    print("Execution time: {:.2f}".format(elapsed) + "s")
