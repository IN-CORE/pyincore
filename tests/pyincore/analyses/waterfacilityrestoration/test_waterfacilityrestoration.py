# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


from pyincore import IncoreClient, MappingSet, RestorationCurveSet, RestorationService
from pyincore.analyses.waterfacilityrestoration import WaterFacilityRestoration
import pyincore.globals as pyglobals
from pyincore.models.mapping import Mapping


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)
    wf_rest = WaterFacilityRestoration(client)

    # use local mapping and restoration curves
    # entry_1 = {"Restoration ID Code": RestorationCurveSet.from_json_file("/tests/data/restorationset.json")}
    # # capable of handling multiple rules
    # rules_1 = [["java.lang.String utilfcltyc EQUALS 'PWT2'"]]
    # # rules_1 = [["java.lang.String utilfcltyc EQUALS 'PWT2'", "java.lang.String utilfcltyc EQUALS 'PPP2'"]]
    # # rules_1 = {"AND": ["java.lang.String utilfcltyc EQUALS 'PWT2'", "java.lang.String utilfcltyc EQUALS 'PPP2'"]}
    # # rules_1 = {"AND": ["java.lang.String utilfcltyc EQUALS 'PWT2'", {"OR": ["java.lang.String utilfcltyc EQUALS "
    # #                                                                  "'PPP2'", "java.lang.String utilfcltyc EQUALS "
    # #                                                                  "'PPP1'"]}]}
    # mapping_1 = Mapping(entry_1, rules_1)
    # mapping_set = {
    #     'id': 'restoration mapping id',
    #     'name': 'testing local mapping object creation',
    #     'hazardType': 'earthquake',
    #     'inventoryType': 'water_facility',
    #     'mappings': [
    #         mapping_1,
    #     ],
    #     'mappingType': 'restoration'
    # }
    # local_mapping_set = MappingSet(mapping_set)
    # wf_rest.set_input_dataset('dfr3_mapping_set', local_mapping_set)

    # Load fragility mapping
    restorationsvc = RestorationService(client)
    # mapping_set = MappingSet(restorationsvc.get_mapping("61f075bf903e515036cee0a4"))
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
