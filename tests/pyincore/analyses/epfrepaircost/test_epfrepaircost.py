from pyincore import IncoreClient, Dataset
from pyincore.analyses.epfrepaircost import EpfRepairCost
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)
    # client = IncoreClient()

    epf_repair_cost = EpfRepairCost(client)

    # Seaside EPF
    epf_repair_cost.load_remote_input_dataset("epfs", "5eebcaa17a00803abc85ec11")  # dev
    # epf_repair_cost.load_remote_input_dataset("epfs", "5d263f08b9219cf93c056c68")  # prod

    epf_repair_cost.load_remote_input_dataset("replacement_cost", "6470c09a5bc8b26ddf99bb59")

    # can be chained with MCS
    epf_repair_cost.load_remote_input_dataset("sample_damage_states", "6470c23d5bc8b26ddf99bb65")

    # substation_dmg_ratios
    epf_repair_cost.load_remote_input_dataset("epf_dmg_ratios", "6470c1c35bc8b26ddf99bb5f")

    epf_repair_cost.set_parameter("result_name", "seaside_epf")
    epf_repair_cost.set_parameter("num_cpu", 4)

    # Run Analysis
    epf_repair_cost.run_analysis()


if __name__ == "__main__":
    run_with_base_class()
