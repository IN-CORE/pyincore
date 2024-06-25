from pyincore import IncoreClient, FragilityService, MappingSet, HazardService, Earthquake
from pyincore.analyses.gasfacilitydamage import GasFacilityDamage
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    # New madrid earthquake using Atkinson Boore 1995
    hazard_svc = HazardService(client)
    eq = Earthquake.from_hazard_service("5b902cb273c3371e1236b36b", hazard_svc)

    # Gas Facility inventory
    gas_facility_id = "5a284f26c7d30d13bc081bb8"

    gas_facility_dmg = GasFacilityDamage(client)
    gas_facility_dmg.load_remote_input_dataset("gas_facilities", gas_facility_id)
    gas_facility_dmg.set_input_hazard("hazard", eq)
    gas_facility_dmg.set_parameter("num_cpu", 4)

    # Uncomment to include liquefaction
    # liq_geology_dataset_id = "5a284f53c7d30d13bc08249c"
    # gas_facility_dmg.set_parameter("use_liquefaction", True)
    # gas_facility_dmg.set_parameter("liquefaction_geology_dataset_id", liq_geology_dataset_id)

    # Gas facility mapping for earthquake with liquefaction fragilities
    mapping_id = "5b47c292337d4a38568f8386"
    fragility_svc = FragilityService(client)
    mapping_set = MappingSet(fragility_svc.get_mapping(mapping_id))

    gas_facility_dmg.set_input_dataset("dfr3_mapping_set", mapping_set)

    result_name = "shelby gas facility"
    gas_facility_dmg.set_parameter("result_name", result_name)

    gas_facility_dmg.run_analysis()


if __name__ == "__main__":
    run_with_base_class()
