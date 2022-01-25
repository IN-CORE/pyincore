# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


from pyincore import IncoreClient, MappingSet, RestorationCurveSet
from pyincore.analyses.waterfacilityrestoration import WaterFacilityRestoration
import pyincore.globals as pyglobals
from pyincore.models.mapping import Mapping


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)
    hazard_type = "earthquake"
    # mapping_id = "5b47c383337d4a387669d592"
    wf_rest = WaterFacilityRestoration(client)

    # Load restoration mapping
    # fragility_service = FragilityService(client)

    entry_1 = {"Restoration ID Code": RestorationCurveSet.from_json_file("/Users/cwang138/Documents/INCORE-2.0/pyincore/tests/data/restorationset.json")}
    rules_1 = [["java.lang.String utilfcltyc EQUALS 'PWT2'"]]
    mapping_1 = Mapping(entry_1, rules_1)

    entry_2 = {"Restoration ID Code": RestorationCurveSet.from_json_file("/Users/cwang138/Documents/INCORE-2.0/pyincore/tests/data/restorationset.json")}
    rules_2 = [["java.lang.String utilfcltyc EQUALS 'PPP2'"]]
    mapping_2 = Mapping(entry_2, rules_2)
    mapping_set = {
        'id': 'restoration mapping id',
        'name': 'testing local mapping object creation',
        'hazardType': 'earthquake',
        'inventoryType': 'water_facility',
        'mappings': [
            mapping_1,
            mapping_2,
        ],
        'mappingType': 'restoration'
    }
    local_mapping_set = MappingSet(mapping_set)
    wf_rest.set_input_dataset('dfr3_mapping_set', local_mapping_set)

    wf_rest.set_parameter("result_name", "wf_restoration.csv")
    wf_rest.set_parameter("hazard_type", "earthquake")
    wf_rest.set_parameter("restoration_key", "Restoration ID Code")
    wf_rest.set_parameter("end_time", 100.0)
    wf_rest.set_parameter("time_interval", 1.0)
    wf_rest.set_parameter("pf_interval", 0.1)

    wf_rest.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
