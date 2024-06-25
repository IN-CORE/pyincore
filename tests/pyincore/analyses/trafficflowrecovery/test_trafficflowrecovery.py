from pyincore import IncoreClient
from pyincore.analyses.trafficflowrecovery import TrafficFlowRecovery


def run_with_base_class():
    client = IncoreClient()
    traffic_flow_recovery = TrafficFlowRecovery(client)

    nodes = "603d37ec34f29a7fa4211fc4"
    traffic_flow_recovery.load_remote_input_dataset("nodes", nodes)

    links = "5c5de25ec5c0e488fc035613"
    traffic_flow_recovery.load_remote_input_dataset("links", links)

    bridges = "5a284f2dc7d30d13bc082040"
    traffic_flow_recovery.load_remote_input_dataset('bridges', bridges)

    bridge_damage = "5c5ddff0c5c0e488fc0355df"
    traffic_flow_recovery.load_remote_input_dataset('bridge_damage_value', bridge_damage)

    unrepaired = "5c5de0c5c5c0e488fc0355eb"
    traffic_flow_recovery.load_remote_input_dataset('unrepaired_bridge', unrepaired)

    ADT_data = "5c5dde00c5c0e488fc032d7f"
    traffic_flow_recovery.load_remote_input_dataset('ADT', ADT_data)

    traffic_flow_recovery.set_parameter("num_cpu", 4)
    traffic_flow_recovery.set_parameter("pm", 1)
    traffic_flow_recovery.set_parameter('ini_num_population', 5)
    traffic_flow_recovery.set_parameter("population_size", 3)
    traffic_flow_recovery.set_parameter("num_generation", 2)
    traffic_flow_recovery.set_parameter("mutation_rate", 0.1)
    traffic_flow_recovery.set_parameter("crossover_rate", 1.0)

    traffic_flow_recovery.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
