from pyincore import IncoreClient, Dataset, FragilityService, MappingSet
from pyincore.analyses.pipelinedamagerepairrate import PipelineDamageRepairRate
from pyincore.analyses.pipelinerepaircost import PipelineRepairCost
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    pipeline_repair_cost = PipelineRepairCost(client)

    # Seaside pipeline
    # pipeline_repair_cost.load_remote_input_dataset("pipeline", "")  # dev
    pipeline = Dataset.from_file("data/seaside_water_pipeline_cleaned_schema.shp", "ergo:buriedPipelineTopology")
    pipeline_repair_cost.set_input_dataset("pipeline", pipeline)

    # pipeline_repair_cost.load_remote_input_dataset("replacement_cost", "")
    replacement_cost = Dataset.from_file("data/pipeline_replacement_cost.csv", "incore:replacementCost")
    pipeline_repair_cost.set_input_dataset("replacement_cost", replacement_cost)

    # can be chained with pipeline repair rate damage
    test_pipeline_dmg_w_rr = PipelineDamageRepairRate(client)
    test_pipeline_dmg_w_rr.set_input_dataset("pipeline", pipeline)

    # Load fragility mapping
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping("5b47c227337d4a38464efea8"))
    test_pipeline_dmg_w_rr.set_input_dataset('dfr3_mapping_set', mapping_set)

    test_pipeline_dmg_w_rr.set_parameter("result_name", "seaside_eq_pipeline_result")
    test_pipeline_dmg_w_rr.set_parameter("fragility_key", "pgv")
    test_pipeline_dmg_w_rr.set_parameter("hazard_type", "earthquake")
    test_pipeline_dmg_w_rr.set_parameter("hazard_id", "5ba8f127ec2309043520906c")  # seaside probability 1000 yr
    test_pipeline_dmg_w_rr.set_parameter("num_cpu", 4)
    test_pipeline_dmg_w_rr.run_analysis()
    pipeline_dmg = test_pipeline_dmg_w_rr.get_output_dataset("result")
    # pipeline_repair_cost.load_remote_input_dataset("pipeline_dmg", "")
    # pipeline_dmg = Dataset.from_file("data/pipe_eq_1000yr.csv", "ergo:pipelineDamageVer3")

    pipeline_repair_cost.set_input_dataset("pipeline_dmg", pipeline_dmg)

    # pipeline damage ratio
    # pipeline_repair_cost.load_remote_input_dataset("pipeline_dmg_ratios", "")
    pipeline_dmg_ratios = Dataset.from_file("data/pipeline_dmg_ratios.csv", "incore:pipelineDamageRatios")
    pipeline_repair_cost.set_input_dataset("pipeline_dmg_ratios", pipeline_dmg_ratios)

    pipeline_repair_cost.set_parameter("result_name", "seaside_pipeline")
    pipeline_repair_cost.set_parameter("num_cpu", 4)

    # Run Analysis
    pipeline_repair_cost.run_analysis()


if __name__ == "__main__":
    run_with_base_class()
