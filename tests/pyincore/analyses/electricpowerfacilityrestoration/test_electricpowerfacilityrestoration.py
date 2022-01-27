# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


from pyincore import IncoreClient, MappingSet, RestorationCurveSet, RestorationService
from pyincore.analyses.electricpowerfacilityrestoration import ElectricPowerFacilityRestoration
import pyincore.globals as pyglobals
from pyincore.models.mapping import Mapping


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)
    wf_rest = ElectricPowerFacilityRestoration(client)

    # Load restoration mapping
    restorationsvc = RestorationService(client)
    mapping_set = MappingSet(restorationsvc.get_mapping("61f075ee903e515036cee0a5"))  # new format of mapping
    wf_rest.set_input_dataset('dfr3_mapping_set', mapping_set)
    wf_rest.set_parameter("result_name", "wf_restoration.csv")
    wf_rest.set_parameter("restoration_key", "Restoration ID Code")
    wf_rest.set_parameter("end_time", 100.0)
    wf_rest.set_parameter("time_interval", 1.0)
    wf_rest.set_parameter("pf_interval", 0.01)

    wf_rest.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
