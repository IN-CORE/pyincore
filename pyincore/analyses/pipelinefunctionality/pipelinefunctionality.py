# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


"""Buried Pipeline Damage Analysis with Repair Rate Calculation

"""

import numpy as np
import pandas as pd
from scipy.stats import poisson, bernoulli

from pyincore import BaseAnalysis


class PipelineFunctionality(BaseAnalysis):
    """Computes pipeline functionality.

    Args:
        incore_client: Service client with authentication info

    """

    def __init__(self, incore_client):
        super(PipelineFunctionality, self).__init__(incore_client)

    def run(self):
        """Execute pipeline functionality analysis """
        # pipeline damage
        pipeline_dmg_df = self.get_input_dataset("pipeline_repair_rate_damage").get_dataframe_from_csv()

        num_samples = self.get_parameter("num_samples")

        (fs_results, fp_results) = self.pipeline_functionality(pipeline_dmg_df, edges_gdf, num_samples)
        self.set_result_csv_data("sample_failure_state",
                                 fs_results, name=self.get_parameter("result_name") + "_failure_state",
                                 source="dataframe")
        self.set_result_csv_data("failure_probability",
                                 fp_results,
                                 name=self.get_parameter("result_name") + "_failure_probability",
                                 source="dataframe")

        return True

    def pipeline_functionality(self, pipeline_dmg_df, num_samples):
        """Run pipeline damage analysis for multiple pipelines.

        Args:
            pipeline_dmg_df (dataframe): dataframe of pipeline damage values and other data/metadata

        Returns:
            fs_results (list): A list of dictionary with id/guid and failure state for N samples
            fp_results (list): A list dictionary with failure probability and other data/metadata.

        """

        # todo there is more efficient pandas manipulation
        sampcols = ['s' + samp for samp in np.arange(num_samples).astype(str)]

        pipeline_dmg_df['pgv_pf'] = 1 - poisson.pmf(0, pipeline_dmg_df.loc[:, 'numpgvrpr'].values)
        fs_results = pd.DataFrame(
            bernoulli.rvs(1 - pipeline_dmg_df.loc[:, 'pgv_pf'].values, size=(num_samples, pipeline_dmg_df.shape[0])).T,
            index=pipeline_dmg_df.guid.values, columns=sampcols)

        fs_results =

        return fs_results, fp_results

    def get_spec(self):
        """Get specifications of the pipeline damage analysis.

        Returns:
            obj: A JSON object of specifications of the pipeline damage analysis.

        """
        return {
            'name': 'pipeline-functionlaity',
            'description': 'buried pipeline functionality analysis',
            'input_parameters': [
                {
                    'id': 'result_name',
                    'required': True,
                    'description': 'result dataset name',
                    'type': str
                },
                {
                    'id': 'num_samples',
                    'required': True,
                    'description': 'Number of MC samples',
                    'type': int
                },
            ],
            'input_datasets': [
                {
                    'id': 'pipeline_repair_rate_damage',
                    'required': True,
                    'description': 'Output of pipelinedamagerepairrate analysis',
                    'type': ['ergo:pipelineDamageVer3'],
                },
            ],
            'output_datasets': [
                {
                    'id': 'failure_probability',
                    'description': 'CSV file of failure probability',
                    'type': 'incore:failureProbability'
                },
                {
                    'id': 'sample_failure_state',
                    'description': 'CSV file of failure state for each sample',
                    'type': 'incore:sampleFailureState'
                },
            ]
        }
