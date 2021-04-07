from pyincore.client import IncoreClient
from pyincore.analyses.montecarlofailureprobability import \
    MonteCarloFailureProbability
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)
    mc = MonteCarloFailureProbability(client)

    # # example of using local dataset
    # damage_dataset = Dataset.from_file("memphis_bldg_dmg_result.csv",
    #                                    "ergo:buildingDamageVer4")
    # mc.set_input_dataset("damage", damage_dataset)
    mc.load_remote_input_dataset("damage", "5a29782fc7d30d4af537ace5")
    mc.set_parameter("result_name", "building_damage")
    mc.set_parameter("num_cpu", 8)
    mc.set_parameter("num_samples", 10)
    mc.set_parameter("damage_interval_keys",
                     ["insignific", "moderate", "heavy", "complete"])
    mc.set_parameter("failure_state_keys", ["moderate", "heavy", "complete"])

    mc.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
