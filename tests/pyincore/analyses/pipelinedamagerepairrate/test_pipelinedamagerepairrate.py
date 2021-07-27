# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import pyincore.globals as pyglobals
from pyincore import IncoreClient, FragilityService, MappingSet
from pyincore.analyses.pipelinedamagerepairrate import PipelineDamageRepairRate


def test_pipeline_dmg_w_repair_rate():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

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
    # Load fragility mapping
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    test_pipeline_dmg_w_rr.set_input_dataset('dfr3_mapping_set', mapping_set)
    # Specify the result name
    result_name = "pipeline_result"
    # Set analysis parameters
    test_pipeline_dmg_w_rr.set_parameter("result_name", result_name)
    test_pipeline_dmg_w_rr.set_parameter("hazard_type", hazard_type)
    test_pipeline_dmg_w_rr.set_parameter("hazard_id", hazard_id)
    test_pipeline_dmg_w_rr.set_parameter("liquefaction_fragility_key", "pgd")
    # test_pipeline_dmg_w_rr.set_parameter("use_liquefaction", False)
    test_pipeline_dmg_w_rr.set_parameter("use_liquefaction", True)  # toggle on and off to see liquefaction
    test_pipeline_dmg_w_rr.set_parameter("num_cpu", 4)
    test_pipeline_dmg_w_rr.set_parameter("liquefaction_geology_dataset_id",
                                         liq_geology_dataset_id)
    # Run pipeline damage analysis
    result = test_pipeline_dmg_w_rr.run_analysis()

    ##################################
    # test with refactored fragility curves
    mapping_id = "60b801231f2b7d4a916da689"
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    test_pipeline_dmg_w_rr.set_input_dataset('dfr3_mapping_set', mapping_set)

    result_name = "pipeline_result_refactored"
    test_pipeline_dmg_w_rr.set_parameter("result_name", result_name)

    result = test_pipeline_dmg_w_rr.run_analysis()

    assert result is True


if __name__ == "__main__":
    test_pipeline_dmg_w_repair_rate()
