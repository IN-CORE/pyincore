# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


from pyincore import IncoreClient
from pyincore.analyses.pipelinefunctionality import PipelineFunctionality
import pyincore.globals as pyglobals


def test_pipeline_functionality():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    # Create pipeline functionality
    pipeline_func = PipelineFunctionality(client)

    # Load input datasets
    pipeline_func.load_remote_input_dataset(
        "pipeline_repair_rate_damage", "62cdec9c861e370172c8da77"
    )
    # Load fragility mapping

    # Set analysis parameters
    pipeline_func.set_parameter("result_name", "mmsa_pipeline_functionality")
    pipeline_func.set_parameter("num_samples", 20000)

    # Run pipeline analysis
    result = pipeline_func.run_analysis()

    assert result is True


if __name__ == "__main__":
    test_pipeline_functionality()
