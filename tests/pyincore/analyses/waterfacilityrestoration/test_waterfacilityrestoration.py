# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


from pyincore import IncoreClient, MappingSet, RestorationService
from pyincore.analyses.waterfacilityrestoration import WaterFacilityRestoration
from pyincore.analyses.waterfacilityrestoration import WaterFacilityRestorationUtil
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)
    wf_rest = WaterFacilityRestoration(client)

    # Load restoration mapping
    restorationsvc = RestorationService(client)
    mapping_set = MappingSet(restorationsvc.get_mapping("61f075ee903e515036cee0a5"))  # new format of mapping
    wf_rest.load_remote_input_dataset("water_facilities", "5a284f2ac7d30d13bc081e52")  # water facility
    wf_rest.set_input_dataset('dfr3_mapping_set', mapping_set)
    wf_rest.set_parameter("result_name", "wf_restoration")
    wf_rest.set_parameter("restoration_key", "Restoration ID Code")
    wf_rest.set_parameter("end_time", 100.0)
    wf_rest.set_parameter("time_interval", 1.0)
    wf_rest.set_parameter("pf_interval", 0.05)

    wf_rest.run_analysis()

    # test utility function
    wf_util = WaterFacilityRestorationUtil(wf_rest)
    functionality = wf_util.get_percentage_func(guid="e1bce78d-00a1-4605-95f3-3776ff907f73",
                                                damage_state="DS_0", time=2.0)
    time = wf_util.get_restoration_time(guid="e1bce78d-00a1-4605-95f3-3776ff907f73", damage_state="DS_1", pf=0.81)
    print(functionality, time)


if __name__ == '__main__':
    run_with_base_class()
