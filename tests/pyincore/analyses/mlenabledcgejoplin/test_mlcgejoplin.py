from pyincore import IncoreClient, globals as pyglobals
from pyincore.analyses.mlenabledcgejoplin import MlEnabledCgeJoplin

client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

mlcgejoplin = MlEnabledCgeJoplin(client)

sector_shocks = "5f20653e7887544479c6b94a"

mlcgejoplin.load_remote_input_dataset("sector_shocks", sector_shocks)
# optional
mlcgejoplin.set_parameter("result_name", "test_joplin_mlcge_result")

mlcgejoplin.run_analysis()