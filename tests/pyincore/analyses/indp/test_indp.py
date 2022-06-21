from pyincore import IncoreClient, Dataset
from pyincore.analyses.indp import INDP
import pyincore.globals as pyglobals


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
    indp_analysis.set_parameter("RC", [{"budget": 240000, "time": 70}])  # test just one resource

    indp_analysis.set_parameter("layers", [1, 3])
    indp_analysis.set_parameter("method", "INDP")
    # indp_analysis.set_parameter("method", "TDINDP")

    indp_analysis.set_parameter("t_steps", 10)
    indp_analysis.set_parameter("time_resource", True)
    indp_analysis.set_parameter("save_model", True)
    indp_analysis.set_parameter("solver", "glpk")

    # input datasets
    indp_analysis.load_remote_input_dataset("nodes_reptime_func", "61c0f82a837ac508f9a16d79")
    indp_analysis.load_remote_input_dataset("nodes_damge_ratio", "61c0fe11837ac508f9a16d85")
    indp_analysis.load_remote_input_dataset("arcs_reptime_func", "61c0f92d837ac508f9a16d7f")
    indp_analysis.load_remote_input_dataset("arcs_damge_ratio", "61c0fe4b837ac508f9a16d8b")
    indp_analysis.load_remote_input_dataset("dmg_sce_data", "61c104f0837ac508f9a17e5f")
    indp_analysis.load_remote_input_dataset("power_arcs", "61c0ff2f837ac508f9a16d9d")
    indp_analysis.load_remote_input_dataset("power_nodes", "61c0ff9a837ac508f9a16da3")
    indp_analysis.load_remote_input_dataset("water_arcs", "61c1003d837ac508f9a178e0")
    indp_analysis.load_remote_input_dataset("water_nodes", "61c10081837ac508f9a178e9")

    # this can be chained with pipeline damage
    pipeline_dmg = Dataset.from_file("data/pipe_dmg.csv", "ergo:pipelineDamageVer3")
    indp_analysis.set_input_dataset("pipeline_dmg", pipeline_dmg)

    indp_analysis.load_remote_input_dataset("interdep", "61c10104837ac508f9a178ef")
    indp_analysis.load_remote_input_dataset("initial_node", "61c1015e837ac508f9a178f5")
    indp_analysis.load_remote_input_dataset("initial_link", "61c101a6837ac508f9a178fb")

    # # optional inputs
    # indp_analysis.load_remote_input_dataset("bldgs2elec", "61c10219837ac508f9a17904")
    # indp_analysis.load_remote_input_dataset("bldgs2wter", "c102b0837ac508f9a1790a")

    # this can be chained with population dislocation model
    pop_dislocation = Dataset.from_file("data/PopDis_results.csv", "incore:popDislocation")
    indp_analysis.set_input_dataset("pop_dislocation", pop_dislocation)

    # Run Analysis
    indp_analysis.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
