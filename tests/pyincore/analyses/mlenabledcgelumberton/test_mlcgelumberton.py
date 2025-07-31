from pyincore import IncoreClient, globals as pyglobals
from pyincore.analyses.mlenabledcgelumberton import MlEnabledCgeLumberton

client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

mlcgelumberton = MlEnabledCgeLumberton(client)

sector_shocks = "688913ee54892f07695f541c"

mlcgelumberton.load_remote_input_dataset("sector_shocks", sector_shocks)
# optional
mlcgelumberton.set_parameter("result_name", "test_lumberton_mlcge_result")

mlcgelumberton.run_analysis()
