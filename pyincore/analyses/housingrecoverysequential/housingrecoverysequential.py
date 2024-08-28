# Copyright (c) 2021 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
from pyincore import BaseAnalysis, AnalysisUtil

import numpy as np
import pandas as pd
import concurrent.futures
from itertools import repeat


class HousingRecoverySequential(BaseAnalysis):
    """
    This analysis computes the series of household recovery states given a population
    dislocation dataset, a transition probability matrix (TPM) and an initial state vector.

    The computation operates by segregating household units into five zones as a way of
    assigning social vulnerability or household income. Using this vulnerability in conjunction with the TPM
    and the initial state vector, a Markov chain computation simulates most probable
    states to generate a stage history of housing recovery changes for each household.

    The output of the computation is the history of housing recovery changes for each household unit in CSV format.

    Contributors
        | Science: Elaina Sutley, Sara Hamideh
        | Implementation: Nathanael Rosenheim, Santiago Núñez-Corrales, and NCSA IN-CORE Dev Team

    Related publications
        Sutley, E.J. and Hamideh, S., 2020. Postdisaster housing stages: a Markov chain approach to model sequences
        and duration based on social vulnerability. Risk Analysis, 40(12), pp.2675-2695.

    Args:
        incore_client (IncoreClient): Service authentication.
    """

    # threshold and definition per zone based on social vulnerability analysis
    __zone_def_sv = {
        "Z1": {
            "threshold_0": 0.95,
            "below_lower": 0.00,
            "below_upper": 0.20,
            "above_lower": 0.20,
            "above_upper": 1.00,
        },
        "Z2": {
            "threshold_0": 0.85,
            "below_lower": 0.20,
            "below_upper": 0.40,
            "threshold_1": 0.90,
            "middle_lower": 0.00,
            "middle_upper": 0.20,
            "above_lower": 0.40,
            "above_upper": 1.00,
        },
        "Z3": {
            "threshold_0": 0.80,
            "below_lower": 0.40,
            "below_upper": 0.60,
            "threshold_1": 0.90,
            "middle_lower": 0.00,
            "middle_upper": 0.40,
            "above_lower": 0.60,
            "above_upper": 1.00,
        },
        "Z4": {
            "threshold_0": 0.85,
            "below_lower": 0.60,
            "below_upper": 0.80,
            "threshold_1": 0.95,
            "middle_lower": 0.00,
            "middle_upper": 0.40,
            "above_lower": 0.80,
            "above_upper": 1.00,
        },
        "Z5": {
            "threshold_0": 0.95,
            "below_lower": 0.80,
            "below_upper": 1.00,
            "above_lower": 0.00,
            "above_upper": 0.80,
        },
    }

    # threshold and definition per zone based on household income
    __zone_def_hhinc = {
        "Z1": {
            "threshold": 0.95,
            "below_lower": 0.01,
            "below_upper": 0.15,
            "above_lower": 0.10,
            "above_upper": 0.90,
        },
        "Z2": {
            "threshold": 0.85,
            "below_lower": 0.10,
            "below_upper": 0.50,
            "above_lower": 0.10,
            "above_upper": 0.90,
        },
        "Z3": {
            "threshold": 0.80,
            "below_lower": 0.30,
            "below_upper": 0.70,
            "above_lower": 0.10,
            "above_upper": 0.90,
        },
        "Z4": {
            "threshold": 0.85,
            "below_lower": 0.50,
            "below_upper": 0.90,
            "above_lower": 0.10,
            "above_upper": 0.90,
        },
        "Z5": {
            "threshold": 0.95,
            "below_lower": 0.85,
            "below_upper": 0.99,
            "above_lower": 0.10,
            "above_upper": 0.90,
        },
    }

    def __init__(self, incore_client):
        super(HousingRecoverySequential, self).__init__(incore_client)

    def run(self):
        """Execute the HHRS analysis using parameters and input data."""
        # Read parameters
        t_delta = self.get_parameter("t_delta")
        t_final = self.get_parameter("t_final")

        # Load population block data from IN-CORE
        households_csv = self.get_input_dataset(
            "population_dislocation_block"
        ).get_csv_reader()

        # Read the header from households_csv
        header = next(households_csv)

        pop_dis_selectors = [
            "guid",
            "huid",
            "blockid",
            "race",
            "hispan",
            "ownershp",
            "dislocated",
        ]

        # Check if 'hhinc' is in the header
        if "hhinc" in header:
            pop_dis_selectors.append("hhinc")

        households_df = (pd.DataFrame(households_csv))[pop_dis_selectors]

        # Perform  conversions across the dataset from object type into the appropriate type
        households_df["blockid"] = households_df["blockid"].astype("int64")
        households_df["race"] = pd.to_numeric(households_df["race"])
        households_df["hispan"] = pd.to_numeric(households_df["hispan"])
        households_df["ownershp"] = pd.to_numeric(households_df["ownershp"])
        households_df["dislocated"] = households_df["dislocated"] == "True"

        # Check if 'hhinc' is in the header
        if "hhinc" in header:
            households_df["hhinc"] = pd.to_numeric(households_df["hhinc"])

        # Load the transition probability matrix from IN-CORE
        tpm_csv = self.get_input_dataset("tpm").get_csv_reader()
        tpm = pd.DataFrame(list(tpm_csv))

        # Make sure all columns have numeric values
        for c_name in list(tpm.columns.values):
            tpm[c_name] = pd.to_numeric(tpm[c_name])

        tpm = tpm.to_numpy()
        tpm[:, 0] = np.around(tpm[:, 0], 3)

        # Load the initial stage probability vector
        initial_prob_csv = self.get_input_dataset(
            "initial_stage_probabilities"
        ).get_csv_reader()
        initial_prob = pd.DataFrame(list(initial_prob_csv))
        initial_prob["value"] = pd.to_numeric(initial_prob["value"])

        # Obtain the number of CPUs (cores) to execute the analysis with
        user_defined_cpu = 4

        if (
            not self.get_parameter("num_cpu") is None
            and self.get_parameter("num_cpu") > 0
        ):
            user_defined_cpu = self.get_parameter("num_cpu")

        num_workers = AnalysisUtil.determine_parallelism_locally(
            self, len(households_df), user_defined_cpu
        )

        # Chop dataset into `num_size` chunks
        max_chunk_size = int(np.ceil(len(households_df) / num_workers))

        households_df_list = list(
            map(
                lambda x: households_df[
                    x * max_chunk_size : x * max_chunk_size + max_chunk_size
                ],
                list(range(num_workers)),
            )
        )

        # Run the analysis
        result = self.hhrs_concurrent_future(
            self.housing_serial_recovery_model,
            num_workers,
            households_df_list,
            repeat(t_delta),
            repeat(t_final),
            repeat(tpm),
            repeat(initial_prob),
        )

        result_name = self.get_parameter("result_name")
        self.set_result_csv_data(
            "ds_result", result, name=result_name, source="dataframe"
        )

        return True

    def hhrs_concurrent_future(self, function_name, parallelism, *args):
        """Utilizes concurrent.future module.

        Args:
            function_name (function): The function to be parallelized.
            parallelism (int): Number of workers in parallelization.
            *args: All the arguments in order to pass into parameter function_name.

        Returns:
            pd.DataFrame: outcome DataFrame containing the results from the concurrent function.

        """
        output_ds = pd.DataFrame()

        with concurrent.futures.ProcessPoolExecutor(
            max_workers=parallelism
        ) as executor:
            for ret in executor.map(function_name, *args):
                output_ds = pd.concat([output_ds, ret], ignore_index=True)

        return output_ds

    def housing_serial_recovery_model(
        self, households_df, t_delta, t_final, tpm, initial_prob
    ):
        """Performs the computation of the model as indicated in Sutley and Hamide (2020).

        Args:
            households_df (pd.DataFrame): Households with population dislocation data.
            t_delta (float): Time step size.
            t_final (float): Final time.
            tpm (np.Array): Transition probability matrix.
            initial_prob (pd.DataFrame): Initial probability Markov vector.

        Returns:
            pd.DataFrame: outcome of the HHRS model for a given household dataset.
        """
        seed = self.get_parameter("seed")
        rng = np.random.RandomState(seed)

        sv_result = self.get_input_dataset("sv_result")
        are_zones_from_sv = False

        if sv_result is not None:
            are_zones_from_sv = True
            sv_result = sv_result.get_dataframe_from_csv(low_memory=False)

            # turn fips code to string for ease of matching
            sv_result["FIPS"] = sv_result["FIPS"].astype(str)

            # Compute the social vulnerability zone using known factors
            households_df = self.compute_social_vulnerability_zones(
                sv_result, households_df
            )
        else:
            # If sv result is Null, calculate the zones by using household income (hhinc)
            households_df = self.compute_zones_by_household_income(households_df)

        # Set the number of Markov chain stages
        stages = int(t_final / t_delta)

        # Data structure for selection operations
        initial_prob["cumulative"] = initial_prob["value"].cumsum()

        # Obtain number of households with social vulnerability zones
        num_households = households_df.shape[0]

        # Obtain a social vulnerability score stochastically per household
        # We use them later to construct the final output dataset
        sv_scores = self.compute_social_vulnerability_values(
            households_df, num_households, rng, are_zones_from_sv
        )

        # We store Markov states as a list of numpy arrays for convenience and add each one by one
        markov_stages = np.zeros((stages, num_households))

        for household in range(0, num_households):
            if households_df["dislocated"].iat[household]:
                spin = rng.rand()

                if spin < initial_prob["cumulative"][0]:
                    markov_stages[0][household] = 1.0
                elif spin < initial_prob["cumulative"][1]:
                    markov_stages[0][household] = 2.0
                else:
                    markov_stages[0][household] = 3.0
            else:
                markov_stages[0][household] = 4.0

        # With all data in place, run the Markov chain (Cell 36 onwards)

        # Iterate over all stages
        for t in range(1, stages):
            # Generate a vector with random numbers for all households
            spins = rng.rand(num_households)

            # Iterate over all households
            for household in range(0, num_households):
                stage_val = markov_stages[t - 1][household]

                if stage_val == 5:
                    # If the household has already transitioned to stage 5, the household will remain in stage 5.
                    markov_stages[t][household] = 5
                else:
                    # Obtain the vector used to setup the stage
                    mv_index = np.where(tpm[:, 0] == sv_scores[household])[0][0]
                    lower = int((stage_val - 1) * 4 + 1)
                    upper = int(stage_val * 4 + 1)
                    mv = tpm[mv_index, lower:upper]
                    markov_vector = [mv[0], sum(mv[0:2]), sum(mv[0:3])]

                    # Set the new stage using the Markov property
                    if spins[household] < markov_vector[0]:
                        markov_stages[t][household] = 1
                    elif spins[household] < markov_vector[1]:
                        markov_stages[t][household] = 2
                    elif spins[household] < markov_vector[2]:
                        markov_stages[t][household] = 3
                    else:
                        markov_stages[t][household] = 4

                    # Alternative method: use deques to simplify the algorithm

                    # We create three sliding windows into the past, one for 12 steps, one for 24 ad one for all stages
                    # regressions_12 = cl.deque(maxlen=12)
                    # regressions_24 = cl.deque(maxlen=24)
                    # regressions_all = cl.deque()

                    # We check if during this step there was a regression
                    # if markov_stages[t][household] < markov_stages[t - 1][household]:
                    #    regression_happened = 1
                    # else:
                    #    regression_happened = 0

                    # And add the result to both queues
                    # regressions_12.append(regression_happened)
                    # regressions_24.append(regression_happened)
                    # regressions_all.append(regression_happened)

                    # Finally test the stage 5 condition per queue and a special condition when t reaches 85.
                    # if (sum(regressions_12) > 4) or \
                    #    (sum(regressions_24) > 7) or \
                    #    (sum(regressions_all) > 10) or \
                    #    t == 85:
                    #    markov_stages[t][household] = 5

                    if t >= 1:
                        # Check every timestep that occurred prior to the current timestep.
                        regressions = self.compute_regressions(
                            markov_stages, household, 1, t
                        )

                        if regressions > 10:
                            markov_stages[t][household] = 5
                    if t >= 12:
                        # Check the previous 12 timesteps that occurred prior to the current timestep.
                        regressions = self.compute_regressions(
                            markov_stages, household, t - 11, t
                        )

                        # If the number of regressive steps in the household's past 12 timesteps is greater than 4,
                        # the household transitions to stage 5.
                        if regressions > 4:
                            markov_stages[t][household] = 5
                    if t >= 24:
                        # Check the previous 24 timesteps that occurred prior to the current timestep.
                        regressions = self.compute_regressions(
                            markov_stages, household, t - 23, t
                        )

                        # If the number of regressive steps in the household's past 24 timesteps is greater than 7,
                        # the household transitions to stage 5.
                        if regressions > 7:
                            markov_stages[t][household] = 5
                    if t == 85:
                        # If the household has not reached stage 4 after 85 timesteps, the household transitions to
                        # stage 5.
                        if markov_stages[t][household] != 4:
                            markov_stages[t][household] = 5

        # We make a copy to be used for numerical purposes, from which drop some of the columns
        result = pd.DataFrame()
        result["guid"] = households_df["guid"]
        result["huid"] = households_df["huid"]
        result["Zone"] = households_df["Zone"]
        result["zone_indic"] = households_df["zone_indic"]
        result["SV"] = sv_scores
        column_names = [str(i) for i in range(1, stages + 1)]

        for i, c in enumerate(column_names):
            result[c] = markov_stages[i]

        return result

    @staticmethod
    def compute_social_vulnerability_zones(sv_result, households_df):
        """
        Compute the social vulnerability score based on dislocation attributes. Updates the dislocation dataset
        by adding a new `Zone` column and removing values with missing Zone.

        Args:
            sv_result (pd.DataFrame): output from social vulnerability analysis
            households_df (pd.DataFrame): Vector position of a household.

        Returns:
            pd.DataFrame: Social vulnerability score.

        """
        # if FIPS has 11 digits (Tract level)
        if len(sv_result["FIPS"].iloc[0]) == 11:
            households_df["blockfips"] = (
                households_df["blockid"].apply(lambda x: str(x)[:11]).astype(str)
            )
        # if FIPS has 12 digits (Block Group level)
        elif len(sv_result["FIPS"].iloc[0]) == 12:
            households_df["blockfips"] = (
                households_df["blockid"].apply(lambda x: str(x)[:12]).astype(str)
            )

        households_df = households_df.merge(
            sv_result[["FIPS", "zone"]], left_on="blockfips", right_on="FIPS"
        )
        # e.g.Medium Vulnerable (zone3) extract the number 3 to construct Z3
        households_df["Zone"] = households_df["zone"].apply(lambda row: "Z" + row[-2])

        # add an indicator showing the zones are from Social Vulnerability analysis
        households_df["zone_indic"] = "SV"

        return households_df[households_df["Zone"] != "missing"]

    def compute_social_vulnerability_values(
        self, households_df, num_households, rng, are_zones_from_sv
    ):
        """
        Compute the social vulnerability score of a household depending on its zone
        Args:
            households_df (pd.DataFrame): Information about household zones.
            num_households (int): Number of households.
            rng (np.RandomState): Random state to draw pseudo-random numbers from.
            are_zones_from_sv: Boolean indicating whether zones are from social vulnerability analysis.
        Returns:
            pd.Series: social vulnerability scores.
        """
        # Social vulnerability zone generator: this generalizes the code in the first version
        sv_scores = np.zeros(num_households)
        zones = households_df["Zone"].to_numpy()

        # zones from social vulnerability analusis
        if are_zones_from_sv:
            zone_def = self.get_input_dataset("zone_def_sv")
            if zone_def is None:
                zone_def = self.__zone_def_sv
            else:
                zone_def = zone_def.get_json_reader()

        # zones caulculated by household income (hhinc)
        else:
            zone_def = self.get_input_dataset("zone_def_hhinc")
            if zone_def is None:
                zone_def = self.__zone_def_hhinc
            else:
                zone_def = zone_def.get_json_reader()

        for household in range(0, num_households):
            spin = rng.rand()
            zone = zones[household]

            if are_zones_from_sv:
                if spin < zone_def[zone]["threshold_0"]:
                    sv_scores[household] = round(
                        rng.uniform(
                            zone_def[zone]["below_lower"],
                            zone_def[zone]["below_upper"],
                        ),
                        3,
                    )

                # for zone 2, 3, 4 there is additional middle range
                elif (
                    "threshold_1" in zone_def[zone].keys()
                    and spin < zone_def[zone]["threshold_1"]
                ):
                    sv_scores[household] = round(
                        rng.uniform(
                            zone_def[zone]["middle_lower"],
                            zone_def[zone]["middle_upper"],
                        ),
                        3,
                    )
                else:
                    sv_scores[household] = round(
                        rng.uniform(
                            zone_def[zone]["above_lower"],
                            zone_def[zone]["above_upper"],
                        ),
                        3,
                    )

            else:
                if spin < zone_def[zone]["threshold"]:
                    sv_scores[household] = round(
                        rng.uniform(
                            zone_def[zone]["below_lower"], zone_def[zone]["below_upper"]
                        ),
                        3,
                    )
                else:
                    sv_scores[household] = round(
                        rng.uniform(
                            zone_def[zone]["above_lower"], zone_def[zone]["above_upper"]
                        ),
                        3,
                    )

        return sv_scores

    @staticmethod
    def compute_zones_by_household_income(households_df):
        """
        Compute the zones based on household income. Updates the household dataset
        by adding a new `Zone` column and removing values with missing Zone.

        Args:
            households_df (pd.DataFrame): Vector position of a household.

        Returns:
            households_df (pd.DataFrame): Vector position of a household with additional zones.

        """
        zone_map = {0: "Z5", 1: "Z4", 2: "Z3", 3: "Z2", 4: "Z1", np.nan: "missing"}

        households_df["Zone"] = "missing"
        households_df.loc[households_df["hhinc"] == 5, "Zone"] = zone_map[4]
        households_df.loc[households_df["hhinc"] == 4, "Zone"] = zone_map[3]
        households_df.loc[households_df["hhinc"] == 3, "Zone"] = zone_map[2]
        households_df.loc[households_df["hhinc"] == 2, "Zone"] = zone_map[1]
        households_df.loc[households_df["hhinc"] == 1, "Zone"] = zone_map[0]

        # add an indicator showing the zones are from Social Vulnerability analysis
        households_df["zone_indic"] = "hhinc"

        return households_df[households_df["Zone"] != "missing"]

    @staticmethod
    def compute_regressions(markov_stages, household, lower, upper):
        """
        Compute regressions for a given household in the interval near t using the interval [lower, upper], and
        adjust for stage inversion at the upper boundary.

        Args:
            markov_stages (np.Array): Markov chain stages for all households.
            household (int): Index of the household.
            lower (int): Lower index to check past history.
            upper (int): Upper index to check past history.

        Returns:
            int: Number of regressions between a given time window.

        """
        regressions = 0

        # Check the previous timesteps between [lower, upper] prior to the current timestep.

        for t in range(lower, upper):
            if markov_stages[t][household] < markov_stages[t - 1][household]:
                regressions += 1

        return regressions

    def get_spec(self):
        """Get specifications of the housing serial recovery model.

        Returns:
            obj: A JSON object of specifications of the housing serial recovery model.

        """
        return {
            "name": "housing-recovery-serial",
            "description": "Household-level housing recovery serial model",
            "input_parameters": [
                {
                    "id": "result_name",
                    "required": True,
                    "description": "Result CSV dataset name",
                    "type": str,
                },
                {
                    "id": "t_delta",
                    "required": True,
                    "description": "size of the analysis time step",
                    "type": float,
                },
                {
                    "id": "t_final",
                    "required": True,
                    "description": "total duration",
                    "type": float,
                },
                {
                    "id": "seed",
                    "required": False,
                    "description": "Seed to ensure replication of the Markov Chain path"
                    "in connection with Population Dislocation.",
                    "type": int,
                },
                {
                    "id": "num_cpu",
                    "required": False,
                    "description": "If using parallel execution, the number of cpus to request",
                    "type": int,
                },
            ],
            "input_datasets": [
                {
                    "id": "population_dislocation_block",
                    "required": True,
                    "description": "A csv file with population dislocation result "
                    "aggregated to the block group level",
                    "type": ["incore:popDislocation"],
                },
                {
                    "id": "tpm",
                    "required": True,
                    "description": "Transition probability matrix in CSV format that specifies "
                    "the corresponding Markov chain per social vulnerability level.",
                    "type": ["incore:houseRecTransitionProbMatrix"],
                },
                {
                    "id": "initial_stage_probabilities",
                    "required": True,
                    "description": "initial mass probability function for stage 0 of the Markov Chain",
                    "type": ["incore:houseRecInitialStageProbability"],
                },
                {
                    "id": "sv_result",
                    "required": False,
                    "description": "A csv file with zones containing demographic factors"
                    "qualified by a social vulnerability score",
                    "type": ["incore:socialVulnerabilityScore"],
                },
                {
                    "id": "zone_def_sv",
                    "required": False,
                    "description": "A json file with thresholds and definitions per zone "
                    "based on social vulnerability analysis",
                    "type": ["incore:zoneDefinitionsSocialVulnerability"],
                },
                {
                    "id": "zone_def_hhinc",
                    "required": False,
                    "description": "A json file with thresholds and definitions per zone based on household income",
                    "type": ["incore:zoneDefinitionsHouseholdIncome"],
                },
            ],
            "output_datasets": [
                {
                    "id": "ds_result",
                    "parent_type": "housing_recovery_block",
                    "description": "A csv file with housing recovery sequences"
                    "at the individual household level",
                    "type": "incore:housingRecoveryHistory",
                }
            ],
        }
