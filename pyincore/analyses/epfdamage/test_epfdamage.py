from pyincore import InsecureIncoreClient
from pyincore.analyses.epfdamage import EpfDamage


def run_with_base_class():
    client = InsecureIncoreClient(
        "http://incore2-services-dev.ncsa.illinois.edu:8888", "incrtest")

    hazard_type = "earthquake"

    hazard_id = "5b902cb273c3371e1236b36b"

    epf_dataset_id = "5d4ae03a5648c4049cea28c7"

    # Earthquake mapping
    mapping_id = "5b47be72337d4a37ba8090e2"

    # Run Memphis earthquake building damage
    epf_dmg = EpfDamage(client)
    epf_dmg.load_remote_input_dataset("epfs", epf_dataset_id)

    result_name = "hazus_epf_dmg_result"
    # epf_dmg.set_parameter("fragility_key", "pga")
    epf_dmg.set_parameter("result_name", result_name)
    epf_dmg.set_parameter("mapping_id", mapping_id)
    epf_dmg.set_parameter("hazard_type", hazard_type)
    epf_dmg.set_parameter("hazard_id", hazard_id)
    epf_dmg.set_parameter("num_cpu", 1)

    # Run Analysis
    epf_dmg.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
