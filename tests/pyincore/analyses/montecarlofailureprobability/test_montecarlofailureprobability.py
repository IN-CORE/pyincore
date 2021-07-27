import pyincore.globals as pyglobals
from pyincore.analyses.montecarlofailureprobability import \
    MonteCarloFailureProbability
from pyincore.client import IncoreClient


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)
    mc = MonteCarloFailureProbability(client)

    # # example of using local dataset
    # damage_dataset = Dataset.from_file("memphis_bldg_dmg_result.csv",
    #                                    "ergo:buildingDamageVer4")
    # mc.set_input_dataset("damage", damage_dataset)
    mc.load_remote_input_dataset("damage", "602d96e4b1db9c28aeeebdce")
    mc.set_parameter("result_name", "building_damage")
    mc.set_parameter("num_cpu", 8)
    mc.set_parameter("num_samples", 10)
    mc.set_parameter("damage_interval_keys",
                     ["DS_0", "DS_1", "DS_2", "DS_3"])
    mc.set_parameter("failure_state_keys", ["DS_1", "DS_2", "DS_3"])

    # optional parameter
    mc.set_parameter("seed", 2)

    mc.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
