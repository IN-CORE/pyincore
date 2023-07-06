import pandas as pd

from pyincore import IncoreClient, Dataset, RestorationService, MappingSet, FragilityService
from pyincore.analyses.indp import INDP
import pyincore.globals as pyglobals
from pyincore.analyses.waterfacilitydamage import WaterFacilityDamage
from pyincore.analyses.epfdamage import EpfDamage
from pyincore.analyses.pipelinedamagerepairrate import pipelinedamagerepairrate, PipelineDamageRepairRate
from pyincore.analyses.montecarlofailureprobability import MonteCarloFailureProbability
from pyincore.analyses.pipelinefunctionality import PipelineFunctionality
from pyincore.analyses.waterfacilityrestoration import WaterFacilityRestoration, WaterFacilityRestorationUtil


def run_with_base_class():
    dev_client = IncoreClient(pyglobals.INCORE_API_DEV_URL)
    prod_client = IncoreClient()
    hazard_type = "earthquake"
    hazard_id = "5dfa3e36b9219c934b64c231"  # 1000 yr eq
    num_cpu = 8
    sim_number = 10
    # sample_range = range(0, sim_number)
    sample_range = range(0, 1)
    result_name = "seaside_indp"

    # ###################################################
    # # water facility damage
    # ###################################################
    # wterfclty_dmg = WaterFacilityDamage(prod_client)
    # fragility_service = FragilityService(prod_client)
    # wterfclty_dmg.load_remote_input_dataset("water_facilities", "60e5e91960b3f41243faa3b2")
    # mapping_id = "5d39e010b9219cc18bd0b0b6"  # 5 DS
    # mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    # wterfclty_dmg.set_input_dataset("dfr3_mapping_set", mapping_set)
    # wterfclty_dmg.set_parameter("hazard_type", hazard_type)
    # wterfclty_dmg.set_parameter("fragility_key", "pga")
    # wterfclty_dmg.set_parameter("num_cpu", 4)
    # wterfclty_dmg.set_parameter("hazard_id", hazard_id)
    # wterfclty_dmg.set_parameter("result_name", result_name)
    # wterfclty_dmg.run_analysis()
    # wterfclty_dmg_result = wterfclty_dmg.get_output_dataset("result")
    #
    # ###################################################
    # # water facility mcs
    # ###################################################
    # wterfclty_mc = MonteCarloFailureProbability(prod_client)
    # wterfclty_mc.set_input_dataset("damage", wterfclty_dmg_result)
    # wterfclty_mc.set_parameter("num_cpu", num_cpu)
    # wterfclty_mc.set_parameter("num_samples", sim_number)
    # wterfclty_mc.set_parameter("damage_interval_keys", ["DS_0", "DS_1", "DS_2", "DS_3", "DS_4"])
    # wterfclty_mc.set_parameter("failure_state_keys", ["DS_1", "DS_2", "DS_3", "DS_4"])
    # wterfclty_mc.set_parameter("result_name", result_name + "_wf")  # name of csv file with results
    # wterfclty_mc.run()
    # wterfclty_sample_failure_state = wterfclty_mc.get_output_dataset("sample_failure_state")
    #
    # ###################################################
    # # epf damage
    # ###################################################
    # epf_dmg = EpfDamage(prod_client)
    # fragility_service = FragilityService(prod_client)
    # epf_dmg.load_remote_input_dataset("epfs", "5d263f08b9219cf93c056c68")
    # mapping_id = "5d489aa1b9219c0689f1988e"  # 5 DS
    # mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    # epf_dmg.set_input_dataset('dfr3_mapping_set', mapping_set)
    # epf_dmg.set_parameter("hazard_type", hazard_type)
    # epf_dmg.set_parameter("num_cpu", num_cpu)
    # epf_dmg.set_parameter('fragility_key', "pga")
    # epf_dmg.set_parameter("hazard_id", hazard_id)
    # epf_dmg.set_parameter("result_name", result_name)
    # epf_dmg.run_analysis()
    # epf_dmg_result = epf_dmg.get_output_dataset("result")
    #
    # ###################################################
    # # epf mcs
    # ###################################################
    # epf_mc = MonteCarloFailureProbability(prod_client)
    # epf_mc.set_input_dataset("damage", epf_dmg_result)
    # epf_mc.set_parameter("num_cpu", num_cpu)
    # epf_mc.set_parameter("num_samples", sim_number)
    # epf_mc.set_parameter("damage_interval_keys", ["DS_0", "DS_1", "DS_2", "DS_3", "DS_4"])
    # epf_mc.set_parameter("failure_state_keys", ["DS_1", "DS_2", "DS_3", "DS_4"])
    # epf_mc.set_parameter("result_name", result_name + "_epf")  # name of csv file with results
    # epf_mc.run()
    # epf_sample_failure_state = epf_mc.get_output_dataset("sample_failure_state")
    #
    # ###################################################
    # # pipeline repair rate damage
    # ###################################################
    # pipeline_dmg = PipelineDamageRepairRate(prod_client)
    # fragility_service = FragilityService(prod_client)
    # pipeline_dmg.load_remote_input_dataset("pipeline", "60e72f9fd3c92a78c89636c7")
    # mapping_id = "5b47c227337d4a38464efea8"
    # mapping_set = MappingSet(fragility_service.get_mapping(mapping_id))
    # pipeline_dmg.set_input_dataset('dfr3_mapping_set', mapping_set)
    # pipeline_dmg.set_parameter("hazard_type", hazard_type)
    # pipeline_dmg.set_parameter("fragility_key", 'pgv')
    # pipeline_dmg.set_parameter("num_cpu", num_cpu)
    # pipeline_dmg.set_parameter("hazard_id", hazard_id)
    # pipeline_dmg.set_parameter("result_name", result_name)
    # pipeline_dmg.run_analysis()
    # pipeline_dmg_result = pipeline_dmg.get_output_dataset("result")
    #
    # ###################################################
    # # pipeline functionality
    # ###################################################
    # pipeline_func = PipelineFunctionality(prod_client)
    # pipeline_func.set_input_dataset("pipeline_repair_rate_damage", pipeline_dmg_result)
    # pipeline_func.set_parameter("result_name", result_name + "_pipeline")
    # pipeline_func.set_parameter("num_samples", sim_number)
    # pipeline_func.run_analysis()
    # pipeline_sample_failure_state = pipeline_func.get_output_dataset("sample_failure_state")

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

    wf_restoration_time = Dataset.from_file("data/seaside_wf_repair_time.csv", "incore:restorationTime")
    indp_analysis.set_input_dataset("wf_restoration_time", wf_restoration_time)

    wf_repair_cost = Dataset.from_file("data/seaside_wf_repair_cost.csv", "incore:repairCost")
    indp_analysis.set_input_dataset("wf_repair_cost", wf_repair_cost)

    epf_restoration_time = Dataset.from_file("data/seaside_epf_repair_time.csv", "incore:restorationTime")
    indp_analysis.set_input_dataset("epf_restoration_time", epf_restoration_time)

    epf_repair_cost = Dataset.from_file("data/seaside_epf_repair_cost.csv", "incore:repairCost")
    indp_analysis.set_input_dataset("epf_repair_cost", epf_repair_cost)

    pipeline_restoration_time = Dataset.from_file("data/seaside_pipeline_repair_time.csv",
                                                  "incore:pipelineRestorationVer1")
    indp_analysis.set_input_dataset("pipeline_restoration_time", pipeline_restoration_time)

    pipeline_repair_cost = Dataset.from_file("data/seaside_pipeline_repair_cost.csv", "incore:pipelineRepairCost")
    indp_analysis.set_input_dataset("pipeline_repair_cost", pipeline_repair_cost)

    indp_analysis.load_remote_input_dataset("power_network", "634d99f51f950c126bca46a9")
    indp_analysis.load_remote_input_dataset("water_network", "645d67675bc8b26ddf913565")
    indp_analysis.load_remote_input_dataset("interdep", "61c10104837ac508f9a178ef")

    wterfclty_sample_failure_state = Dataset.from_file("data/seaside_indp_wf_failure_state.csv", "incore:sampleFailureState")
    indp_analysis.set_input_dataset("wf_failure_state", wterfclty_sample_failure_state)
    pipeline_sample_failure_state = Dataset.from_file("data/seaside_indp_pipeline_failure_state.csv", "incore:sampleFailureState")
    indp_analysis.set_input_dataset("pipeline_failure_state", pipeline_sample_failure_state)
    epf_sample_failure_state = Dataset.from_file("data/seaside_indp_epf_failure_state.csv", "incore:sampleFailureState")
    indp_analysis.set_input_dataset("epf_failure_state", epf_sample_failure_state)

    # indp_analysis.load_remote_input_dataset("initial_node", "61c1015e837ac508f9a178f5")
    # indp_analysis.load_remote_input_dataset("initial_link", "61c101a6837ac508f9a178fb")

    # # optional inputs
    # indp_analysis.load_remote_input_dataset("bldgs2elec", "61c10219837ac508f9a17904")
    # indp_analysis.load_remote_input_dataset("bldgs2wter", "c102b0837ac508f9a1790a")

    # TODO this can be chained with population dislocation model
    pop_dislocation = Dataset.from_file("data/PopDis_results.csv", "incore:popDislocation")
    indp_analysis.set_input_dataset("pop_dislocation", pop_dislocation)

    # Run Analysis
    indp_analysis.run_analysis()


if __name__ == "__main__":
    run_with_base_class()
