from pyincore import InsecureIncoreClient
from pyincore.analyses.buildingdamage import BuildingDamage


def run_with_base_class():
    client = InsecureIncoreClient(
        "http://incore2-services.ncsa.illinois.edu:8888", "incrtest")

    # EQ Building Dataset - Memphis Hospitals
    bldg_dataset_id = "5a284f0bc7d30d13bc081a28"

    # New madrid earthquake using Atkinson Boore 1995
    hazard_type = "earthquake"
    hazard_id = "5b902cb273c3371e1236b36b"

    # Building damage ratios
    dmg_ratio_id = "5a284f2ec7d30d13bc08209a"

    bldg_dataset_id = "5a284f0bc7d30d13bc081a28"

    # Earthquake mapping
    mapping_id = "5b47b350337d4a3629076f2c"

    # Run Memphis earthquake building damage
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

    # Seaside example Tsunami
    hazard_type = "tsunami"
    hazard_id = "5bc9e25ef7b08533c7e610dc"

    # Seaside building dataset
    bldg_dataset_id = "5bcf2fcbf242fe047ce79dad"

    # Tsunami mapping
    mapping_id = "5b48fb1f337d4a478e7bd54d"

    # Run seaside tsunami building damage
    bldg_dmg = BuildingDamage(client)
    bldg_dmg.load_remote_input_dataset("buildings", bldg_dataset_id)
    bldg_dmg.load_remote_input_dataset("dmg_ratios", dmg_ratio_id)
    result_name = "seaside_bldg_dmg_result"
    bldg_dmg.set_parameter("result_name", result_name)
    bldg_dmg.set_parameter("mapping_id", mapping_id)
    bldg_dmg.set_parameter("hazard_type", hazard_type)
    bldg_dmg.set_parameter("hazard_id", hazard_id)
    bldg_dmg.set_parameter("num_cpu", 1)
    bldg_dmg.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
