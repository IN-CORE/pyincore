# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


from pyincore import IncoreClient, MappingSet, RestorationService, FragilityService
from pyincore.analyses.epfrestoration import EpfRestoration, EpfRestorationUtil
from pyincore.analyses.epfdamage import EpfDamage

import pyincore.globals as pyglobals


def run_with_base_class():

    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)
    
    # Memphis EPF Damage with Earthquake
    hazard_type_eq = "earthquake"
    hazard_id_eq = "5b902cb273c3371e1236b36b"
    epf_dataset_id = "6189c103d5b02930aa3efc35"
    mapping_id = "61980cf5e32da63f4b9d86f5"  # PGA and PGD

    use_liquefaction = True
    use_hazard_uncertainty = False
    liquefaction_geology_dataset_id = "5a284f53c7d30d13bc08249c"

    # Run epf damage
    epf_dmg_eq_memphis = EpfDamage(client)
    epf_dmg_eq_memphis.load_remote_input_dataset("epfs", epf_dataset_id)

    # Load fragility mapping
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    epf_dmg_eq_memphis.set_input_dataset('dfr3_mapping_set', mapping_set)

    epf_dmg_eq_memphis.set_parameter("result_name", "memphis_eq_epf_dmg_result")
    epf_dmg_eq_memphis.set_parameter("hazard_type", hazard_type_eq)
    epf_dmg_eq_memphis.set_parameter("hazard_id", hazard_id_eq)
    epf_dmg_eq_memphis.set_parameter("use_liquefaction", use_liquefaction)
    epf_dmg_eq_memphis.set_parameter("use_hazard_uncertainty", use_hazard_uncertainty)
    epf_dmg_eq_memphis.set_parameter("liquefaction_geology_dataset_id", liquefaction_geology_dataset_id)
    epf_dmg_eq_memphis.set_parameter("num_cpu", 1)

    # Run Analysis
    epf_dmg_eq_memphis.run_analysis()
    
    epf_rest = EpfRestoration(client)
    restorationsvc = RestorationService(client)
    mapping_set = MappingSet(restorationsvc.get_mapping("61f302e6e3a03e465500b3eb"))  # new format of mapping
    epf_rest.load_remote_input_dataset("epfs", "6189c103d5b02930aa3efc35")
    epf_rest.set_input_dataset("dfr3_mapping_set", mapping_set)
    epf_rest.set_input_dataset('damage', epf_dmg_eq_memphis.get_output_dataset("result"))
    epf_rest.set_parameter("result_name", "memphis-epf")
    epf_rest.set_parameter("discretized_days", [1, 3, 7, 30, 90])
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
