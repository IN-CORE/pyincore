from pyincore import IncoreClient, globals as pyglobals
from pyincore.analyses.mlenabledcgejoplin import MlEnabledCgeJoplin

client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

mlcgejoplin = MlEnabledCgeJoplin(client)

sector_shocks = "6706b97443810e1298e8fbfc"

mlcgejoplin.load_remote_input_dataset("sector_shocks", sector_shocks)
# optional
mlcgejoplin.set_parameter("result_name", "test_joplin_mlcge_result")

mlcgejoplin.run_analysis()
