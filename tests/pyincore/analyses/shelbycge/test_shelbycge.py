from pyincore import IncoreClient
from pyincore.analyses.shelbycge import ShelbyCGEModel
import pyincore.globals as pyglobals


def run_base_analysis():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)
    shelby_cge = ShelbyCGEModel(client)

    # SAM
    sam = "630e5906c8f8b7614f6e5c6d"

    # CAPITAL COMP
    bb = "630e5ac3c8f8b7614f6e5c76"

    # MISC TABLES
    employ = "630e5ba5c8f8b7614f6e5c7e"
    jobcr = "630e5c59c8f8b7614f6e5c86"
    hhtable = "630e5d08c8f8b7614f6e5c8e"
    sims = "630e5e0bc8f8b7614f6e5c96"

    shelby_cge.set_parameter("print_solver_output", False)

    shelby_cge.load_remote_input_dataset("SAM", sam)
    shelby_cge.load_remote_input_dataset("BB", bb)
    shelby_cge.load_remote_input_dataset("EMPLOY", employ)
    shelby_cge.load_remote_input_dataset("JOBCR", jobcr)
    shelby_cge.load_remote_input_dataset("HHTABLE", hhtable)
    shelby_cge.load_remote_input_dataset("SIMS", sims)

    shelby_cge.run_analysis()


if __name__ == '__main__':
    run_base_analysis()
