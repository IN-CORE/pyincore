from pyincore import IncoreClient
from pyincore.analyses.buildingeconloss.buildingeconloss import BuildingEconLoss
from pyincore.globals import INCORE_API_DEV_URL


def run_with_base_class():
    # client = IncoreClient()
    client = IncoreClient(INCORE_API_DEV_URL)

    # Building inventory shapefile, Seaside, OR
    bldg_dataset_id = "5bcf2fcbf242fe047ce79dad"
    # original ERGO Building inventory shapefile
    # bldg_dataset_id = "5f518b76301b3c1b569d7e9c"
    # Building structural damage, csv file, earthquake Seaside - kube
    bldg_dmg_id = "5f514554bd2164309e79f67c"
    # original ERGO Building structural damage, csv file
    # bldg_dmg_id = "5f5191763f9bbf5a2bbbb4a9"

    bldg_econ_dmg = BuildingEconLoss(client)
    bldg_econ_dmg.load_remote_input_dataset("buildings", bldg_dataset_id)
    bldg_econ_dmg.load_remote_input_dataset("building_mean_dmg", bldg_dmg_id)

    # Ergo consumer index - kube
    consumer_price_idx = "5f487cc852147a614c708039"
    bldg_econ_dmg.load_remote_input_dataset("consumer_price_index", consumer_price_idx)

    result_name = "seaside_bldg_econ_loss"
    bldg_econ_dmg.set_parameter("result_name", result_name)
    # Inflation factor is used if consumer_price_idx is not provided
    # bldg_econ_dmg.set_parameter("inflation_factor", 100.0)
    bldg_econ_dmg.set_parameter("num_cpu", 1)

    # Run Analysis
    bldg_econ_dmg.run_analysis()


if __name__ == '__main__':
    run_with_base_class()

