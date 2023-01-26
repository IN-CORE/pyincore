# Copyright (c) 2021 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


class HHRSOutputPRocess:
    """This class converts results outputs of housing household recovery sequential analysis to certain format."""

    @staticmethod
    def get_hhrs_stage_count(timesteps, hhrs_df):
        """

        Args:
            timesteps: timesteps in the unit of month ["0", "6", "12", "24", "48", etc]
            hhrs_df: pandas dataframe of the output of housingrecoverysequential

        Returns:

        """

        # hhr_result = housing_recovery.get_output_dataset("ds_result")
        # hhrs_df = hhr_result.get_dataframe_from_csv()

        hhrs_stage_count = {}
        for t in timesteps:
            stage = hhrs_df[t]
            hhrs_stage_count[t] = [(stage == 1.0).sum(), (stage == 2.0).sum(), (stage == 3.0).sum(),
                                   (stage == 4.0).sum(), (stage == 5.0).sum()]
        return hhrs_stage_count
