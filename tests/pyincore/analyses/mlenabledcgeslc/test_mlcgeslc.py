import os

from pyincore import IncoreClient, globals as pyglobals
from pyincore.analyses.mlenabledcgeslc import MlEnabledCgeSlc

client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

mlcgeslc = MlEnabledCgeSlc(client)

sector_shocks = "65fdeed7e42f3b0da56c4eef"

mlcgeslc.load_remote_input_dataset("sector_shocks", sector_shocks)
# optional
mlcgeslc.set_parameter("result_name", "slc_7_region")

mlcgeslc.run_analysis()