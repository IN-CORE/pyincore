# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import numpy as np
import pandas as pd
import time

from pyincore import BaseAnalysis, RepairService
from pyincore.analyses.buildingdamage.buildingutil import BuildingUtil


class CommercialBuildingRecovery(BaseAnalysis):
    """
    This analysis computes the recovery time needed for each commercial building from any damage states to receive the
    full restoration. Currently, supported hazards are tornadoes.

    The methodology incorporates the multi-layer Monte Carlo simulation approach and determines the two-step recovery
    time that includes delay and repair. The delay model was modified based on the REDi framework and calculated the
    end-result outcomes resulted from delay impeding factors such as post-disaster inspection, insurance claim,
    financing and government permit. The repair model followed the FEMA P-58 approach and was controlled by fragility
    functions.

    The outputs of this analysis is a CSV file with time-stepping recovery probabilities at the building level.

    Contributors
        | Science: Wanting Lisa Wang, John W. van de Lindt
        | Implementation: Wanting Lisa Wang, and NCSA IN-CORE Dev Team

    Related publications
        Wang, W.L., Watson, M., van de Lindt, J.W. and Xiao, Y., 2023. Commercial Building Recovery Methodology for Use
        in Community Resilience Modeling. Natural Hazards Review, 24(4), p.04023031.

    Args:
        incore_client (IncoreClient): Service authentication.

    """

    def __init__(self, incore_client):
        self.repairsvc = RepairService(incore_client)

        super(CommercialBuildingRecovery, self).__init__(incore_client)

    def run(self):
        """Executes the commercial building recovery analysis.

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
        mcs_failure = self.get_input_dataset("mcs_failure").get_dataframe_from_csv(
            low_memory=False
        )
        redi_delay_factors = self.get_input_dataset(
            "delay_factors"
        ).get_dataframe_from_csv(low_memory=False)
        building_dmg = self.get_input_dataset("building_dmg").get_dataframe_from_csv(
            low_memory=False
        )

        # Returns dataframe
        total_delay, recovery, time_stepping_recovery = self.commercial_recovery(
            buildings,
            sample_damage_states,
            mcs_failure,
            redi_delay_factors,
            building_dmg,
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

    def commercial_recovery(
        self,
        buildings,
        sample_damage_states,
        mcs_failure,
        redi_delay_factors,
        building_dmg,
        num_samples,
    ):
        """
        Calculates commercial building recovery for buildings

        Args:
            buildings(list): Buildings dataset
            sample_damage_states (pd.DataFrame): Sample damage states
            redi_delay_factors (pd.DataFrame): Delay factors based on REDi framework
            mcs_failure (pd.DataFrame): Building inventory failure probabilities
            building_dmg (pd.DataFrame): Building damage states
            num_samples (int): number of sample scenarios to use

        Returns:
            dict: dictionary with id/guid and commercial recovery for each quarter

        """

        start_total_delay = time.process_time()
        total_delay = CommercialBuildingRecovery.total_delay(
            buildings,
            sample_damage_states,
            mcs_failure,
            redi_delay_factors,
            building_dmg,
            num_samples,
        )
        end_total_delay = time.process_time()
        print(
            "Finished executing total_delay() in "
            + str(end_total_delay - start_total_delay)
            + " secs"
        )

        recovery = self.recovery_rate(buildings, sample_damage_states, total_delay)
        end_recovery = time.process_time()
        print(
            "Finished executing recovery_rate() in "
            + str(end_recovery - end_total_delay)
            + " secs"
        )

        time_stepping_recovery = CommercialBuildingRecovery.time_stepping_recovery(
            recovery
        )
        end_time_stepping_recovery = time.process_time()
        print(
            "Finished executing time_stepping_recovery() in "
            + str(end_time_stepping_recovery - end_recovery)
            + " secs"
        )

        end_time = time.process_time()
        print("Analysis completed in " + str(end_time - start_total_delay) + " secs")

        return total_delay, recovery, time_stepping_recovery

    @staticmethod
    def total_delay(
        buildings,
        sample_damage_states,
        mcs_failure,
        redi_delay_factors,
        damage,
        num_samples,
    ):
        """Calculates total delay by combining financial delay and other factors from REDi framework

        Args:
            buildings (list): List of buildings
            sample_damage_states (pd.DataFrame): Building inventory damage states.
            mcs_failure (pd.DataFrame): Building inventory failure probabilities
            redi_delay_factors (pd.DataFrame): Delay impeding factors such as post-disaster inspection, insurance claim,
                financing, and government permit based on building's damage state.
            damage (pd.DataFrame): Damage states for building structural damage
            num_samples (int): number of sample scenarios to use

        Returns:
            pd.DataFrame: Total delay time of all impeding factors from REDi framework.
        """

        # Obtain the commercial buildings in damage
        damage = mcs_failure[damage["haz_expose"] == "yes"]
        commercial = []
        commercial_archetypes = [6, 7, 8, 15, 16, 18, 19]
        for i, b in enumerate(buildings):
            if b["properties"]["archetype"] in commercial_archetypes:
                commercial.append(b["properties"]["guid"])
        commercial_pd = pd.DataFrame(commercial, columns=["guid"])
        commercial_damage = pd.merge(damage, commercial_pd, on="guid")

        # Obtain the column names
        colnames = [f"sample_{i}" for i in range(0, num_samples)]
        samples = np.zeros((len(commercial_damage), num_samples))
        delay_time = pd.DataFrame(samples, columns=colnames)
        delay_time.insert(0, "guid", commercial_damage.reset_index(drop=True)["guid"])

        # Perform an inner join to ensure only buildings with damage states are processed
        merged_delay = pd.merge(sample_damage_states, delay_time, on="guid")

        # Obtain the guids
        merged_delay_guids = merged_delay["guid"]

        # Obtain the damage states
        merged_delay_damage_states = merged_delay["sample_damage_states"]

        # Convert to numpy
        samples_np = merged_delay.drop(
            columns=["guid", "sample_damage_states"]
        ).to_numpy()

        # First, we decompose redi_delay_factors into two dictionaries that can be used to compute vector operations
        redi_idx = dict(
            zip(
                redi_delay_factors["Building_specific_conditions"],
                redi_delay_factors.index,
            )
        )

        # Next, we produce two intermediate numpy matrices: one for med and one for sdv
        redi_med = redi_delay_factors[
            ["Ins_med", "Enmo_med", "Como_med", "Per_med", "Fin_med"]
        ].to_numpy()
        redi_sdv = redi_delay_factors[
            ["Ins_sdv", "Enmo_sdv", "Como_sdv", "Per_sdv", "Fin_sdv"]
        ].to_numpy()

        # Define indices to facilitate interpretation of the code
        inspection_idx = 0
        engineer_idx = 1
        contractor_idx = 2
        permit_idx = 3
        financing_idx = 4

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

                if dmg_state_idx == 3 or dmg_state_idx == 2:
                    delay_vec[4] = np.random.normal(mean_vec[4], sdv_vec[4])

                # Compute the delay using that vector, already computed in the prior step
                samples_np[i, j] = np.round(
                    delay_vec[inspection_idx]
                    + np.max(
                        [
                            delay_vec[engineer_idx],
                            delay_vec[financing_idx],
                            delay_vec[contractor_idx],
                        ]
                    )
                    + delay_vec[permit_idx]
                )

        total_delay = pd.DataFrame(samples_np, columns=colnames)
        total_delay.insert(0, "guid", merged_delay_guids)

        return total_delay

    def recovery_rate(self, buildings, sample_damage_states, total_delay):
        """Gets total time required for each commercial building to receive full restoration. Determined by the
        combination of delay time and repair time

        Args:
            buildings (list): List of buildings
            sample_damage_states (pd.DataFrame): Samples' damage states
            total_delay (pd.DataFrame): Total delay time of financial delay and other factors from REDi framework.

        Returns:
            pd.DataFrame: Recovery time of all commercial buildings for each sample
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
            # if building id has a matched repair curve set
            if b["id"] in repair_sets.keys():
                repair_sets_by_guid[b["properties"]["guid"]] = repair_sets[b["id"]]
            else:
                repair_sets_by_guid[b["properties"]["guid"]] = None

        # Obtain the column names
        colnames = list(total_delay.columns)[1:]

        # Perform an inner join to ensure only buildings with damage states are processed
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
        num_buildings = samples_np.shape[0]

        # Generate a long numpy matrix for combined N1, N2 samples
        samples_n1_n2 = np.zeros((num_buildings, num_samples * num_samples))

        # Now, we define an internal function to take care of the index for the prior case
        def idx(x, y):
            return x * num_samples + y

        for build in range(0, num_buildings):
            # Obtain the damage states
            mapped_repair = repair_sets_by_guid[merged_delay_guids.iloc[build]]
            samples_mcs = merged_delay_damage_states.iloc[build].split(",")

            # Use a lambda to obtain the damage state in numeric form. Note that since damage states are single digits,
            # it suffices to look at the last character and convert into an integer value. Do this computation once
            # per building only.
            extract_ds = lambda x: int(x[-1])  # noqa: E731
            samples_mcs_ds = list(map(extract_ds, samples_mcs))  # noqa: E731

            # Now, perform the two nested loops, using the indexing function to simplify the syntax.
            for i in range(0, num_samples):
                state = samples_mcs_ds[i]
                percent_func = np.random.random(num_samples)
                # NOTE: Even though the kwarg name is "repair_time", it actually takes  percent of functionality. DFR3
                # system currently doesn't have a way to represent the name correctly when calculating the inverse.
                if mapped_repair is not None:
                    repair_time = (
                        mapped_repair.repair_curves[state].solve_curve_for_inverse(
                            hazard_values={},
                            curve_parameters=mapped_repair.curve_parameters,
                            **{"repair_time": percent_func},
                        )
                        / 7
                    )
                else:
                    repair_time = np.full(num_samples, np.nan)

                for j in range(0, num_samples):
                    samples_n1_n2[build, idx(i, j)] = round(
                        samples_np[build, i] + repair_time[j], 1
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

        # Convert recovery time results to numpy
        samples_n1_n2 = recovery_results.drop(columns=["guid"]).to_numpy()

        # Number of guids
        num_buildings = recovery_results.shape[0]
        num_samples = samples_n1_n2.shape[1]
        num_times = len(total_time)

        # Generate a numpy to hold the results as desired
        times_np = np.full((num_buildings, num_times), 1111.0)

        for build in range(0, num_buildings):
            for i in range(len(total_time)):
                fun_state = (
                    np.count_nonzero(samples_n1_n2[build, :] < total_time[i])
                    / num_samples
                )
                times_np[build, i] = np.round(fun_state, 2)

        colnames = [f"quarter_{i}" for i in range(0, num_times)]

        time_stepping_recovery = pd.DataFrame(times_np, columns=colnames)
        time_stepping_recovery.insert(0, "guid", recovery_results_guids)

        return time_stepping_recovery

    def get_spec(self):
        """Get specifications of the commercial building recovery analysis.

        Returns:
            obj: A JSON object of specifications of the commercial building recovery analysis.

        """
        return {
            "name": "commercial-building-recovery",
            "description": "calculate commercial building recovery",
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
                    "required": True,
                    "description": "Sample damage states",
                    "type": ["incore:sampleDamageState"],
                },
                {
                    "id": "mcs_failure",
                    "required": True,
                    "description": "mcs_failure",
                    "type": ["incore:failureProbability"],
                },
                {
                    "id": "delay_factors",
                    "required": True,
                    "description": "Delay impeding factors such as post-disaster inspection, insurance claim, "
                    "and government permit based on building's damage state. Provided by REDi framework",
                    "type": ["incore:buildingRecoveryFactors"],
                },
                {
                    "id": "building_dmg",
                    "required": True,
                    "description": "damage result that has damage intervals",
                    "type": ["ergo:buildingDamageVer6"],
                },
            ],
            "output_datasets": [
                {
                    "id": "total_delay",
                    "description": "CSV file of commercial building delay time",
                    "type": "incore:buildingRecoveryDelay",
                },
                {
                    "id": "recovery",
                    "description": "CSV file of commercial building recovery time",
                    "type": "incore:buildingRecoveryTime",
                },
                {
                    "id": "time_stepping_recovery",
                    "description": "CSV file of commercial building recovery percent",
                    "type": "incore:buildingRecovery",
                },
            ],
        }
