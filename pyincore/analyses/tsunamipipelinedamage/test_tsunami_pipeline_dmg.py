from pyincore import IncoreClient
from pyincore.analyses.tsunamipipelinedamage import TsunamiPipelineDamage


def test_pipeline_dmg():
    client = IncoreClient()
    tsu_pipeline_dmg = TsunamiPipelineDamage(client)

    # test tsunami pipeline
    tsu_pipeline_dmg.load_remote_input_dataset("pipeline",
                                               "5d2666b5b9219c3c5595ee65")
    tsu_pipeline_dmg.set_parameter("result_name",
                                   "seaside_tsunami_pipeline_result")
    tsu_pipeline_dmg.set_parameter("mapping_id", "5d320a87b9219c6d66398b45")
    tsu_pipeline_dmg.set_parameter("hazard_id", "5bc9eaf7f7b08533c7e610e1")
    tsu_pipeline_dmg.set_parameter("num_cpu", 4)

    # Run pipeline damage analysis
    result = tsu_pipeline_dmg.run_analysis()

    assert result is True


if __name__ == "__main__":
    test_pipeline_dmg()
