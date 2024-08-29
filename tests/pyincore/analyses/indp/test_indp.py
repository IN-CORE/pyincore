from pyincore import (
    IncoreClient,
    Dataset,
    RestorationService,
    MappingSet,
    FragilityService,
    NetworkDataset,
)
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
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)
    datasvc = DataService(client)

    hazard_type = "earthquake"
    hazard_id = "5ba8f127ec2309043520906c"  # 1000 yr eq
    num_cpu = 8
    sim_number = 2
    sample_range = range(0, sim_number)
    result_name = "seaside_indp"
    seed = 1111

    power_network_dataset = Dataset.from_data_service(
        "669048e0b65495213330a10e", data_service=datasvc
    )
    power_network = NetworkDataset.from_dataset(power_network_dataset)
    water_network_dataset = Dataset.from_data_service(
        "66904a7bb65495213330c8f2", data_service=datasvc
    )
    water_network = NetworkDataset.from_dataset(water_network_dataset)
    water_facilities = water_network.nodes
    epfs = power_network.nodes
    pipeline = water_network.links
    bldg_dataset = Dataset.from_data_service(
        "66904cbeb65495213330c920", data_service=datasvc
    )

    ###################################################
    # water facility damage
    ###################################################
    wterfclty_dmg = WaterFacilityDamage(client)
    fragility_service = FragilityService(client)
    wterfclty_dmg.set_input_dataset("water_facilities", water_facilities)
    mapping_id = "66904d9bed7e39392d75f761"  # 5 DS
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
    wterfclty_mc = MonteCarloFailureProbability(client)
    wterfclty_mc.set_input_dataset("damage", wterfclty_dmg_result)
    wterfclty_mc.set_parameter("num_cpu", num_cpu)
    wterfclty_mc.set_parameter("num_samples", sim_number)
    wterfclty_mc.set_parameter(
        "damage_interval_keys", ["DS_0", "DS_1", "DS_2", "DS_3", "DS_4"]
    )
    wterfclty_mc.set_parameter("failure_state_keys", ["DS_1", "DS_2", "DS_3", "DS_4"])
    wterfclty_mc.set_parameter(
        "result_name", result_name + "_wf"
    )  # name of csv file with results
    wterfclty_mc.run()
    wterfclty_sample_failure_state = wterfclty_mc.get_output_dataset(
        "sample_failure_state"
    )
    wterfclty_sample_damage_states = wterfclty_mc.get_output_dataset(
        "sample_damage_states"
    )

    ###################################################
    # water facility repair time
    ###################################################
    wterfclty_rest = WaterFacilityRestoration(client)
    restorationsvc = RestorationService(client)
    mapping_set = MappingSet(restorationsvc.get_mapping("61f075ee903e515036cee0a5"))
    wterfclty_rest.set_input_dataset("water_facilities", water_facilities)
    wterfclty_rest.set_input_dataset("dfr3_mapping_set", mapping_set)
    wterfclty_rest.set_input_dataset("damage", wterfclty_dmg_result)
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
    wf_repair_cost = WaterFacilityRepairCost(client)
    wf_repair_cost.set_input_dataset("water_facilities", water_facilities)
    wf_repair_cost.load_remote_input_dataset(
        "replacement_cost", "669140f5b6549521333118a9"
    )
    wf_repair_cost.set_input_dataset(
        "sample_damage_states", wterfclty_sample_damage_states
    )
    wf_repair_cost.load_remote_input_dataset(
        "wf_dmg_ratios", "66914b3cb654952133316832"
    )
    wf_repair_cost.set_parameter("result_name", result_name + "_wf_repair_cost")
    wf_repair_cost.set_parameter("num_cpu", 4)
    wf_repair_cost.run_analysis()
    wf_repair_cost_result = wf_repair_cost.get_output_dataset("result")

    ###################################################
    # epf damage
    ###################################################
    epf_dmg = EpfDamage(client)
    fragility_service = FragilityService(client)
    epf_dmg.set_input_dataset("epfs", epfs)
    mapping_id = "66914c5bed7e39392d75f762"  # 5 DS
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    epf_dmg.set_input_dataset("dfr3_mapping_set", mapping_set)
    epf_dmg.set_parameter("hazard_type", hazard_type)
    epf_dmg.set_parameter("num_cpu", num_cpu)
    epf_dmg.set_parameter("fragility_key", "pga")
    epf_dmg.set_parameter("hazard_id", hazard_id)
    epf_dmg.set_parameter("result_name", result_name + "_epf_dmg")
    epf_dmg.run_analysis()
    epf_dmg_result = epf_dmg.get_output_dataset("result")

    ###################################################
    # epf repair time
    ###################################################
    epf_rest = EpfRestoration(client)
    restorationsvc = RestorationService(client)
    mapping_set = MappingSet(restorationsvc.get_mapping("61f302e6e3a03e465500b3eb"))
    epf_rest.set_input_dataset("epfs", epfs)
    epf_rest.set_input_dataset("dfr3_mapping_set", mapping_set)
    epf_rest.set_input_dataset("damage", epf_dmg_result)
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
    epf_mc = MonteCarloFailureProbability(client)
    epf_mc.set_input_dataset("damage", epf_dmg_result)
    epf_mc.set_parameter("num_cpu", num_cpu)
    epf_mc.set_parameter("num_samples", sim_number)
    epf_mc.set_parameter(
        "damage_interval_keys", ["DS_0", "DS_1", "DS_2", "DS_3", "DS_4"]
    )
    epf_mc.set_parameter("failure_state_keys", ["DS_1", "DS_2", "DS_3", "DS_4"])
    epf_mc.set_parameter(
        "result_name", result_name + "_epf"
    )  # name of csv file with results
    epf_mc.run()
    epf_sample_failure_state = epf_mc.get_output_dataset("sample_failure_state")
    epf_sample_damage_states = epf_mc.get_output_dataset("sample_damage_states")

    ###################################################
    # epf repair cost
    ###################################################
    epf_repair_cost = EpfRepairCost(client)
    epf_repair_cost.set_input_dataset("epfs", epfs)
    epf_repair_cost.load_remote_input_dataset(
        "replacement_cost", "66914cd5b65495213331900d"
    )
    epf_repair_cost.set_input_dataset("sample_damage_states", epf_sample_damage_states)
    epf_repair_cost.load_remote_input_dataset(
        "epf_dmg_ratios", "66914d2ab654952133319012"
    )
    epf_repair_cost.set_parameter("result_name", result_name + "_epf_repair_cost")
    epf_repair_cost.set_parameter("num_cpu", 4)
    epf_repair_cost.run_analysis()
    epf_repair_cost_result = epf_repair_cost.get_output_dataset("result")

    ###################################################
    # pipeline repair rate damage
    ###################################################
    pipeline_dmg = PipelineDamageRepairRate(client)
    fragility_service = FragilityService(client)
    pipeline_dmg.set_input_dataset("pipeline", pipeline)
    mapping_id = "5b47c227337d4a38464efea8"
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    pipeline_dmg.set_input_dataset("dfr3_mapping_set", mapping_set)
    pipeline_dmg.set_parameter("hazard_type", hazard_type)
    pipeline_dmg.set_parameter("fragility_key", "pgv")
    pipeline_dmg.set_parameter("num_cpu", num_cpu)
    pipeline_dmg.set_parameter("hazard_id", hazard_id)
    pipeline_dmg.set_parameter("result_name", result_name + "_pipeline_dmg")
    pipeline_dmg.run_analysis()
    pipeline_dmg_result = pipeline_dmg.get_output_dataset("result")

    ###################################################
    # pipeline functionality
    ###################################################
    pipeline_func = PipelineFunctionality(client)
    pipeline_func.set_input_dataset("pipeline_repair_rate_damage", pipeline_dmg_result)
    pipeline_func.set_parameter("result_name", result_name + "_pipeline")
    pipeline_func.set_parameter("num_samples", sim_number)
    pipeline_func.run_analysis()
    pipeline_sample_failure_state = pipeline_func.get_output_dataset(
        "sample_failure_state"
    )

    ###################################################
    # pipeline repair time
    ###################################################
    pipeline_rest = PipelineRestoration(client)
    restorationsvc = RestorationService(client)
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
    pipeline_repair_cost = PipelineRepairCost(client)
    pipeline_repair_cost.set_input_dataset("pipeline", pipeline)
    pipeline_repair_cost.load_remote_input_dataset(
        "replacement_cost", "66914deeb65495213331b7db"
    )
    pipeline_repair_cost.set_input_dataset("pipeline_dmg", pipeline_dmg_result)
    pipeline_repair_cost.load_remote_input_dataset(
        "pipeline_dmg_ratios", "66914e4ab65495213331b7e0"
    )
    pipeline_repair_cost.set_parameter(
        "result_name", result_name + "_pipeline_repair_cost"
    )
    pipeline_repair_cost.set_parameter("num_cpu", 4)
    pipeline_repair_cost.run_analysis()
    pipeline_repair_cost_result = pipeline_repair_cost.get_output_dataset("result")

    ###################################################
    # building damage
    ###################################################
    bldg_dmg = BuildingDamage(client)
    fragility_service = FragilityService(client)
    bldg_dmg.set_input_dataset("buildings", bldg_dataset)
    mapping_id = "5e99c86d6129af000136defa"  # 4 DS dev
    # mapping_id = "5d2789dbb9219c3c553c7977"  # 4 DS prod
    mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    bldg_dmg.set_input_dataset("dfr3_mapping_set", mapping_set)
    bldg_dmg.set_parameter("hazard_type", hazard_type)
    bldg_dmg.set_parameter("num_cpu", 4)
    bldg_dmg.set_parameter("hazard_id", hazard_id)
    bldg_dmg.set_parameter("result_name", result_name + "_bldg_dmg")
    bldg_dmg.run_analysis()
    building_dmg_result = bldg_dmg.get_output_dataset("ds_result")

    ###################################################
    # housing unit allocation
    ###################################################
    hua = HousingUnitAllocation(client)
    housing_unit_inv_id = "5df7cd3a425e0b00092cffa4"
    address_point_inv_id = "5df7cd88425e0b00092cffc9"
    hua.load_remote_input_dataset("housing_unit_inventory", housing_unit_inv_id)
    hua.load_remote_input_dataset("address_point_inventory", address_point_inv_id)
    hua.set_input_dataset("buildings", bldg_dataset)
    hua.set_parameter("result_name", result_name + "_hua")
    hua.set_parameter("seed", seed)
    hua.set_parameter("iterations", 1)
    hua.run_analysis()
    hua_result = hua.get_output_dataset("result")

    ###################################################
    # population dislocation
    ###################################################
    pop_dis = PopulationDislocation(client)
    pop_dis.set_input_dataset("building_dmg", building_dmg_result)
    pop_dis.set_input_dataset("housing_unit_allocation", hua_result)
    pop_dis.load_remote_input_dataset("block_group_data", "6035432c1e456929c8609402")
    pop_dis.load_remote_input_dataset("value_loss_param", "602d508fb1db9c28aeedb2a5")
    pop_dis.set_parameter("result_name", result_name + "_popdislocation")
    pop_dis.set_parameter("seed", seed)
    pop_dis.run_analysis()
    pop_dislocation_result = pop_dis.get_output_dataset("result")

    ###################################################
    # INDP
    ###################################################
    indp_analysis = INDP(client)
    indp_analysis.set_parameter("network_type", "from_csv")
    indp_analysis.set_parameter("MAGS", [1000])
    indp_analysis.set_parameter("sample_range", sample_range)
    indp_analysis.set_parameter("dislocation_data_type", "incore")
    indp_analysis.set_parameter("return_model", "step_function")
    indp_analysis.set_parameter("testbed_name", "seaside")
    indp_analysis.set_parameter("extra_commodity", {1: ["PW"], 3: []})
    indp_analysis.set_parameter(
        "RC", [{"budget": 240000, "time": 700}, {"budget": 300000, "time": 600}]
    )
    indp_analysis.set_parameter("layers", [1, 3])
    indp_analysis.set_parameter("method", "INDP")
    # indp_analysis.set_parameter("method", "TDINDP")
    indp_analysis.set_parameter("t_steps", 10)
    indp_analysis.set_parameter("time_resource", True)
    # indp_analysis.set_parameter("save_model", False)
    indp_analysis.set_parameter("save_model", True)

    # scip
    # indp_analysis.set_parameter("solver_engine", "scip") # recommended
    # indp_analysis.set_parameter("solver_path", "/usr/local/bin/scip")

    # cbc
    # indp_analysis.set_parameter("solver_engine", "cbc")
    # indp_analysis.set_parameter("solver_path", "/usr/local/bin/cbc")

    # glpk
    # indp_analysis.set_parameter("solver_engine", "glpk")
    # indp_analysis.set_parameter("solver_path", "/usr/local/bin/glpsol")

    # gurobi
    # indp_analysis.set_parameter("solver_engine", "gurobi")

    indp_analysis.set_parameter(
        "solver_time_limit", 3600
    )  # if not set default to never timeout

    indp_analysis.set_input_dataset("wf_restoration_time", wf_restoration_time)
    indp_analysis.set_input_dataset("wf_repair_cost", wf_repair_cost_result)
    indp_analysis.set_input_dataset("epf_restoration_time", epf_restoration_time)
    indp_analysis.set_input_dataset("epf_repair_cost", epf_repair_cost_result)
    indp_analysis.set_input_dataset(
        "pipeline_restoration_time", pipeline_restoration_time
    )
    indp_analysis.set_input_dataset("pipeline_repair_cost", pipeline_repair_cost_result)
    indp_analysis.set_input_dataset("power_network", power_network_dataset)
    indp_analysis.set_input_dataset(
        "water_network", water_network_dataset
    )  # with distribution noes
    powerline_supply_demand_info = Dataset.from_data_service(
        "66914f5cb65495213331b7f0", data_service=datasvc
    )
    indp_analysis.set_input_dataset(
        "powerline_supply_demand_info", powerline_supply_demand_info
    )

    epf_supply_demand_info = Dataset.from_data_service(
        "66914faeb65495213331b7f5", data_service=datasvc
    )
    indp_analysis.set_input_dataset("epf_supply_demand_info", epf_supply_demand_info)

    wf_supply_demand_info = Dataset.from_data_service(
        "66915039b65495213331b7fc", data_service=datasvc
    )
    indp_analysis.set_input_dataset("wf_supply_demand_info", wf_supply_demand_info)

    pipeline_supply_demand_info = Dataset.from_data_service(
        "669150fdb65495213331b807", data_service=datasvc
    )
    indp_analysis.set_input_dataset(
        "pipeline_supply_demand_info", pipeline_supply_demand_info
    )
    indp_analysis.load_remote_input_dataset("interdep", "61c10104837ac508f9a178ef")
    indp_analysis.set_input_dataset("wf_failure_state", wterfclty_sample_failure_state)
    indp_analysis.set_input_dataset("wf_damage_state", wterfclty_sample_damage_states)
    indp_analysis.set_input_dataset(
        "pipeline_failure_state", pipeline_sample_failure_state
    )
    indp_analysis.set_input_dataset("epf_failure_state", epf_sample_failure_state)
    indp_analysis.set_input_dataset("epf_damage_state", epf_sample_damage_states)
    indp_analysis.set_input_dataset("pop_dislocation", pop_dislocation_result)

    # # optional inputs
    # indp_analysis.load_remote_input_dataset("bldgs2elec", "61c10219837ac508f9a17904")
    # indp_analysis.load_remote_input_dataset("bldgs2wter", "c102b0837ac508f9a1790a")
    # dt_params = Dataset.from_file("dt_params.json", data_type="incore:dTParams")
    # indp_analysis.set_input_dataset("dt_params", dt_params)

    # Run Analysis
    indp_analysis.run_analysis()


if __name__ == "__main__":
    run_with_base_class()
