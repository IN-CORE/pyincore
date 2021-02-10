# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


from pyincore import IncoreClient, FragilityService, MappingSet
from pyincore.analyses.waterfacilitydamage import WaterFacilityDamage
from pyincore.globals import INCORE_TEST_URL


def run_with_base_class():
    client = IncoreClient(INCORE_TEST_URL)
    hazard_type = "earthquake"
    hazard_id = "5b902cb273c3371e1236b36b"
    facility_datasetid = "5a284f2ac7d30d13bc081e52"

    mapping_id = "5b47c3b1337d4a387e85564b"  # Hazus Potable Water Facility Fragility Mapping - Only PGA

    liq_geology_dataset_id = "5a284f53c7d30d13bc08249c"

    uncertainty = False
    liquefaction = False
    liq_fragility_key = "pgd"

    wf_dmg = WaterFacilityDamage(client)
    wf_dmg.load_remote_input_dataset("water_facilities", facility_datasetid)

    # Load fragility mapping
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    wf_dmg.set_input_dataset('dfr3_mapping_set', mapping_set)

    result_name = "wf-dmg-results.csv"
    wf_dmg.set_parameter("result_name", result_name)
    wf_dmg.set_parameter("hazard_type", hazard_type)
    wf_dmg.set_parameter("hazard_id", hazard_id)
    wf_dmg.set_parameter("fragility_key", "pga")
    wf_dmg.set_parameter("use_liquefaction", liquefaction)
    wf_dmg.set_parameter("liquefaction_geology_dataset_id", liq_geology_dataset_id)
    wf_dmg.set_parameter("liquefaction_fragility_key", liq_fragility_key)
    wf_dmg.set_parameter("use_hazard_uncertainty", uncertainty)
    wf_dmg.set_parameter("num_cpu", 4)

    wf_dmg.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
