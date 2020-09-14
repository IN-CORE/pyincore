from pyincore import IncoreClient
from pyincore.analyses.seasidecge import SeasideCGEModel
import pyincore.globals as pyglobals


def run_base_analysis():
    client = IncoreClient()
    seaside_cge = SeasideCGEModel(client)

    # SAM
    sam = "5f17393633b2700c11feab38"

    # CAPITAL COMP
    bb = "5f173a8ec98cf43417c8953b"

    # MISC TABLES
    employ = "5f173c97c98cf43417c8955d"
    jobcr = "5f173d262fab4d660a8e9f9c"
    hhtable = "5f173d6bc98cf43417c89561"
    sims = "5f174211c98cf43417c89565"
    sector_shocks = "5f5fdbc1b7745919a9e2482d"

    seaside_cge.set_parameter("print_solver_output", False)

    seaside_cge.load_remote_input_dataset("SAM", sam)
    seaside_cge.load_remote_input_dataset("BB", bb)
    seaside_cge.load_remote_input_dataset("EMPLOY", employ)
    seaside_cge.load_remote_input_dataset("JOBCR", jobcr)
    seaside_cge.load_remote_input_dataset("HHTABLE", hhtable)
    seaside_cge.load_remote_input_dataset("SIMS", sims)
    seaside_cge.load_remote_input_dataset("sector_shocks", sector_shocks)

    seaside_cge.run_analysis()


if __name__ == '__main__':
    run_base_analysis()
