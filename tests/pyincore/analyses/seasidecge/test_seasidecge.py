from pyincore import IncoreClient
from pyincore.analyses.seasidecge import SeasideCGEModel
import pyincore.globals as pyglobals


def run_base_analysis():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)
    seaside_cge = SeasideCGEModel(client)

    # SAM
    sam = "5f6127105060967d84ab0f99"

    # CAPITAL COMP
    bb = "5f6132ad5060967d84abdfd3"

    # MISC TABLES
    employ = "5f6127e85060967d84ab0feb"
    jobcr = "5f61284d5060967d84ab1014"
    hhtable = "5f6128b85060967d84ab103d"
    sims = "5f6129035060967d84ab1066"
    sector_shocks = "5f6123e35060967d84ab0f70"

    seaside_cge.set_parameter("print_solver_output", False)

    seaside_cge.load_remote_input_dataset("SAM", sam)
    seaside_cge.load_remote_input_dataset("BB", bb)
    seaside_cge.load_remote_input_dataset("EMPLOY", employ)
    seaside_cge.load_remote_input_dataset("JOBCR", jobcr)
    seaside_cge.load_remote_input_dataset("HHTABLE", hhtable)
    seaside_cge.load_remote_input_dataset("SIMS", sims)
    seaside_cge.load_remote_input_dataset("sector_shocks", sector_shocks)

    seaside_cge.run_analysis()


if __name__ == "__main__":
    run_base_analysis()
