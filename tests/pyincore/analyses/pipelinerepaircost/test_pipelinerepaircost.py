from pyincore import IncoreClient, FragilityService, MappingSet
from pyincore.analyses.pipelinedamagerepairrate import PipelineDamageRepairRate
from pyincore.analyses.pipelinerepaircost import PipelineRepairCost
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    pipeline_repair_cost = PipelineRepairCost(client)

    pipeline_id = "647782045bc8b26ddfa1116c"

    # Seaside pipeline
    pipeline_repair_cost.load_remote_input_dataset("pipeline", pipeline_id)  # dev

    pipeline_repair_cost.load_remote_input_dataset("replacement_cost", "647782c95bc8b26ddfa11c2f")

    # can be chained with pipeline repair rate damage
    test_pipeline_dmg_w_rr = PipelineDamageRepairRate(client)
    test_pipeline_dmg_w_rr.load_remote_input_dataset("pipeline", pipeline_id)

    # Load fragility mapping
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping("5b47c227337d4a38464efea8"))
    test_pipeline_dmg_w_rr.set_input_dataset('dfr3_mapping_set', mapping_set)

    test_pipeline_dmg_w_rr.set_parameter("result_name", "seaside_eq_pipeline_result")
    test_pipeline_dmg_w_rr.set_parameter("fragility_key", "pgv")
    test_pipeline_dmg_w_rr.set_parameter("hazard_type", "earthquake")
    test_pipeline_dmg_w_rr.set_parameter("hazard_id", "5ba8f2b9ec2309043520906e")  # seaside probability 5000 yr
    test_pipeline_dmg_w_rr.set_parameter("num_cpu", 4)
    test_pipeline_dmg_w_rr.run_analysis()
    pipeline_dmg = test_pipeline_dmg_w_rr.get_output_dataset("result")

    # pipeline_repair_cost.load_remote_input_dataset("pipeline_dmg", "647784ca5bc8b26ddfa1437b")
    pipeline_repair_cost.set_input_dataset("pipeline_dmg", pipeline_dmg)

    # pipeline damage ratio
    pipeline_repair_cost.load_remote_input_dataset("pipeline_dmg_ratios", "647783ad5bc8b26ddfa11c5f")

    pipeline_repair_cost.set_parameter("result_name", "seaside_pipeline")
    pipeline_repair_cost.set_parameter("num_cpu", 4)

    # Run Analysis
    pipeline_repair_cost.run_analysis()


if __name__ == "__main__":
    run_with_base_class()
