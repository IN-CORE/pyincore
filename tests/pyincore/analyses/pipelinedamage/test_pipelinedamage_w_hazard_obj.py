# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


from pyincore import IncoreClient, FragilityService, MappingSet, HazardService, Tsunami
from pyincore.analyses.pipelinedamage import PipelineDamage
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)
    hazard_service = HazardService(client)
    tsunami = Tsunami.from_hazard_service("5bc9eaf7f7b08533c7e610e1", hazard_service)

    pipeline_dmg = PipelineDamage(client)

    # test tsunami pipeline
    pipeline_dmg.load_remote_input_dataset("pipeline", "5ef1171b2367ff111d082f0c")

    # Load fragility mapping
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(
        fragility_service.get_mapping("60b124e01f2b7d4a916ba456")
    )  # new format fragility curves
    # mapping_set = MappingSet(fragility_service.get_mapping("5ef11888da15730b13b84353")) # legacy fragility curves
    pipeline_dmg.set_input_dataset("dfr3_mapping_set", mapping_set)

    pipeline_dmg.set_input_hazard("hazard", tsunami)

    pipeline_dmg.set_parameter(
        "result_name", "seaside_tsunami_pipeline_result_w_hazard_obj"
    )
    pipeline_dmg.set_parameter(
        "fragility_key", "Non-Retrofit inundationDepth Fragility ID Code"
    )
    pipeline_dmg.set_parameter("num_cpu", 4)

    # Run pipeline damage analysis
    result = pipeline_dmg.run_analysis()


if __name__ == "__main__":
    run_with_base_class()
