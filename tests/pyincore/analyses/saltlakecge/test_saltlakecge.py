from pyincore import IncoreClient, Dataset
from pyincore.analyses.saltlakecge import SaltLakeCGEModel
import pyincore.globals as pyglobals

# This script runs SaltLakeCGEModel analysis with input files from
# IN-CORE development services.


def run_base_analysis():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)
    saltlake_cge = SaltLakeCGEModel(client)

    saltlake_cge.set_parameter("model_iterations", 1)
    saltlake_cge.load_remote_input_dataset("SAM", "63a353d94b8432383268cd33")
    saltlake_cge.load_remote_input_dataset("BB", "63a354f54b8432383268cd92")
    saltlake_cge.load_remote_input_dataset("MISCH", "63a355a44b8432383268cd9e")
    saltlake_cge.load_remote_input_dataset("EMPLOY", "63a3563b4b8432383268cece")
    saltlake_cge.load_remote_input_dataset("JOBCR", "63a356cf4b8432383268ced4")
    saltlake_cge.load_remote_input_dataset("OUTCR", "63a357ec4b8432383268ceda")
    saltlake_cge.load_remote_input_dataset("sector_shocks", "63a358404b8432383268cee0")

    saltlake_cge.run_analysis()


if __name__ == '__main__':
    run_base_analysis()
