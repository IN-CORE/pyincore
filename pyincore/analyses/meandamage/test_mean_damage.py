from pyincore import IncoreClient
from pyincore.analyses.meandamage import MeanDamage


def run_with_base_class():
    client = IncoreClient()

    md = MeanDamage(client)

    md.load_remote_input_dataset("damage", "5a29782fc7d30d4af537ace5")
    md.load_remote_input_dataset("dmg_ratios", "5a284f2ec7d30d13bc08209a")
    md.set_parameter("result_name", "mean_damage")
    md.set_parameter("damage_interval_keys",
                     ["insignific", "moderate", "heavy", "complete"])
    md.set_parameter("num_cpu", 1)

    # Run analysis
    md.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
