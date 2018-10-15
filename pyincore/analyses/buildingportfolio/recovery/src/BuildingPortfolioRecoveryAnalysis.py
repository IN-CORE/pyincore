#!/usr/bin/env python3

"""Building Portfolio Recovery Analysis

Usage:
    BuildingPortfolioRecoveryAnalysis.py --directory foo/data --building_damage file_name.csv --building_data
    file_name2.csv --utility file_name_3.csv --mean_repair file_name_4.csv --occupancy_mapping file_name_5.csv
    --output_file_name file_name_6 --number_of_simulations 1000

Options:
    DIRECTORY               Directory where all the files listed below are located.
    BUILDING_DAMAGE         Building damage file in csv
    BUILDING_DATA           Building data file in csv
    UTILITY                 Utility availability per service area in csv
    MEAN_REPAIR             Percentage of mean repair in csv
    OUTPUT_FILE_NAME        Name for the output file
    NUMBER_OF_SIMULATIONS   Number of Monte Carlo simulations

"""

import os
import math
import csv
import argparse
import pandas as pd
import numpy as np
import scipy as sp
import scipy.stats
from scipy.special import ndtri
import matplotlib.pyplot as plt
import concurrent.futures

from BuildingData import BuildingData


def load_csv_file(file_directory, file_name):
    read_file = pd.read_csv(os.path.join(file_directory, file_name), header="infer")
    return read_file


