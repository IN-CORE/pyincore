# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


from pyincore import IncoreClient, FragilityService, MappingSet
from pyincore.analyses.roadfailure import RoadFailure
from pyincore.globals import INCORE_TEST_URL


def test_road_failure():
    client = IncoreClient(INCORE_TEST_URL, token_file_name=".incrtesttoken")

    # road inventory for Galveston island
    road_dataset_id = "5f0dd5ecb922f96f4e962caf"
    # distance table for Galveston island
    distance_dataset_id = "5f1883abfeef2d758c4e857d"
    # road damage by hurricane inundation mapping
    mapping_id = "5f0cb04fe392b24d4800f316"
    # Galveston Deterministic Hurricane - Kriging inundationDuration
    hazard_type = "hurricane"
    hazard_id = "5f10837c01d3241d77729a4f"

    # Create road damage
    road_failure = RoadFailure(client)
    # Load input datasets
    road_failure.load_remote_input_dataset("roads", road_dataset_id)
    road_failure.load_remote_input_dataset("distance_table", distance_dataset_id)
    # Load fragility mapping
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    road_failure.set_input_dataset('dfr3_mapping_set', mapping_set)
    # Specify the result name
    result_name = "road_result"
    # Set analysis parameters
    road_failure.set_parameter("result_name", result_name)
    road_failure.set_parameter("hazard_type", hazard_type)
    road_failure.set_parameter("hazard_id", hazard_id)
    road_failure.set_parameter("num_cpu", 4)

    # Run road damage by hurricane inundation analysis
    result = road_failure.run_analysis()

    assert result is True


if __name__ == "__main__":
    test_road_failure()
