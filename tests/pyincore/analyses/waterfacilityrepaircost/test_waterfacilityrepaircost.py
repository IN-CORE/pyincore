from pyincore import IncoreClient
from pyincore.analyses.waterfacilityrepaircost import WaterFacilityRepairCost
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    wf_repair_cost = WaterFacilityRepairCost(client)

    # Seaside wf
    wf_repair_cost.load_remote_input_dataset("water_facilities", "647644fe5bc8b26ddf9c5ddb")  # dev

    wf_repair_cost.load_remote_input_dataset("replacement_cost", "647645c75bc8b26ddf9c8f66")

    # can be chained with MCS
    wf_repair_cost.load_remote_input_dataset("sample_damage_states", "647646bb5bc8b26ddf9cb775")

    # dmg ratiose
    wf_repair_cost.load_remote_input_dataset("wf_dmg_ratios", "647646705bc8b26ddf9cb747")

    wf_repair_cost.set_parameter("result_name", "seaside_wf")
    wf_repair_cost.set_parameter("num_cpu", 4)

    # Run Analysis
    wf_repair_cost.run_analysis()


if __name__ == "__main__":
    run_with_base_class()
