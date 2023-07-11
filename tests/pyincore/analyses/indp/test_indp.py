import pandas as pd

from pyincore import IncoreClient, Dataset, RestorationService, MappingSet, FragilityService, NetworkDataset
from pyincore.analyses.buildingdamage import BuildingDamage
from pyincore.analyses.epfrepaircost import EpfRepairCost
from pyincore.analyses.epfrestoration import EpfRestoration
from pyincore.analyses.housingunitallocation import HousingUnitAllocation
from pyincore.analyses.indp import INDP
import pyincore.globals as pyglobals
from pyincore.analyses.pipelinerepaircost import PipelineRepairCost
from pyincore.analyses.populationdislocation import PopulationDislocation
from pyincore.analyses.waterfacilitydamage import WaterFacilityDamage
from pyincore.analyses.epfdamage import EpfDamage
from pyincore.analyses.pipelinedamagerepairrate import PipelineDamageRepairRate
from pyincore.analyses.montecarlofailureprobability import MonteCarloFailureProbability
from pyincore.analyses.pipelinefunctionality import PipelineFunctionality
from pyincore.analyses.pipelinerestoration import PipelineRestoration
from pyincore.analyses.waterfacilityrepaircost import WaterFacilityRepairCost
from pyincore.analyses.waterfacilityrestoration import WaterFacilityRestoration
from pyincore.dataservice import DataService


