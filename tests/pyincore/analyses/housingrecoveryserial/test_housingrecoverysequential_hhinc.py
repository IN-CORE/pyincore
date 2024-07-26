# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
import os

from pyincore import IncoreClient, HHRSOutputProcess, Dataset
from pyincore.analyses.housingrecoverysequential import HousingRecoverySequential
from timeit import default_timer as timer
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    start = timer()

    #population_dislocation = "60f098f502897f12fcda19ec"  # dev Galveston testbed
    population_dislocation = Dataset.from_file(
        os.path.join(
            pyglobals.TEST_DATA_DIR, "pop-dislocation-results.csv"
        ),
        data_type="incore:popDislocation",
    )

    zone_def_sv_json = Dataset.from_file(
        os.path.join(
            pyglobals.TEST_DATA_DIR, "zone_def_sv.json"
        ),
        data_type="incore:socialVulnerabilityValueGenerator",
    )

    transition_probability_matrix = "60ef513802897f12fcd9765c"
    initial_probability_vector = "60ef532e02897f12fcd9ac63"
    # sv_result = "62c5be23861e370172c5e412"  # dev tract level
    sv_result = "62c70445861e370172c6eaab"  # dev block group level

    seed = 1234
    t_delta = 1.0
    t_final = 90.0

    housing_recovery = HousingRecoverySequential(client)

    # Parameter setup
    housing_recovery.set_parameter("num_cpu", 4)
    housing_recovery.set_parameter("seed", seed)
    housing_recovery.set_parameter("t_delta", t_delta)
    housing_recovery.set_parameter("t_final", t_final)
    housing_recovery.set_parameter("result_name", "results_hhrs_joplin.csv")

    # Dataset inputs
    housing_recovery.set_input_dataset(
        "population_dislocation_block", population_dislocation
    )
    housing_recovery.set_input_dataset(
        "zone_def_sv", zone_def_sv_json
    )
    housing_recovery.load_remote_input_dataset("tpm", transition_probability_matrix)
    housing_recovery.load_remote_input_dataset(
        "initial_stage_probabilities", initial_probability_vector
    )

    housing_recovery.run()

    # test the utilility
    housing_recovery.set_parameter("result_name", "results_hhrs_galveston_wo_sv.csv")
    hhr_result = housing_recovery.get_output_dataset("ds_result")
    hhrs_df = hhr_result.get_dataframe_from_csv(low_memory=False)

    end = timer()

    print(f"Elapsed time: {end - start:.3f} seconds")

    timesteps = ["1", "7", "13", "25", "49"]  # t0, t6, t12, t24, t48

    print(HHRSOutputProcess.get_hhrs_stage_count(timesteps, hhrs_df))


if __name__ == "__main__":
    run_with_base_class()
