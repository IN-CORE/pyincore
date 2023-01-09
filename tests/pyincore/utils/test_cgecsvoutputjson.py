# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from pyincore import IncoreClient
from pyincore.analyses.joplincge import JoplinCGEModel
from pyincore.utils.cgeoutputprocess import CGEOutputProcess
import pyincore.globals as pyglobals
import os


# This script runs JoplinCGEModel analysis with input files from
# IN-CORE development services. The output csv files are converted to json
# format suitable for the IN-CORE Playbook tool.

def run_convert_cge_json_chained():
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
    cge_json.get_cge_domestic_supply(domestic_supply_result, ["Goods", "Trade", "Other", "HS1", "HS2", "HS3"], None,
                                     "cge_domestic_supply.json")
    # cge_json.get_cge_household_count(household_count_result, ["HH1", "HH2", "HH3", "HH4", "HH5"], None,
    # "cge_total_household_count.json")
    cge_json.get_cge_gross_income(gross_income_result, ["HH1", "HH2", "HH3", "HH4", "HH5"], None,
                                  "cge_total_household_income.json")
    cge_json.get_cge_employment(pre_demand_result, post_demand_result, ["Goods", "Trade", "Other"], None, None,
                                "cge_employment.json")

    return True


def run_convert_cge_json_path(testpath):
    # test the external file with a path

    cge_json = CGEOutputProcess()
    cge_json.get_cge_household_count(None, ["HH1", "HH2", "HH3", "HH4", "HH5"],
                                     os.path.join(testpath, "household-count.csv"),
                                     "cge_total_household_count.json")
    cge_json.get_cge_gross_income(None, ["HH1", "HH2", "HH3", "HH4", "HH5"],
                                  os.path.join(testpath, "gross-income.csv"),
                                  "cge_total_household_income.json")
    cge_json.get_cge_employment(None, None, ["Goods", "Trade", "Other"],
                                os.path.join(testpath, "pre-disaster-factor-demand.csv"),
                                os.path.join(testpath, "post-disaster-factor-demand.csv"),
                                "cge_employment.json")
    cge_json.get_cge_domestic_supply(None, ["Goods", "Trade", "Other", "HS1", "HS2", "HS3"],
                                     os.path.join(testpath, "domestic-supply.csv"),
                                     "cge_domestic_supply.json")
    return True


if __name__ == '__main__':
    # test chaining with Joplin CGE analysis
    run_convert_cge_json_chained()

    # test the external file with a path
    testpath = ""
    # testpath = "/Users/<user>/<path_to_pyincore>/pyincore/tests/pyincore/utils"
    if testpath:
        run_convert_cge_json_path(testpath)

    print("DONE")
