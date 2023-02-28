from pyincore import IncoreClient, Dataset
from pyincore.analyses.galvestoncge import GalvestonCGEModel
import pyincore.globals as pyglobals

# This script runs SaltLakeCGEModel analysis with input files from
# IN-CORE development services.


def run_base_analysis():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)
    galveston_cge = GalvestonCGEModel(client)

    galveston_cge.set_parameter("model_iterations", 1)
    galveston_cge.load_remote_input_dataset("SAM", "63c8398f4b843238326be519")
    galveston_cge.load_remote_input_dataset("BB", "63a354f54b8432383268cd92")
    galveston_cge.load_remote_input_dataset("MISCH", "63c838954b843238326be513")
    galveston_cge.load_remote_input_dataset("EMPLOY", "63c836d94b843238326bd982")
    galveston_cge.load_remote_input_dataset("JOBCR", "63c837f74b843238326be507")
    galveston_cge.load_remote_input_dataset("OUTCR", "63c838414b843238326be50d")
    galveston_cge.load_remote_input_dataset("sector_shocks", "63a358404b8432383268cee0")

    galveston_cge.run_analysis()


if __name__ == '__main__':
    run_base_analysis()
