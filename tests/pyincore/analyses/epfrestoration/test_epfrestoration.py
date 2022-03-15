# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


from pyincore import IncoreClient, MappingSet, RestorationService
from pyincore.analyses.epfrestoration import EpfRestoration, EpfRestorationUtil
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)
    epf_rest = EpfRestoration(client)
    restorationsvc = RestorationService(client)
    mapping_set = MappingSet(restorationsvc.get_mapping("61f302e6e3a03e465500b3eb"))  # new format of mapping
    epf_rest.load_remote_input_dataset('epfs', '6189c103d5b02930aa3efc35')
    epf_rest.set_input_dataset('dfr3_mapping_set', mapping_set)
    epf_rest.set_parameter("result_name", "epf_restoration.csv")
    epf_rest.set_parameter("restoration_key", "Restoration ID Code")
    epf_rest.set_parameter("end_time", 100.0)
    epf_rest.set_parameter("time_interval", 1.0)
    epf_rest.set_parameter("pf_interval", 0.01)

    epf_rest.run_analysis()

    # test utility function
    epf_rest_util = EpfRestorationUtil(epf_rest)
    functionality = epf_rest_util.get_percentage_func(guid="60748fbd-67c3-4f8d-beb9-26685a53d3c5",
                                                      damage_state="DS_0", time=2.0)
    time = epf_rest_util.get_restoration_time(guid="60748fbd-67c3-4f8d-beb9-26685a53d3c5", damage_state="DS_1", pf=0.81)
    print(functionality, time)


if __name__ == '__main__':
    run_with_base_class()
