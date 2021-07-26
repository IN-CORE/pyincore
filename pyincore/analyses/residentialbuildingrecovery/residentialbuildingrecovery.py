# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import numpy as np
import pandas as pd
from scipy.stats import lognorm
import time
import random

from pyincore import BaseAnalysis, RepairService
from pyincore.analyses.buildingdamage.buildingutil import BuildingUtil


class ResidentialBuildingRecovery(BaseAnalysis):
    """
    Args:
        incore_client (IncoreClient): Service authentication.

    """

    def __init__(self, incore_client):
        self.repairsvc = RepairService(incore_client)

        super(ResidentialBuildingRecovery, self).__init__(incore_client)

    def get_spec(self):
        """Get specifications of the residential building recovery analysis.

        Returns:
            obj: A JSON object of specifications of the residential building recovery analysis.

        """
        return {
            'name': 'residential-building-recovery',
            'description': 'calculate residential building recovery',
            'input_parameters': [
                {
                    'id': 'result_name',
                    'required': True,
                    'description': 'name of the result',
                    'type': str
                },
                {
                    'id': 'num_samples',
                    'required': True,
                    'description': 'Number of sample scenarios',
                    'type': int
                },
                {
                    'id': 'repair_key',
                    'required': False,
                    'description': 'Repair key to use in mapping dataset',
                    'type': str
                },
                {
                    'id': 'seed',
                    'required': False,
                    'description': 'Initial seed for the probabilistic model',
                    'type': int
                }
            ],
            'input_datasets': [
                {
                    'id': 'buildings',
                    'required': True,
                    'description': 'Building Inventory',
                    'type': ['ergo:buildingInventoryVer4', 'ergo:buildingInventoryVer5', 'ergo:buildingInventoryVer6',
                             'ergo:buildingInventoryVer7']
                },
                {
                    'id': 'dfr3_mapping_set',
                    'required': True,
                    'description': 'DFR3 Mapping Set Object',
                    'type': ['incore:dfr3MappingSet'],
                },
                {
                    'id': 'sample_damage_states',
                    'required': True,
                    'description': 'Sample damage states',
                    'type': ['incore:sampleDamageState']
                },
                {
                    'id': 'socio_demographic_data',
                    'required': True,
                    'description': 'Socio-demographic data with household income group predictions',
                    'type': ['incore:socioDemograhicData']
                },
                {
                    'id': 'financial_resources',
                    'required': True,
                    'description': 'Financial resources by household income groups',
                    'type': ['incore:householdFinancialResources']
                },
                {
                    'id': 'delay_factors',
                    'required': True,
                    'description': 'Delay impeding factors such as post-disaster inspection, insurance claim, '
                                   'and government permit based on building\'s damage state. Provided by REDi framework',
                    'type': ['incore:buildingRecoveryFactors']
                }
            ],
            'output_datasets': [
                {
                    'id': 'residential_building_recovery',
                    'description': 'CSV file of residential building recovery percent',
                    'type': 'incore:buildingRecovery'
                }
            ]
        }

    def run(self):
        """Executes the residential building recovery analysis.

        Returns:
            bool: True if successful, False otherwise.

        """
        # TODO: Start using seed
        seed = self.get_parameter("seed")

        num_samples = self.get_parameter("num_samples")
        result_name = self.get_parameter("result_name")

        repair_key = self.get_parameter("repair_key")
        if repair_key is None:
            repair_key = BuildingUtil.DEFAULT_REPAIR_KEY
            self.set_parameter("repair_key", repair_key)

        buildings = self.get_input_dataset("buildings").get_inventory_reader()
        buildings = list(buildings)
        sample_damage_states = self.get_input_dataset("sample_damage_states").get_dataframe_from_csv(low_memory=False)
        socio_demographic_data = self.get_input_dataset("socio_demographic_data").get_dataframe_from_csv(
            low_memory=False)
        # socio_demographic_data.set_index("guid", inplace=True)
        financial_resources = self.get_input_dataset("financial_resources").get_dataframe_from_csv(low_memory=False)
        redi_delay_factors = self.get_input_dataset("delay_factors").get_dataframe_from_csv(low_memory=False)

        # Returns dataframe
        recovery_results = self.residential_recovery(buildings, sample_damage_states, socio_demographic_data,
                                                     financial_resources, redi_delay_factors, num_samples)
        self.set_result_csv_data("residential_building_recovery", recovery_results, result_name, "dataframe")

        return True

    def residential_recovery(self, buildings, sample_damage_states, socio_demographic_data, financial_resources,
                             redi_delay_factors, num_samples):
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
        household_income_prediction = ResidentialBuildingRecovery.household_income_prediction(socio_demographic_data,
                                                                                              num_samples)
        end_start_household_income_prediction = time.process_time()
        print("Finished executing household_income_prediction() in " +
              str(end_start_household_income_prediction - start_household_income_prediction) + " secs")


        household_aggregation = ResidentialBuildingRecovery.household_aggregation(household_income_prediction, num_samples)
        end_household_aggregation = time.process_time()
        print("Finished executing household_aggregation() in " +
              str(end_household_aggregation - end_start_household_income_prediction) + " secs")

        financing_delay = ResidentialBuildingRecovery.financing_delay(household_aggregation, financial_resources, num_samples)
        end_financing_delay = time.process_time()
        print("Finished executing financing_delay() in " +
              str(end_financing_delay - end_household_aggregation) + " secs")

        total_delay = ResidentialBuildingRecovery.total_delay(sample_damage_states, redi_delay_factors, financing_delay,
                                                              num_samples)
        end_total_delay = time.process_time()
        print("Finished executing total_delay() in " + str(end_total_delay - end_financing_delay) + " secs")

        recovery = self.recovery_rate(buildings, sample_damage_states, total_delay, num_samples)
        end_recovery = time.process_time()
        print("Finished executing recovery_rate() in " + str(end_recovery - end_total_delay) + " secs")

        time_stepping_recovery = ResidentialBuildingRecovery.time_stepping_recovery(recovery, num_samples)
        end_time_stepping_recovery = time.process_time()
        print("Finished executing time_stepping_recovery() in " +
              str(end_time_stepping_recovery - end_recovery) + " secs")

        result = time_stepping_recovery

        end_time = time.process_time()
        print("Analysis completed in " + str(end_time - start_household_income_prediction) + " secs")

        return result

    @staticmethod
    def household_income_prediction(income_groups, num_samples):
        """ Get Income group prediction for each household

        Args:
            income_groups (pd.DataFrame): Socio-demographic data with household income group prediction.
            num_samples (int): Number of sample scenarios.

        Returns:
            pd.DataFrame: Income group prediction for each household

        """

        blockid = income_groups.groupby('blockid')
        prediction_results = pd.DataFrame()
        count = 0
        for name, group in blockid:
            mean = group['hhinc'].mean()
            std = group['hhinc'].std()
            if np.isnan(mean):
                mean = 3
            if np.isnan(std):
                std = 0
            number = group['hhinc'].isna().sum()
            for i in range(num_samples):
                sample = np.random.normal(mean, std, number)
                inds = np.where(group['hhinc'].isna())
                sample[np.where(sample > 5)] = 5
                sample[np.where(sample < 1)] = 1
                group['sample_{}'.format(i)] = group['hhinc']
                group['sample_{}'.format(i)][count + inds[0]] = np.around(sample)
                # TODO: Fix the warning here
                # group.loc[group['sample_{}'.format(i)], count + inds[0]] = np.around(sample)
            count += group['blockid'].count()
            prediction_results = prediction_results.append(group, ignore_index=True)
        return prediction_results

    @staticmethod
    def household_aggregation(household_income_predictions, num_samples):
        """ Gets household aggregation of income groups at the building level.

        Args:
            household_income_predictions (pd.DataFrame): Income group prediction for each household
            num_samples (int): Number of sample scenarios.

        Returns:
            pd.DataFrame: Results of household aggregation of income groups at the building level.
        """

        guid = household_income_predictions.groupby('guid')
        household_aggregation_results = pd.DataFrame(columns=household_income_predictions.columns)
        household_aggregation_results = household_aggregation_results.drop(columns=['huid', 'blockid', 'hhinc'])

        count = 0
        for name, group in guid:
            household_aggregation_results = household_aggregation_results.append({'guid': name}, ignore_index=True)
            for i in range(num_samples):
                household_aggregation_results['sample_{}'.format(i)][count] = group['sample_{}'.format(i)].max()
            count += 1
        return household_aggregation_results

    @staticmethod
    def financing_delay(household_aggregated_income_groups, financial_resources, num_samples):
        """ Gets financing delay, the percentages calculated are the probabilities of housing units financed by
        different resources.

        Args:
            household_aggregated_income_groups (pd.DataFrame): Household aggregation of income groups at the building
                level.
            financial_resources (pd.DataFrame): Financial resources by household income groups.
            num_samples (int): Number of sample scenarios.

        Returns:
            pd.DataFrame: Results of financial delay
        """

        financing_delay = pd.DataFrame(columns=household_aggregated_income_groups.columns)
        for index, row in household_aggregated_income_groups.iterrows():
            for i in range(num_samples):
                value = row['sample_{}'.format(i)]
                hhinc = financial_resources.loc[financial_resources['hhinc'] == float(value)]
                ind = financial_resources.loc[financial_resources['hhinc'] == float(value)].index[0]
                delay = np.random.lognormal(np.log(financial_resources['Insurance'][5]),
                                            financial_resources['Insurance'][6]) * hhinc['Insurance'] + \
                        np.random.lognormal(np.log(financial_resources['Private'][5]),
                                            financial_resources['Private'][6]) * hhinc['Private'] + \
                        np.random.lognormal(np.log(financial_resources['SBA'][5]),
                                            financial_resources['SBA'][6]) * hhinc['SBA'] + \
                        np.random.lognormal(np.log(financial_resources['Savings'][5]),
                                            financial_resources['Savings'][6]) * hhinc['Savings']
                delay = np.round(delay, 1)
                row['sample_{}'.format(i)] = delay[ind]
            financing_delay.loc[index] = row
        return financing_delay

    @staticmethod
    def total_delay(sample_damage_states, redi_delay_factors, financing_delay, num_samples):
        """ Calculates total delay by combining financial delay and other factors from REDi framework

        Args:
            sample_damage_states (pd.DataFrame): Building inventory damage states.
            redi_delay_factors (pd.DataFrame): Delay impeding factors such as post-disaster inspection, insurance claim,
                and government permit based on building's damage state.
            financing_delay (pd.DataFrame): Financing delay, the percentages calculated are the probabilities of housing
                units financed by different resources.
            num_samples (int): Number of sample scenarios.

        Returns:
            pd.DataFrame: Total delay time of financial delay and other factors from REDi framework.
        """

        total_delay = pd.DataFrame(columns=financing_delay.columns)
        for index, row in sample_damage_states.iterrows():
            samples_mcs = row["sample_damage_states"].split(",")
            for i in range(num_samples):
                value = samples_mcs[i]

                # redi_delay_factors dataset represents DS0
                building_conditions = redi_delay_factors.loc[redi_delay_factors['Building_specific_conditions']
                                                             == value]
                inspection = np.random.lognormal(np.log(building_conditions['Ins_med']), building_conditions['Ins_sdv'])
                engmob = np.random.lognormal(np.log(building_conditions['Enmo_med']), building_conditions['Enmo_sdv'])
                conmob = np.random.lognormal(np.log(building_conditions['Como_med']), building_conditions['Como_sdv'])
                permitting = np.random.lognormal(np.log(building_conditions['Per_med']), building_conditions['Per_sdv'])
                financing_time = financing_delay['sample_{}'.format(i)][index]
                delay = np.round(inspection[0] + max(engmob[0], conmob[0], financing_time) + permitting[0], 1)
                row['sample_{}'.format(i)] = delay
            total_delay.loc[index] = row
        return total_delay

    def recovery_rate(self, buildings, sample_damage_states, total_delay, num_samples):
        """ Gets total time required for each building to receive full restoration. Determined by the combination of
        delay time and repair time

        Args:
            buildings (list): List of buildings
            sample_damage_states (pd.DataFrame): Samples' damage states
            total_delay (pd.DataFrame): Total delay time of financial delay and other factors from REDi framework.
            num_samples (int): Number of sample scenarios.

        Returns:
            pd.DataFrame: Recovery rates of all buildings for each sample
        """

        repair_key = self.get_parameter("repair_key")
        repair_sets = self.repairsvc.match_inventory(self.get_input_dataset("dfr3_mapping_set"), buildings, repair_key)
        repair_sets_by_guid = {}  # get repair sets by guid so they can be mapped with output of monte carlo

        # This is sort of a workaround until we define Repair Curve models and abstract this out there
        i = 0
        for b in buildings:
            repair_sets_by_guid[b["properties"]['guid']] = repair_sets[str(i)]
            i += 1

        recovery_time = total_delay.drop(total_delay.columns[1: num_samples + 1], axis=1)

        for count_N1 in range(num_samples):
            for count_N2 in range(num_samples):
                recovery_time['sample_{}_{}'.format(count_N1, count_N2)] = 'default'

        for index, row in sample_damage_states.iterrows():
            guid = row["guid"]
            samples_mcs = row["sample_damage_states"].split(",")
            for count_N1 in range(num_samples):
                state = int(samples_mcs[count_N1].replace("DS_", ""))  # map DS_0 to repair curve at index 0, etc.
                for count_N2 in range(num_samples):
                    rand = random.random()
                    mapped_repair = repair_sets_by_guid[guid]
                    lognormal_mean = mapped_repair.repair_curves[state].alpha
                    lognormal_sdv = mapped_repair.repair_curves[state].beta
                    repair_time = (lognorm.ppf(rand, lognormal_sdv, scale=np.exp(lognormal_mean))) / 7
                    recovery_time['sample_{}_{}'.format(count_N1, count_N2)][index] = \
                        round(total_delay['sample_{}'.format(count_N1)][index] + repair_time, 1)
        return recovery_time

    @staticmethod
    def time_stepping_recovery(recovery_results, num_samples):
        """ Converts results to a time frame. Currently gives results for 16 quarters over 4 year.

        Args:
            recovery_results (pd.DataFrame): Total recovery time of financial delay and other factors from REDi framework.
            num_samples (int): Number of sample scenarios.

        Returns:
            pd.DataFrame: Time formatted recovery results.

        """

        time_step = 90 / 7  # a quarter in weeks
        year = 4
        total_time = [x * time_step for x in range(4 * year + 1)]
        for i in range(len(total_time)):
            recovery_results['quarter_{}'.format(i)] = float(1111)
        for index, row in recovery_results.iterrows():
            row = row.drop('guid').values
            for i in range(len(total_time)):
                fun_state = len(row[row < total_time[i]]) / (len(row) - len(total_time))
                recovery_results['quarter_{}'.format(i)][index] = round(fun_state, 2)
        recovery_results = recovery_results.drop(recovery_results.columns[1: num_samples ** 2 + 1], axis=1)
        return recovery_results
