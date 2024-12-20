# Copyright (c) 2021 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
import json


class HHRSOutputProcess:
    """This class converts results outputs of housing household recovery sequential analysis to certain format."""

    @staticmethod
    def get_hhrs_stage_count(timesteps, hhrs_df, filename_json="hhrs_stage_count.json"):
        """

        Args:
            timesteps: timesteps in the unit of month ["0", "6", "12", "24", "48", etc]
            hhrs_df: pandas dataframe of the output of housingrecoverysequential
            filename_json: the name of the json file to store the output

        Returns:

        """

        hhrs_stage_count = {}
        for t in timesteps:
            stage = hhrs_df[t]
            hhrs_stage_count[t] = [
                int((stage == 1.0).sum()),
                int((stage == 2.0).sum()),
                int((stage == 3.0).sum()),
                int((stage == 4.0).sum()),
                int((stage == 5.0).sum()),
            ]

        if filename_json:
            with open(filename_json, "w") as outfile:
                json.dump(hhrs_stage_count, outfile, indent=2)

        return hhrs_stage_count
