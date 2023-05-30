from pyincore import IncoreClient, Dataset
from pyincore.analyses.waterfacilityrepaircost import WaterFacilityRepairCost
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient()
    # client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    wf_repair_cost = WaterFacilityRepairCost(client)

    # Seaside wf
    wf_repair_cost.load_remote_input_dataset("water_facilities", "60e5e91960b3f41243faa3b2")  # prod
    # wf_repair_cost.load_remote_input_dataset("water_facilities", "60e5e91960b3f41243faa3b2")  # prod

    # wf_repair_cost.load_remote_input_dataset("replacement_cost", "6470c09a5bc8b26ddf99bb59")
    replacement_cost = Dataset.from_file("data/waterfacility_replacement_cost.csv", "incore:replacementCost")
    wf_repair_cost.set_input_dataset("replacement_cost", replacement_cost)

    # can be chained with MCS
    # wf_repair_cost.load_remote_input_dataset("sample_damage_states", "6470c23d5bc8b26ddf99bb65")
    sample_damage_states = Dataset.from_file("data/mc_wterfclty_cumulative_1000yr_sample_damage_states.csv", "incore:sampleDamageState")
    wf_repair_cost.set_input_dataset("sample_damage_states", sample_damage_states)

    # dmg ratios
    # wf_repair_cost.load_remote_input_dataset("wf_dmg_ratios", "6470c1c35bc8b26ddf99bb5f")
    wf_dmg_ratios = Dataset.from_file("data/wf_dmg_ratios.csv", "incore:waterFacilityDamageRatios")
    wf_repair_cost.set_input_dataset("wf_dmg_ratios", wf_dmg_ratios)

    wf_repair_cost.set_parameter("result_name", "seaside_wf")
    wf_repair_cost.set_parameter("num_cpu", 4)

    # Run Analysis
    wf_repair_cost.run_analysis()


if __name__ == "__main__":
    run_with_base_class()
