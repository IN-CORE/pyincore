# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from pyincore import IncoreClient, FragilityService, MappingSet
from pyincore.analyses.housingrecoverysequential import HousingRecoverySequential
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    population_dislocation = "60f098f502897f12fcda19ec"  # dev Galveston testbed
    transition_probability_matrix = "60ef513802897f12fcd9765c"
    initial_probability_vector = "60ef532e02897f12fcd9ac63"
    # sv_result = "62c5be23861e370172c5e412"  # dev tract level
    sv_result = "62c70445861e370172c6eaab"  # dev block group level

    seed = 1234
    t_delta = 1.0
    t_final = 90.0

    housing_recovery = HousingRecoverySequential(client)

    # Parameter setup
    housing_recovery.set_parameter('seed', seed)
    housing_recovery.set_parameter('t_delta', t_delta)
    housing_recovery.set_parameter('t_final', t_final)

    # Dataset inputs
    housing_recovery.load_remote_input_dataset("population_dislocation_block", population_dislocation)
    housing_recovery.load_remote_input_dataset('tpm', transition_probability_matrix)
    housing_recovery.load_remote_input_dataset('initial_stage_probabilities', initial_probability_vector)
    housing_recovery.load_remote_input_dataset('sv_result', sv_result)

    housing_recovery.run()


if __name__ == '__main__':
    run_with_base_class()
