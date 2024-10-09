from pyincore import IncoreClient
from pyincore.analyses.meandamage import MeanDamage
import pyincore.globals as pyglobals


def run_with_base_class():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    md = MeanDamage(client)

    md.load_remote_input_dataset("damage", "61044192ca3e973ce13c054a")
    md.load_remote_input_dataset("dmg_ratios", "5a284f2ec7d30d13bc08209a")
    md.set_parameter("result_name", "mean_damage_building")
    md.set_parameter("damage_interval_keys", ["DS_0", "DS_1", "DS_2", "DS_3"])
    md.set_parameter("num_cpu", 1)

    # Run analysis
    md.run_analysis()


if __name__ == "__main__":
    run_with_base_class()
