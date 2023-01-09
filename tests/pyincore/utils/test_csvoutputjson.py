# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from pyincore.utils.cgeoutputprocess import CGEOutputProcess
import os

PYINCOREPATH = "path-to-pyincore"
TESTAPATH = "pyincore/tests/pyincore/analyses/"

def run_convert_cge_json():
    # run the JoplinCGE analysis first to get results, csv files
    cge_json = CGEOutputProcess()
    filepath = os.path.join(PYINCOREPATH, TESTAPATH, "joplincge")

    cge_json.get_cge_household_count(None, ["HH1", "HH2", "HH3", "HH4", "HH5"],
                                     os.path.join(filepath, "joplin-pop-disl-results.csv"),
                                     "cge_total_household_count.json")
    cge_json.get_cge_gross_income(None, ["HH1", "HH2", "HH3", "HH4", "HH5"],
                                  os.path.join(filepath, "gross-income.csv"),
                                  "cge_total_household_income.json")
    cge_json.get_cge_employment(None, None, ["Goods", "Trade", "Other"],
                                os.path.join(filepath, "pre-disaster-factor-demand.csv"),
                                os.path.join(filepath, "post-disaster-factor-demand.csv"),
                                "cge_employment.json")
    cge_json.get_cge_domestic_supply(None, ["Goods", "Trade", "Other", "HS1", "HS2", "HS3"],
                                     os.path.join(filepath, "domestic-supply.csv"),
                                     "cge_domestic_supply.json")
    return True


if __name__ == '__main__':
    run_convert_cge_json()
