# Copyright (c) 2018 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import math
import csv
import numpy as np
import scipy as sp
import scipy.stats
import concurrent.futures

from pyincore.analyses.buildingclusterrecovery.buildingdata import BuildingData
from pyincore import BaseAnalysis, Dataset


class BuildingClusterRecovery(BaseAnalysis):
    """The Building Portfolio Recovery analysis uses damage probabilities of structural components,
    nonstructural drift-sensitive components, and nonstructural acceleration-sensitive components
    to calculate building’s initial functionality loss.

    Args:
        incore_client (IncoreClient): Service authentication.

    """

    def __init__(self, incore_client):
        super(BuildingClusterRecovery, self).__init__(incore_client)

    def get_spec(self):
        return {
            "name": "building-cluster-recovery-analysis",
            "description": "Building Cluster Recovery Analysis (with uncertainty)",
            "input_parameters": [
                {
                    "id": "result_name",
                    "required": False,
                    "description": "Result dataset name",
                    "type": str,
                },
                {
                    "id": "uncertainty",
                    "required": True,
                    "description": "Use uncertainty",
                    "type": bool,
                },
                {
                    "id": "sample_size",
                    "required": False,
                    "description": "No. of buildings to be considered from input buildings",
                    "type": int,
                },
                {
                    "id": "random_sample_size",
                    "required": True,
                    "description": "Number of iterations for Monte Carlo Simulation",
                    "type": int,
                },
                {
                    "id": "no_of_weeks",
                    "required": True,
                    "description": "Number of weeks to run the recovery model",
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
                    "id": "building_data",
                    "required": True,
                    "description": "Building Data",
                    "type": ["incore:portfolioBuildingInventory"],
                },
                {
                    "id": "occupancy_mapping",
                    "required": True,
                    "description": "Occupancy code mapping",
                    "type": ["incore:portfolioOccupancyMapping"],
                },
                {
                    "id": "building_damage",
                    "required": True,
                    "description": "Building Damage Results",
                    "type": ["incore:portfolioBuildingDamage"],
                },
                {
                    "id": "dmg_ratios",
                    "required": True,
                    "description": "Percentage of mean repair by occupancy / building type",
                    "type": ["incore:portfolioDamageRatios"],
                },
                {
                    "id": "utility",
                    "required": True,
                    "description": "Full utility availability at each utility service area - joint area of power"
                    'and water (row), at each week (column)"',
                    "type": ["incore:portfolioUtilityAvailability"],
                },
                {
                    "id": "utility_partial",
                    "required": True,
                    "description": "Partial utility availability at each utility service area",
                    "type": ["incore:portfolioUtilityAvailability"],
                },
                {
                    "id": "coefFL",
                    "required": True,
                    "description": "Correlation coefficient of initial functionality states",
                    "type": ["incore:portfolioCoefficients"],
                },
            ],
            "output_datasets": [
                {
                    "id": "result",
                    "parent_type": "buildingClusterRecovery",
                    "description": "Building cluster recovery result.",
                    "type": "incore:clusterRecovery",
                }
            ],
        }

    def run(self):
        uncertainty = self.get_parameter("uncertainty")
        utility_initial = self.get_input_dataset("utility").get_dataframe_from_csv()
        building_damage_results = self.get_input_dataset(
            "building_damage"
        ).get_dataframe_from_csv()
        building_data = self.get_input_dataset("building_data").get_dataframe_from_csv()
        mean_repair = self.get_input_dataset("dmg_ratios").get_dataframe_from_csv()
        occupancy_mapping = self.get_input_dataset(
            "occupancy_mapping"
        ).get_dataframe_from_csv()
        coeFL = self.get_input_dataset("coefFL").get_dataframe_from_csv()

        print(
            "INFO: Data for Building Portfolio Recovery Analysis loaded successfully."
        )

        sample_size = self.get_parameter(
            "sample_size"
        )  # len(building  _damage_results)
        if sample_size is None:
            sample_size = len(building_damage_results)
        else:
            building_damage_results = building_damage_results.head(sample_size)
            coeFL = coeFL.iloc[0:sample_size, 0:sample_size]

        permutation = np.random.permutation(len(building_data))
        permutation_subset = permutation[0:sample_size]
        sample_buildings = [
            BuildingData(
                building_data["Tract_ID"][i],
                building_data["X_Lon"][i],
                building_data["Y_Lat"][i],
                building_data["Structural"][i],
                building_data["Code_Level"][i],
                building_data["EPSANodeID"][i],
                building_data["PWSANodeID"][i],
                building_data["TEP_ID"][i],
                building_data["Build_ID_X"][i],
                building_data["EPSAID"][i],
                building_data["PWSAID"][i],
                building_data["Finance"][i],
                building_data["EP_PW_ID"][i],
                building_data["Occu_Code"][i],
            )
            for i in permutation_subset
        ]
        occupancy_map = {
            occupancy_mapping["Occu_ID"][i]: occupancy_mapping["Occupancy"][i]
            for i in range(len(occupancy_mapping))
        }
        repair_mean = {
            mean_repair["Occupancy"][i]: [
                mean_repair["RC1"][i],
                mean_repair["RC2"][i],
                mean_repair["RC3"][i],
                mean_repair["RC4"][i],
            ]
            for i in range(len(mean_repair))
        }

        building_damage = [
            [
                building_damage_results["Restricted Entry"][i],
                building_damage_results["Restricted Use"][i],
                building_damage_results["Reoccupancy"][i],
                building_damage_results["Best Line Functionality"][i],
                building_damage_results["Full Functionality"][i],
            ]
            for i in range(len(building_damage_results))
        ]

        # START: Calculate waiting time statistics using Monte Carlo Simulations
        nsd = 5000  # TODO: Input?
        number_of_simulations = self.get_parameter("random_sample_size")

        output_base_name = self.get_parameter("result_name")
        if output_base_name is None:
            output_base_name = ""
        sample_delay = np.zeros(nsd)
        impeding_mean = np.zeros((5, 4))
        impeding_std = np.zeros((5, 4))

        for i in range(4):
            for j in range(5):
                for k in range(nsd):
                    sample_delay[k] = self.calculate_delay_time(i, j)
                impeding_mean[j, i] = np.mean(sample_delay)
                impeding_std[j, i] = np.std(sample_delay)

        # END: Calculate waiting time statistics using Monte Carlo Simulations

        # Recovery time step from week 1 to n
        time_steps = self.get_parameter("no_of_weeks")
        utility = np.ones((len(utility_initial), time_steps))

        # START initializing variables for uncertainty analysis
        target_mean_recovery = np.zeros(time_steps)
        utility2 = np.zeros((len(utility_initial), time_steps))
        # END code for uncertainty analysis

        # Utility matrix. Represents the recovery for each of the utility areas at a given number of weeks after the event
        # The utility matrix uses utility Initial input file for the first 22 weeks and ones for the rest of the time.

        if uncertainty:
            for i in range(time_steps):
                utility[:, i] = [1 - j for j in utility_initial[str(i)]]
        else:
            for i in range(time_steps):
                utility[:, i] = [j for j in utility_initial[str(i)]]

        # with concurrent.futures.ProcessPoolExecutor(max_workers=sample_size) as executor:
        #     for response in executor.map(self.calculate_transition_probability_matrix(sample_size, time_steps, sample_buildings,
        #                                                                          repair_mean, occupancy_map, uncertainty,
        #                                                                          impeding_mean, impeding_std,
        #                                                                          building_damage, utility, utility2)):
        response = self.calculate_transition_probability_matrix(
            time_steps,
            sample_buildings,
            repair_mean,
            occupancy_map,
            uncertainty,
            impeding_mean,
            impeding_std,
            building_damage,
            utility,
            utility2,
        )
        temporary_correlation1 = response["temporary_correlation1"]
        temporary_correlation2 = response["temporary_correlation2"]
        mean_over_time = response["mean_over_time"]
        variance_over_time = response["variance_over_time"]

        # Functionality Recovery (Best Line Functionality + Full functionality) for each building on the sample
        recovery_fp = response["recovery_fp"]

        # Mean recovery trajectory at portfolio level
        mean_recovery = response["mean_recovery"]

        # Trajectory for the Restricted entry, Restricted Use, Reoccupancy, Best Line Functionality, Full Functionality
        mean_recovery = mean_recovery / sample_size

        # Trajectory for Best Line Functionality and Full Functionality
        mean_recovery_output = sum(recovery_fp) / sample_size

        with open(
            output_base_name + "_building-recovery.csv", "w+", newline=""
        ) as output_file:
            spam_writer = csv.writer(
                output_file, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
            )
            spam_writer.writerow(
                ["Building_ID", "Building_Lon", "Building_Lat"]
                + list(range(1, time_steps + 1))
            )
            for i in range(sample_size):
                spam_writer.writerow(
                    [
                        building_data["Build_ID_X"][i],
                        building_data["X_Lon"][i],
                        building_data["Y_Lat"][i],
                    ]
                    + list(recovery_fp[i])
                )

        if uncertainty:
            # START: Additional Code for uncertainty analysis
            mean_u = np.zeros(sample_size)
            covar = np.matrix(coeFL)  # np.zeros([sample_size, sample_size])
            random_distribution = np.random.multivariate_normal(mean_u, covar, 10000)
            random_samples = sp.stats.norm.cdf(random_distribution)

            sample_total = self.calculate_sample_total(
                number_of_simulations, sample_size, building_damage, random_samples
            )

            for k in range(sample_size):
                for t in range(time_steps):
                    if variance_over_time[t][k] <= 0:
                        variance_over_time[t][k] = 0

            # Start calculating standard deviation of the mean recovery trajectory
            total_standard_deviation = self.calculate_std_of_mean_bulk_input(
                range(time_steps),
                sample_size,
                number_of_simulations,
                variance_over_time,
                mean_over_time,
                temporary_correlation1,
                temporary_correlation2,
                sample_total,
            )

            # Calculate distribution of Portfolio Recovery Time (PRT) assume normal distribution
            x_range = np.arange(0.0, 1.001, 0.001)
            pdf_full = np.zeros((time_steps, len(x_range)))
            irt = np.zeros(time_steps)
            for t in range(time_steps):
                total_standard_deviation[t] = (
                    math.sqrt(total_standard_deviation[t]) / sample_size
                )
                target_mean_recovery[t] = mean_recovery[t][3] + mean_recovery[t][4]
                pdf_full[t] = sp.stats.norm.pdf(
                    x_range, target_mean_recovery[t], total_standard_deviation[t]
                )

            coeR = np.trapz(pdf_full, x_range)

            for t in range(time_steps):
                pdf_full[t] = pdf_full[t] / coeR[t]
                idx = int(len(x_range) * 95 / 100 + 1)
                irt[t] = np.trapz(pdf_full[t, idx:], x_range[idx:])

            pdf = np.zeros(time_steps)
            for t in range(1, time_steps - 1):
                pdf[t] = (irt[t + 1] - irt[t]) if irt[t + 1] - irt[t] > 0 else 0

            # Calculate truncated normal distribution and 75% & 95% percentile band
            # 75% percentile upper bound
            upper_bound75 = target_mean_recovery + [
                1.15 * i for i in total_standard_deviation
            ]
            # 75% percentile lower bound
            lower_bound75 = target_mean_recovery - [
                1.15 * i for i in total_standard_deviation
            ]
            # 95% percentile upper bound
            upper_bound95 = target_mean_recovery + [
                1.96 * i for i in total_standard_deviation
            ]
            # 95% percentile lower bound
            lower_bound95 = target_mean_recovery - [
                1.96 * i for i in total_standard_deviation
            ]

            for t in range(time_steps):
                coet = sp.stats.norm.cdf(
                    0, target_mean_recovery[t], total_standard_deviation[t]
                )
                coet2 = sp.stats.norm.cdf(
                    1, target_mean_recovery[t], total_standard_deviation[t]
                )

                if coet >= 0.000005 and 1 - coet2 < 0.00005:
                    coeAmp = 1 / (1 - coet)
                    lower_bound95[t] = sp.stats.norm.ppf(
                        0.05 / coeAmp + coet,
                        target_mean_recovery[t],
                        total_standard_deviation[t],
                    )
                    upper_bound95[t] = sp.stats.norm.ppf(
                        0.95 / coeAmp + coet,
                        target_mean_recovery[t],
                        total_standard_deviation[t],
                    )
                    lower_bound75[t] = sp.stats.norm.ppf(
                        0.25 / coeAmp + coet,
                        target_mean_recovery[t],
                        total_standard_deviation[t],
                    )
                    upper_bound75[t] = sp.stats.norm.ppf(
                        0.75 / coeAmp + coet,
                        target_mean_recovery[t],
                        total_standard_deviation[t],
                    )

                    pdf_full[t] = pdf_full[t] * coeAmp
                if coet < 0.00005 and 1 - coet2 >= 0.000005:
                    coeAmp = 1 / coet2
                    lower_bound95[t] = sp.stats.norm.ppf(
                        (coet2) - 0.95 / coeAmp,
                        target_mean_recovery[t],
                        total_standard_deviation[t],
                    )
                    upper_bound95[t] = sp.stats.norm.ppf(
                        (coet2) - 0.05 / coeAmp,
                        target_mean_recovery[t],
                        total_standard_deviation[t],
                    )
                    lower_bound75[t] = sp.stats.norm.ppf(
                        (coet2) - 0.75 / coeAmp,
                        target_mean_recovery[t],
                        total_standard_deviation[t],
                    )
                    upper_bound75[t] = sp.stats.norm.ppf(
                        (coet2) - 0.25 / coeAmp,
                        target_mean_recovery[t],
                        total_standard_deviation[t],
                    )

                    pdf_full[t] = pdf_full[t] * coeAmp
                if coet >= 0.000005 and 1 - coet2 >= 0.000005:
                    coeAmp = 1 / (coet2 - coet)
                    lower_bound95[t] = sp.stats.norm.ppf(
                        0.05 / coeAmp + coet,
                        target_mean_recovery[t],
                        total_standard_deviation[t],
                    )
                    upper_bound95[t] = sp.stats.norm.ppf(
                        coet2 - 0.05 / coeAmp,
                        target_mean_recovery[t],
                        total_standard_deviation[t],
                    )
                    lower_bound75[t] = sp.stats.norm.ppf(
                        0.25 / coeAmp + coet,
                        target_mean_recovery[t],
                        total_standard_deviation[t],
                    )
                    upper_bound75[t] = sp.stats.norm.ppf(
                        coet2 - 0.25 / coeAmp,
                        target_mean_recovery[t],
                        total_standard_deviation[t],
                    )

            # TODO: Confirm with PI if this can be removed. These conditions are never hit
            if time_steps > 100:
                for t in range(100):
                    if lower_bound75[t] < 0:
                        lower_bound75[t] = 1
                    if upper_bound75[t] < 0:
                        upper_bound75[t] = 1
                for t in range(100, time_steps):
                    if lower_bound95[t] < 0:
                        lower_bound95[t] = 1
                    if upper_bound95[t] < 0:
                        upper_bound95[t] = 1

            # END: Additional Code for uncertainty Analysis
            with open(
                output_base_name + "_cluster-recovery.csv", "w+", newline=""
            ) as output_file:
                spam_writer = csv.writer(
                    output_file, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
                )
                spam_writer.writerow(
                    [
                        "Week",
                        "Recovery_Percent_Func_Probability",
                        "75P_Upper_Bound",
                        "75P_Lower_Bound",
                        "95P_Upper_Bound",
                        "95P_Lower_Bound",
                        "RecPercent_RE",
                        "RecPercent_RU",
                        "RecPercent_RO",
                        "RecPercent_BF",
                        "RecPercent_FF",
                        "Probability_Density_Func",
                    ]
                )
                for i in range(time_steps):
                    spam_writer.writerow(
                        [
                            i + 1,
                            mean_recovery_output[i],
                            lower_bound75[i],
                            upper_bound75[i],
                            lower_bound95[i],
                            upper_bound95[i],
                        ]
                        + list(mean_recovery[i])
                        + [pdf[i]]
                    )
        else:
            with open(
                output_base_name + "_cluster-recovery.csv", "w+", newline=""
            ) as output_file:
                spam_writer = csv.writer(
                    output_file, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
                )
                spam_writer.writerow(
                    [
                        "Week",
                        "Recovery_Percent_Func_Probability",
                        "RecPercent_RE",
                        "RecPercent_RU",
                        "RecPercent_RO",
                        "RecPercent_BF",
                        "RecPercent_FF",
                    ]
                )
                for i in range(time_steps):
                    spam_writer.writerow(
                        [i + 1, mean_recovery_output[i]] + list(mean_recovery[i])
                    )

        self.set_output_dataset(
            "result",
            Dataset.from_file(
                output_base_name + "_cluster-recovery.csv",
                data_type=self.output_datasets["result"]["spec"]["type"],
            ),
        )

        print("INFO: Finished executing Building Portfolio Recovery Analysis")

        return True

    def calculate_transition_probability_matrix(
        self,
        time_steps,
        sample_buildings,
        repair_mean,
        occupancy_map,
        uncertainty,
        impeding_mean,
        impeding_std,
        building_damage,
        utility,
        utility2,
    ):
        sample_size = len(sample_buildings)
        total_mean = np.zeros((4, 4))
        total_var = np.zeros((4, 4))
        transition_probability = np.zeros((4, 4))
        state_probabilities = np.zeros((time_steps, 5))
        output = np.zeros(time_steps)
        temporary_correlation1 = np.zeros((time_steps, sample_size, 5))
        temporary_correlation2 = np.zeros((time_steps, sample_size, 5))
        mean_over_time = np.zeros((time_steps, sample_size))
        variance_over_time = np.zeros((time_steps, sample_size))
        recovery_fp = np.zeros((sample_size, time_steps))
        mean_recovery = np.zeros((time_steps, 5))
        print("Calculating transition probability matrix for each building..")
        for k in range(sample_size):
            # print("Calculating transition probability matrix for " + str(k))
            # The index for finance starts in 1 they are one off from the matrix
            finance_id = sample_buildings[k].finance - 1
            utility_id = sample_buildings[k].ep_pw_id
            for j in range(4):
                mean = impeding_mean[finance_id, j]
                std = impeding_std[finance_id, j] ** 2

                for i in range(j, 4):
                    mean += repair_mean[
                        occupancy_map[sample_buildings[k].occupation_code]
                    ][i]
                    total_mean[j][i] = mean
                    std += (
                        0.4
                        * repair_mean[
                            occupancy_map[sample_buildings[k].occupation_code]
                        ][i]
                        ** 2
                    )
                    total_var[j][i] = math.sqrt(std)

            for t in range(time_steps):
                for i in range(4):
                    for j in range(i, 4):
                        zeta = math.sqrt(
                            math.log(1 + (total_var[i][j] / total_mean[i][j]) ** 2)
                        )
                        lambda_log = math.log(total_mean[i][j]) - 1 / 2 * zeta**2
                        transition_probability[i][j] = self.log_n_cdf(
                            t + 1, lambda_log, zeta
                        )
                # tpm = transition probability matrix
                tpm = np.matrix(
                    [
                        [
                            1 - transition_probability[0, 0],
                            transition_probability[0, 0] - transition_probability[0, 1],
                            transition_probability[0, 1] - transition_probability[0, 2],
                            transition_probability[0, 2] - transition_probability[0, 3],
                            transition_probability[0, 3],
                        ],
                        [
                            0.0,
                            1 - transition_probability[1, 1],
                            transition_probability[1, 1] - transition_probability[1, 2],
                            transition_probability[1, 2] - transition_probability[1, 3],
                            transition_probability[1, 3],
                        ],
                        [
                            0.0,
                            0.0,
                            1 - transition_probability[2, 2],
                            transition_probability[2, 2] - transition_probability[2, 3],
                            transition_probability[2, 3],
                        ],
                        [
                            0.0,
                            0.0,
                            0.0,
                            1 - transition_probability[3, 3],
                            transition_probability[3, 3],
                        ],
                        [0.0, 0.0, 0.0, 0.0, 1.0],
                    ],
                    dtype=float,
                )
                # State Probability vector, pie(t) = initial vector * Transition Probability Matrix
                state_probabilities[t] = np.matmul(building_damage[k], tpm)
                if not uncertainty:
                    output[t] = state_probabilities[t, 3] + state_probabilities[t, 4]

                if uncertainty:
                    # Considering the effect of utility availability
                    # Utility Dependence Matrix
                    utility_matrix = np.matrix(
                        [
                            [1, 0, 0, 0, 0],
                            [0, 1, 0, 0, 0],
                            [0, 0, 1, utility[utility_id][t], utility[utility_id][t]],
                            [
                                0,
                                0,
                                0,
                                1 - utility[utility_id][t],
                                utility2[utility_id][t],
                            ],
                            [
                                0,
                                0,
                                0,
                                0,
                                1 - utility[utility_id][t] - utility2[utility_id][t],
                            ],
                        ],
                        dtype=float,
                    )
                    updated_tpm = np.matmul(tpm, utility_matrix.transpose())
                    state_probabilities[t] = np.matmul(
                        state_probabilities[t], utility_matrix.transpose()
                    )

                    # Calculation functionality statee indicator wheen j=4+5 Conditional mean
                    temporary_correlation1[t][k][0] = updated_tpm[0, 3]
                    temporary_correlation1[t][k][1] = updated_tpm[1, 3]
                    temporary_correlation1[t][k][2] = updated_tpm[2, 3]
                    temporary_correlation1[t][k][3] = updated_tpm[3, 3]
                    temporary_correlation1[t][k][4] = updated_tpm[4, 3]
                    temporary_correlation2[t][k][0] = updated_tpm[0, 4]
                    temporary_correlation2[t][k][1] = updated_tpm[1, 4]
                    temporary_correlation2[t][k][2] = updated_tpm[2, 4]
                    temporary_correlation2[t][k][3] = updated_tpm[3, 4]
                    temporary_correlation2[t][k][4] = updated_tpm[4, 4]
                    mean_over_time[t][k] = (
                        state_probabilities[t][3] + state_probabilities[t][4]
                    )
                    variance_over_time[t][k] = (
                        state_probabilities[t][3] + state_probabilities[t][4]
                    ) * (1 - (state_probabilities[t][3] + state_probabilities[t][4]))

            # Considering the effect of utility availability
            # Service Area ID of individual buildings
            # START: Code from only recovery analysis
            if not uncertainty:
                for i in range(len(state_probabilities)):
                    state_probabilities[i, 2] = (
                        state_probabilities[i, 2]
                        + state_probabilities[i, 3]
                        + state_probabilities[i, 4] * (1 - utility[utility_id, i])
                    )
                    state_probabilities[i, 3] = (
                        state_probabilities[i, 3] * utility[utility_id, i]
                    )
                    state_probabilities[i, 4] = (
                        state_probabilities[i, 4] * utility[utility_id, i]
                    )

            # END: Code from only recovery analysis

            # Save functional probability (Best Line Functionality + Full functionality) for each building
            recovery_fp[k, :] = state_probabilities[:, 4] + state_probabilities[:, 3]

            # Aggregate state probability vector to portfolio level
            mean_recovery = mean_recovery + state_probabilities

        print("Transition probability matrix calculation complete.")

        return {
            "temporary_correlation1": temporary_correlation1,
            "temporary_correlation2": temporary_correlation2,
            "mean_over_time": mean_over_time,
            "variance_over_time": variance_over_time,
            "recovery_fp": recovery_fp,
            "mean_recovery": mean_recovery,
        }

    # TODO: nS=10000 should be used line:301
    def calculate_sample_total(
        self, number_of_simulations, sample_size, building_damage, random_samples
    ):
        sample_total = np.zeros((sample_size, number_of_simulations))
        for j in range(number_of_simulations):
            sample = np.zeros(sample_size)
            for i in range(sample_size):
                threshold = building_damage[i]
                if random_samples[j][i] <= threshold[0]:
                    sample[i] = 1
                elif (
                    random_samples[j][i] <= threshold[0] + threshold[1]
                    and random_samples[j][i] >= threshold[0]
                ):
                    sample[i] = 2
                elif (
                    threshold[0] + threshold[1]
                    <= random_samples[j][i]
                    <= threshold[0] + threshold[1] + threshold[2]
                ):
                    sample[i] = 3
                elif (
                    threshold[0] + threshold[1] + threshold[2]
                    <= random_samples[j][i]
                    <= threshold[0] + threshold[1] + threshold[2] + threshold[3]
                ):
                    sample[i] = 4
                else:
                    sample[i] = 5
                sample_total[i][j] = sample[i]
        return sample_total

    def calculate_std_of_mean_concurrent_future(
        self, function_name, parallelism, *args
    ):
        output = []
        with concurrent.futures.ProcessPoolExecutor(
            max_workers=parallelism
        ) as executor:
            for ret in executor.map(function_name, *args):
                output.extend(ret)
        return output

    def calculate_std_of_mean_bulk_input(
        self,
        time_steps,
        sample_size,
        number_of_simulations,
        variance_over_time,
        mean_over_time,
        temporary_correlation1,
        temporary_correlation2,
        sample_total,
    ):
        result = []
        for step in time_steps:
            result.append(
                self.calculate_std_of_mean(
                    step,
                    sample_size,
                    number_of_simulations,
                    variance_over_time,
                    mean_over_time,
                    temporary_correlation1,
                    temporary_correlation2,
                    sample_total,
                )
            )
        return result

    # calculating standard deviation of the mean recovery trajectory
    def calculate_std_of_mean(
        self,
        t,
        sample_size,
        number_of_simulations,
        variance_over_time,
        mean_over_time,
        temporary_correlation1,
        temporary_correlation2,
        sample_total,
    ):
        print("Calculating std mean for week " + str(t))
        output = np.sum(variance_over_time[t])

        # Building i
        # start = timer()
        for i in range(sample_size - 1):
            # start = timer()
            # Building j
            for j in range(i + 1, sample_size):
                # starti = timer()
                expect1 = 0
                # Joint probability of initial functionality state P(S0i=k, S0j=l)
                joint_probability = self.joint_probability_calculation(
                    sample_total[i], sample_total[j], number_of_simulations
                )

                # Functionality State k
                for k in range(5):
                    # Functionality State m
                    for m in range(5):
                        expect1 += joint_probability[k][m] * (
                            temporary_correlation1[t][i][k]
                            * temporary_correlation1[t][j][m]
                            + temporary_correlation1[t][i][k]
                            * temporary_correlation1[t][j][m]
                            + temporary_correlation2[t][i][k]
                            * temporary_correlation1[t][j][m]
                            + temporary_correlation2[t][i][k]
                            * temporary_correlation2[t][j][m]
                        )
                expect2 = mean_over_time[t][i] * mean_over_time[t][j]

                if (
                    variance_over_time[t][i] > 0
                    and variance_over_time[t][j] > 0
                    and expect1 - expect2 > 0
                ):
                    covariance = expect1 - expect2
                    output += 2 * covariance

        return output

    # TODO: Review
    def calculate_delay_time(self, res_buildings, finance):
        """This function calculates the delay time given an initial functionality state and a financing resource.

        Args:
            res_buildings (int): Initial Damage State 1: Slight Damage.
            finance (int): Financing types, Can be a number from 1 to 5:

                1. Insurance
                2. SBA Business Loan
                3. Private
                4. Savings
                5. Not covered

        Returns:
            np.Array: Impeding. It takes into account each factor that alters the recovery time.
            Each item in the temporary array represents:

            1. impeding[0]: Initial Damage State
            2. impeding[1]: Engineering Mobilization
            3. impeding[2]: Insurance
            4. impeding[3]: Contractor Mobilization
            5. impeding[4]: Obtain permits

        """
        impeding = np.zeros(5)

        if res_buildings == 3:
            impeding[0] = 0
            impeding[1] = np.random.lognormal(np.log(0.5), 0.4)
            impeding[2] = 0
            impeding[3] = np.random.lognormal(np.log(3), 0.6)

        elif res_buildings == 1 or res_buildings == 2:
            impeding[0] = np.random.lognormal(np.log(1), 0.54)
            if res_buildings == 1:
                impeding[1] = np.random.lognormal(np.log(15), 0.32)
                impeding[3] = np.random.lognormal(np.log(12), 0.38)

            else:
                impeding[1] = np.random.lognormal(np.log(3), 0.4)
                impeding[3] = np.random.lognormal(np.log(6), 0.6)

            if finance == 0:
                impeding[2] = np.random.lognormal(np.log(3), 1.11)
            elif finance == 1:
                impeding[2] = np.random.lognormal(np.log(10), 0.57)
            elif finance == 2:
                impeding[2] = np.random.lognormal(np.log(7), 0.68)
            elif finance == 3:
                impeding[2] = 0
            else:
                impeding[2] = np.random.lognormal(np.log(15), 0.65)

        else:
            impeding[0] = np.random.lognormal(np.log(4), 0.54, 1)
            impeding[1] = np.random.lognormal(np.log(15), 0.32, 1)

            if finance == 0:
                impeding[2] = np.random.lognormal(np.log(6), 1.11)
            elif finance == 1:
                impeding[2] = np.random.lognormal(np.log(30), 0.57)
            elif finance == 2:
                impeding[2] = np.random.lognormal(np.log(15), 0.68)
            elif finance == 3:
                impeding[2] = 0
            else:
                impeding[2] = np.random.lognormal(np.log(40), 0.65)

            impeding[3] = np.random.lognormal(np.log(12), 0.38)

        if res_buildings == 2 or res_buildings == 3:
            impeding[4] = 0
        else:
            impeding[4] = np.random.lognormal(np.log(6), 0.32)

        return impeding[0] + max(impeding[1:4]) + impeding[4]

    # TODO: Improve readability
    def joint_probability_calculation(self, sample_i, sample_j, number_of_samples):
        output = np.zeros((5, 5))
        for n in range(number_of_samples):
            if sample_i[n] == 1 and sample_j[n] == 1:
                output[0][0] += 1.0 / number_of_samples
            elif sample_i[n] == 1 and sample_j[n] == 2:
                output[0][1] += 1.0 / number_of_samples
            elif sample_i[n] == 1 and sample_j[n] == 3:
                output[0][2] += 1.0 / number_of_samples
            elif sample_i[n] == 1 and sample_j[n] == 4:
                output[0][3] += 1.0 / number_of_samples
            elif sample_i[n] == 1 and sample_j[n] == 5:
                output[0][4] += 1.0 / number_of_samples
            if sample_i[n] == 2 and sample_j[n] == 1:
                output[1][0] += 1.0 / number_of_samples
            elif sample_i[n] == 2 and sample_j[n] == 2:
                output[1][1] += 1.0 / number_of_samples
            elif sample_i[n] == 2 and sample_j[n] == 3:
                output[1][2] += 1.0 / number_of_samples
            elif sample_i[n] == 2 and sample_j[n] == 4:
                output[1][3] += 1.0 / number_of_samples
            elif sample_i[n] == 2 and sample_j[n] == 5:
                output[1][4] += 1.0 / number_of_samples
            if sample_i[n] == 3 and sample_j[n] == 1:
                output[2][0] += 1.0 / number_of_samples
            elif sample_i[n] == 3 and sample_j[n] == 2:
                output[2][1] += 1.0 / number_of_samples
            elif sample_i[n] == 3 and sample_j[n] == 3:
                output[2][2] += 1.0 / number_of_samples
            elif sample_i[n] == 3 and sample_j[n] == 4:
                output[2][3] += 1.0 / number_of_samples
            elif sample_i[n] == 3 and sample_j[n] == 5:
                output[2][4] += 1.0 / number_of_samples
            if sample_i[n] == 4 and sample_j[n] == 1:
                output[3][0] += 1.0 / number_of_samples
            elif sample_i[n] == 4 and sample_j[n] == 2:
                output[3][1] += 1.0 / number_of_samples
            elif sample_i[n] == 4 and sample_j[n] == 3:
                output[3][2] += 1.0 / number_of_samples
            elif sample_i[n] == 4 and sample_j[n] == 4:
                output[3][3] += 1.0 / number_of_samples
            elif sample_i[n] == 4 and sample_j[n] == 5:
                output[3][4] += 1.0 / number_of_samples
            if sample_i[n] == 5 and sample_j[n] == 1:
                output[4][0] += 1.0 / number_of_samples
            elif sample_i[n] == 5 and sample_j[n] == 2:
                output[4][1] += 1.0 / number_of_samples
            elif sample_i[n] == 5 and sample_j[n] == 3:
                output[4][2] += 1.0 / number_of_samples
            elif sample_i[n] == 5 and sample_j[n] == 4:
                output[4][3] += 1.0 / number_of_samples
            elif sample_i[n] == 5 and sample_j[n] == 5:
                output[4][4] += 1.0 / number_of_samples

        return output

    def log_n_cdf(self, x, mean, sig):
        if x < 0:
            cdf = 0
        elif np.isposinf(x):
            cdf = 1
        else:
            z = (np.log(x) - mean) / float(sig)
            cdf = 0.5 * (math.erfc(-z / np.sqrt(2)))

        return cdf
