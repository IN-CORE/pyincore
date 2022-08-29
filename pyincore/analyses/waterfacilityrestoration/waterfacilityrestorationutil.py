from pyincore.analyses.waterfacilityrestoration import WaterFacilityRestoration


class WaterFacilityRestorationUtil:
    def __init__(self, wfr: WaterFacilityRestoration):

        # merge inventory_restoration_map with pf and time tables
        inventory_restoration_map = wfr.get_output_dataset("inventory_restoration_map").get_dataframe_from_csv()
        pf_results = wfr.get_output_dataset("pf_results").get_dataframe_from_csv()
        time_results = wfr.get_output_dataset("time_results").get_dataframe_from_csv()
        self.pf_results = inventory_restoration_map.merge(pf_results, on="restoration_id").set_index('guid')
        self.time_results = inventory_restoration_map.merge(time_results, on="restoration_id").set_index('guid')

        self.time_interval = wfr.get_parameter("time_interval")
        self.pf_interval = wfr.get_parameter("pf_interval")
        self.end_time = wfr.get_parameter("end_time")

    def get_restoration_time(self, guid, damage_state="DS_0", pf=0.99):
        if pf > 1:
            raise ValueError("Percentage of functionality should not be larger than 1!")

        state = "time_" + damage_state.replace("DS", "PF")
        df = self.pf_results.loc[guid].reset_index(drop=True)
        # round up and get the closest
        time = df.loc[(df["percentage_of_functionality"] >= pf) & (df["percentage_of_functionality"] <
                                                                   pf+self.pf_interval), state].values[0]

        return time

    def get_percentage_func(self, guid, damage_state="DS_0", time=1):
        if time > self.end_time:
            raise ValueError("restore time should not be larger than end time for restoration model!")

        state = damage_state.replace("DS", "PF")
        df = self.time_results.loc[guid].reset_index(drop=True)
        # round up and get the closest
        pf = df.loc[(df["time"] >= time) & df['time'] < time+self.time_interval, state].values[0]

        return pf
