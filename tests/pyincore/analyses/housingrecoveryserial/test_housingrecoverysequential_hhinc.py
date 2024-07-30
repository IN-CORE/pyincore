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

    # dev Joplin testbed
    population_dislocation = Dataset.from_file(
        os.path.join(
            pyglobals.TEST_DATA_DIR, "pop-dislocation-results.csv"
        ),
        data_type="incore:popDislocation",
    )

    zone_def_hhinc_json = Dataset.from_file(
        os.path.join(
            pyglobals.TEST_DATA_DIR, "zone_def_hhinc.json"
        ),
        data_type="incore:zoneDefinitionsHouseholdIncome",
    )

    # Household-level housing serial recovery model TPM
    transition_probability_matrix = "66a8fac64e40247326448873"
    # Galveston HHRS model initial stage probability
    initial_probability_vector = "6420c184b18d026e7c7dc321"

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
        "zone_def_hhinc", zone_def_hhinc_json
    )
    housing_recovery.load_remote_input_dataset("tpm", transition_probability_matrix)
    housing_recovery.load_remote_input_dataset(
        "initial_stage_probabilities", initial_probability_vector
    )

    housing_recovery.run()

    # test the utilility
    housing_recovery.set_parameter("result_name", "results_hhrs_joplin.csv")
    hhr_result = housing_recovery.get_output_dataset("ds_result")
    hhrs_df = hhr_result.get_dataframe_from_csv(low_memory=False)

    end = timer()

    print(f"Elapsed time: {end - start:.3f} seconds")

    timesteps = ["1", "7", "13", "25", "49"]  # t0, t6, t12, t24, t48

    print(HHRSOutputProcess.get_hhrs_stage_count(timesteps, hhrs_df))


if __name__ == "__main__":
    run_with_base_class()
