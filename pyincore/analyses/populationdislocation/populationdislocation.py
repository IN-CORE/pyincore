# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import numpy as np
import pandas as pd
import warnings
from pyincore import BaseAnalysis
from pyincore.analyses.populationdislocation.populationdislocationutil import PopulationDislocationUtil


class PopulationDislocation(BaseAnalysis):
    """Population Dislocation Analysis computes dislocation for each residential structure based on the direct
    economic damage. The dislocation is calculated from four probabilites of dislocation based on a random normal
    distribution of the four damage factors presented by Bai, Hueste, Gardoni 2009.

    These four damage factors correspond to value loss. The sum of the four probabilities multiplied
    by the four probabilities of damage states was used as the probability for dislocation.

    This is different from Lin 2008
    http://hrrc.arch.tamu.edu/publications/research%20reports/08-05R%20Dislocation%20Algorithm%203.pdf
    which calculates a value loss which is the sum of the four damage factors times the four probabilities
    of damage. The two approaches produce different results.

    Args:
        incore_client (IncoreClient): Service authentication.

    """
    def __init__(self, incore_client):
        # coefficients for the Logistic regression model
        self.coefficient = {"beta0": -0.42523,
                            "beta1": 0.02480,
                            "beta2": -0.50166,  # single family coefficient
                            "beta3": -0.01826,  # black block group coefficient
                            "beta4": -0.01198   # hispanic block group coefficient
                            }

        super(PopulationDislocation, self).__init__(incore_client)

    def get_spec(self):
        return {
            'name': 'population-dislocation',
            'description': 'Population Dislocation Analysis',
            'input_parameters': [
                {
                    'id': 'result_name',
                    'required': False,
                    'description': 'Result CSV dataset name',
                    'type': str
                },
                {
                    'id': 'seed',
                    'required': True,
                    'description': 'Seed to ensure replication if run as part of a stochastic analysis, '
                                   'for example in connection with Population Allocation analysis.',
                    'type': int
                }
            ],
            'input_datasets': [
                {
                    'id': 'building_dmg',
                    'required': True,
                    'description': 'Building damage results CSV file from hazard service',
                    'type': ['ergo:buildingDamageVer4']
                },
                {
                    'id': 'population_allocation',
                    'required': True,
                    'description': 'Population Allocation CSV data',
                    'type': ['ergo:PopAllocation']
                },
                {
                    'id': 'block_group_data',
                    'required': True,
                    'description': 'Block group racial distribution census CSV data',
                    'type': ['ergo:blockGroupData']
                }
            ],
            'output_datasets': [
                {
                    'id': 'result',
                    'parent_type': 'population_block',
                    'description': 'A csv file with population dislocation result '
                                   'aggregated to the block group level',
                    'type': 'csv'
                }
            ]
        }

    def run(self):
        """Executes the Population dislocation analysis.

        Returns:
            bool: True if successful, False otherwise.

        """
        # Get seed
        seed_i = self.get_parameter("seed")

        # Get desired result name
        result_name = self.get_parameter("result_name")

        # Building Damage Dataset
        building_dmg = self.get_input_dataset("building_dmg").get_file_path('csv')

        # Population Allocation Dataset
        sto_pop_alloc = self.get_input_dataset("population_allocation").get_file_path('csv')

        # Block Group data
        bg_data = self.get_input_dataset("block_group_data").get_file_path('csv')

        merged_block_inv = PopulationDislocationUtil.merge_damage_population_block(
            building_dmg, sto_pop_alloc, bg_data
        )

        # Returns dataframe
        merged_final_inv = self.get_dislocation(seed_i, merged_block_inv)

        csv_source = "dataframe"
        self.set_result_csv_data("result", merged_final_inv, result_name, csv_source)

        return True

    def get_dislocation(self, seed_i: int, inventory: pd.DataFrame):
        """Calculates dislocation probability.

        Probability of dislocation, a binary variable based on the logistic probability of dislocation.
        A random number between 0 and 1 was assigned to each household.
        If the random number was less than the probability of dislocation
        then the household was determined to dislocate. This follows the logic
        that households with a greater chance of dislocated were more likely
        to have a random number less than the probability predicted.

        Args:
            seed_i (int): Seed for random normal to ensure replication if run as part of a stochastic analysis,
                for example in connection with Population Allocation analysis.
            inventory (pd.DataFrame): Merged building, population allocation and block group inventories

        Returns:
            pd.DataFrame: An inventory with probabilities of dislocation in a separate column

        """
        # pd.Series to np.array
        dsf = inventory["d_sf"].values
        pbd = inventory["pblackbg"].values
        phd = inventory["phispbg"].values

        prob_ins = inventory["insignific"].values
        prob_mod = inventory["moderate"].values
        prob_hvy = inventory["heavy"].values
        prob_cmp = inventory["complete"].values

        prob_disl_ins = self.get_disl_probability(prob_ins, dsf, pbd, phd)
        prob_disl_mod = self.get_disl_probability(prob_mod, dsf, pbd, phd)
        prob_disl_hvy = self.get_disl_probability(prob_hvy, dsf, pbd, phd)
        prob_disl_cmp = self.get_disl_probability(prob_cmp, dsf, pbd, phd)

        # total_prob_disl is the sum of the probability of dislocation at four damage states
        # times the probability of being in that damage state.
        total_prob_disl = prob_disl_ins * prob_ins + prob_disl_mod * prob_mod + prob_disl_hvy * prob_hvy + \
            prob_disl_cmp * prob_cmp

        inventory["prdis"] = total_prob_disl

        # Randomly assign dislocation based on probability of dislocation
        np.random.seed(seed_i)
        randomdis = np.random.uniform(0, 1, total_prob_disl.size)

        # Probability of dislocation, a binary variable based on the logistic probability of dislocation.
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        # comparisons involving np.nan outputs False, supress RuntimeWarning above
        dislocated = np.less_equal(randomdis, total_prob_disl)

        inventory["dislocated"] = dislocated

        return inventory

    def get_disl_probability(self, value_loss: np.array, d_sf: np.array,
                             percent_black_bg: np.array, percent_hisp_bg: np.array):
        """
        Calculate dislocation, the probability of dislocation for the household and population.
        Probability of dislocation Damage factor,
        based on current IN-COREv1 algorithm and Bai et al 2009 damage factors.

        The following variables are need to predict dislocation using logistic model
        see detailed explanation https://opensource.ncsa.illinois.edu/confluence/
        display/INCORE1/Household+and+Population+Dislocation?
        preview=%2F66224473%2F68289561%2FAlgorithm+3+Logistic.pdf

        Args:
            value_loss (np.array): Value loss.
            d_sf (np.array): 'Dummy' parameter.
            percent_black_bg (np.array): Block group data, percentage of black minority.
            percent_hisp_bg (np.array): Block group data, percentage of hispanic minority.

        Returns:
            numpy.array: Dislocation probability for the household and population.

        """
        disl_prob = np.zeros_like(d_sf)
        try:
            disl_prob = 1.0 / (1 + np.exp(-1.0 * (self.coefficient["beta0"] * 1 +
                                                  self.coefficient["beta1"] * (value_loss * 100) +
                                                  self.coefficient["beta2"] * d_sf +
                                                  self.coefficient["beta3"] * percent_black_bg +
                                                  self.coefficient["beta4"] * percent_hisp_bg)))
        except Exception as e:
            print()
            # raise e

        return disl_prob
