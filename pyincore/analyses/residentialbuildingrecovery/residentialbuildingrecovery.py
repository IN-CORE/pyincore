# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import numpy as np
import pandas as pd
import time

import warnings

from pyincore import BaseAnalysis, RepairService
from pyincore.analyses.buildingdamage.buildingutil import BuildingUtil


class ResidentialBuildingRecovery(BaseAnalysis):
    """
    This analysis computes the recovery time needed for each residential building from any damage states to receive the
    full restoration. Currently, supported hazards are tornadoes.

    The methodology incorporates the multi-layer Monte Carlo simulation approach and determines the two-step recovery
    time that includes delay and repair. The delay model was modified based on the REDi framework and calculated the
    end-result outcomes resulted from delay impeding factors such as post-disaster inspection, insurance claim, and
    government permit. The repair model followed the FEMA P-58 approach and was controlled by fragility functions.

    The outputs of this analysis is a CSV file with time-stepping recovery probabilities at the building level.

    Contributors
        | Science: Wanting Lisa Wang, John W. van de Lindt
        | Implementation: Wanting Lisa Wang, Gowtham Naraharisetty, and NCSA IN-CORE Dev Team

    Related publications
        Wang, Wanting Lisa, and John W. van de Lindt. "Quantitative Modeling of Residential Building Disaster Recovery
        and Effects of Pre-and Post-event Policies." International Journal of Disaster Risk Reduction (2021): 102259.

    Args:
        incore_client (IncoreClient): Service authentication.

    """

    def __init__(self, incore_client):
        self.repairsvc = RepairService(incore_client)

        super(ResidentialBuildingRecovery, self).__init__(incore_client)

    def run(self):
        """Executes the residential building recovery analysis.

        Returns:
            bool: True if successful, False otherwise.

        """
        # TODO: Start using seed
        # seed = self.get_parameter("seed")

        num_samples = self.get_parameter("num_samples")
        result_name = self.get_parameter("result_name")

        repair_key = self.get_parameter("repair_key")
        if repair_key is None:
            repair_key = BuildingUtil.DEFAULT_REPAIR_KEY
            self.set_parameter("repair_key", repair_key)

        buildings = self.get_input_dataset("buildings").get_inventory_reader()
        buildings = list(buildings)
        sample_damage_states = self.get_input_dataset(
            "sample_damage_states"
        ).get_dataframe_from_csv(low_memory=False)
        socio_demographic_data = self.get_input_dataset(
            "socio_demographic_data"
        ).get_dataframe_from_csv(low_memory=False)
        # socio_demographic_data.set_index("guid", inplace=True)
        financial_resources = self.get_input_dataset(
            "financial_resources"
        ).get_dataframe_from_csv(low_memory=False)
        redi_delay_factors = self.get_input_dataset(
            "delay_factors"
        ).get_dataframe_from_csv(low_memory=False)

        # Returns dataframe
        total_delay, recovery, time_stepping_recovery = self.residential_recovery(
            buildings,
            sample_damage_states,
            socio_demographic_data,
            financial_resources,
            redi_delay_factors,
            num_samples,
        )

        self.set_result_csv_data(
            "total_delay", total_delay, result_name + "_delay", "dataframe"
        )
        self.set_result_csv_data(
            "recovery", recovery, result_name + "_recovery", "dataframe"
        )
        self.set_result_csv_data(
            "time_stepping_recovery",
            time_stepping_recovery,
            result_name + "_time_stepping_recovery",
            "dataframe",
        )

        return True

    def residential_recovery(
        self,
        buildings,
        sample_damage_states,
        socio_demographic_data,
        financial_resources,
        redi_delay_factors,
        num_samples,
    ):
        """
        Calculates residential building recovery for buildings

        Args:
            buildings(list): Buildings dataset
            sample_damage_states (pd.DataFrame): Sample damage states
            socio_demographic_data (pd.DataFrame): Socio-demographic data for household income groups
            financial_resources (pd.DataFrame): Financial resources by household income groups
            redi_delay_factors (pd.DataFrame): Delay factors based on REDi framework
            num_samples (int): number of sample scenarios to use

        Returns:
            dict: dictionary with id/guid and residential recovery for each quarter

        """

        start_household_income_prediction = time.process_time()
        household_income_prediction = (
            ResidentialBuildingRecovery.household_income_prediction(
                socio_demographic_data, num_samples
            )
        )
        end_start_household_income_prediction = time.process_time()
        print(
            "Finished executing household_income_prediction() in "
            + str(
                end_start_household_income_prediction
                - start_household_income_prediction
            )
            + " secs"
        )

        household_aggregation = ResidentialBuildingRecovery.household_aggregation(
            household_income_prediction
        )
        end_household_aggregation = time.process_time()
        print(
            "Finished executing household_aggregation() in "
            + str(end_household_aggregation - end_start_household_income_prediction)
            + " secs"
        )

        financing_delay = ResidentialBuildingRecovery.financing_delay(
            household_aggregation, financial_resources
        )
        end_financing_delay = time.process_time()
        print(
            "Finished executing financing_delay() in "
            + str(end_financing_delay - end_household_aggregation)
            + " secs"
        )

        total_delay = ResidentialBuildingRecovery.total_delay(
            sample_damage_states, redi_delay_factors, financing_delay
        )
        end_total_delay = time.process_time()
        print(
            "Finished executing total_delay() in "
            + str(end_total_delay - end_financing_delay)
            + " secs"
        )

        recovery = self.recovery_rate(buildings, sample_damage_states, total_delay)
        end_recovery = time.process_time()
        print(
            "Finished executing recovery_rate() in "
            + str(end_recovery - end_total_delay)
            + " secs"
        )

        time_stepping_recovery = ResidentialBuildingRecovery.time_stepping_recovery(
            recovery
        )
        end_time_stepping_recovery = time.process_time()
        print(
            "Finished executing time_stepping_recovery() in "
            + str(end_time_stepping_recovery - end_recovery)
            + " secs"
        )

        end_time = time.process_time()
        print(
            "Analysis completed in "
            + str(end_time - start_household_income_prediction)
            + " secs"
        )

        return total_delay, recovery, time_stepping_recovery

    @staticmethod
    def household_income_prediction(income_groups, num_samples):
        """Get Income group prediction for each household

        Args:
            income_groups (pd.DataFrame): Socio-demographic data with household income group prediction.
            num_samples (int): Number of sample scenarios.

        Returns:
            pd.DataFrame: Income group prediction for each household

        """

        blockid = income_groups.groupby("blockid")
        prediction_results = pd.DataFrame()

        for name, group in blockid:
            # Prepare data for numpy processing
            group_size = group.shape[0]
            group_hhinc_values = group["hhinc"].values

            # Compute normal distribution parameters from group data

            # suppress nan warnings.
            # 1. Mean of nans - https://stackoverflow.com/questions/29688168/
            # mean-nanmean-and-warning-mean-of-empty-slice
            # 2. Mean of empty slice - https://stackoverflow.com/questions/43301112/
            # mean-of-empty-slice-and-degrees-of-freedom-0
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=RuntimeWarning)
                mean = np.nanmean(group_hhinc_values)
                std = np.nanstd(group_hhinc_values)

            if np.isnan(mean):
                mean = 3
            if np.isnan(std):
                std = 0
            # Directly compute the indices of NaN values in the hhinc vector
            group_nan_idx = np.where(np.isnan(group_hhinc_values))
            number_nan = len(group_nan_idx[0])

            # Now, generate a numpy matrix to hold the samples for the group
            group_samples = np.zeros((num_samples, group_size))

            for i in range(num_samples):
                # Note to Lisa that this is not the appropriate distribution. Since this case is discrete,
                # the natural choice is a Bernoulli distribution parameterized as to approximate the
                # corresponding normal.
                sample = np.random.normal(mean, std, number_nan)
                sample[np.where(sample > 5)] = 5
                sample[np.where(sample < 1)] = 1
                group_samples[i, :] = group_hhinc_values
                group_samples[i, group_nan_idx[0]] = np.around(sample)
                # Now reassemble into Pandas DataFrame
                group["sample_{}".format(i)] = group_samples[i, :]

            prediction_results = pd.concat(
                [prediction_results, group], ignore_index=True
            )

        return prediction_results

    @staticmethod
    def household_aggregation(household_income_predictions):
        """Gets household aggregation of income groups at the building level.

        Args:
            household_income_predictions (pd.DataFrame): Income group prediction for each household

        Returns:
            pd.DataFrame: Results of household aggregation of income groups at the building level.
        """

        # Drop all unnecessary columns first
        household_income_predictions_dropped = household_income_predictions.drop(
            columns=["huid", "blockid", "hhinc"]
        )
        guid_group = household_income_predictions_dropped.groupby("guid")

        # Obtain sample column names
        colnames = list(household_income_predictions_dropped.columns[1:])

        # Iterate over all groups
        new_groups = []

        for name, group in guid_group:
            # Obtain guids
            local_guids = group["guid"]

            # Remove guids
            no_guids = group.drop(columns=["guid"]).to_numpy()

            # Compute the maxima of all columns
            maxima = list(no_guids.max(axis=0))

            # Generate a matrix to store the results efficiently
            num_guids = no_guids.shape[0]
            num_cols = len(colnames)
            no_guids_maxima = np.zeros((num_guids, num_cols))

            for i in range(0, num_cols):
                no_guids_maxima[:, i] = maxima[i]

            group_new = pd.DataFrame(
                no_guids_maxima, columns=colnames, index=group.index
            )
            group_new.insert(0, "guid", local_guids)
            new_groups.append(group_new.head(1))

        # Construct a new DataFrame
        household_aggregation_results = pd.concat(new_groups).reset_index(drop=True)

        return household_aggregation_results

    @staticmethod
    def financing_delay(household_aggregated_income_groups, financial_resources):
        """Gets financing delay, the percentages calculated are the probabilities of housing units financed by
        different resources.

        Args:
            household_aggregated_income_groups (pd.DataFrame): Household aggregation of income groups at the building
                level.
            financial_resources (pd.DataFrame): Financial resources by household income groups.

        Returns:
            pd.DataFrame: Results of financial delay
        """
        colnames = list(household_aggregated_income_groups.columns)[1:]

        # Save guid's for later
        household_guids = household_aggregated_income_groups["guid"]

        # Convert household aggregated income to numpy
        samples_np = household_aggregated_income_groups.drop(
            columns=["guid"]
        ).to_numpy()

        # Number of guids
        num_households = household_guids.shape[0]
        num_samples = len(colnames)

        # Convert the sample matrix to numpy
        resources_np = financial_resources.to_numpy()

        # Also, convert financial resources to numpy to perform linear algebra
        hhinc = resources_np[0:5, 0]
        sources = resources_np[:, 1:]

        # Give names to mean and sigma indices
        mean_idx = 5
        sigma_idx = 6

        for household in range(0, num_households):
            for sample in range(0, num_samples):
                value = samples_np[household, sample]
                idx = np.where(hhinc == value)

                # 1. Sample the lognormal distribution vectorially
                lognormal_vec = np.random.lognormal(
                    np.log(sources[mean_idx, :]), sources[sigma_idx, :]
                )

                # 2. Compute the delay using the dot product of the prior vector and sources for the current index,
                # round to one significant figure
                samples_np[household, sample] = np.round(
                    np.dot(lognormal_vec, sources[idx, :].flatten()), 1
                )

        financing_delay = pd.DataFrame(
            samples_np, columns=colnames, index=household_aggregated_income_groups.index
        )
        financing_delay.insert(0, "guid", household_guids)

        return financing_delay

    @staticmethod
    def total_delay(sample_damage_states, redi_delay_factors, financing_delay):
        """Calculates total delay by combining financial delay and other factors from REDi framework

        Args:
            sample_damage_states (pd.DataFrame): Building inventory damage states.
            redi_delay_factors (pd.DataFrame): Delay impeding factors such as post-disaster inspection, insurance claim,
                and government permit based on building's damage state.
            financing_delay (pd.DataFrame): Financing delay, the percentages calculated are the probabilities of housing
                units financed by different resources.

        Returns:
            pd.DataFrame: Total delay time of financial delay and other factors from REDi framework.
        """

        # Obtain the column names
        colnames = list(financing_delay.columns)[1:]

        # Perform an inner join to ensure only households with damage states are processed
        merged_delay = pd.merge(financing_delay, sample_damage_states, on="guid")

        # Obtain the guids
        merged_delay_guids = merged_delay["guid"]

        # Obtain the damage states
        merged_delay_damage_states = merged_delay["sample_damage_states"]

        # Convert to numpy
        samples_np = merged_delay.drop(
            columns=["guid", "sample_damage_states"]
        ).to_numpy()
        num_samples = len(colnames)

        # First, we decompose redi_delay_factors into two dictionaries that can be used to compute vector operations
        redi_idx = dict(
            zip(
                redi_delay_factors["Building_specific_conditions"],
                redi_delay_factors.index,
            )
        )

        # Next, we produce two intermediate numpy matrices: one for med and one for sdv
        redi_med = redi_delay_factors[
            ["Ins_med", "Enmo_med", "Como_med", "Per_med"]
        ].to_numpy()
        redi_sdv = redi_delay_factors[
            ["Ins_sdv", "Enmo_sdv", "Como_sdv", "Per_sdv"]
        ].to_numpy()

        # Define indices to facilitate interpretation of the code
        inspection_idx = 0
        engineer_idx = 1
        contractor_idx = 2
        permit_idx = 3

        for i, ds_list in enumerate(list(merged_delay_damage_states)):
            samples_mcs = ds_list.split(",")

            for j in range(num_samples):
                # TODO: ask why there are many more damage states than samples
                # Obtain the index for the corresponding damage state
                dmg_state_idx = redi_idx[samples_mcs[j]]

                # Use the index to select the appropriate mean and stdev vectors
                mean_vec = redi_med[dmg_state_idx, :]
                sdv_vec = redi_sdv[dmg_state_idx, :]

                # Compute the delay vector
                delay_vec = np.random.lognormal(np.log(mean_vec), sdv_vec)

                # Compute the delay using that vector and financing delays, already computed in the prior step
                samples_np[i, j] = np.round(
                    delay_vec[inspection_idx]
                    + np.max(
                        [
                            delay_vec[engineer_idx],
                            samples_np[i, j],
                            delay_vec[contractor_idx],
                        ]
                    )
                    + delay_vec[permit_idx]
                )

        total_delay = pd.DataFrame(samples_np, columns=colnames)
        total_delay.insert(0, "guid", merged_delay_guids)

        return total_delay

    def recovery_rate(self, buildings, sample_damage_states, total_delay):
        """Gets total time required for each building to receive full restoration. Determined by the combination of
        delay time and repair time

        Args:
            buildings (list): List of buildings
            sample_damage_states (pd.DataFrame): Samples' damage states
            total_delay (pd.DataFrame): Total delay time of financial delay and other factors from REDi framework.

        Returns:
            pd.DataFrame: Recovery rates of all buildings for each sample
        """

        repair_key = self.get_parameter("repair_key")
        repair_sets = self.repairsvc.match_inventory(
            self.get_input_dataset("dfr3_mapping_set"), buildings, repair_key
        )
        repair_sets_by_guid = (
            {}
        )  # get repair sets by guid so they can be mapped with output of monte carlo

        # This is sort of a workaround until we define Repair Curve models and abstract this out there
        for i, b in enumerate(buildings):
            repair_sets_by_guid[b["properties"]["guid"]] = repair_sets[str(i)]

        # Obtain the column names
        colnames = list(total_delay.columns)[1:]

        # Perform an inner join to ensure only households with damage states are processed
        merged_delay = pd.merge(total_delay, sample_damage_states, on="guid")

        # Obtain the guids
        merged_delay_guids = merged_delay["guid"]

        # Obtain the damage states
        merged_delay_damage_states = merged_delay["sample_damage_states"]

        # Convert to numpy
        samples_np = merged_delay.drop(
            columns=["guid", "sample_damage_states"]
        ).to_numpy()
        num_samples = len(colnames)
        num_households = samples_np.shape[0]

        # Generate a long numpy matrix for combined N1, N2 samples
        samples_n1_n2 = np.zeros((num_households, num_samples * num_samples))

        # Now, we define an internal function to take care of the index for the prior case
        # Now, we define an internal function to take care of the index for the prior case
        def idx(x, y):
            return x * num_samples + y

        for household in range(0, num_households):
            # Obtain the damage states
            mapped_repair = repair_sets_by_guid[merged_delay_guids.iloc[household]]
            samples_mcs = merged_delay_damage_states.iloc[household].split(",")

            # Use a lambda to obtain the damage state in numeric form. Note that since damage states are single digits,
            # it suffices to look at the last character and convert into an integer value. Do this computation once
            # per household only.
            extract_ds = lambda x: int(x[-1])  # noqa: E731
            samples_mcs_ds = list(map(extract_ds, samples_mcs))

            # Now, perform the two nested loops, using the indexing function to simplify the syntax.
            for i in range(0, num_samples):
                state = samples_mcs_ds[i]
                percent_func = np.random.random(num_samples)
                # NOTE: Even though the kwarg name is "repair_time", it actually takes  percent of functionality. DFR3
                # system currently doesn't have a way to represent the name correctly when calculating the inverse.
                repair_time = (
                    mapped_repair.repair_curves[state].solve_curve_for_inverse(
                        hazard_values={},
                        curve_parameters=mapped_repair.curve_parameters,
                        **{"repair_time": percent_func},
                    )
                    / 7
                )

                for j in range(0, num_samples):
                    samples_n1_n2[household, idx(i, j)] = round(
                        samples_np[household, i] + repair_time[j], 1
                    )

        # Now, generate all the labels using list comprehension outside the loops
        colnames = [
            f"sample_{i}_{j}"
            for i in range(0, num_samples)
            for j in range(0, num_samples)
        ]
        recovery_time = pd.DataFrame(samples_n1_n2, columns=colnames)
        recovery_time.insert(0, "guid", merged_delay_guids)

        return recovery_time

    @staticmethod
    def time_stepping_recovery(recovery_results):
        """Converts results to a time frame. Currently gives results for 16 quarters over 4 year.

        Args:
            recovery_results (pd.DataFrame): Total recovery time of financial delay and other factors from REDi framework.

        Returns:
            pd.DataFrame: Time formatted recovery results.

        """
        time_step = 90 / 7  # a quarter in weeks
        year = 4

        total_time = time_step * np.linspace(0, 4 * year, num=17, endpoint=True)

        # Save guid's for later
        recovery_results_guids = recovery_results["guid"]

        # Convert household aggregated income to numpy
        samples_n1_n2 = recovery_results.drop(columns=["guid"]).to_numpy()

        # Number of guids
        num_households = recovery_results.shape[0]
        num_samples = samples_n1_n2.shape[1]
        num_times = len(total_time)

        # Generate a numpy to hold the results as desired
        times_np = np.full((num_households, num_times), 1111.0)

        for household in range(0, num_households):
            for i in range(len(total_time)):
                fun_state = (
                    np.count_nonzero(samples_n1_n2[household, :] < total_time[i])
                    / num_samples
                )
                times_np[household, i] = np.round(fun_state, 2)

        colnames = [f"quarter_{i}" for i in range(0, num_times)]

        time_stepping_recovery = pd.DataFrame(times_np, columns=colnames)
        time_stepping_recovery.insert(0, "guid", recovery_results_guids)

        return time_stepping_recovery

    def get_spec(self):
        """Get specifications of the residential building recovery analysis.

        Returns:
            obj: A JSON object of specifications of the residential building recovery analysis.

        """
        return {
            "name": "residential-building-recovery",
            "description": "calculate residential building recovery",
            "input_parameters": [
                {
                    "id": "result_name",
                    "required": True,
                    "description": "name of the result",
                    "type": str,
                },
                {
                    "id": "num_samples",
                    "required": True,
                    "description": "Number of sample scenarios",
                    "type": int,
                },
                {
                    "id": "repair_key",
                    "required": False,
                    "description": "Repair key to use in mapping dataset",
                    "type": str,
                },
                {
                    "id": "seed",
                    "required": False,
                    "description": "Initial seed for the probabilistic model",
                    "type": int,
                },
            ],
            "input_datasets": [
                {
                    "id": "buildings",
                    "required": True,
                    "description": "Building Inventory",
                    "type": [
                        "ergo:buildingInventoryVer4",
                        "ergo:buildingInventoryVer5",
                        "ergo:buildingInventoryVer6",
                        "ergo:buildingInventoryVer7",
                    ],
                },
                {
                    "id": "dfr3_mapping_set",
                    "required": True,
                    "description": "DFR3 Mapping Set Object",
                    "type": ["incore:dfr3MappingSet"],
                },
                {
                    "id": "sample_damage_states",
                    "required": False,
                    "description": "Sample damage states",
                    "type": ["incore:sampleDamageState"],
                },
                {
                    "id": "socio_demographic_data",
                    "required": True,
                    "description": "Socio-demographic data with household income group predictions",
                    "type": ["incore:socioDemograhicData"],
                },
                {
                    "id": "financial_resources",
                    "required": True,
                    "description": "Financial resources by household income groups",
                    "type": ["incore:householdFinancialResources"],
                },
                {
                    "id": "delay_factors",
                    "required": True,
                    "description": "Delay impeding factors such as post-disaster inspection, insurance claim, "
                    "and government permit based on building's damage state. Provided by REDi framework",
                    "type": ["incore:buildingRecoveryFactors"],
                },
            ],
            "output_datasets": [
                {
                    "id": "total_delay",
                    "description": "CSV file of residential building delay time",
                    "type": "incore:buildingRecoveryDelay",
                },
                {
                    "id": "recovery",
                    "description": "CSV file of residential  building recovery time",
                    "type": "incore:buildingRecoveryTime",
                },
                {
                    "id": "time_stepping_recovery",
                    "description": "CSV file of residential building recovery percent",
                    "type": "incore:buildingRecovery",
                },
            ],
        }
