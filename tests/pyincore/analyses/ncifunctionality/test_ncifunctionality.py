from pyincore import IncoreClient, Dataset, FragilityService, MappingSet, RestorationService
from pyincore.analyses.epfdamage.epfdamage import EpfDamage
from pyincore.analyses.epfrestoration import EpfRestoration
from pyincore.analyses.waterfacilitydamage import WaterFacilityDamage
from pyincore.analyses.waterfacilityrestoration import WaterFacilityRestoration
from pyincore.analyses.montecarlofailureprobability import MonteCarloFailureProbability
from pyincore.analyses.ncifunctionality import NciFunctionality
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient()

    num_samples = 10000
    hazard_type = "earthquake"
    hazard_id = "5e3dd04f7fdf7e0008032bfe"

    epf_mapping_id = "5b47be62337d4a37b6197a3a"
    epf_restoration_mapping_id = "61f302e6e3a03e465500b3eb"

    facility_dataset_id = "5a284f2ac7d30d13bc081e52"
    wds_mapping_id = "5b47c383337d4a387669d592"
    wds_fragility_key = "pga"
    liq_geology_dataset_id = "5a284f53c7d30d13bc08249c"
    liquefaction = False
    liq_fragility_key = "pgd"
    uncertainty = False
    wds_restoration_mapping_id = "61f075ee903e515036cee0a5"

    epf_mmsa_network = "62d85b399701070dbf8c65fe"
    wds_mmsa_network = "62d586120b99e237881b0519"

    # EPF substation damage analysis
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(epf_mapping_id))

    print("Electric power facility damage analysis...")
    epn_sub_dmg = EpfDamage(client)
    epn_dataset = Dataset.from_file("shapefiles/Mem_power_link5_node.shp", data_type="incore:epf")
    epn_sub_dmg.set_input_dataset("epfs", epn_dataset)
    epn_sub_dmg.set_input_dataset("dfr3_mapping_set", mapping_set)

    result_name = "3_MMSA_EPN_substations_dmg_result"
    epn_sub_dmg.set_parameter("result_name", result_name)
    epn_sub_dmg.set_parameter("hazard_type", hazard_type)
    epn_sub_dmg.set_parameter("hazard_id", hazard_id)
    epn_sub_dmg.set_parameter("num_cpu", 16)

    epn_sub_dmg.run_analysis()

    substation_dmg_result = epn_sub_dmg.get_output_dataset('result')

    # EPF substation functionality analysis
    print("Electric power facility MonteCarlo failure analysis...")
    mc_sub = MonteCarloFailureProbability(client)

    result_name = "3_MMSA_EPN_substations_mc_failure_probability"
    mc_sub.set_input_dataset("damage", substation_dmg_result)
    mc_sub.set_parameter("num_cpu", 16)
    mc_sub.set_parameter("num_samples", num_samples)
    mc_sub.set_parameter("damage_interval_keys", ["DS_0", "DS_1", "DS_2", "DS_3", "DS_4"])
    mc_sub.set_parameter("failure_state_keys", ["DS_3", "DS_4"])
    mc_sub.set_parameter("result_name", result_name)  # name of csv file with results
    mc_sub.run_analysis()

    epf_subst_failure_results = mc_sub.get_output_dataset('failure_probability')

    # EPF restoration analysis
    print("Electric power facility restoration analysis...")
    epf_rest = EpfRestoration(client)
    restorationsvc = RestorationService(client)
    mapping_set = MappingSet(restorationsvc.get_mapping(epf_restoration_mapping_id))
    epf_rest.set_input_dataset("epfs", epn_dataset)
    epf_rest.set_input_dataset('dfr3_mapping_set', mapping_set)
    epf_rest.set_input_dataset("damage", substation_dmg_result)
    result_name = "4_MMSA_epf_restoration_result"
    epf_rest.set_parameter("result_name", result_name)
    epf_rest.set_parameter("restoration_key", "Restoration ID Code")
    epf_rest.set_parameter("end_time", 90.0)
    epf_rest.set_parameter("time_interval", 1.0)
    epf_rest.run_analysis()

    epf_time_results = epf_rest.get_output_dataset("time_results")
    epf_inventory_rest_map = epf_rest.get_output_dataset("inventory_restoration_map")

    # Water damage analysis
    print("Water facility damage analysis...")
    wf_dmg = WaterFacilityDamage(client)
    wf_dmg.load_remote_input_dataset("water_facilities", facility_dataset_id)
    fragility_service = FragilityService(client)
    mapping_set = MappingSet(fragility_service.get_mapping(wds_mapping_id))
    wf_dmg.set_input_dataset("dfr3_mapping_set", mapping_set)
    result_name = "2_MMSA_facility_dmg_result"
    wf_dmg.set_parameter("result_name", result_name)
    wf_dmg.set_parameter("hazard_type", hazard_type)
    wf_dmg.set_parameter("hazard_id", hazard_id)
    wf_dmg.set_parameter("fragility_key", wds_fragility_key)
    wf_dmg.set_parameter("use_liquefaction", liquefaction)
    wf_dmg.set_parameter("liquefaction_geology_dataset_id", liq_geology_dataset_id)
    wf_dmg.set_parameter("liquefaction_fragility_key", liq_fragility_key)
    wf_dmg.set_parameter("use_hazard_uncertainty", uncertainty)
    wf_dmg.set_parameter("num_cpu", 4)
    wf_dmg.run_analysis()

    wds_dmg_results = wf_dmg.get_output_dataset("result")

    # WDS restoration
    print("Water facility restoration analysis...")
    wf_rest = WaterFacilityRestoration(client)
    mapping_set = MappingSet(restorationsvc.get_mapping(wds_restoration_mapping_id))  # new format of mapping
    wf_rest.load_remote_input_dataset("water_facilities", "5a284f2ac7d30d13bc081e52")  # water facility
    wf_rest.set_input_dataset('dfr3_mapping_set', mapping_set)
    wf_rest.set_input_dataset("damage", wds_dmg_results)
    wf_rest.set_parameter("result_name", "wf_restoration")
    wf_rest.set_parameter("restoration_key", "Restoration ID Code")
    wf_rest.set_parameter("end_time", 90.0)
    wf_rest.set_parameter("time_interval", 1.0)
    wf_rest.run_analysis()

    wds_time_results = wf_rest.get_output_dataset("time_results")
    wds_inventory_rest_map = wf_rest.get_output_dataset("inventory_restoration_map")

    # Network cascading interdependency functionality
    print("EPF/WDS network cascading interdependency analysis...")
    nic_func = NciFunctionality(client)
    nic_func.set_parameter("result_name", "test")
    nic_func.set_parameter("discretized_days", [1, 3, 7, 30, 90])
    nic_func.load_remote_input_dataset("epf_network", epf_mmsa_network)
    nic_func.load_remote_input_dataset("wds_network", wds_mmsa_network)
    nic_func.set_input_dataset("epf_wds_intdp_table", Dataset.from_csv_data([],
                                                                            "epf_wds_interdependencies.csv",
                                                                            'incore:networkInterdependencyTable'))
    nic_func.set_input_dataset("wds_epf_intdp_table", Dataset.from_csv_data([],
                                                                            "wds_epf_interdependencies.csv",
                                                                            'incore:networkInterdependencyTable'))
    nic_func.set_input_dataset("epf_subst_failure_results", epf_subst_failure_results)
    nic_func.set_input_dataset("epf_inventory_rest_map", epf_inventory_rest_map)
    nic_func.set_input_dataset("epf_time_results", epf_time_results)
    nic_func.set_input_dataset("wds_dmg_results", wds_dmg_results)
    nic_func.set_input_dataset("wds_inventory_rest_map", wds_inventory_rest_map)
    nic_func.set_input_dataset("wds_time_results", wds_time_results)
    nic_func.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
