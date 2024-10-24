# Copyright (c) 2022 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import numpy as np
import pandas as pd
from scipy.stats import poisson, bernoulli

from pyincore import BaseAnalysis


class PipelineFunctionality(BaseAnalysis):
    """
    This analysis computes pipeline functionality using repair rate calculations from pipeline damage analysis
    (earthquake).
    The computation operates by computing Monte Carlo samples derived from Poisson sample deviates from the damage
    analysis as input to Bernoulli experiments, later used to determine average functionality.
    The output of the computation is the average pipeline functionality.

    Contributors
        | Science: Neetesh Sharma, Armin Tabandeh, Paolo Gardoni
        | Implementation: Neetesh Sharma, Chen Wang, and NCSA IN-CORE Dev Team

    Related publications
        Sharma, N., Tabandeh, A., & Gardoni, P. (2019). Regional resilience analysis: A multi-scale approach to model
        the recovery of interdependent infrastructure. In P. Gardoni (Ed.), Handbook of sustainable and resilient
        infrastructure (pp. 521–544). New York, NY: Routledge.
        Sharma, N., Tabandeh, A., & Gardoni, P. (2020). Regional resilience analysis: A multi-scale approach to
        optimize the resilience of interdependent infrastructure. Computer‐Aided Civil and Infrastructure Engineering,
        35(12), 1315-1330.
        Sharma, N., & Gardoni, P. (2022). Mathematical modeling of interdependent infrastructure: An object-oriented
        approach for generalized network-system analysis. Reliability Engineering & System Safety, 217, 108042.

    Args:
    incore_client (IncoreClient): Service authentication.

    """

    def __init__(self, incore_client):
        super(PipelineFunctionality, self).__init__(incore_client)

    def run(self):
        pipeline_dmg_df = self.get_input_dataset(
            "pipeline_repair_rate_damage"
        ).get_dataframe_from_csv()

        num_samples = self.get_parameter("num_samples")

        (fs_results, fp_results) = self.pipeline_functionality(
            pipeline_dmg_df, num_samples
        )
        self.set_result_csv_data(
            "sample_failure_state",
            fs_results,
            name=self.get_parameter("result_name") + "_failure_state",
            source="dataframe",
        )
        self.set_result_csv_data(
            "failure_probability",
            fp_results,
            name=self.get_parameter("result_name") + "_failure_probability",
            source="dataframe",
        )

        return True

    def pipeline_functionality(self, pipeline_dmg_df, num_samples):
        """Run pipeline functionality analysis for multiple pipelines.

        Args:
            pipeline_dmg_df (dataframe): dataframe of pipeline damage values and other data/metadata
            num_samples (int): number of samples
        Returns:
            fs_results (list): A list of dictionary with id/guid and failure state for N samples
            fp_results (list): A list dictionary with failure probability and other data/metadata.

        """

        pipeline_dmg_df["pgv_pf"] = 1 - poisson.pmf(
            0, pipeline_dmg_df.loc[:, "numpgvrpr"].values
        )

        # todo there is more efficient pandas manipulation
        sampcols = ["s" + samp for samp in np.arange(num_samples).astype(str)]

        fs_results = pd.DataFrame(
            bernoulli.rvs(
                1 - pipeline_dmg_df.loc[:, "pgv_pf"].values,
                size=(num_samples, pipeline_dmg_df.shape[0]),
            ).T,
            index=pipeline_dmg_df.guid.values,
            columns=sampcols,
        )
        fp_results = fs_results.copy(deep=True)

        # calculate sample failure
        # concatenate all columns into one failure column
        fs_results["failure"] = fs_results.astype(str).apply(",".join, axis=1)
        fs_results = fs_results.filter(["failure"])
        # set guid column
        fs_results.reset_index(inplace=True)
        fs_results = fs_results.rename(columns={"index": "guid"})

        # calculate failure probability
        # count of 0s divided by sample size
        fp_results["failure_probability"] = (
            num_samples - fp_results.sum(axis=1).astype(int)
        ) / num_samples
        fp_results = fp_results.filter(["failure_probability"])
        # set guid column
        fp_results.reset_index(inplace=True)
        fp_results = fp_results.rename(columns={"index": "guid"})

        return fs_results, fp_results

    def get_spec(self):
        """Get specifications of the pipeline functionality analysis.

        Returns:
            obj: A JSON object of specifications of the pipeline functionality analysis.

        """
        return {
            "name": "pipeline-functionality",
            "description": "buried pipeline functionality analysis",
            "input_parameters": [
                {
                    "id": "result_name",
                    "required": True,
                    "description": "result dataset name",
                    "type": str,
                },
                {
                    "id": "num_samples",
                    "required": True,
                    "description": "Number of MC samples",
                    "type": int,
                },
            ],
            "input_datasets": [
                {
                    "id": "pipeline_repair_rate_damage",
                    "required": True,
                    "description": "Output of pipeline damage repair rate analysis",
                    "type": ["ergo:pipelineDamageVer3"],
                },
            ],
            "output_datasets": [
                {
                    "id": "failure_probability",
                    "description": "CSV file of failure probability",
                    "type": "incore:failureProbability",
                },
                {
                    "id": "sample_failure_state",
                    "description": "CSV file of failure state for each sample",
                    "type": "incore:sampleFailureState",
                },
            ],
        }
