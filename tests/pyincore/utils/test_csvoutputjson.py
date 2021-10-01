# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from pyincore.utils.cgeoutputprocess import CGEOutputProcess
from pyincore.utils.huapdoutputprocess import HUADislOutputProcess


def run_convert_cge_json():
    cge_json = CGEOutputProcess()
    cge_json.get_cge_household_count(None,
                                     "/Users/mo/dev/incore/pyincore/tests/pyincore/analyses/joplincge/household-count.csv",
                                     "cge_total_household_count.json")
    cge_json.get_cge_gross_income(None,
                                  "/Users/mo/dev/incore/pyincore/tests/pyincore/analyses/joplincge/gross-income.csv",
                                  "cge_total_household_income.json")
    cge_json.get_cge_employment(None, None,
                                "/Users/mo/dev/incore/pyincore/tests/pyincore/analyses/joplincge/pre-disaster-factor-demand.csv",
                                "/Users/mo/dev/incore/pyincore/tests/pyincore/analyses/joplincge/post-disaster-factor-demand.csv",
                                "cge_employment.json")
    cge_json.get_cge_domestic_supply(None,
                                     "/Users/mo/dev/incore/pyincore/tests/pyincore/analyses/joplincge/domestic-supply.csv",
                                     "cge_domestic_supply.json")
    return True


def run_convert_pd_json():
    pd_json = HUADislOutputProcess(None,
                                   "/Users/mo/dev/GitHub/pyincore/tests/pyincore/analyses/populationdislocation/joplin-pop-disl-results.csv",
                                   )
    pd_json.pd_by_race("PD_by_race.json")
    pd_json.pd_by_income("PD_by_income.json")
    pd_json.pd_by_tenure("PD_by_tenure.json")
    pd_json.pd_by_housing("PD_by_housing.json")
    pd_json.pd_total("PD_by_total.json")
    return True


if __name__ == '__main__':
    # run_convert_cge_json()
    run_convert_pd_json()
