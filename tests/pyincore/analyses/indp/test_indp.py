from pyincore import IncoreClient, Dataset
from pyincore.analyses.indp import INDP
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    indp_analysis = INDP(client)
    indp_analysis.set_parameter("network_type", "from_csv")
    indp_analysis.set_parameter("MAGS", [1000])
    indp_analysis.set_parameter("sample_range", range(0, 1))
    indp_analysis.set_parameter("dislocation_data_type", "incore")
    indp_analysis.set_parameter("return", "step_function")
    indp_analysis.set_parameter("testbed_name", "seaside")
    indp_analysis.set_parameter("extra_commodity", {1: ["PW"], 3: []})
    indp_analysis.set_parameter("RC", [{"budget": 240000, "time": 70}])
    indp_analysis.set_parameter("layers", [1, 3])
    indp_analysis.set_parameter("method", "INDP")
    # indp_analysis.set_parameter("method", "TDINDP")
    indp_analysis.set_parameter("t_steps", 10)
    indp_analysis.set_parameter("time_resource", True)

    nodes_reptime_func = Dataset.from_file("data/repair_time_curves_nodes.csv", "incore:RepairTimeCurvesNodes")
    indp_analysis.set_input_dataset("nodes_reptime_func", nodes_reptime_func)

    nodes_damge_ratio = Dataset.from_file("data/damage_ratio_nodes.csv", "incore:DamageRatioNodes")
    indp_analysis.set_input_dataset("nodes_damge_ratio", nodes_damge_ratio)

    arcs_reptime_func = Dataset.from_file("data/repair_time_curves_arcs.csv", "incore:RepairTimeCurvesArcs")
    indp_analysis.set_input_dataset("arcs_reptime_func", arcs_reptime_func)

    arcs_damge_ratio = Dataset.from_file("data/damage_ratio_arcs.csv", "incore:DamageRatioArcs")
    indp_analysis.set_input_dataset("arcs_damge_ratio", arcs_damge_ratio)

    dmg_sce_data = Dataset.from_file("data/Initial_node_ds.csv", "incore:DmgSceData")
    indp_analysis.set_input_dataset("dmg_sce_data", dmg_sce_data)

    power_arcs = Dataset.from_file("data/PowerArcs.csv", "incore:PowerArcs")
    indp_analysis.set_input_dataset("power_arcs", power_arcs)

    power_nodes = Dataset.from_file("data/PowerNodes.csv", "incore:PowerNodes")
    indp_analysis.set_input_dataset("power_nodes", power_nodes)

    water_arcs = Dataset.from_file("data/WaterArcs.csv", "incore:WaterArcs")
    indp_analysis.set_input_dataset("water_arcs", water_arcs)

    water_nodes = Dataset.from_file("data/WaterNodes.csv", "incore:WaterNodes")
    indp_analysis.set_input_dataset("water_nodes", water_nodes)

    pipeline_dmg = Dataset.from_file("data/pipe_dmg.csv", "ergo:pipelineDamageVer3")
    indp_analysis.set_input_dataset("pipeline_dmg", pipeline_dmg)

    interdep = Dataset.from_file("data/Interdep.csv", "incore:Interdep")
    indp_analysis.set_input_dataset("interdep", interdep)

    initial_node = Dataset.from_file("data/Initial_node.csv", "incore:InitialNode")
    indp_analysis.set_input_dataset("initial_node", initial_node)

    initial_link = Dataset.from_file("data/Initial_link.csv", "incore:InitialLink")
    indp_analysis.set_input_dataset("initial_link", initial_link)

    pop_dislocation = Dataset.from_file("data/PopDis_results.csv", "incore:popDislocation")
    indp_analysis.set_input_dataset("pop_dislocation", pop_dislocation)

    # Run Analysis
    indp_analysis.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
