from pyincore import IncoreClient
from pyincore.analyses.epfdamage import EpfDamage


def run_with_base_class():
    client = IncoreClient()

    hazard_type = "earthquake"

    hazard_id = "5d3b6a31b9219cf53284c73d"

    epf_dataset_id = "5d263f08b9219cf93c056c68"

    # Earthquake mapping
    mapping_id = "5d489aa1b9219c0689f1988e"

    # Run epf damage
    epf_dmg = EpfDamage(client)

    epf_dmg.load_remote_input_dataset("epfs", epf_dataset_id)

    epf_dmg.set_parameter("result_name", "earthquake_epf_dmg_result")
    epf_dmg.set_parameter("mapping_id", mapping_id)
    epf_dmg.set_parameter("hazard_type", hazard_type)
    epf_dmg.set_parameter("hazard_id", hazard_id)
    epf_dmg.set_parameter("num_cpu", 1)

    # Run Analysis
    epf_dmg.run_analysis()

    hazard_type = "tsunami"

    hazard_id = "5bc9eaf7f7b08533c7e610e1"

    epf_dataset_id = "5d263f08b9219cf93c056c68"

    # Tsunami mapping
    mapping_id = "5d489acfb9219c0689f19891"

    # Run epf damage
    epf_dmg = EpfDamage(client)
    epf_dmg.load_remote_input_dataset("epfs", epf_dataset_id)

    epf_dmg.set_parameter("result_name", "tsunami_epf_dmg_result")
    epf_dmg.set_parameter("mapping_id", mapping_id)
    epf_dmg.set_parameter("hazard_type", hazard_type)
    epf_dmg.set_parameter("hazard_id", hazard_id)
    epf_dmg.set_parameter("num_cpu", 1)

    # Run Analysis
    epf_dmg.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
