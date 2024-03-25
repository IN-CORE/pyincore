from pyincore import IncoreClient, FragilityService, MappingSet, Earthquake, HazardService, DataService
from pyincore.analyses.buildingdamage import BuildingDamage
import time


if __name__ == "__main__":
    client = IncoreClient()

    # Initiate fragility service
    fragility_services = FragilityService(client)
    hazard_services = HazardService(client)
    data_services = DataService(client)

    # Analysis setup
    start_time = time.time()
    bldg_dmg = BuildingDamage(client)

    mapping_set = MappingSet(fragility_services.get_mapping("6309005ad76c6d0e1f6be081"))
    bldg_dmg.set_input_dataset('dfr3_mapping_set', mapping_set)

    bldg_dmg.load_remote_input_dataset("buildings", "62fea288f5438e1f8c515ef8")  # Salt Lake County All Building
    bldg_dmg.set_parameter("result_name", "SLC_bldg_dmg_no_retrofit-withLIQ7.1")

    eq = Earthquake.from_hazard_service("640a03ea73a1642180262450", hazard_services)  # Mw 7.1
    # eq = Earthquake.from_hazard_service("64108b6486a52d419dd69a41", hazard_services) #  Mw 7.0
    bldg_dmg.set_input_hazard("hazard", eq)

    bldg_dmg.set_parameter("use_liquefaction", True)
    bldg_dmg.set_parameter("liquefaction_geology_dataset_id", "62fe9ab685ac6b569e372429")
    bldg_dmg.set_parameter("num_cpu", 8)

    # Run building damage without liquefaction
    bldg_dmg.run_analysis()

    end_time = time.time()
    print(f"total runtime: {end_time - start_time}")