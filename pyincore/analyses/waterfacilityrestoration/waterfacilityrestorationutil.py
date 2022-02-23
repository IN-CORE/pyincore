from pyincore.analyses.waterfacilityrestoration import WaterFacilityRestoration


class WaterFacilityRestorationUtil:
    def __init__(self, wfr: WaterFacilityRestoration):
        self.inventory_restoration_map = wfr.get_output_dataset("inventory_restoration_map").get_dataframe_from_csv()
        self.pf_results = wfr.get_output_dataset("pf_results").get_dataframe_from_csv()
        self.time_results = wfr.get_output_dataset("time_results").get_dataframe_from_csv()

    def get_restoration_time(self, guid, damage_state="DS_0", PF="0.99"):
        state = "time_" + damage_state.replace("DS", "PF")
        df = self.inventory_restoration_map.merge(self.time_results, on="restoration_id")
        return df[df['guid'].str.match(guid)].loc[df["percentage_of_functionality"] == PF, state].values[0]

    def get_percentage_func(self, guid, damage_state="DS_0", time=1):
        state = damage_state.replace("DS", "PF")
        df = self.inventory_restoration_map.merge(self.time_results, on="restoration_id")
        return df[df['guid'].str.match(guid)].loc[df["time"] == time, state].values[0]