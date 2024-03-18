import os

from pyincore import IncoreClient, Dataset, globals as pyglobals
from pyincore.analyses.mlenabledcgeslc import MlEnabledCgeSlc

client = IncoreClient()

mlcgeslc = MlEnabledCgeSlc(client)

curr_dir = os.path.dirname(__file__)
capital_shocks = Dataset.from_file(
    os.path.join(
        curr_dir,
        "slc_capital_shocks.csv",
    ),
    data_type="incore:capitalShocks",
)


mlcgeslc.set_input_dataset("sector_shocks", capital_shocks)
mlcgeslc.set_parameter("domestic_supply_fname", "slc_7_region_domestic_supply.csv")
mlcgeslc.set_parameter("gross_income_fname", "slc_7_region_gross_income.csv")
mlcgeslc.set_parameter("household_count_fname", "slc_7_region_household_count.csv")
mlcgeslc.set_parameter("pre_factor_demand_fname", "slc_7_region_pre_factor_demand.csv")
mlcgeslc.set_parameter("post_factor_demand_fname", "slc_7_region_post_factor_demand.csv")

mlcgeslc.run_analysis()