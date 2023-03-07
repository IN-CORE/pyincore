from pyincore import IncoreClient, Dataset
from pyincore.analyses.saltlakecge import SaltLakeCGEModel
import pyincore.globals as pyglobals

# This script runs SaltLakeCGEModel analysis with input files from
# IN-CORE development services.


def run_base_analysis():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)
    saltlake_cge = SaltLakeCGEModel(client)

    saltlake_cge.set_parameter("model_iterations", 1)

    saltlake_cge.load_remote_input_dataset("SAM", "640758d66121f943887299a2")
    saltlake_cge.load_remote_input_dataset("BB", "640759b56121f94388729d01")
    saltlake_cge.load_remote_input_dataset("MISCH", "64075a5d6121f94388729f8a")
    saltlake_cge.load_remote_input_dataset("EMPLOY", "64075b116121f94388729f91")
    saltlake_cge.load_remote_input_dataset("JOBCR", "64075d1c6121f9438872a648")
    saltlake_cge.load_remote_input_dataset("OUTCR", "64075e306121f9438872a7fb")
    saltlake_cge.load_remote_input_dataset("sector_shocks", "64075ec46121f9438872a802")

    saltlake_cge.run_analysis()


if __name__ == '__main__':
    run_base_analysis()
