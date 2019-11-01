import logging
import warnings
from pyincore import IncoreClient
from pyincore.analyses.waternetworkrecovery import WaterNetworkRecovery

warnings.filterwarnings('ignore')
logger = logging.getLogger()
logger.setLevel(logging.CRITICAL)


def run_with_base_class():
    client = IncoreClient()

    # Water Network Recovery (without additional dislocation)
    # - Note: some times the model does not converge, you have to run this block several times to get it converge.
    # This is a known issue with WNTR and we are working on solving it
    wn_recovery = WaterNetworkRecovery(client)

    wn_inp_file = "5c5cb530c5c0e488fcfbe308"
    wn_recovery.load_remote_input_dataset("wn_inp_file", wn_inp_file)

    demand_initial = "5c5cb424c5c0e488fcfbc24c"
    wn_recovery.load_remote_input_dataset("demand_initial", demand_initial)

    pipe_dmg = "5c5cb705c5c0e488fcfbe314"
    wn_recovery.load_remote_input_dataset("pipe_dmg", pipe_dmg)

    pump_dmg = "5c5cb78ec5c0e488fcfbe320"
    wn_recovery.load_remote_input_dataset("pump_dmg", pump_dmg)

    tank_dmg = "5c5cb7dcc5c0e488fcfbe32c"
    wn_recovery.load_remote_input_dataset("tank_dmg", tank_dmg)

    demand = "5c5cb834c5c0e488fcfbe338"
    wn_recovery.load_remote_input_dataset("demand", demand)

    pipe_zone = "5c5cb918c5c0e488fcfbe350"
    wn_recovery.load_remote_input_dataset("pipe_zone", pipe_zone)

    wn_recovery.set_parameter("n_days", 3)
    wn_recovery.set_parameter("seed", 2)
    wn_recovery.set_parameter("result_name", "3_day_recovery")

    wn_recovery.run_analysis()

    # Water Network Recovery (with additional dislocation)
    wn_recovery = WaterNetworkRecovery(client)

    wn_inp_file = "5c5cb530c5c0e488fcfbe308"
    wn_recovery.load_remote_input_dataset("wn_inp_file", wn_inp_file)

    demand_initial = "5c5cb424c5c0e488fcfbc24c"
    wn_recovery.load_remote_input_dataset("demand_initial", demand_initial)

    pipe_dmg = "5c5cb705c5c0e488fcfbe314"
    wn_recovery.load_remote_input_dataset("pipe_dmg", pipe_dmg)

    pump_dmg = "5c5cb78ec5c0e488fcfbe320"
    wn_recovery.load_remote_input_dataset("pump_dmg", pump_dmg)

    tank_dmg = "5c5cb7dcc5c0e488fcfbe32c"
    wn_recovery.load_remote_input_dataset("tank_dmg", tank_dmg)

    demand = "5c5cb834c5c0e488fcfbe338"
    wn_recovery.load_remote_input_dataset("demand", demand)

    pipe_zone = "5c5cb918c5c0e488fcfbe350"
    wn_recovery.load_remote_input_dataset("pipe_zone", pipe_zone)

    demand_additional = "5c5cb88ec5c0e488fcfbe344"
    wn_recovery.load_remote_input_dataset("demand_additional",
                                          demand_additional)

    wn_recovery.set_parameter("n_days", 5)
    wn_recovery.set_parameter("result_name", "5_day_recovery")
    wn_recovery.set_parameter("seed", 2)
    wn_recovery.set_parameter("intrp_day", 3)

    wn_recovery.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
