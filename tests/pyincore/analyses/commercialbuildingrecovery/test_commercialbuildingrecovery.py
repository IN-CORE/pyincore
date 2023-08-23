from pyincore import IncoreClient, RepairService, MappingSet
from pyincore.analyses.commercialbuildingrecovery.commercialbuildingrecovery import CommercialBuildingRecovery
from pyincore import Dataset


def run_with_base_class():
    # Connect to IN-CORE service
    client = IncoreClient()
    # client.clear_cache()
    # Joplin
    buildings = "5dbc8478b9219c06dd242c0d"  # ergo:buildingInventoryVer6 5dbc8478b9219c06dd242c0d

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
    # sample_damage_states = "612e4038cf04e0131fb6156c"  # 10 samples 28k buildings - MCS output format

    sample_damage_states = Dataset.from_file("Joplin_bldg_failure_SAM_sample_damage_states.csv",
                                             "incore:sampleDamageState")
    com_recovery.set_input_dataset("sample_damage_states", sample_damage_states)
    mcs_failure = Dataset.from_file("Joplin_bldg_failure_SAM_failure_probability.csv",
                                    "incore:failureProbability")
    com_recovery.set_input_dataset("mcs_failure", mcs_failure)
    # delay_factors = "60fb433cd3c92a78c89d21cc"  # DS_0, etc.
    delay_factors = Dataset.from_file("Dataset1_REDi_business_new.csv",
                                      "incore:buildingRecoveryFactors")
    com_recovery.set_input_dataset("delay_factors", delay_factors)

    # Load input datasets
    # com_recovery.load_remote_input_dataset("sample_damage_states", sample_damage_states)
    # com_recovery.load_remote_input_dataset("delay_factors", delay_factors)

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
