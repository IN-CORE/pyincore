from pyincore import IncoreClient
from pyincore.analyses.pipelinerepaircost import PipelineRepairCost
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    pipeline_repair_cost = PipelineRepairCost(client)

    # Seaside pipeline
    pipeline_repair_cost.load_remote_input_dataset("epfs", "")  # dev

    pipeline_repair_cost.load_remote_input_dataset("replacement_cost", "")

    # can be chained with pipeline repair rate damage
    pipeline_repair_cost.load_remote_input_dataset("sample_damage_states", "")

    # substation_dmg_ratios
    pipeline_repair_cost.load_remote_input_dataset("pipeline_dmg_ratios", "")

    pipeline_repair_cost.set_parameter("result_name", "seaside_pipeline")
    pipeline_repair_cost.set_parameter("num_cpu", 4)

    # Run Analysis
    pipeline_repair_cost.run_analysis()


if __name__ == "__main__":
    run_with_base_class()
