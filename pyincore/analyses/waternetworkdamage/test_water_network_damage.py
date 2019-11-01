from pyincore import IncoreClient
from pyincore.analyses.waternetworkdamage import WaterNetworkDamage


def run_with_base_class():
    client = IncoreClient()
    wn_dmg = WaterNetworkDamage(client)
    wn_dmg.load_remote_input_dataset("water_network",
                                     "5cf696b05648c477129bfc21")
    wn_dmg.set_parameter("earthquake_id", '5ba92505ec23090435209071')
    wn_dmg.set_parameter("water_facility_mapping_id",
                         '5b47c3b1337d4a387e85564a')
    wn_dmg.set_parameter("water_pipeline_mapping_id",
                         '5ba55a2aec2309043530887c')
    wn_dmg.set_parameter("num_cpu", 4)

    wn_dmg.run_analysis()


if __name__ == '__main__':
    run_with_base_class()
