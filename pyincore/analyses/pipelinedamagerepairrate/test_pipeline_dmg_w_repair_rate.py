from pyincore import InsecureIncoreClient
from pyincore.analyses.pipelinedamagerepairrate import PipelineDamageRepairRate


def test_pipeline_dmg_w_repair_rate():
    client = InsecureIncoreClient(
        "http://incore2-services-dev.ncsa.illinois.edu:8888", "incrtest")

    # This is the Memphis Water Buried Pipeline with Topology dataset the Ergo repository
    pipeline_dataset_id = "5a284f28c7d30d13bc081d14"
    # pipeline mapping
    mapping_id = "5b47c227337d4a38464efea8"

    # New madrid earthquake using Atkinson Boore 1995
    hazard_type = "earthquake"
    hazard_id = "5b902cb273c3371e1236b36b"

    # Geology dataset
    liq_geology_dataset_id = "5a284f53c7d30d13bc08249c"

    # Create pipeline damage
    test_pipeline_dmg_w_rr = PipelineDamageRepairRate(client)
    # Load input datasets
    test_pipeline_dmg_w_rr.load_remote_input_dataset("pipeline", pipeline_dataset_id)
    # Specify the result name
    result_name = "pipeline_result"
    # Set analysis parameters
    test_pipeline_dmg_w_rr.set_parameter("result_name", result_name)
    test_pipeline_dmg_w_rr.set_parameter("mapping_id", mapping_id)
    test_pipeline_dmg_w_rr.set_parameter("hazard_type", hazard_type)
    test_pipeline_dmg_w_rr.set_parameter("hazard_id", hazard_id)
    test_pipeline_dmg_w_rr.set_parameter("liquefaction_fragility_key", "pgd")
    test_pipeline_dmg_w_rr.set_parameter("use_liquefaction", False)
    test_pipeline_dmg_w_rr.set_parameter("num_cpu", 4)
    test_pipeline_dmg_w_rr.set_parameter("liquefaction_geology_dataset_id",
                                         liq_geology_dataset_id)
    # Run pipeline damage analysis
    result = test_pipeline_dmg_w_rr.run_analysis()

    assert result is True


if __name__ == "__main__":
    test_pipeline_dmg_w_repair_rate()