def run_with_base_class():
    dev_client = IncoreClient(pyglobals.INCORE_API_DEV_URL)
    prod_client = IncoreClient()
    dev_datasvc = DataService(dev_client)

    hazard_type = "earthquake"
    hazard_id = "5dfa3e36b9219c934b64c231"  # 1000 yr eq
    num_cpu = 8
    sim_number = 10
    sample_range = range(0, sim_number)
    result_name = "seaside_indp"

    bldg_inv_id = "613ba5ef5d3b1d6461e8c415"
    seed = 1111

    power_network_dataset = Dataset.from_data_service("64ac73694e01de3af8fd8f2b", data_service=dev_datasvc)
    power_network = NetworkDataset.from_dataset(power_network_dataset)
    water_network_dataset = Dataset.from_data_service("64ad6abb4e01de3af8fe5201", data_service=dev_datasvc)
    water_network = NetworkDataset.from_dataset(water_network_dataset)
    water_facilities = water_network.nodes
    epfs = power_network.nodes
    pipeline = water_network.links

    ###################################################
    # water facility damage
    ###################################################
    wterfclty_dmg = WaterFacilityDamage(prod_client)
    fragility_service = FragilityService(prod_client)
    wterfclty_dmg.set_input_dataset("water_facilities", water_facilities)
    mapping_id = "5d39e010b9219cc18bd0b0b6"  # 5 DS
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    wterfclty_dmg.set_input_dataset("dfr3_mapping_set", mapping_set)
    wterfclty_dmg.set_parameter("hazard_type", hazard_type)
    wterfclty_dmg.set_parameter("fragility_key", "pga")
    wterfclty_dmg.set_parameter("num_cpu", 4)
    wterfclty_dmg.set_parameter("hazard_id", hazard_id)
    wterfclty_dmg.set_parameter("result_name", result_name + "_wf_damage")
    wterfclty_dmg.run_analysis()
    wterfclty_dmg_result = wterfclty_dmg.get_output_dataset("result")

    ###################################################
    # water facility mcs
    ###################################################
    wterfclty_mc = MonteCarloFailureProbability(prod_client)
    wterfclty_mc.set_input_dataset("damage", wterfclty_dmg_result)
    wterfclty_mc.set_parameter("num_cpu", num_cpu)
    wterfclty_mc.set_parameter("num_samples", sim_number)
    wterfclty_mc.set_parameter("damage_interval_keys", ["DS_0", "DS_1", "DS_2", "DS_3", "DS_4"])
    wterfclty_mc.set_parameter("failure_state_keys", ["DS_1", "DS_2", "DS_3", "DS_4"])
    wterfclty_mc.set_parameter("result_name", result_name + "_wf")  # name of csv file with results
    wterfclty_mc.run()
    wterfclty_sample_failure_state = wterfclty_mc.get_output_dataset("sample_failure_state")
    wterfclty_sample_damage_states = wterfclty_mc.get_output_dataset("sample_damage_states")

    ###################################################
    # water facility repair time
    ###################################################
    wterfclty_rest = WaterFacilityRestoration(prod_client)
    restorationsvc = RestorationService(prod_client)
    mapping_set = MappingSet(restorationsvc.get_mapping("61f075ee903e515036cee0a5"))
    wterfclty_rest.set_input_dataset("water_facilities", water_facilities)
    wterfclty_rest.set_input_dataset("dfr3_mapping_set", mapping_set)
    wterfclty_rest.set_input_dataset('damage', wterfclty_dmg_result)
    wterfclty_rest.set_parameter("result_name", result_name + "_wf_restoration")
    wterfclty_rest.set_parameter("discretized_days", [1, 3, 7, 30, 90])
    wterfclty_rest.set_parameter("restoration_key", "Restoration ID Code")
    wterfclty_rest.set_parameter("end_time", 100.0)
    wterfclty_rest.set_parameter("time_interval", 1.0)
    wterfclty_rest.set_parameter("pf_interval", 0.01)
    wterfclty_rest.run_analysis()
    wf_restoration_time = wterfclty_rest.get_output_dataset("repair_times")

    ###################################################
    # water facility repair cost
    ###################################################
    wf_repair_cost = WaterFacilityRepairCost(prod_client)
    wf_repair_cost.set_input_dataset("water_facilities", water_facilities)
    wf_repair_cost.load_remote_input_dataset("replacement_cost", "64833bcdd3f39a26a0c8b147")
    wf_repair_cost.set_input_dataset("sample_damage_states", wterfclty_sample_damage_states)
    wf_repair_cost.load_remote_input_dataset("wf_dmg_ratios", "647e423d7ae18139d9758607")
    wf_repair_cost.set_parameter("result_name", result_name + "_wf_repair_cost")
    wf_repair_cost.set_parameter("num_cpu", 4)
    wf_repair_cost.run_analysis()
    wf_repair_cost_result = wf_repair_cost.get_output_dataset("result")

    ###################################################
    # epf damage
    ###################################################
    epf_dmg = EpfDamage(prod_client)
    fragility_service = FragilityService(prod_client)
    epf_dmg.set_input_dataset("epfs", epfs)
    mapping_id = "64ac5f3ad2122d1f95f36356"  # 5 DS
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    epf_dmg.set_input_dataset('dfr3_mapping_set', mapping_set)
    epf_dmg.set_parameter("hazard_type", hazard_type)
    epf_dmg.set_parameter("num_cpu", num_cpu)
    epf_dmg.set_parameter('fragility_key', "pga")
    epf_dmg.set_parameter("hazard_id", hazard_id)
    epf_dmg.set_parameter("result_name", result_name + "_epf_dmg")
    epf_dmg.run_analysis()
    epf_dmg_result = epf_dmg.get_output_dataset("result")

    ###################################################
    # epf repair time
    ###################################################
    epf_rest = EpfRestoration(prod_client)
    restorationsvc = RestorationService(prod_client)
    mapping_set = MappingSet(restorationsvc.get_mapping("61f302e6e3a03e465500b3eb"))
    epf_rest.set_input_dataset("epfs", epfs)
    epf_rest.set_input_dataset("dfr3_mapping_set", mapping_set)
    epf_rest.set_input_dataset('damage', epf_dmg_result)
    epf_rest.set_parameter("result_name", result_name + "_epf_restoration")
    epf_rest.set_parameter("discretized_days", [1, 3, 7, 30, 90])
    epf_rest.set_parameter("restoration_key", "Restoration ID Code")
    epf_rest.set_parameter("end_time", 100.0)
    epf_rest.set_parameter("time_interval", 1.0)
    epf_rest.set_parameter("pf_interval", 0.01)
    epf_rest.run_analysis()
    epf_restoration_time = epf_rest.get_output_dataset("repair_times")

    ###################################################
    # epf mcs
    ###################################################
    epf_mc = MonteCarloFailureProbability(prod_client)
    epf_mc.set_input_dataset("damage", epf_dmg_result)
    epf_mc.set_parameter("num_cpu", num_cpu)
    epf_mc.set_parameter("num_samples", sim_number)
    epf_mc.set_parameter("damage_interval_keys", ["DS_0", "DS_1", "DS_2", "DS_3", "DS_4"])
    epf_mc.set_parameter("failure_state_keys", ["DS_1", "DS_2", "DS_3", "DS_4"])
    epf_mc.set_parameter("result_name", result_name + "_epf")  # name of csv file with results
    epf_mc.run()
    epf_sample_failure_state = epf_mc.get_output_dataset("sample_failure_state")
    epf_sample_damage_states = epf_mc.get_output_dataset("sample_damage_states")

    ###################################################
    # epf repair cost
    ###################################################
    epf_repair_cost = EpfRepairCost(prod_client)
    epf_repair_cost.set_input_dataset("epfs", epfs)
    epf_repair_cost.load_remote_input_dataset("replacement_cost", "647dff5b4dd25160127ca192")
    epf_repair_cost.set_input_dataset("sample_damage_states", epf_sample_damage_states)
    epf_repair_cost.load_remote_input_dataset("epf_dmg_ratios", "6483354b41181d20004efbd7")
    epf_repair_cost.set_parameter("result_name", result_name + "_epf_repair_cost")
    epf_repair_cost.set_parameter("num_cpu", 4)
    epf_repair_cost.run_analysis()
    epf_repair_cost_result = epf_repair_cost.get_output_dataset("result")

    ###################################################
    # pipeline repair rate damage
    ###################################################
    pipeline_dmg = PipelineDamageRepairRate(prod_client)
    fragility_service = FragilityService(prod_client)
    pipeline_dmg.set_input_dataset("pipeline", pipeline)
    mapping_id = "5b47c227337d4a38464efea8"
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    pipeline_dmg.set_input_dataset('dfr3_mapping_set', mapping_set)
    pipeline_dmg.set_parameter("hazard_type", hazard_type)
    pipeline_dmg.set_parameter("fragility_key", 'pgv')
    pipeline_dmg.set_parameter("num_cpu", num_cpu)
    pipeline_dmg.set_parameter("hazard_id", hazard_id)
    pipeline_dmg.set_parameter("result_name", result_name + "_pipeline_dmg")
    pipeline_dmg.run_analysis()
    pipeline_dmg_result = pipeline_dmg.get_output_dataset("result")

    ###################################################
    # pipeline functionality
    ###################################################
    pipeline_func = PipelineFunctionality(prod_client)
    pipeline_func.set_input_dataset("pipeline_repair_rate_damage", pipeline_dmg_result)
    pipeline_func.set_parameter("result_name", result_name + "_pipeline")
    pipeline_func.set_parameter("num_samples", sim_number)
    pipeline_func.run_analysis()
    pipeline_sample_failure_state = pipeline_func.get_output_dataset("sample_failure_state")

    ###################################################
    # pipeline repair time
    ###################################################
    pipeline_rest = PipelineRestoration(prod_client)
    restorationsvc = RestorationService(prod_client)
    mapping_set = MappingSet(restorationsvc.get_mapping("61f35f09903e515036cee106"))
    pipeline_rest.set_input_dataset("pipeline", pipeline)
    pipeline_rest.set_input_dataset("pipeline_damage", pipeline_dmg_result)
    pipeline_rest.set_input_dataset("dfr3_mapping_set", mapping_set)
    pipeline_rest.set_parameter("num_available_workers", 4)
    pipeline_rest.set_parameter("result_name", result_name + "_pipeline_restoration")
    pipeline_rest.run_analysis()
    pipeline_restoration_time = pipeline_rest.get_output_dataset("pipeline_restoration")

    ###################################################
    # pipeline repair cost
    ###################################################
    pipeline_repair_cost = PipelineRepairCost(prod_client)
    pipeline_repair_cost.set_input_dataset("pipeline", pipeline)
    pipeline_repair_cost.load_remote_input_dataset("replacement_cost", "6480a2787ae18139d975e919")
    pipeline_repair_cost.set_input_dataset("pipeline_dmg", pipeline_dmg_result)
    pipeline_repair_cost.load_remote_input_dataset("pipeline_dmg_ratios", "6480a2d44dd25160127d2fcc")
    pipeline_repair_cost.set_parameter("result_name", result_name + "_pipeline_repair_cost")
    pipeline_repair_cost.set_parameter("num_cpu", 4)
    pipeline_repair_cost.run_analysis()
    pipeline_repair_cost_result = pipeline_repair_cost.get_output_dataset("result")

    ###################################################
    # building damage
    ###################################################
    bldg_dmg = BuildingDamage(prod_client)
    fragility_service = FragilityService(prod_client)
    bldg_dmg.load_remote_input_dataset("buildings", bldg_inv_id)
    mapping_id = "5d2789dbb9219c3c553c7977"  # 4 DS
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    bldg_dmg.set_input_dataset('dfr3_mapping_set', mapping_set)
    bldg_dmg.set_parameter("hazard_type", hazard_type)
    bldg_dmg.set_parameter("num_cpu", 4)
    bldg_dmg.set_parameter("hazard_id", hazard_id)
    bldg_dmg.set_parameter("result_name", result_name + "_bldg_dmg")
    bldg_dmg.run_analysis()
    building_dmg_result = bldg_dmg.get_output_dataset("ds_result")

    ###################################################
    # housing unit allocation
    ###################################################
    hua = HousingUnitAllocation(prod_client)
    housing_unit_inv_id = "5d543087b9219c0689b98234"
    address_point_inv_id = "5d542fefb9219c0689b981fb"
    hua.load_remote_input_dataset("housing_unit_inventory", housing_unit_inv_id)
    hua.load_remote_input_dataset("address_point_inventory", address_point_inv_id)
    hua.load_remote_input_dataset("buildings", bldg_inv_id)
    hua.set_parameter("result_name", result_name + "_hua")
    hua.set_parameter("seed", seed)
    hua.set_parameter("iterations", 1)
    hua.run_analysis()
    hua_result = hua.get_output_dataset("result")

    ###################################################
    # population dislocation
    ###################################################
    pop_dis = PopulationDislocation(prod_client)
    pop_dis.set_input_dataset("building_dmg", building_dmg_result)
    pop_dis.set_input_dataset("housing_unit_allocation", hua_result)
    pop_dis.load_remote_input_dataset("block_group_data", "5d542bd8b9219c0689b90408")
    pop_dis.load_remote_input_dataset("value_loss_param", "60354810e379f22e16560dbd")
    pop_dis.set_parameter("result_name", result_name + "_popdislocation")
    pop_dis.set_parameter("seed", seed)
    pop_dis.run_analysis()
    pop_dislocation_result = pop_dis.get_output_dataset("result")

    ###################################################
    # INDP
    ###################################################
    indp_analysis = INDP(dev_client)
    indp_analysis.set_parameter("network_type", "from_csv")
    indp_analysis.set_parameter("MAGS", [1000])
    indp_analysis.set_parameter("sample_range", sample_range)  # test just one sample
    indp_analysis.set_parameter("dislocation_data_type", "incore")
    indp_analysis.set_parameter("return_model", "step_function")
    indp_analysis.set_parameter("testbed_name", "seaside")
    indp_analysis.set_parameter("extra_commodity", {1: ["PW"], 3: []})
    # indp_analysis.set_parameter("RC", [{"budget": 240000, "time": 70}, {"budget": 300000, "time": 60}])
    indp_analysis.set_parameter("RC", [{"budget": 2400000, "time": 700}])  # test just one resource increase the
    indp_analysis.set_parameter("layers", [1, 3])
    indp_analysis.set_parameter("method", "INDP")
    # indp_analysis.set_parameter("method", "TDINDP")
    # indp_analysis.set_parameter("t_steps", 10)
    indp_analysis.set_parameter("t_steps", 1)
    indp_analysis.set_parameter("time_resource", True)
    indp_analysis.set_parameter("save_model", False)
    # indp_analysis.set_parameter("solver_engine", "glpk")
    indp_analysis.set_parameter("solver_engine", "ipopt")  # recommended

    indp_analysis.set_input_dataset("wf_restoration_time", wf_restoration_time)
    indp_analysis.set_input_dataset("wf_repair_cost", wf_repair_cost_result)
    indp_analysis.set_input_dataset("epf_restoration_time", epf_restoration_time)
    indp_analysis.set_input_dataset("epf_repair_cost", epf_repair_cost_result)
    indp_analysis.set_input_dataset("pipeline_restoration_time", pipeline_restoration_time)
    indp_analysis.set_input_dataset("pipeline_repair_cost", pipeline_repair_cost_result)
    indp_analysis.set_input_dataset("power_network", power_network_dataset)
    indp_analysis.set_input_dataset("water_network", water_network_dataset)  # with distribution noes
    indp_analysis.load_remote_input_dataset("powerline_supply_demand_info", "64ad8b434e01de3af8fea0ba")
    indp_analysis.load_remote_input_dataset("epf_supply_demand_info", "64ad9ea54e01de3af8fea0f2")
    indp_analysis.load_remote_input_dataset("wf_supply_demand_info", "64ad9e704e01de3af8fea0ec")
    indp_analysis.load_remote_input_dataset("pipeline_supply_demand_info", "64ad9e274e01de3af8fea0e5")
    indp_analysis.load_remote_input_dataset("interdep", "61c10104837ac508f9a178ef")
    indp_analysis.set_input_dataset("wf_failure_state", wterfclty_sample_failure_state)
    indp_analysis.set_input_dataset("wf_damage_state", wterfclty_sample_damage_states)
    indp_analysis.set_input_dataset("pipeline_failure_state", pipeline_sample_failure_state)
    indp_analysis.set_input_dataset("epf_failure_state", epf_sample_failure_state)
    indp_analysis.set_input_dataset("epf_damage_state", epf_sample_damage_states)
    indp_analysis.set_input_dataset("pop_dislocation", pop_dislocation_result)

    # # optional inputs
    # indp_analysis.load_remote_input_dataset("bldgs2elec", "61c10219837ac508f9a17904")
    # indp_analysis.load_remote_input_dataset("bldgs2wter", "c102b0837ac508f9a1790a")

    # Run Analysis
    indp_analysis.run_analysis()


if __name__ == "__main__":
    run_with_base_class()
