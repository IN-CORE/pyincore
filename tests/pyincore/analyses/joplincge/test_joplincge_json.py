from pyincore import IncoreClient
from pyincore.analyses.joplincge import JoplinCGEModel
from pyincore.utils.cgeoutputprocess import CGEOutputProcess
import pyincore.globals as pyglobals


# This script runs JoplinCGEModel analysis with input files from
# IN-CORE development services. The output csv files are converted to json
# format suitable for the IN-CORE Playbook tool.

def run_base_analysis():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)
    joplin_cge = JoplinCGEModel(client)

    # SAM
    sam = "5cdc7b585648c4048fb53062"

    # CAPITAL COMP
    bb = "5cdc7d295648c4048fb53089"

    # MISC TABLES
    iout = "5cdc7e965648c4048fb530ef"
    misc = "5cdc7f4f5648c4048fb53150"
    misch = "5cdc7fa05648c4048fb53172"
    landcap = "5cdc7f0a5648c4048fb5312e"
    employ = "5cdc7df65648c4048fb530ab"
    igtd = "5cdc7e405648c4048fb530cd"
    tauff = "5cdc81da5648c4048fb532b7"
    jobcr = "5cdc7ed25648c4048fb5310c"
    outcr = "5cdc7fde5648c4048fb53194"
    sector_shocks = "5f20653e7887544479c6b94a"

    joplin_cge.set_parameter("model_iterations", 1)

    joplin_cge.load_remote_input_dataset("SAM", sam)
    joplin_cge.load_remote_input_dataset("BB", bb)
    joplin_cge.load_remote_input_dataset("IOUT", iout)
    joplin_cge.load_remote_input_dataset("MISC", misc)
    joplin_cge.load_remote_input_dataset("MISCH", misch)
    joplin_cge.load_remote_input_dataset("LANDCAP", landcap)
    joplin_cge.load_remote_input_dataset("EMPLOY", employ)
    joplin_cge.load_remote_input_dataset("IGTD", igtd)
    joplin_cge.load_remote_input_dataset("TAUFF", tauff)
    joplin_cge.load_remote_input_dataset("JOBCR", jobcr)
    joplin_cge.load_remote_input_dataset("OUTCR", outcr)
    joplin_cge.load_remote_input_dataset("sector_shocks", sector_shocks)

    joplin_cge.run_analysis()

    domestic_supply_result = joplin_cge.get_output_dataset("domestic-supply")
    # household_count_result = joplin_cge.get_output_dataset("household-count")
    gross_income_result = joplin_cge.get_output_dataset("gross-income")
    pre_demand_result = joplin_cge.get_output_dataset("pre-disaster-factor-demand")
    post_demand_result = joplin_cge.get_output_dataset("post-disaster-factor-demand")

    cge_json = CGEOutputProcess()
    cge_json.get_cge_domestic_supply(domestic_supply_result, None, "cge_domestic_supply.json")
    # cge_json.get_cge_household_count(household_count_result, None, "cge_total_household_count.json")
    cge_json.get_cge_gross_income(gross_income_result, None, "cge_total_household_income.json")
    cge_json.get_cge_employment(pre_demand_result, post_demand_result, None, None, "cge_employment.json")

    # Alternatively, you can run the output conversion with files on the file system.
    # my_path = "PATH_TO_PYINCORE/pyincore/tests/pyincore/analyses/joplincge/"
    # cge_json.get_cge_household_count(None, my_path + "household-count.csv", "cge_total_household_count.json")
    # cge_json.get_cge_gross_income(None, my_path + "gross-income.csv", "cge_total_household_income.json")
    # cge_json.get_cge_employment(None, None,
    #                             my_path + "pre-disaster-factor-demand.csv",
    #                             my_path + "post-disaster-factor-demand.csv",
    #                             "cge_employment.json")
    # cge_json.get_cge_domestic_supply(None, my_path + "domestic-supply.csv", "cge_domestic_supply.json")


if __name__ == '__main__':
    run_base_analysis()
