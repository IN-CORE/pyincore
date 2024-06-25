from pyincore import IncoreClient, Dataset
from pyincore.analyses.galvestoncge import GalvestonCGEModel
import pyincore.globals as pyglobals
import time

# This script runs GalvestonCGEModel analysis with input files from
# IN-CORE development services

def run_base_analysis():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)
    galveston_cge = GalvestonCGEModel(client)

    galveston_cge.set_parameter("model_iterations", 1)
    galveston_cge.load_remote_input_dataset("SAM", "6420c377b18d026e7c7dc327")
    galveston_cge.load_remote_input_dataset("BB", "6420c3d2b18d026e7c7dc328")
    galveston_cge.load_remote_input_dataset("MISCH", "6420c434b18d026e7c7dc32e")
    galveston_cge.load_remote_input_dataset("EMPLOY", "6420c474b18d026e7c7dc334")
    galveston_cge.load_remote_input_dataset("JOBCR", "6420c4d9b18d026e7c7dc33a")
    galveston_cge.load_remote_input_dataset("OUTCR", "6420c511b18d026e7c7dc340")
    galveston_cge.load_remote_input_dataset("sector_shocks", "64219be5b18d026e7c7e1534")

    galveston_cge.run_analysis()


if __name__ == '__main__':
    run_base_analysis()
