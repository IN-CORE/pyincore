import pandas as pd

from pyincore import IncoreClient, Dataset, RestorationService, MappingSet
from pyincore.analyses.indp import INDP
import pyincore.globals as pyglobals
from pyincore.analyses.waterfacilityrestoration import WaterFacilityRestoration, WaterFacilityRestorationUtil


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    indp_analysis = INDP(client)
    indp_analysis.set_parameter("network_type", "from_csv")
    indp_analysis.set_parameter("MAGS", [1000])
    # indp_analysis.set_parameter("sample_range", range(0, 3))
    indp_analysis.set_parameter("sample_range", range(0, 1))  # test just one sample

    indp_analysis.set_parameter("dislocation_data_type", "incore")
    indp_analysis.set_parameter("return_model", "step_function")
    indp_analysis.set_parameter("testbed_name", "seaside")
    indp_analysis.set_parameter("extra_commodity", {1: ["PW"], 3: []})
    # indp_analysis.set_parameter("RC", [{"budget": 240000, "time": 70}, {"budget": 300000, "time": 60}])
    indp_analysis.set_parameter("RC", [{"budget": 2400000, "time": 700}])  # test just one resource increase the
    # resource will see actions

    indp_analysis.set_parameter("layers", [1, 3])
    indp_analysis.set_parameter("method", "INDP")
    # indp_analysis.set_parameter("method", "TDINDP")

    indp_analysis.set_parameter("t_steps", 10)
    indp_analysis.set_parameter("time_resource", True)
    indp_analysis.set_parameter("save_model", False)
    # indp_analysis.set_parameter("solver_engine", "glpk")
    indp_analysis.set_parameter("solver_engine", "ipopt")  # recommended

    # TODO run water facility damage
    # TODO run montecarlo simulation

    # run water facility restoration analysis
    wf_rest = WaterFacilityRestoration(client)
    restorationsvc = RestorationService(client)
    mapping_set = MappingSet(restorationsvc.get_mapping("61f075ee903e515036cee0a5"))  # new format of mapping
    wf_rest.load_remote_input_dataset("water_facilities", "5a284f2ac7d30d13bc081e52")  # water facility
    wf_rest.set_input_dataset("damage", wf_dmg.get_output_dataset("result"))
    wf_rest.set_input_dataset('dfr3_mapping_set', mapping_set)
    wf_rest.set_parameter("discretized_days", [1, 3, 7, 30, 90])
    wf_rest.set_parameter("result_name", "shelby-water-facility")
    wf_rest.set_parameter("restoration_key", "Restoration ID Code")
    wf_rest.set_parameter("end_time", 100.0)
    wf_rest.set_parameter("time_interval", 1.0)
    wf_rest.set_parameter("pf_interval", 0.05)

    wf_rest.run_analysis()

    # test utility function
    wf_util = WaterFacilityRestorationUtil(wf_rest)
    # TODO iterate through each guid of water facility montecarlo failure state
    wf_restoration_time_df = pd.DataFrame()
    time = wf_util.get_restoration_time(guid="e1bce78d-00a1-4605-95f3-3776ff907f73", damage_state="DS_1", pf=0.81)
    wf_restoration_time_df["guid"] = "guid"
    wf_restoration_time_df["repair_time"] = time

    wf_restoration_time = Dataset.from_dataframe(wf_restoration_time_df,
                                                 "data/percentage_of_functionality_indp-water-facility.csv",
                                                 "incore:waterFacilityRestorationTime")

    indp_analysis.set_input_dataset("wf_restoration_time", wf_restoration_time)

    wf_repair_cost = Dataset.from_file("data/seaside_wf_repair_cost.csv", "incore:repairCost")
    indp_analysis.set_input_dataset("wf_repair_cost", wf_repair_cost)

    # TODO data not correct
    epf_restoration_time = Dataset.from_file("data/percentage_of_functionality_memphis-epf.csv",
                                             "incore:epfRestorationTime")
    indp_analysis.set_input_dataset("epf_restoration_time", epf_restoration_time)

    epf_repair_cost = Dataset.from_file("data/seaside_epf_repair_cost.csv", "incore:repairCost")
    indp_analysis.set_input_dataset("epf_repair_cost", epf_repair_cost)

    # TODO data not correct
    pipeline_restoration_time = Dataset.from_file("data/pipeline_restoration_times.csv",
                                                  "incore:pipelineRestorationVer1")
    indp_analysis.set_input_dataset("pipeline_restoration_time", pipeline_restoration_time)

    pipeline_repair_cost = Dataset.from_file("data/seaside_pipeline_repair_cost.csv", "incore:pipelineRepairCost")
    indp_analysis.set_input_dataset("pipeline_repair_cost", pipeline_repair_cost)

    indp_analysis.load_remote_input_dataset("power_network", "634d99f51f950c126bca46a9")
    indp_analysis.load_remote_input_dataset("water_network", "645d67675bc8b26ddf913565")
    indp_analysis.load_remote_input_dataset("interdep", "61c10104837ac508f9a178ef")
    indp_analysis.load_remote_input_dataset("initial_node", "61c1015e837ac508f9a178f5")
    indp_analysis.load_remote_input_dataset("initial_link", "61c101a6837ac508f9a178fb")

    # # optional inputs
    # indp_analysis.load_remote_input_dataset("bldgs2elec", "61c10219837ac508f9a17904")
    # indp_analysis.load_remote_input_dataset("bldgs2wter", "c102b0837ac508f9a1790a")

    # TODO this can be chained with population dislocation model
    pop_dislocation = Dataset.from_file("data/PopDis_results.csv", "incore:popDislocation")
    indp_analysis.set_input_dataset("pop_dislocation", pop_dislocation)

    # Run Analysis
    indp_analysis.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