def calculate_delay_time(res_buildings, finance):
    """
    This function calculates the delay time given an initial functionality state and a financing resource
    :param res_buildings: Initial Damage State
    1: Slight Damage
    :param finance: Financing types, Can be a number from 1 to 5
    1: Insurance
    2: SBA Business Loan
    3: Private
    4: Savings
    5: Not covered
    :return: Impeding
    Takes into account each factor that alters the recovery time. Each item in the temporary array represents:
    impeding[0]: Initial Damage State
    impeding[1]: Engineering Mobilization
    impeding[2]: Insurance
    impeding[3]: Contractor Mobilization
    impeding[4]: Obtain permits
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


def joint_probability_calculation(sample_i, sample_j, number_of_samples):
    output = np.zeros((5,5))
    for n in range(number_of_samples):
        if sample_i[n] == 1 and sample_j[n] == 1:
            output[0][0] += 1.0/number_of_samples
        elif sample_i[n] == 1 and sample_j[n] == 2:
            output[0][1] += 1.0/number_of_samples
        elif sample_i[n] == 1 and sample_j[n] == 3:
            output[0][2] += 1.0/number_of_samples
        elif sample_i[n] == 1 and sample_j[n] == 4:
            output[0][3] += 1.0/number_of_samples
        elif sample_i[n] == 1 and sample_j[n] == 5:
            output[0][4] += 1.0/number_of_samples
        if sample_i[n] == 2 and sample_j[n] == 1:
            output[1][0] += 1.0/number_of_samples
        elif sample_i[n] == 2 and sample_j[n] == 2:
            output[1][1] += 1.0/number_of_samples
        elif sample_i[n] == 2 and sample_j[n] == 3:
            output[1][2] += 1.0/number_of_samples
        elif sample_i[n] == 2 and sample_j[n] == 4:
            output[1][3] += 1.0/number_of_samples
        elif sample_i[n] == 2 and sample_j[n] == 5:
            output[1][4] += 1.0/number_of_samples
        if sample_i[n] == 3 and sample_j[n] == 1:
            output[2][0] += 1.0/number_of_samples
        elif sample_i[n] == 3 and sample_j[n] == 2:
            output[2][1] += 1.0/number_of_samples
        elif sample_i[n] == 3 and sample_j[n] == 3:
            output[2][2] += 1.0/number_of_samples
        elif sample_i[n] == 3 and sample_j[n] == 4:
            output[2][3] += 1.0/number_of_samples
        elif sample_i[n] == 3 and sample_j[n] == 5:
            output[2][4] += 1.0/number_of_samples
        if sample_i[n] == 4 and sample_j[n] == 1:
            output[3][0] += 1.0/number_of_samples
        elif sample_i[n] == 4 and sample_j[n] == 2:
            output[3][1] += 1.0/number_of_samples
        elif sample_i[n] == 4 and sample_j[n] == 3:
            output[3][2] += 1.0/number_of_samples
        elif sample_i[n] == 4 and sample_j[n] == 4:
            output[3][3] += 1.0/number_of_samples
        elif sample_i[n] == 4 and sample_j[n] == 5:
            output[3][4] += 1.0/number_of_samples
        if sample_i[n] == 5 and sample_j[n] == 1:
            output[4][0] += 1.0/number_of_samples
        elif sample_i[n] == 5 and sample_j[n] == 2:
            output[4][1] += 1.0/number_of_samples
        elif sample_i[n] == 5 and sample_j[n] == 3:
            output[4][2] += 1.0/number_of_samples
        elif sample_i[n] == 5 and sample_j[n] == 4:
            output[4][3] += 1.0/number_of_samples
        elif sample_i[n] == 5 and sample_j[n] == 5:
            output[4][4] += 1.0/number_of_samples

    return output


def log_n_cdf(x, mean, sig):
    if x < 0:
        cdf = 0
    elif sp.isposinf(x):
        cdf = 1
    else:
        z = (sp.log(x)-mean)/float(sig)
        cdf = 0.5 * (math.erfc(-z/sp.sqrt(2)))

    return cdf


def main():
    parser = argparse.ArgumentParser()

    # Default directory is ../data
    parser.add_argument("-d", "--directory", help="Directory where all the input files are located",
                        default=os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')))
    parser.add_argument("--building_damage", help="Name for the building damage analysis results",
                        default="DamageAnalysisResults.csv")
    parser.add_argument("--building_data", help="Building Information",
                        default="Building_Data.csv")
    parser.add_argument("--utility", help="% utility availability at each utility service area - joint area of power "
                                          "and water (row), at each week (column)",
                        default="utility.csv")
    parser.add_argument("--utility2", help="Partial utility availability ",
                        default="utility2.csv")
    parser.add_argument("--mean_repair", help="Percentage of mean repair by occupancy / building type",
                        default="Mean_Repair.csv")
    parser.add_argument("--occupancy_mapping", help="",
                        default="Occupancy_Code_Mapping.csv")
    parser.add_argument("--output_file_name", help="Name for the output file",
                        default="building_portfolio_recovery")
    parser.add_argument("--number_of_simulations", help="Number of simulations", default = 100)
                        # default=5000)
    parser.add_argument("--uncertainty", help="True to include uncertainty analysis",
                        default=False)
    parser.add_argument("--sample_size", help="Number of buildings to use as a sample", default = 1000)
                        # default = 1000)

    args = parser.parse_args()
    uncertainty = args.uncertainty                                                           
    utility_initial = load_csv_file(args.directory, args.utility)
    building_damage_results = load_csv_file(args.directory, args.building_damage)
    building_data = load_csv_file(args.directory, args.building_data)
    mean_repair = load_csv_file(args.directory, args.mean_repair)
    occupancy_mapping = load_csv_file(args.directory, args.occupancy_mapping)

    print('INFO: Data for Building Portfolio Recovery Analysis loaded successfully.')

    sample_size = args.sample_size # len(building_damage_results)

    permutation = np.random.permutation(len(building_data))
    permutation_subset = permutation[0:sample_size]
    sample_buildings = [BuildingData(building_data['Tract_ID'][i], building_data['X_Lon'][i],
                                     building_data['Y_Lat'][i], building_data['Structural'][i],
                                     building_data['Code_Level'][i], building_data['EPSANodeID'][i],
                                     building_data['PWSANodeID'][i], building_data['TEP_ID'][i],
                                     building_data['Build_ID_X'][i], building_data['EPSAID'][i],
                                     building_data['PWSAID'][i], building_data['Finance'][i],
                                     building_data['EP_PW_ID'][i], building_data['Occu_Code'][i]
                                     )
                        for i in permutation_subset]
    occupancy_map = {occupancy_mapping["Occu_ID"][i]: occupancy_mapping['Occupancy'][i] for i in
                     range(len(occupancy_mapping)) }
    repair_mean = {mean_repair['Occupancy'][i]: [mean_repair['RC1'][i], mean_repair['RC2'][i],
                                                 mean_repair['RC3'][i], mean_repair['RC4'][i]]
                   for i in range(len(mean_repair))}

    building_damage = [[building_damage_results['Restricted Entry'][i],
                        building_damage_results['Restricted Use'][i],
                        building_damage_results['Reoccupancy'][i],
                        building_damage_results['Best Line Functionality'][i],
                        building_damage_results['Full Functionality'][i]]
                       for i in range(len(building_damage_results))]

    # START: Calculate waiting time statistics using Monte Carlo Simulations
    number_of_simulations = args.number_of_simulations
    sample_delay = np.zeros(number_of_simulations)
    impeding_mean = np.zeros((5, 4))
    impeding_std = np.zeros((5, 4))

    for i in range(4):
        for j in range(5):
            for k in range(number_of_simulations):
                sample_delay[k] = calculate_delay_time(i, j)
            impeding_mean[j, i] = np.mean(sample_delay)
            impeding_std[j, i] = np.std(sample_delay)

    # END: Calculate waiting time statistics using Monte Carlo Simulations

    # Recovery time step from week 1 to 300
    time_steps = 300
    utility = np.ones((len(utility_initial), time_steps))

    # START initializing variables for uncertainty analysis
    target_mean_recovery = np.zeros(time_steps)
    temporary_correlation1 = np.zeros((time_steps, sample_size, 5))
    temporary_correlation2 = np.zeros((time_steps, sample_size, 5))
    mean_over_time = np.zeros((time_steps, sample_size))
    variance_over_time = np.zeros((time_steps, sample_size))
    utility2 = np.zeros((len(utility_initial), time_steps))
    # END code for uncertainty analysis

    # Utility matrix. Represents the recovery for each of the utility areas at a given number of weeks after the event
    # The utility matrix uses utility Initial input file for the first 22 weeks and ones for the rest of the time.

    for i in range(len(utility_initial.columns)):
        utility[:, i] = [j for j in utility_initial[str(i)]]

    # Mean recovery trajectory at portfolio level
    mean_recovery = np.zeros((time_steps, 5))
    total_mean = np.zeros((4, 4))
    total_var = np.zeros((4, 4))
    transition_probability = np.zeros((4,4))
    state_probabilities = np.zeros((time_steps, 5))
    output = np.zeros(time_steps)

    # Functionality Recovery (Best Line Functionality + Full functionality) for each building on the sample
    recovery_fp = np.zeros((sample_size, time_steps))

    for k in range(sample_size):

        # The index for finance starts in 1 they are one off from the matrix
        finance_id = sample_buildings[k].finance - 1
        utility_id = sample_buildings[k].ep_pw_id
        for j in range(4):
            mean = impeding_mean[finance_id, j]
            std = impeding_std[finance_id, j] ** 2

            for i in range(j, 4):

                mean += repair_mean[occupancy_map[sample_buildings[k].occupation_code]][i]
                total_mean[j][i] = mean
                std += 0.4 * repair_mean[occupancy_map[sample_buildings[k].occupation_code]][i] ** 2
                total_var[j][i] = math.sqrt(std)

        for t in range(time_steps):
            for i in range(4):
                for j in range(i, 4):
                    zeta = math.sqrt(math.log(1+(total_var[i][j]/total_mean[i][j])**2))
                    lambda_log = math.log(total_mean[i][j]) - 1/2 * zeta **2
                    transition_probability[i][j] = log_n_cdf(t+1, lambda_log, zeta)
            # tpm = transition probability matrix
            tpm = np.matrix([[1 - transition_probability[0, 0],
                    transition_probability[0, 0] - transition_probability[0, 1],
                    transition_probability[0, 1] - transition_probability[0, 2],
                    transition_probability[0, 2] - transition_probability[0, 3], transition_probability[0, 3]],
                   [0.0, 1 - transition_probability[1, 1], transition_probability[1, 1] - transition_probability[1, 2],
                    transition_probability[1, 2] - transition_probability[1, 3], transition_probability[1, 3]],
                   [0.0, 0.0, 1 - transition_probability[2, 2],
                    transition_probability[2, 2] - transition_probability[2, 3], transition_probability[2, 3]],
                   [0.0, 0.0, 0.0, 1 - transition_probability[3, 3], transition_probability[3, 3]],
                   [0.0, 0.0, 0.0, 0.0, 1.0]], dtype=float)
            # State Probability vector, pie(t) = initial vector * Transition Probability Matrix
            state_probabilities[t] = np.matmul(building_damage[k], tpm)
            if not uncertainty:
                output[t] = state_probabilities[t, 3] + state_probabilities[t, 4]

            if uncertainty:
                # Considering the effect of utility availability
                # Utility Dependence Matrix
                utility_matrix = np.matrix([[1, 0, 0, 0, 0],
                                  [0, 1, 0, 0, 0],
                                  [0, 0, 1, utility[utility_id][t], utility[utility_id][t]],
                                  [0, 0, 0, 1 - utility[utility_id][t], utility2[utility_id][t]],
                                  [0, 0, 0, 0, 1 - utility[utility_id][t] - utility2[utility_id][t]]
                                  ], dtype=float)
                updated_tpm = np.matmul(tpm, utility_matrix.transpose())
                state_probabilities[t] = np.matmul(state_probabilities[t], utility_matrix.transpose())

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
                mean_over_time[t][k] = state_probabilities[t][3] + state_probabilities[t][4]
                variance_over_time[t][k] = (state_probabilities[t][3]+state_probabilities[t][4]) * \
                                           (1 - (state_probabilities[t][3] + state_probabilities[t][4]))

        # Considering the effect of utility availability
        # Service Area ID of individual buildings
        # START: Code from only recovery analysis
        if not uncertainty:

            for i in range(len(state_probabilities)):
                state_probabilities[i, 2] = state_probabilities[i, 2] + state_probabilities[i, 3] + \
                                            state_probabilities[i, 4] * (1 - utility[utility_id, i])
                state_probabilities[i, 3] = state_probabilities[i, 3] * utility[utility_id, i]
                state_probabilities[i, 4] = state_probabilities[i, 4] * utility[utility_id, i]

        # END: Code from only recovery analysis

        # Save functional probability (Best Line Functionality + Full functionality) for each building
        recovery_fp[k, :] = state_probabilities[:, 4] + state_probabilities[:, 3]

        # Aggregate state probability vector to portfolio level
        mean_recovery = mean_recovery + state_probabilities

    # Trajectory for the Restricted entry, Restricted Use, Reoccupancy, Best Line Functionality, Full Functionality
    mean_recovery = mean_recovery/sample_size

    # Trajectory for Best Line Functionality and Full Functionality
    mean_recovery_output = sum(recovery_fp)/sample_size

    fig = plt.figure(1)
    plt.plot(range(300), mean_recovery_output)
    plt.xlabel('# of Weeks since event')
    plt.ylabel('Probability of Portfolio Recovery')
    plt.title('Building Portfolio Recovery Analysis')
    output_directory = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'output'))
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    output_image = os.path.join(output_directory, args.output_file_name+'.png')
    fig.savefig(output_image)

    output_file = os.path.join(output_directory, args.output_file_name+'.csv')
    with open(output_file, 'w+', newline='') as output_file:
        spam_writer = csv.writer(output_file, delimiter=' ', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        spam_writer.writerow(['Week', 'Recovery Percentage'])
        for i in range(len(mean_recovery_output)):
            spam_writer.writerow([i, mean_recovery_output[i]])

    if uncertainty:
        # START: Additional Code for uncertainty analysis
        mean_u = np.zeros(sample_size)
        # sample_size2 = args.sample_size
        covar = np.zeros([sample_size, sample_size]) #TODO: Should read a coefFL file
        random_distribution = np.random.multivariate_normal(mean_u, covar, number_of_simulations)
        random_samples = sp.stats.norm.cdf(random_distribution)
        sample_total = np.zeros((sample_size, number_of_simulations))

        for j in range(number_of_simulations):
            sample = np.zeros(sample_size)
            for i in range(sample_size):
                threshold = building_damage[i]
                if random_samples[j][i] <= threshold[0]:
                    sample[i] = 1
                elif random_samples[j][i] <= threshold[0] + threshold[1] and random_samples[j][i] <= threshold[0]:
                    sample[i] = 2
                elif threshold[0] + threshold[1] <= random_samples[j][i] <= threshold[0] + threshold[1] + threshold[2] :
                    sample[i] = 3
                elif threshold[0] + threshold[1] + threshold[2] <= random_samples[j][i] <= threshold[0] + threshold[1] + threshold[2] + threshold[3] :
                    sample[i] = 4
                else:
                    sample[i] = 5
                sample_total[i][j] = sample[i]

        for k in range(sample_size):
            for t in range(time_steps):
                if variance_over_time[t][k] <= 0:
                    variance_over_time[t][k] = 0

        # Start calculating standard deviation of the mean recovery trajectory
        total_standard_deviation = np.zeros(time_steps)
        for t in range(time_steps):
            total_standard_deviation[t] = np.sum(variance_over_time[t])

            # Building i
            for i in range(sample_size - 1):
                # Building j
                for j in range(i + 1, sample_size):
                    expect1 = 0
                    # Joint probability of initial functionality state P(S0i=k, S0j=l)
                    joint_probability = joint_probability_calculation(sample_total[i], sample_total[j], number_of_simulations)

                    # Functionality State k
                    for k in range(5):
                        # Functionality State l
                        for l in range(5):
                            expect1 += joint_probability[k][l] * temporary_correlation1[t][i][k] * temporary_correlation1[t][j][l]\
                                       + temporary_correlation1[t][i][k] * temporary_correlation1[t][j][l]\
                                       + temporary_correlation2[t][i][k] * temporary_correlation1[t][j][l]\
                                       + temporary_correlation2[t][i][k] * temporary_correlation2[t][j][l]
                    expect2 = mean_over_time[t][i] * mean_over_time[t][j]

                    covariance = 0
                    if variance_over_time[t][i] > 0 and variance_over_time[t][j] > 0 and expect1 - expect2 > 0:
                        covariance = expect1 - expect2
                    total_standard_deviation[t] += 2 * covariance
        # total_standard_deviation = math.sqrt(total_standard_deviation) / sample_size
        # for t in range(time_steps):
        #     total_standard_deviation[t] = math.sqrt(total_standard_deviation[t]) / sample_size
        ## TODO: Create some plots;
        # Plot uncertainty of the mean recovery trajectory

        # Calculate distribution of Portfolio Recovery Time (PRT) assume normal distribution

        x_range = np.arange(0.0, 1.0, 0.001)
        pdf_full = np.zeros((time_steps, len(x_range)))
        irt = np.zeros(time_steps)
        for t in range(time_steps):
            total_standard_deviation[t] = math.sqrt(total_standard_deviation[t]) / sample_size
            pdf_full[t] = sp.stats.norm.pdf(x_range, target_mean_recovery[t], total_standard_deviation[t])
        # for t in range(time_steps):
            coeR = np.trapz(x_range, pdf_full[t])
            pdf_full[t] = pdf_full[t]/coeR
        # np.trapz(x_range, pdf_full.transpose())

        # for t in range(time_steps):
            idx = int(len(x_range) * 95 / 100 + 1)
            irt[t] = np.trapz(x_range[idx:], pdf_full[t, idx:])

        pdf = np.zeros(time_steps)
        for t in range(1, time_steps-1):
            pdf[t] = (irt[t+1] - irt[t]) if irt[t+1] - irt[t] > 0 else 0

        #TODO: Some more figures. End of page 8

        # Expected portfolio Recovery Time, output variable
        meanPRT = np.trapz(np.arange(time_steps), np.arange(time_steps)*pdf)

        # Calculate truncated normal distribution and 75% & 95% percentile band
        # 75% percentile upper bound
        upper_bound75 = target_mean_recovery + 1.15 *total_standard_deviation
        # 75% percentile lower bound
        lower_bound75 = target_mean_recovery - 1.15 * total_standard_deviation
        # 95% percentile upper bound
        upper_bound95 = target_mean_recovery + 1.96 * total_standard_deviation
        # 95% percentile lower bound
        lower_bound95 = target_mean_recovery - 1.96 * total_standard_deviation

        for t in range(time_steps):
            coet = sp.stats.norm.cdf(0, target_mean_recovery[t], total_standard_deviation[t])
            coet2 = 1 - sp.stats.norm.cdf(1, target_mean_recovery[t], total_standard_deviation[t])

            if coet >= 0.000005 and 1 - coet2 < 0.00005:
                coeAmp = 1 / (1 - coet)
                lower_bound95[t] = sp.stats.norm.ppf(0.05 / coeAmp + coet, target_mean_recovery[t], total_standard_deviation[t])
                upper_bound95[t] = sp.stats.norm.ppf(0.95 / coeAmp + coet, target_mean_recovery[t], total_standard_deviation[t])
                lower_bound75[t] = sp.stats.norm.ppf(0.25 / coeAmp + coet, target_mean_recovery[t], total_standard_deviation[t])
                upper_bound75[t] = sp.stats.norm.ppf(0.75 / coeAmp + coet, target_mean_recovery[t], total_standard_deviation[t])

                pdf_full[t] = pdf_full[t] * coeAmp
            if coet2 >= 0.000005 and coet < 0.00005:
                coeAmp = 1/ (1-coet2)
                lower_bound95[t] = sp.stats.norm.ppf((1 - coet2) - 0.95 / coeAmp, target_mean_recovery[t], total_standard_deviation[t])
                upper_bound95[t] = sp.stats.norm.ppf((1 - coet2) - 0.05 / coeAmp, target_mean_recovery[t], total_standard_deviation[t])
                lower_bound75[t] = sp.stats.norm.ppf((1 - coet2) - 0.75 / coeAmp, target_mean_recovery[t], total_standard_deviation[t])
                upper_bound75[t] = sp.stats.norm.ppf((1 - coet2) - 0.25 / coeAmp, target_mean_recovery[t], total_standard_deviation[t])

                pdf_full[t] = pdf_full[t]*coeAmp
            if coet >= 0.000005 and 1 - coet2 >= 0.00005:
                coeAmp = 1/(coet2 - coet)
                lower_bound95[t] = sp.stats.norm.ppf(0.05/coeAmp+coet, target_mean_recovery[t], total_standard_deviation[t])
                upper_bound95[t] = sp.stats.norm.ppf(coet2-0.05/coeAmp, target_mean_recovery[t], total_standard_deviation[t])
                lower_bound75[t] = sp.stats.norm.ppf(0.25/coeAmp, target_mean_recovery[t], total_standard_deviation[t])
                upper_bound75[t] = sp.stats.norm.ppf(coet2-0.25/coeAmp, target_mean_recovery[t], total_standard_deviation[t])

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

        fig2 = plt.figure(2)
        plt.plot(range(time_steps), target_mean_recovery, color="black")
        plt.plot(range(time_steps), lower_bound75, color="red")
        plt.plot(range(time_steps), upper_bound75, color="red")
        plt.plot(range(time_steps), lower_bound95, color="blue")
        plt.plot(range(time_steps), upper_bound95, color="blue")
        plt.xlabel('Expected recovery time (weeks)')
        plt.ylabel('Percentage of Buildings Recovered')
        plt.title('Building Portfolio Recovery Analysis with uncertainty')
        output_directory = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'output'))
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        output_image2 = os.path.join(output_directory, args.output_file_name+'2.png')
        fig2.savefig(output_image2)

        output_file = os.path.join(output_directory, args.output_file_name+'.csv')
        with open(output_file, 'w+', newline='') as output_file:
            spam_writer = csv.writer(output_file, delimiter=' ', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            spam_writer.writerow(['Week', 'Recovery Percentage', '75% Upper Bound', '75% Lower Bound', '95% Upper Bound',
                                  '95% Lower Bound'])
            for i in range(time_steps):
                spam_writer.writerow([i, mean_recovery_output[i], lower_bound75[i], upper_bound75[i], lower_bound95[i],
                                      upper_bound95[i]])


    print("INFO: Finished executing Building Portfolio Recovery Analysis")


# def calculate_transition_probability_matrix():

# calculating standard deviation of the mean recovery trajectory
# def calculate_std_of_mean():


if __name__ == '__main__':
    main()
