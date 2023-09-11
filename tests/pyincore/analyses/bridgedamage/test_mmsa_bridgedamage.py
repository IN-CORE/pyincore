from pyincore import IncoreClient, FragilityService, MappingSet, Earthquake, HazardService
from pyincore.analyses.bridgedamage import BridgeDamage
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient()

    # New madrid earthquake using Atkinson Boore 1995
    hazard_service = HazardService(client)
    eq = Earthquake.from_hazard_service("5b902cb273c3371e1236b36b", hazard_service=hazard_service)
    # mmsa highway bridges
    highway_bridges_id_list = {
        "Highway_Bridges": "60e86d6b544e944c3ce622d2"
    }

    # mmsa railway bridges
    railway_bridges_id_list = {
        "Railway_Bridges_BNSF": "60e86e6f60b3f41243fb9df3",
        "Railway_Bridges_CN": "60e86e91544e944c3ce62376",
        "Railway_Bridges_CSXT": "60e86eab60b3f41243fb9e44",
        "Railway_Bridges_NS": "60e86ed1544e944c3ce6241a",
        "Railway_Bridges_UP": "60e86ee960b3f41243fb9ee8"
    }

    # Default Bridge Fragility Mapping on incore-service
    highway_bridge_mapping_id_list = {
        "ABP": "60f89fce52e10319df8086c4",
        "ABA": "60f89fd647290977c8994353",
        "EBL": "60f89fd7a0c8a24d7eedf916",
        "EBT": "60f89fd96fb1bc236b68d3f7",
        "Col": "60f89fdc47290977c8994578",
        "FBL": "60f89fdda0c8a24d7eedfa9f",
        "ABT": "60f89fdf6fb1bc236b68d61c",
        "FBT": "60f89fdf52e10319df808b5f"
    }

    railway_bridge_mapping_id_list = {
        "ABT": "60f89fc947290977c8994215",
        "FBL": "60f89fcba0c8a24d7eedf6a0",
        "FBT": "60f89fcd6fb1bc236b68d049",
        "Col": "60f89fd047290977c8994302",
        "EBL": "60f89fd2a0c8a24d7eedf6f1",
        "EBT": "60f89fd36fb1bc236b68d3a6",
        "ABA": "60f89fd452e10319df8088e9",
        "ABP": "60f89fda52e10319df808a72"
    }

    # Use hazard uncertainty for computing damage
    use_hazard_uncertainty = False
    # Use liquefaction (LIQ) column of bridges to modify fragility curve
    use_liquefaction = False

    # Create bridge damage
    bridge_dmg = BridgeDamage(client)

    # Load input datasets
    for bridge_name, highway_bridge_id in highway_bridges_id_list.items():
        bridge_dmg.load_remote_input_dataset("bridges", highway_bridge_id)

        # Load fragility mapping
        fragility_service = FragilityService(client)
        for component_name, highway_bridge_mapping_id in highway_bridge_mapping_id_list.items():
            mapping_set = MappingSet(fragility_service.get_mapping(highway_bridge_mapping_id))
            bridge_dmg.set_input_dataset('dfr3_mapping_set', mapping_set)

            bridge_dmg.set_input_hazard("hazard", eq)

            # Set analysis parameters
            bridge_dmg.set_parameter("result_name", bridge_name + "_" + component_name)
            bridge_dmg.set_parameter("num_cpu", 4)

            # Run bridge damage analysis
            bridge_dmg.run_analysis()

    # Load input datasets
    for bridge_name, railway_bridge_id in railway_bridges_id_list.items():
        bridge_dmg.load_remote_input_dataset("bridges", railway_bridge_id)

        # Load fragility mapping
        fragility_service = FragilityService(client)
        for component_name, railway_bridge_mapping_id in railway_bridge_mapping_id_list.items():
            mapping_set = MappingSet(fragility_service.get_mapping(railway_bridge_mapping_id))
            bridge_dmg.set_input_dataset('dfr3_mapping_set', mapping_set)

            bridge_dmg.set_input_hazard("hazard", eq)

            # Set analysis parameters
            bridge_dmg.set_parameter("result_name", bridge_name + "_" + component_name)
            bridge_dmg.set_parameter("num_cpu", 4)

            # Run bridge damage analysis
            bridge_dmg.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
