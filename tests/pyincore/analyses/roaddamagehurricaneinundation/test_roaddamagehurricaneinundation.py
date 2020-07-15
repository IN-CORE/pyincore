# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


from pyincore import IncoreClient, FragilityService, MappingSet
from pyincore.analyses.roaddamagehurricaneinundation import RoadDamageHurricaneInundation
from pyincore.globals import INCORE_API_DEV_URL


def test_pipeline_dmg_w_repair_rate():
    client = IncoreClient(INCORE_API_DEV_URL)

    # This is the Memphis Water Buried Pipeline with Topology dataset the Ergo repository
    road_dataset_id = "5f0dd5ecb922f96f4e962caf"
    # pipeline mapping
    mapping_id = "5f0cb04fe392b24d4800f316"

    # New madrid earthquake using Atkinson Boore 1995
    hazard_type = "hurricane"
    hazard_id = "5b902cb273c3371e1236b36b"

    # Create pipeline damage
    test_roaddamagehurricaneinundation = RoadDamageHurricaneInundation(client)
    # Load input datasets
    test_roaddamagehurricaneinundation.load_remote_input_dataset("roads", road_dataset_id)
    # Load fragility mapping
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    test_roaddamagehurricaneinundation.set_input_dataset('dfr3_mapping_set', mapping_set)
    # Specify the result name
    result_name = "road_result"
    # Set analysis parameters
    test_roaddamagehurricaneinundation.set_parameter("result_name", result_name)
    test_roaddamagehurricaneinundation.set_parameter("hazard_type", hazard_type)
    test_roaddamagehurricaneinundation.set_parameter("hazard_id", hazard_id)
    # test_roaddamagehurricaneinundation.set_parameter("liquefaction_fragility_key", "pgd")
    # test_roaddamagehurricaneinundation.set_parameter("use_liquefaction", False)
    test_roaddamagehurricaneinundation.set_parameter("num_cpu", 4)
    # test_roaddamagehurricaneinundation.set_parameter("liquefaction_geology_dataset_id",
    #                                      liq_geology_dataset_id)
    # Run pipeline damage analysis
    result = test_roaddamagehurricaneinundation.run_analysis()

    assert result is True


if __name__ == "__main__":
    test_pipeline_dmg_w_repair_rate()
