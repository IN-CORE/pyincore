from pyincore import IncoreClient
from pyincore.analyses.transportationrecovery import TransportationRecovery


def run_with_base_class():
    client = IncoreClient()
    transportation_recovery = TransportationRecovery(client)

    nodes = "5c5de1dec5c0e488fc0355f7"
    transportation_recovery.load_remote_input_dataset("nodes", nodes)

    links = "5c5de25ec5c0e488fc035613"
    transportation_recovery.load_remote_input_dataset("links", links)

    bridges = "5a284f2dc7d30d13bc082040"
    transportation_recovery.load_remote_input_dataset('bridges', bridges)

    bridge_damage = "5c5ddff0c5c0e488fc0355df"
    transportation_recovery.load_remote_input_dataset('bridge_damage_value', bridge_damage)

    unrepaired = "5c5de0c5c5c0e488fc0355eb"
    transportation_recovery.load_remote_input_dataset('unrepaired_bridge', unrepaired)

    ADT_data = "5c5dde00c5c0e488fc032d7f"
    transportation_recovery.load_remote_input_dataset('ADT', ADT_data)

    transportation_recovery.set_parameter("num_cpu", 4)
    transportation_recovery.set_parameter("pm", 1)
    transportation_recovery.set_parameter('ini_num_population', 5)
    transportation_recovery.set_parameter("population_size", 3)
    transportation_recovery.set_parameter("num_generation", 2)
    transportation_recovery.set_parameter("mutation_rate", 0.1)
    transportation_recovery.set_parameter("crossover_rate", 1.0)

    transportation_recovery.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
