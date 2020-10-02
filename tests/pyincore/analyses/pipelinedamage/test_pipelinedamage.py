# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


from pyincore import IncoreClient, FragilityService, MappingSet
from pyincore.analyses.pipelinedamage import PipelineDamage
from pyincore.globals import INCORE_API_DEV_URL


def test_pipeline_dmg():
    client = IncoreClient(service_url=INCORE_API_DEV_URL, token_file_name=".incrtesttoken")
    pipeline_dmg = PipelineDamage(client)

    # test tsunami pipeline
    pipeline_dmg.load_remote_input_dataset("pipeline",
                                           "5ef1171b2367ff111d082f0c")

    # Load fragility mapping
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping("5ef11888da15730b13b84353"))
    pipeline_dmg.set_input_dataset('dfr3_mapping_set', mapping_set)

    pipeline_dmg.set_parameter("result_name",
                               "seaside_tsunami_pipeline_result")
    pipeline_dmg.set_parameter("hazard_type", "tsunami")
    pipeline_dmg.set_parameter("fragility_key",
                               "Non-Retrofit inundationDepth Fragility ID Code")
    pipeline_dmg.set_parameter("hazard_id", "5bc9eaf7f7b08533c7e610e1")
    pipeline_dmg.set_parameter("num_cpu", 4)

    # Run pipeline damage analysis
    result = pipeline_dmg.run_analysis()

    assert result is True


if __name__ == "__main__":
    test_pipeline_dmg()
