# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


from pyincore import IncoreClient, FragilityService, MappingSet
from pyincore.analyses.pipelinerestoration import PipelineRestoration
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)
    client.clear_cache()
    pipeline_restoration = PipelineRestoration(client)

    # shelby county pipelines
    pipeline_restoration.load_remote_input_dataset("pipeline", "5a284f28c7d30d13bc081d14")
    pipeline_restoration.load_remote_input_dataset("pipeline_damage", "61f36023c53b3620b6b614c6")

    # Load fragility mapping
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping("61f35f09903e515036cee106"))
    pipeline_restoration.set_input_dataset('dfr3_mapping_set', mapping_set)

    pipeline_restoration.set_parameter("result_name", "pipeline_restoration_times")

    pipeline_restoration.set_parameter("restoration_key", "Restoration ID Code")
    pipeline_restoration.set_parameter("num_available_workers", 4)
    pipeline_restoration.set_parameter("num_cpu", 4)

    # Run pipeline damage analysis
    result = pipeline_restoration.run_analysis()


if __name__ == "__main__":
    run_with_base_class()
