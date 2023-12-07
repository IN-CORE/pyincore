from pyincore import IncoreClient, RepairService, MappingSet
from pyincore.analyses.commercialbuildingrecovery.commercialbuildingrecovery import CommercialBuildingRecovery
import pyincore.globals as pyglobals


def run_with_base_class():
    # Connect to IN-CORE service
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)
    client.clear_cache()
    buildings = "5df7d0de425e0b00092d0082"  # ergo:buildingInventoryVer6 5dbc8478b9219c06dd242c0d

    # Create commercial recovery instance
    com_recovery = CommercialBuildingRecovery(client)
    com_recovery.load_remote_input_dataset("buildings", buildings)

    # Recovery mapping
    mapping_id = "60edfa3efc0f3a7af53a21b5"
    # Create repair service
    repair_service = RepairService(client)
    mapping_set = MappingSet(repair_service.get_mapping(mapping_id))
    com_recovery.set_input_dataset('dfr3_mapping_set', mapping_set)

    # input datsets ids
    sample_damage_states = "64ee146456b25759cfc599ac"  # 10 samples 28k buildings - MCS output format
    mcs_failure = '64ee144256b25759cfc599a5'
    delay_factors = "64ee10e756b25759cfc53243"
    bld_dmg = '65723c3f9bc3c806024c69b0'

    # Load input datasets
    com_recovery.load_remote_input_dataset("sample_damage_states", sample_damage_states)
    com_recovery.load_remote_input_dataset("mcs_failure", mcs_failure)
    com_recovery.load_remote_input_dataset("delay_factors", delay_factors)
    com_recovery.load_remote_input_dataset("damages", bld_dmg)



    # Input parameters
    num_samples = 10

    # Specify the result name
    result_name = "joplin_commercial_test"

    # Set analysis parameters
    com_recovery.set_parameter("result_name", result_name)
    com_recovery.set_parameter("num_samples", num_samples)

    # Run the analysis (NOTE: with SettingWithCopyWarning)
    com_recovery.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
