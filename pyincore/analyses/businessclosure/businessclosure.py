# Copyright (c) 2021 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import numpy as np
import pandas as pd

from pyincore import BaseAnalysis


class BusinessClosure(BaseAnalysis):
    """The model predicts closure days of a business based on a number of predictors,
    including damage state of the building, content, and machinery of the business, as well as disruptions
    in the utilities. This model is developed using a stepwise modeling approach based on Bayesian linear
    regression which was proposed by Aghababaei et al. (2020).

    Args:
        incore_client (IncoreClient): Service authentication.

    """

    def __init__(self, incore_client):

        super(BusinessClosure, self).__init__(incore_client)

    def run(self):
        """Executes business closure model analysis."""
        # Get predictors dataset and create Pandas DataFrame
        pred_set = self.get_input_dataset("predictors").get_dataframe_from_csv(low_memory=False)

        closure_days = self.get_closure_days(pred_set)
        print("\nBusiness closure days:", closure_days)

        return True

    def get_closure_days(self, predictors):
        """Utilizes concurrent.future module.

        Args:
            predictors (pd.DataFrame): Predictors include damage state of building, machinery, and content
                                       also, days of loss of water, electricity, gas, internet, and sewer.

        Returns:
            float: Business closure days

        """
        db = predictors['deltaB']
        dc = predictors['deltaC']
        dm = predictors['deltaM']
        le = predictors['electricityLossDays']
        lw = predictors['waterLossDays']
        lg = predictors['gasLossDays']
        ls = predictors['sewerLossDays']
        li = predictors['internetLossDays']
        n_businesses = len(db)

        # model has two model parameters called theta1 and theta2
        # which have normal distribution
        theta1 = np.random.normal(loc=-2.0536, scale=0.03 * 2.0536, size=n_businesses)
        theta2 = np.random.normal(loc=0.0529, scale=0.049 * 0.0529, size=n_businesses)

        # Sigma is a random number and is stdv of
        # error term in Bayesian regression
        sigma = np.random.normal(loc=0.2339, scale=0.057 * 0.2339, size=n_businesses)

        # using the generated sigma, a random realization of epsilon
        # which is the standard normal error can be generated
        epsilon = np.random.normal(loc=0.0, scale=sigma, size=n_businesses)

        # now, using the randomly generated parameters and imported
        # predictors, closure days can be calculated
        transformed_value = theta1 * (1 - 0.263 * np.log(le + lw + lg + ls + li + 1))
        +theta2 * (db + dc + dm) - 0.47 * np.log(le + lw + lg + ls + li + 1) + epsilon

        # finally, the predicted closure days can be calculated as follows
        closure_days = np.exp(-np.exp(-transformed_value)) * 3 * 365

        return float(closure_days)

    def get_spec(self):
        """Get specifications of the building closure analysis.

        Returns:
            obj: A JSON object of specifications of the building closure analysis.

        """
        return {
            'name': 'business-closure-operation',
            'description': 'business closure model analysis',
            'input_parameters': [
                {
                    'id': 'result_name',
                    'required': True,
                    'description': 'result dataset name',
                    'type': str
                },
                {
                    'id': 'seed',
                    'required': False,
                    'description': 'Seed to ensure replication if run as part of a probabilistic analysis.',
                    'type': int
                }
            ],
            'input_datasets': [
                {
                    'id': 'predictors',
                    'required': True,
                    'description': 'Damage and Utility Loss Predictors',
                    'type': ['incore:businessPredictorsVer1'],
                }
            ],
            'output_datasets': [
                {
                    'id': 'result',
                    'parent_type': 'businesses',
                    'description': 'A dataset containing results (format: CSV) with values for the predicted '
                                   'closure operation days of the businesses.',
                    'type': 'incore:businessClosureOperation'
                }
            ]
        }
