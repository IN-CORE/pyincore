# Copyright (c) 2024 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import numpy as np
from pyincore import BaseAnalysis
from pyincore.analyses.equitymetric.equitymetricutil import EquityMetricUtil


class EquityMetric(BaseAnalysis):
    """Computes equity metric.
    Args:
        incore_client: Service client with authentication info
    """

    def __init__(self, incore_client):
        super(EquityMetric, self).__init__(incore_client)

    def run(self):
        """Execute equity metric analysis"""

        division_decision_column = self.get_parameter("division_decision_column")
        scarce_resource_df = self.get_input_dataset(
            "scarce_resource"
        ).get_dataframe_from_csv()
        hua_df = self.get_input_dataset(
            "housing_unit_allocation"
        ).get_dataframe_from_csv()
        if division_decision_column == "SVI" and "SVI" not in hua_df.columns:
            hua_df = EquityMetricUtil.prepare_svi_as_division_decision(hua_df)

        merged_df = hua_df.merge(
            scarce_resource_df, how="inner", left_on="guid", right_on="guid"
        )

        equity_metric = self.equity_metric(merged_df, division_decision_column)

        self.set_result_csv_data(
            "equity_metric",
            equity_metric,
            name=self.get_parameter("result_name") + "_equity_metric",
        )

        return True

    def equity_metric(self, merged_df, division_decision_column):
        """
        Compute equity metric
        Args:
            merged_df: Merging housing unit allocation and scarce resource to create dataframes
            division_decision_column: column name of the division decision variable e.g. SVI

        Returns:
            equity_metric: equity metric values that consist of Theil’s T Value, Between Zone Inequality, Within Zone Inequality

        """
        # Calculation of households in each group
        total_1 = merged_df[merged_df[division_decision_column] > 0].shape[
            0
        ]  # socially vulnerable populations
        total_2 = merged_df[merged_df[division_decision_column] < 1].shape[
            0
        ]  # non socially vulnerable populations
        total_households = (
            total_1 + total_2
        )  # for non-vacant households (i.e., non-vacant are not included)

        # Metric Computation
        scarce_resource = merged_df["scarce_resource"]
        yi = scarce_resource / np.sum(scarce_resource)
        Yg_1 = np.sum(yi[merged_df[division_decision_column] > 0])
        Yg_2 = np.sum(yi[merged_df[division_decision_column] < 1])
        TheilT = np.sum(yi * np.log(yi * total_households))
        bzi = np.sum(yi[merged_df[division_decision_column] > 0]) * np.log(
            np.average(yi[merged_df[division_decision_column] > 0]) / np.average(yi)
        ) + np.sum(yi[merged_df[division_decision_column] < 1]) * np.log(
            np.average(yi[merged_df[division_decision_column] < 1]) / np.average(yi)
        )
        wzi = Yg_1 * np.sum(
            yi[merged_df[division_decision_column] > 0]
            / Yg_1
            * np.log((yi[merged_df[division_decision_column] > 0] / Yg_1 * total_1))
        ) + Yg_2 * np.sum(
            yi[merged_df[division_decision_column] < 1]
            / Yg_2
            * np.log((yi[merged_df[division_decision_column] < 1] / Yg_2 * total_2))
        )

        return [{"Theils T": TheilT, "BZI": bzi, "WZI": wzi}]

    def get_spec(self):
        """Get specifications of the Equity Metric analysis.
        Returns:
            obj: A JSON object of specifications of the Equity Metric analysis.
        """
        return {
            "name": "equity-metric",
            "description": "Equity metric analysis",
            "input_parameters": [
                {
                    "id": "result_name",
                    "required": True,
                    "description": "result dataset name",
                    "type": str,
                },
                {
                    "id": "division_decision_column",
                    "required": True,
                    "description": "Division decision. "
                    "Binary variable associated with each household used to group it into two groups "
                    "(e.g. low income vs non low income, minority vs non-minority, "
                    "social vulnerability)",
                    "type": str,
                },
            ],
            "input_datasets": [
                {
                    "id": "housing_unit_allocation",
                    "required": True,
                    "description": "A csv file with the merged dataset of the inputs, aka Probabilistic"
                    "House Unit Allocation",
                    "type": ["incore:housingUnitAllocation"],
                },
                {
                    "id": "scarce_resource",
                    "required": True,
                    "description": "Scarce resource dataset e.g. probability of service, return time, etc",
                    "type": ["incore:scarceResource"],
                },
            ],
            "output_datasets": [
                {
                    "id": "equity_metric",
                    "description": "CSV file of equity metric, including Theil’s T Value, Between Zone Inequality, Within Zone Inequality",
                    "type": "incore:equityMetric",
                }
            ],
        }
