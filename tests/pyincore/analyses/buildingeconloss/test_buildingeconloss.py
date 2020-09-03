from pyincore import IncoreClient
from pyincore.analyses.buildingeconloss.buildingeconloss import BuildingEconLoss
from pyincore.globals import INCORE_API_DEV_URL


def run_with_base_class():
    # client = IncoreClient()
    client = IncoreClient(INCORE_API_DEV_URL)

    # Building datasets
    # Ergo building damage - prod
    # bldg_dataset_id = "5bcf2fcbf242fe047ce79dad"
    # Ergo building damage - kube
    bldg_dataset_id = "5bcf2fcbf242fe047ce79dad"
    # Building structural damage, earthquake Seaside
    # bldg_dmg_id = "5c5c9686c5c0e488fcf91903"
    # Ergo building damage - prod
    # bldg_dmg_id = "5f5062977b38705fff49c494"
    # Ergo building damage - kube
    bldg_dmg_id = "5f50651252147a614c73ca83"

    bldg_econ_dmg = BuildingEconLoss(client)
    # bldg_econ_dmg.load_remote_input_dataset("buildings", bldg_dataset_id)
    bldg_econ_dmg.load_remote_input_dataset("building_dmg", bldg_dmg_id)

    # Ergo building occupancy - prod
    # bldg_occupancy_id = "5f47dba83998816e84c6d7ce"
    # Ergo building occupancy - kube
    bldg_occupancy_id = "5f487e9f37e20751c11bfb6d"
    # Ergo consumer index - prod
    # consumer_price_idx = "5f47daa5ef0df52132b766aa"
    # Ergo consumer index - kube
    consumer_price_idx = "5f487cc852147a614c708039"

    bldg_econ_dmg.load_remote_input_dataset("building_occupancy", bldg_occupancy_id)
    bldg_econ_dmg.load_remote_input_dataset("consumer_price_index", consumer_price_idx)

    result_name = "seaside_bldg_econ_loss"
    bldg_econ_dmg.set_parameter("result_name", result_name)
    bldg_econ_dmg.set_parameter("num_cpu", 1)

    # Run Analysis
    bldg_econ_dmg.run_analysis()


if __name__ == '__main__':
    import time
    start_time = time.time()

    run_with_base_class()

    end_time = time.time()
    elapsed = end_time - start_time
    print("Execution time: {:.2f}".format(elapsed) + "s")
