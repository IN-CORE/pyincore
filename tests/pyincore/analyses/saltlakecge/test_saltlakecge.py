from pyincore import IncoreClient, Dataset
from pyincore.analyses.saltlakecge import SaltLakeCGEModel
import pyincore.globals as pyglobals

# This script runs SaltLakeCGEModel analysis with input files from
# IN-CORE development services.


def run_base_analysis():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)
    saltlake_cge = SaltLakeCGEModel(client)

    # TODO add these files to incore-dev and replace locally read files
    # SAM
    sam_type = "incore:JoplinCGEsam"

    # CAPITAL COMP
    bb_type = "incore:JoplinCGEbb"

    # MISC TABLES
    misch_type = "incore:JoplinCGEmisch"
    employ_type = "incore:JoplinCGEemploy"
    jobcr_type = "incore:JoplinCGEjobcr"
    outcr_type = "incore:JoplinCGEoutcr"
    sector_shocks_type = "incore:capitalShocks"

    # Load local datasets for Salt Lake CGE
    sam = Dataset.from_file("data/Salt_Lake_SAM_2019.csv", sam_type)
    bb = Dataset.from_file("data/Salt_Lake_CAPCOM_2019.csv", bb_type)
    misch = Dataset.from_file("data/Salt_Lake_HH_2019.csv", misch_type)
    employ = Dataset.from_file("data/Salt_Lake_FACTOR_2019.csv", employ_type)
    jobcr = Dataset.from_file("data/Salt_Lake_JOBCORE_2019.csv", jobcr_type)
    outcr = Dataset.from_file("data/Salt_Lake_OUTCR_2019.csv", outcr_type)
    sector_shocks = Dataset.from_file("data/sector_shocks.csv", sector_shocks_type)

    saltlake_cge.set_parameter("model_iterations", 1)

    saltlake_cge.set_input_dataset("SAM", sam)
    saltlake_cge.set_input_dataset("BB", bb)
    saltlake_cge.set_input_dataset("MISCH", misch)
    saltlake_cge.set_input_dataset("EMPLOY", employ)
    saltlake_cge.set_input_dataset("JOBCR", jobcr)
    saltlake_cge.set_input_dataset("OUTCR", outcr)
    saltlake_cge.set_input_dataset("sector_shocks", sector_shocks)
    saltlake_cge.set_parameter("solver_path", "/home/cnavarro/git/Ipopt/src/Apps/AmplSolver/ipopt")
    saltlake_cge.run_analysis()


if __name__ == '__main__':
    run_base_analysis()
