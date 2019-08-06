from pyincore import InsecureIncoreClient
from pyincore.analyses.joplincgeanalysis import JoplinCGEModel


def run_base_analysis():
    client = InsecureIncoreClient(service_url="http://incore2-services-dev.ncsa.illinois.edu:8888")
    joplin_cge = JoplinCGEModel(client)

    # SAM
    SAM = "5cdc7b585648c4048fb53062"

    # CAPITAL COMP
    BB = "5cdc7d295648c4048fb53089"

    # MISC TABLES
    IOUT = "5cdc7e965648c4048fb530ef"
    MISC = "5cdc7f4f5648c4048fb53150"
    MISCH = "5cdc7fa05648c4048fb53172"
    LANDCAP = "5cdc7f0a5648c4048fb5312e"
    EMPLOY = "5cdc7df65648c4048fb530ab"
    IGTD = "5cdc7e405648c4048fb530cd"
    TAUFF = "5cdc81da5648c4048fb532b7"
    TPC = "5cdc805a5648c4048fb531d8"
    JOBCR = "5cdc7ed25648c4048fb5310c"
    OUTCR = "5cdc7fde5648c4048fb53194"

    joplin_cge.set_parameter("solver_path", "")
    joplin_cge.set_parameter("model_iterations", 1)

    joplin_cge.load_remote_input_dataset("SAM", SAM)
    joplin_cge.load_remote_input_dataset("BB", BB)
    joplin_cge.load_remote_input_dataset("IOUT", IOUT)
    joplin_cge.load_remote_input_dataset("MISC", MISC)
    joplin_cge.load_remote_input_dataset("MISCH", MISCH)
    joplin_cge.load_remote_input_dataset("LANDCAP", LANDCAP)
    joplin_cge.load_remote_input_dataset("EMPLOY", EMPLOY)
    joplin_cge.load_remote_input_dataset("IGTD", IGTD)
    joplin_cge.load_remote_input_dataset("TAUFF", TAUFF)
    joplin_cge.load_remote_input_dataset("TPC", TPC)
    joplin_cge.load_remote_input_dataset("JOBCR", JOBCR)
    joplin_cge.load_remote_input_dataset("OUTCR", OUTCR)

    joplin_cge.run_analysis()


if __name__ == '__main__':
    run_base_analysis()
