import os

from pyincore import IncoreClient, Dataset, globals as pyglobals
from pyincore.analyses.mmsacge import MMSACGE

client = IncoreClient()

mmsacge = MMSACGE(client)

curr_dir = os.path.dirname(__file__)
capital_shocks = Dataset.from_file(
    os.path.join(
        curr_dir,
        "mmsa_capital_shocks.csv",
    ),
    data_type="incore:capitalShocks",
)


mmsacge.set_input_dataset("sector_shocks", capital_shocks)
mmsacge.set_parameter("domestic_supply_fname", "mmsa_shelby_county_domestic_supply.csv")

mmsacge.run_analysis()