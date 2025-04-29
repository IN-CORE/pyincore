from pyincore import IncoreClient, globals as pyglobals
from pyincore.analyses.mlenabledcgeseaside import MlEnabledCgeSeaside

client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

mlcgeseaside = MlEnabledCgeSeaside(client)

sector_shocks = ""

mlcgeseaside.load_remote_input_dataset("sector_shocks", sector_shocks)
# optional
mlcgeseaside.set_parameter("result_name", "seaside")

mlcgeseaside.run_analysis()
