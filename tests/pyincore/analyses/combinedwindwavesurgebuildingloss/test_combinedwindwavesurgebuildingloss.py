from pyincore import IncoreClient, FragilityService, MappingSet
from pyincore.analyses.combinedwindwavesurgebuildingloss import CombinedWindWaveSurgeBuildingLoss
from pyincore.analyses.buildingdamage import BuildingDamage
import pyincore.globals as pyglobals
from timeit import default_timer as timer


def run_with_base_class():

    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    # Galveston building inventory
    bldg_dataset_id = "63053e74c8f8b7614f6cff9f"

    # Hazard information
    hazard_id = "5fa472033c1f0c73fe81461a"
    hazard_type = "hurricane"

    # Fragility Service
    fragility_service = FragilityService(client)

    # Surge-wave mapping
    mapping_id = "6303e51bd76c6d0e1f6be080"
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))

    # surge-wave building damage
    sw_bldg_dmg = BuildingDamage(client)
    sw_bldg_dmg.load_remote_input_dataset("buildings", bldg_dataset_id)
    sw_bldg_dmg.set_input_dataset('dfr3_mapping_set', mapping_set)
    sw_bldg_dmg.set_parameter("result_name", "Galveston-sw-dmg")
    sw_bldg_dmg.set_parameter("hazard_type", hazard_type)
    sw_bldg_dmg.set_parameter("hazard_id", hazard_id)
    sw_bldg_dmg.set_parameter("num_cpu", 4)
    sw_bldg_dmg.run_analysis()

    # wind mapping
    mapping_id = "62fef3a6cef2881193f2261d"
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))

    # wind building damage
    w_bldg_dmg = BuildingDamage(client)
    w_bldg_dmg.load_remote_input_dataset("buildings", bldg_dataset_id)
    w_bldg_dmg.set_input_dataset('dfr3_mapping_set', mapping_set)
    w_bldg_dmg.set_parameter("result_name", "Galveston-wind-dmg")
    w_bldg_dmg.set_parameter("hazard_type", hazard_type)
    w_bldg_dmg.set_parameter("hazard_id", hazard_id)
    w_bldg_dmg.set_parameter("num_cpu", 4)
    w_bldg_dmg.run_analysis()

    # flood mapping
    mapping_id = "62fefd688a30d30dac57bbd7"
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))

    # flood building damage
    f_bldg_dmg = BuildingDamage(client)
    f_bldg_dmg.load_remote_input_dataset("buildings", bldg_dataset_id)
    f_bldg_dmg.set_input_dataset('dfr3_mapping_set', mapping_set)
    f_bldg_dmg.set_parameter("result_name", "Galveston-flood-dmg")
    f_bldg_dmg.set_parameter("hazard_type", hazard_type)
    f_bldg_dmg.set_parameter("hazard_id", hazard_id)
    f_bldg_dmg.set_parameter("num_cpu", 4)
    f_bldg_dmg.run_analysis()

    # Get damage outputs from different hazards
    surge_wave_damage = sw_bldg_dmg.get_output_dataset("ds_result")
    wind_damage = w_bldg_dmg.get_output_dataset("ds_result")
    flood_damage = f_bldg_dmg.get_output_dataset("ds_result")

    start = timer()

    # Combined building loss from each hazard
    combined_bldg_loss = CombinedWindWaveSurgeBuildingLoss(client)
    combined_bldg_loss.load_remote_input_dataset("buildings", bldg_dataset_id)
    combined_bldg_loss.set_input_dataset("surge_wave_damage", surge_wave_damage)
    combined_bldg_loss.set_input_dataset("wind_damage", wind_damage)
    combined_bldg_loss.set_input_dataset("flood_damage", flood_damage)
    combined_bldg_loss.load_remote_input_dataset("structural_cost", "63fd15716d3b2a308ba914c8")
    combined_bldg_loss.load_remote_input_dataset("content_cost", "63fd16956d3b2a308ba9269a")
    combined_bldg_loss.set_parameter("result_name", "Galveston")
    combined_bldg_loss.run_analysis()

    end = timer()
    print(f'Elapsed time: {end - start:.3f} seconds')


if __name__ == '__main__':
    run_with_base_class()
