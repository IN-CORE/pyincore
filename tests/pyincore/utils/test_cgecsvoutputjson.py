# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
from build.lib.pyincore.analyses.saltlakecge.saltlakecge import SaltLakeCGEModel
from pyincore import IncoreClient
from pyincore.analyses.joplincge import JoplinCGEModel
from pyincore.utils.cgeoutputprocess import CGEOutputProcess
import pyincore.globals as pyglobals
import os


# This script runs JoplinCGEModel analysis with input files from
# IN-CORE development services. The output csv files are converted to json
# format suitable for the IN-CORE Playbook tool.

def run_convert_SLC_cge_json_path(testpath):
    # test the external file with a path

    cge_json = CGEOutputProcess()
    region = ["R1", "R2"]

    categories = []
    for h in ["HH1", "HH2", "HH3", "HH4"]:
        for r in region:
            categories.append(h + "_" + r)

    cge_json.get_cge_household_count(None,
                                     os.path.join(testpath, "household-count.csv"),
                                     "slc_cge_total_household_count.json", income_categories=categories)
    cge_json.get_cge_gross_income(None,
                                  os.path.join(testpath, "gross-income.csv"),
                                  "slc_cge_total_household_income.json", income_categories=categories)

    categories = []
    for d in ["AG_MI", "UTIL", "CONS", "MANU", "COMMER", "EDU", "HEALTH", "ART_ACC", "RELIG"]:
        for r in region:
            categories.append(d + "_" + r)
    cge_json.get_cge_employment(None, None, os.path.join(testpath, "pre-disaster-factor-demand.csv"),
                                os.path.join(testpath, "post-disaster-factor-demand.csv"),
                                "slc_cge_employment.json", demand_categories=categories)

    categories = []
    for d in ["AG_MI", "UTIL", "CONS", "MANU", "COMMER", "EDU", "HEALTH", "ART_ACC", "RELIG", "HS1", "HS2", "HS3"]:
        for r in region:
            categories.append(d + "_" + r)
    cge_json.get_cge_domestic_supply(None,
                                     os.path.join(testpath, "domestic-supply.csv"), "slc_cge_domestic_supply.json",
                                     supply_categories=categories)
    return True


def run_convert_Joplin_cge_json_path(testpath):
    # test the external file with a path

    cge_json = CGEOutputProcess()
    region = []

    categories = ["HH1", "HH2", "HH3", "HH4", "HH5"]
    cge_json.get_cge_household_count(None,
                                     os.path.join(testpath, "household-count.csv"),
                                     "joplin_cge_total_household_count.json", income_categories=categories)
    cge_json.get_cge_gross_income(None,
                                  os.path.join(testpath, "gross-income.csv"),
                                  "joplin_cge_total_household_income.json", income_categories=categories)

    categories = []
    for d in ["GOODS", "TRADE", "OTHER"]:
        for r in region:
            categories.append(d + "_" + r)
    cge_json.get_cge_employment(None, None, os.path.join(testpath, "pre-disaster-factor-demand.csv"),
                                os.path.join(testpath, "post-disaster-factor-demand.csv"),
                                "joplin_cge_employment.json", demand_categories=categories)

    categories = []
    for d in ["Goods", "Trades", "Others", "HS1", "HS2", "HS3"]:
        for r in region:
            categories.append(d + "_" + r)
    cge_json.get_cge_domestic_supply(None,
                                     os.path.join(testpath, "domestic-supply.csv"), "slc_cge_domestic_supply.json",
                                     supply_categories=categories)
    return True


if __name__ == '__main__':

    # run slc cge
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)
    saltlake_cge = SaltLakeCGEModel(client)

    saltlake_cge.set_parameter("model_iterations", 1)

    saltlake_cge.load_remote_input_dataset("SAM", "640758d66121f943887299a2")
    saltlake_cge.load_remote_input_dataset("BB", "640759b56121f94388729d01")
    saltlake_cge.load_remote_input_dataset("MISCH", "64075a5d6121f94388729f8a")
    saltlake_cge.load_remote_input_dataset("EMPLOY", "64075b116121f94388729f91")
    saltlake_cge.load_remote_input_dataset("JOBCR", "64075d1c6121f9438872a648")
    saltlake_cge.load_remote_input_dataset("OUTCR", "64075e306121f9438872a7fb")
    saltlake_cge.load_remote_input_dataset("sector_shocks", "64075ec46121f9438872a802")

    saltlake_cge.run_analysis()
    run_convert_SLC_cge_json_path(testpath="./")
    print("Salt lake city post processing done.")

    # run joplin cge
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
    run_convert_Joplin_cge_json_path("./")
    print("Joplin post processing done.")
