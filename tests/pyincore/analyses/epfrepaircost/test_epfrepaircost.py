from pyincore import IncoreClient, Dataset
from pyincore.analyses.epfrepaircost import EpfRepairCost
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    # Seaside EPF
    epf_dataset_id = "6189c103d5b02930aa3efc35"

    # Run epf damage
    epf_repair_cost = EpfRepairCost(client)
    epf_repair_cost.load_remote_input_dataset("epfs", epf_dataset_id)

    replacement_cost = Dataset.from_file("data/replacement_cost.csv", "incore:replacementCost")
    epf_repair_cost.set_input_dataset("replacement_cost", replacement_cost)

    # can be chained with MCS
    sample_damage_states = Dataset.from_file("data/sample_damage_states.csv", "incore:sampleDamageState")
    epf_repair_cost.set_input_dataset("sample_damage_states", sample_damage_states)
    
    # substation_dmg_ratios
    substation_dmg_ratios = Dataset.from_file("data/substation_dmg_ratios.csv", "incore:epfDamageRatios")
    epf_repair_cost.set_input_dataset("substation_dmg_ratios", substation_dmg_ratios)

    # circuit_dmg_ratios
    circuit_dmg_ratios = Dataset.from_file("data/circuit_dmg_ratios.csv", "incore:epfDamageRatios")
    epf_repair_cost.set_input_dataset("circuit_dmg_ratios", circuit_dmg_ratios)

    # generation_plant_dmg_ratios
    generation_plant_dmg_ratios = Dataset.from_file("data/generation_plant_dmg_ratios.csv", "incore:epfDamageRatios")
    epf_repair_cost.set_input_dataset("generation_plant_dmg_ratios", generation_plant_dmg_ratios)

    epf_repair_cost.set_parameter("result_name", "seaside_epf")
    epf_repair_cost.set_parameter("num_cpu", 4)
    # epf_repair_cost.set_parameter("epf_substation_types", ["ESSL"])
    # epf_repair_cost.set_parameter("epf_circuit_types", ["EDC"])
    # epf_repair_cost.set_parameter("epf_generation_plant_types", ["EPPL"])

    # Run Analysis
    epf_repair_cost.run_analysis()


if __name__ == "__main__":
    run_with_base_class()
