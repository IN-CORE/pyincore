# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from pyincore import IncoreClient, RepairService, MappingSet
from pyincore.analyses.residentialbuildingrecovery.residentialbuildingrecovery import ResidentialBuildingRecovery
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    # Joplin
    buildings = "5df7d0de425e0b00092d0082"  # joplin ergo:buildingInventoryVer6 28k buildings

    # sample_damage_states = "6112d9ccca3e973ce144b4d9"  # 500 samples 28k buildings - MCS output format
    sample_damage_states = "60f883c059a8cc52bab4dd77"  # 10 samples 28k buildings - MCS output format
    socio_demographic_data = "60dbd77602897f12fcd449c3"
    financial_resources = "60dbd64702897f12fcd448f5"
    delay_factors = "60eca71302897f12fcd70843"  # DS_0, etc.
    result_name = "joplin_recovery"

    seed = 1238  # not used yet
    num_samples = 10

    res_recovery = ResidentialBuildingRecovery(client)
    res_recovery.load_remote_input_dataset("buildings", buildings)

    mapping_id = "60edfa3efc0f3a7af53a21b5"
    repair_service = RepairService(client)
    mapping_set = MappingSet(repair_service.get_mapping(mapping_id))
    res_recovery.set_input_dataset('dfr3_mapping_set', mapping_set)

    res_recovery.load_remote_input_dataset("sample_damage_states", sample_damage_states)
    res_recovery.load_remote_input_dataset("socio_demographic_data", socio_demographic_data)
    res_recovery.load_remote_input_dataset("financial_resources", financial_resources)
    res_recovery.load_remote_input_dataset("delay_factors", delay_factors)

    res_recovery.set_parameter("result_name", result_name)
    res_recovery.set_parameter("seed", seed)
    res_recovery.set_parameter("num_samples", num_samples)

    res_recovery.run_analysis()
    return True


if __name__ == '__main__':
    run_with_base_class()
