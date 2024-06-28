# Copyright (c) 2024 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


class EpfRestorationUtil:
    def __init__(
        self,
        inventory_restoration_map,
        pf_results,
        time_results,
        time_interval,
        pf_interval,
        end_time,
    ):
        # merge inventory_restoration_map with pf and timetables
        inventory_restoration_map_df = (
            inventory_restoration_map.get_dataframe_from_csv()
        )
        pf_results_df = pf_results.get_dataframe_from_csv()
        time_results_df = time_results.get_dataframe_from_csv()
        self.pf_results_df = inventory_restoration_map_df.merge(
            pf_results_df, on="restoration_id"
        ).set_index("guid")
        self.time_results_df = inventory_restoration_map_df.merge(
            time_results_df, on="restoration_id"
        ).set_index("guid")

        self.time_interval = time_interval
        self.pf_interval = pf_interval
        self.end_time = end_time

    def get_restoration_time(self, guid, damage_state="DS_0", pf=0.99):
        if pf > 1:
            raise ValueError("Percentage of functionality should not be larger than 1!")

        state = "time_" + damage_state.replace("DS", "PF")
        df = self.pf_results_df.loc[guid].reset_index(drop=True)
        # round up and get the closest
        time = df.loc[
            (df["percentage_of_functionality"] >= pf)
            & (df["percentage_of_functionality"] < pf + self.pf_interval),
            state,
        ].values[0]

        return time

    def get_percentage_func(self, guid, damage_state="DS_0", time=1):
        if time > self.end_time:
            raise ValueError(
                "restore time should not be larger than end time for restoration model!"
            )

        state = damage_state.replace("DS", "PF")
        df = self.time_results_df.loc[guid].reset_index(drop=True)
        # round up and get the closest
        pf = df.loc[
            (df["time"] >= time) & df["time"] < time + self.time_interval, state
        ].values[0]

        return pf
