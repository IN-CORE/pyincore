from pyincore import InsecureIncoreClient
from pyincore.analyses.buildingdamage import BuildingDamage


def run_with_base_class():
    client = InsecureIncoreClient(
        "http://incore2-services-dev.ncsa.illinois.edu:8888", "incrtest")

    # Memphis Earthquake damage
    # New madrid earthquake using Atkinson Boore 1995
    hazard_type = "earthquake"
    hazard_id = "5b902cb273c3371e1236b36b"

    # Building damage ratios
    dmg_ratio_id = "5a284f2ec7d30d13bc08209a"
    # Building dataset
    # 5a284f0bc7d30d13bc081a28  5kb
    # 5bcf2fcbf242fe047ce79dad 300kb
    # 5a284f37c7d30d13bc08219c 20mb
    bldg_dataset_id = "5a284f0bc7d30d13bc081a28"

    # Earthquake mapping
    mapping_id = "5b47b350337d4a3629076f2c"
    bldg_dmg = BuildingDamage(client)
    bldg_dmg.load_remote_input_dataset("buildings", bldg_dataset_id)
    bldg_dmg.load_remote_input_dataset("dmg_ratios", dmg_ratio_id)

    result_name = "memphis_bldg_dmg_result"
    bldg_dmg.set_parameter("result_name", result_name)
    bldg_dmg.set_parameter("mapping_id", mapping_id)
    bldg_dmg.set_parameter("hazard_type", hazard_type)
    bldg_dmg.set_parameter("hazard_id", hazard_id)
    bldg_dmg.set_parameter("num_cpu", 1)

    # Run Analysis
    bldg_dmg.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
