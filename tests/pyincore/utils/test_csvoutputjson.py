# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from pyincore.utils.cgeoutputprocess import CGEOutputProcess
from pyincore.utils.huapdoutputprocess import HUADislOutputProcess


def run_convert_json():
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

    huapd_json = HUADislOutputProcess()
    huapd_json.get_pd_income(None, None,
                             "/Users/mo/dev/incore/pyincore/tests/pyincore/analyses/housingunitallocation/IN-CORE_2ev3_HUA_1238.csv",
                             "/Users/mo/dev/incore/pyincore/tests/pyincore/analyses/populationdislocation/joplin-pop-disl-results.csv",
                             "HUA_by_income.json")
    # huapd_json.get_pd_tenure(None)
    # huapd_json.get_pd_race(None)
    # huapd_json.get_pd_total(None)

    return True


if __name__ == '__main__':
    run_convert_json()
