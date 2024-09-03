# Copyright (c) 2024 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import pandas as pd


class EquityMetricUtil:
    @staticmethod
    def prepare_svi_as_division_decision(hua_df):
        """
        socially vulnerability as division decision variable which is a binary variable associated with each household
        used to group it into two groups
        Args:
            hua_df:

        Returns:

        """
        # Add variable to indicate if high socially vulnerability for metric's computation
        median_income = hua_df["randincome"].median()

        condition1 = hua_df["randincome"] <= median_income
        condition2 = hua_df["ownershp"] == 2
        condition3 = hua_df["race"] != 1
        condition4 = hua_df["hispan"] != 0

        hua_df["SVI"] = condition1 & condition2 & condition3 & condition4
        hua_df["SVI"] = (hua_df["SVI"]).astype(int)

        return hua_df

    @staticmethod
    def prepare_return_time_as_scarce_resource(return_df):
        return_sequence = return_df.iloc[:, 4:94]
        # add return time to the scarce resource dataset
        time_to_return = EquityMetricUtil._time_to_return(return_sequence)
        return_df["Return Time"] = pd.to_numeric(time_to_return)
        return_df["scarce_resource"] = 91 - return_df["Return Time"]

        return return_df

    @staticmethod
    def _time_to_return(return_sequence):
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
