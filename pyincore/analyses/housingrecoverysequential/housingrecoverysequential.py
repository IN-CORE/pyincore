# Copyright (c) 2021 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
from pyincore import BaseAnalysis

import numpy as np
import pandas as pd
import collections as cl


class HousingRecoverySequential(BaseAnalysis):
    """
    This analysis computes the series of household recovery states given a population
    dislocation dataset, a transition probability matrix (TPM) and an initial state vector.

    The computation operates by segregating household units into five zones as a way of
    assigning social vulnerability. Using this vulnerability in conjunction with the TPM
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

    # Social vulnerability value generators per zone
    __sv_generator = {
        'Z1': {
            'threshold': 0.95,
            'below_lower': 0.01,
            'below_upper': 0.15,
            'above_lower': 0.10,
            'above_upper': 0.90
        },
        'Z2': {
            'threshold': 0.85,
            'below_lower': 0.10,
            'below_upper': 0.50,
            'above_lower': 0.10,
            'above_upper': 0.90
        },
        'Z3': {
            'threshold': 0.80,
            'below_lower': 0.30,
            'below_upper': 0.70,
            'above_lower': 0.10,
            'above_upper': 0.90
        },
        'Z4': {
            'threshold': 0.85,
            'below_lower': 0.50,
            'below_upper': 0.90,
            'above_lower': 0.10,
            'above_upper': 0.90
        },
        'Z5': {
            'threshold': 0.95,
            'below_lower': 0.85,
            'below_upper': 0.99,
            'above_lower': 0.10,
            'above_upper': 0.90
        }
    }

    def __init__(self, incore_client):
        super(HousingRecoverySequential, self).__init__(incore_client)

    def run(self):
        """Execute the HHRS analysis using parameters and input data."""
        # Read parameters
        t_delta = self.get_parameter('t_delta')
        t_final = self.get_parameter('t_final')

        # Load population block data from IN-CORE
        pop_dis_selectors = ['guid', 'huid', 'blockid',
                             'numprec', 'race', 'hispan',
                             'ownershp', 'randincome', 'dislocated']
        households_csv = self.get_input_dataset('population_dislocation_block').get_csv_reader()
        households_df = (pd.DataFrame(households_csv))[pop_dis_selectors]

        # Perform  conversions across the dataset from object type into the appropriate type
        households_df['blockid'] = households_df['blockid'].astype('int64')
        households_df['numprec'] = households_df['numprec'].astype(int)
        households_df['race'] = pd.to_numeric(households_df['race'])
        households_df['hispan'] = pd.to_numeric(households_df['hispan'])
        households_df['ownershp'] = pd.to_numeric(households_df['ownershp'])
        households_df['randincome'] = pd.to_numeric(households_df['randincome'])
        households_df['dislocated'] = (households_df['dislocated'] == 'True')

        # Load the transition probability matrix from IN-CORE
        tpm_csv = self.get_input_dataset("tpm").get_csv_reader()
        tpm = pd.DataFrame(list(tpm_csv))

        # Make sure all columns have numeric values
        for c_name in list(tpm.columns.values):
            tpm[c_name] = pd.to_numeric(tpm[c_name])

        tpm = tpm.to_numpy()
        tpm[:, 0] = np.around(tpm[:, 0], 3)

        # Load the initial stage probability vector
        initial_prob_csv = self.get_input_dataset("initial_stage_probabilities").get_csv_reader()
        initial_prob = pd.DataFrame(list(initial_prob_csv))
        initial_prob['value'] = pd.to_numeric(initial_prob['value'])

        # Run the analysis
        self.housing_serial_recovery_model(t_delta, t_final, tpm, initial_prob, households_df)

    def housing_serial_recovery_model(self, t_delta, t_final, tpm, initial_prob, households_df):
        """Performs the computation of the model as indicated in Sutley and Hamide (2020).

        Args:
            t_delta (float): Time step size.
            t_final (float): Final time.
            tpm (np.Array): Transition probability matrix.
            initial_prob (pd.DataFrame): Initial probability Markov vector.
            households_df (pd.DataFrame): Households with population dislocation data.

        """
        seed = self.get_parameter('seed')
        rng = np.random.RandomState(seed)

        # Compute the social vulnerability zone using known factors
        households_df = self.compute_social_vulnerability_zones(households_df)

        # Set the number of Markov chain stages
        stages = int(t_final / t_delta)

        # Data structure for selection operations
        initial_prob['cumulative'] = initial_prob['value'].cumsum()

        # Obtain number of households with social vulnerability zones
        num_households = households_df.shape[0]

        # Obtain a social vulnerability score stochastically per household
        # We use them later to construct the final output dataset
        sv_scores = self.compute_social_vulnerability_values(households_df, num_households, rng)

        # We store Markov states as a list of numpy arrays for convenience and add each one by one
        markov_stages = np.zeros((stages, num_households))

        for household in range(0, num_households):
            if households_df['dislocated'].iat[household]:
                spin = rng.rand()

                if spin < initial_prob['cumulative'][0]:
                    markov_stages[0][household] = 1.0
                elif spin < initial_prob['cumulative'][1]:
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
                        regressions = self.compute_regressions(markov_stages, household, 1, t)

                        if regressions > 10:
                            markov_stages[t][household] = 5
                    if t >= 12:
                        # Check the previous 12 timesteps that occurred prior to the current timestep.
                        regressions = self.compute_regressions(markov_stages, household, t - 11, t)

                        # If the number of regressive steps in the household's past 12 timesteps is greater than 4,
                        # the household transitions to stage 5.
                        if regressions > 4:
                            markov_stages[t][household] = 5
                    if t >= 24:
                        # Check the previous 24 timesteps that occurred prior to the current timestep.
                        regressions = self.compute_regressions(markov_stages, household, t - 23, t)

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
        result['guid'] = households_df['guid']
        result['huid'] = households_df['huid']
        result['Zone'] = households_df['Zone']
        result['SV'] = sv_scores
        column_names = [str(i) for i in range(1, stages + 1)]

        for i, c in enumerate(column_names):
            result[c] = markov_stages[i]

        result_name = self.get_parameter("result_name")
        self.set_result_csv_data("ds_result", result, name=result_name, source="dataframe")

    @staticmethod
    def compute_social_vulnerability_zones(households_df):
        """
        Compute the social vulnerability score based on dislocation attributes. Updates the dislocation dataset
        by adding a new `Zone` column and removing values with missing Zone.

        Args:
            households_df (pd.DataFrame): Vector position of a household.

        Returns:
            pd.DataFrame: Social vulnerability score.

        """
        zone_map = {0: 'Z5', 1: 'Z4', 2: 'Z3', 3: 'Z2', 4: 'Z1', np.nan: 'missing'}

        # TODO: to be replaced in next release by more comprehensive algorithm
        quantile = pd.qcut(households_df['randincome'], 5, labels=False)
        households_df['Zone'] = quantile.map(zone_map)
        return households_df[households_df['Zone'] != 'missing']

    def compute_social_vulnerability_values(self, households_df, num_households, rng):
        """
        Compute the social vulnerability score of a household depending on its zone

        Args:
            households_df (pd.DataFrame): Information about household zones.
            num_households (int): Number of households.
            rng (np.RandomState): Random state to draw pseudo-random numbers from.

        Returns:
            pd.Series: social vulnerability scores.

        """
        # Social vulnerability zone generator: this generalizes the code in the first version
        sv_scores = np.zeros(num_households)
        zones = households_df['Zone'].to_numpy()

        for household in range(0, num_households):
            spin = rng.rand()
            zone = zones[household]

            if spin < self.__sv_generator[zone]['threshold']:
                sv_scores[household] = round(rng.uniform(self.__sv_generator[zone]['below_lower'],
                                                         self.__sv_generator[zone]['below_upper']), 3)
            else:
                sv_scores[household] = round(rng.uniform(self.__sv_generator[zone]['above_lower'],
                                                         self.__sv_generator[zone]['above_upper']), 3)

        return sv_scores

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
            'name': 'housing-recovery-serial',
            'description': 'Household-level housing recovery serial model',
            'input_parameters': [
                {
                    'id': 'result_name',
                    'required': True,
                    'description': 'Result CSV dataset name',
                    'type': str
                },
                {
                    'id': 't_delta',
                    'required': True,
                    'description': 'size of the analysis time step',
                    'type': float
                },
                {
                    'id': 't_final',
                    'required': True,
                    'description': 'total duration',
                    'type': float
                },
                {
                    'id': 'seed',
                    'required': False,
                    'description': 'Seed to ensure replication of the Markov Chain path'
                                   'in connection with Population Dislocation.',
                    'type': int
                }
            ],
            'input_datasets': [
                {
                    'id': 'population_dislocation_block',
                    'required': True,
                    'description': 'A csv file with population dislocation result '
                                   'aggregated to the block group level',
                    'type': 'incore:popDislocation'
                },
                {
                    'id': 'tpm',
                    'required': True,
                    'description': 'Transition probability matrix in CSV format that specifies '
                                   'the corresponding Markov chain per social vulnerability level.',
                    'type': 'incore:houseRecTransitionProbMatrix'
                },
                {
                    'id': 'initial_stage_probabilities',
                    'required': True,
                    'description': 'initial mass probability function for stage 0 of the Markov Chain',
                    'type': 'incore:houseRecInitialStageProbability'
                }
            ],
            'output_datasets': [
                {
                    'id': 'ds_result',
                    'parent_type': 'housing_recovery_block',
                    'description': 'A csv file with housing recovery sequences'
                                   'at the individual household level',
                    'type': 'incore:housingRecoveryHistory'
                }
            ]
        }
