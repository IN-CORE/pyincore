# Copyright (c) 2024 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import pandas as pd


class EquityMetricUtil:
    @staticmethod
    def prepare_svi_as_division_decision(merged_gdf):
        """
        socially vulnerability as division decision variable which is a binary variable associated with each household
        used to group it into two groups
        Args:
            merged_gdf:

        Returns:

        """
        # Add variable to indicate if high socially vulnerability for metric's computation
        median_income = merged_gdf["randincome"].median()

        condition1 = merged_gdf["randincome"] <= median_income
        condition2 = merged_gdf["ownershp"] == 2
        condition3 = merged_gdf["race"] != 1
        condition4 = merged_gdf["hispan"] != 0

        merged_gdf["SVI"] = condition1 & condition2 & condition3 & condition4
        merged_gdf["SVI"] = (merged_gdf["SVI"]).astype(int)

        return merged_gdf

    @staticmethod
    def prepare_return_time_as_scarce_resrouce(return_df):
        return_sequence = return_df.iloc[:, 4:94]
        # add return time to the scarce resource dataset
        time_to_return = EquityMetricUtil.time_to_return(return_sequence)
        return_df["Return Time"] = pd.to_numeric(time_to_return)
        return_df["scarce_resource"] = 91 - return_df["Return Time"]

        return return_df

    @staticmethod
    def time_to_return(return_sequence):
        # now create a for loop to determine the time for each row
        time_to_return = []
        for i in range(0, return_sequence.shape[0]):
            if max(return_sequence.iloc[i]) == 4:
                column_index = (return_sequence == 4).idxmax(axis=1)[i]
            else:
                # assuming for 5 that it is never recovered, so we set it to max time interval of 90
                column_index = 90
            time_to_return.append(column_index)

        return time_to_return
