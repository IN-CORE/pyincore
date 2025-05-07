from pyincore import IncoreClient, globals as pyglobals
from pyincore.analyses.mlenabledcgegalvestonisland import MlEnabledCgeGalvestonIsland

client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

mlcgegalveston = MlEnabledCgeGalvestonIsland(client)

sector_shocks = "677c0c346a42fa7faea05dac"

mlcgegalveston.load_remote_input_dataset("sector_shocks", sector_shocks)
# optional
mlcgegalveston.set_parameter("result_name", "test_galvestonisland_mlcge_result")

mlcgegalveston.run_analysis()
