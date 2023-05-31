from pyincore import IncoreClient, Dataset
from pyincore.analyses.pipelinerepaircost import PipelineRepairCost
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    pipeline_repair_cost = PipelineRepairCost(client)

    # Seaside pipeline
    # pipeline_repair_cost.load_remote_input_dataset("pipeline", "")  # dev
    pipeline = Dataset.from_file("data/", "ergo:buriedPipelineTopology")
    pipeline_repair_cost.set_input_dataset("pipeline", pipeline)

    # pipeline_repair_cost.load_remote_input_dataset("replacement_cost", "")
    replacement_cost = Dataset.from_file("data/pipeline_replacement_cost.csv", "incore:replacementCost")
    pipeline_repair_cost.set_input_dataset("replacement_cost", replacement_cost)

    # can be chained with pipeline repair rate damage
    # pipeline_repair_cost.load_remote_input_dataset("pipeline_dmg", "")
    pipeline_dmg = Dataset.from_file("data/.csv", "ergo:pipelineDamageVer3")
    pipeline_repair_cost.set_input_dataset("pipeline_dmg", pipeline_dmg)

    # pipeline damage ratio
    # pipeline_repair_cost.load_remote_input_dataset("pipeline_dmg_ratios", "")
    pipeline_dmg_ratios = Dataset.from_file("data/pipeline_dmg_ratios.csv", "incore:pipelineDamageRatios")
    pipeline_repair_cost.set_input_dataset("wf_dmg_ratios", pipeline_dmg_ratios)

    pipeline_repair_cost.set_parameter("result_name", "seaside_pipeline")
    pipeline_repair_cost.set_parameter("num_cpu", 4)

    # Run Analysis
    pipeline_repair_cost.run_analysis()


if __name__ == "__main__":
    run_with_base_class()
