from pyincore import IncoreClient, FragilityService, MappingSet, Dataset
from pyincore.analyses.epfdamage import EpfDamage
from pyincore.analyses.electricpoweravailability import ElectricPowerAvailability
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    # Lumberton Flood EPF Damage
    hazard_type = "flood"
    hazard_id_eq = "5f4d02e99f43ee0dde768406"
    epf_dataset_id = "635176081f950c126bcbe296"
    mapping_id = "635171e3297f7611014c2207"

    # Run epf damage
    epf_dmg_flood_lumberton = EpfDamage(client)
    epf_dmg_flood_lumberton.load_remote_input_dataset("epfs", epf_dataset_id)

    # Load fragility mapping
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    epf_dmg_flood_lumberton.set_input_dataset('dfr3_mapping_set', mapping_set)
    epf_dmg_flood_lumberton.set_parameter("fragility_key", "Lumberton Flood Electric Power Fragility ID Code")

    epf_dmg_flood_lumberton.set_parameter("result_name", "lumberton_flood_epf")
    epf_dmg_flood_lumberton.set_parameter("hazard_type", hazard_type)
    epf_dmg_flood_lumberton.set_parameter("hazard_id", hazard_id_eq)
    epf_dmg_flood_lumberton.set_parameter("num_cpu", 1)
    # Run Analysis
    epf_dmg_flood_lumberton.run_analysis()

    # chain with electric power availability model
    epa_lumberton = ElectricPowerAvailability(client)
    epa_lumberton.load_remote_input_dataset("buildings", "603010a4b1db9c28aef5319f")
    epa_lumberton.load_remote_input_dataset("city_polygon", "635175db1f950c126bcbe249")
    epa_lumberton.load_remote_input_dataset("epfs", epf_dataset_id)
    epf_damage_result = epf_dmg_flood_lumberton.get_output_dataset("result")
    epa_lumberton.set_input_dataset("epf_damage", epf_damage_result)

    epa_lumberton.set_parameter("result_name", "lumberton")
    epa_lumberton.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
