from pyincore import IncoreClient, globals as pyglobals
from pyincore.analyses.mlenabledcgemobile import MlEnabledCgeMobile

client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

mlcgemobile = MlEnabledCgeMobile(client)

sector_shocks = "68434532d11a287c7c34a64a"

mlcgemobile.load_remote_input_dataset("sector_shocks", sector_shocks)
# optional
mlcgemobile.set_parameter("result_name", "test_mobile_mlcge_result")

mlcgemobile.run_analysis()
