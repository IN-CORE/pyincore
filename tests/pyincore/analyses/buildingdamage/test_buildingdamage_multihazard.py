import os

from pyincore import IncoreClient, FragilityService, MappingSet
from pyincore.analyses.buildingdamage import BuildingDamage
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    bldg_dmg = BuildingDamage(client)

    # seaside multi-hazard
    bldg_dmg.load_remote_input_dataset("buildings", "5bcf2fcbf242fe047ce79dad")

    mapping_id = "648a3f88c687ae511a1814e2"  # earthquake+tsunami mapping
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    bldg_dmg.set_input_dataset("dfr3_mapping_set", mapping_set)
    bldg_dmg.set_parameter("fragility_key", "Non-Retrofit Fragility ID Code")

    hazard_type = "earthquake+tsunami"
    hazard_id = "5ba8f127ec2309043520906c+5bc9eaf7f7b08533c7e610e1"

    result_folder = "mutliple_hazards"
    if not os.path.exists(result_folder):
        os.mkdir(result_folder)
    result_name = os.path.join(result_folder, "seaside_multihazard")
    bldg_dmg.set_parameter("result_name", result_name)
    bldg_dmg.set_parameter("hazard_type", hazard_type)
    bldg_dmg.set_parameter("hazard_id", hazard_id)
    bldg_dmg.set_parameter("num_cpu", 4)
    bldg_dmg.set_parameter("seed", 1000)
    bldg_dmg.run_analysis()


if __name__ == "__main__":
    run_with_base_class()
