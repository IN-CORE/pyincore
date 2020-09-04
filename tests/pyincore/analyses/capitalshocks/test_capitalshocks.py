from pyincore import IncoreClient
from pyincore.analyses.capitalshocks import CapitalShocks
import pyincore.globals as pyglobals


def run_base_analysis():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)
    capital_shocks = CapitalShocks(client)

    # Building inventory
    building_inventory = "5df40388b9219c06cf8b0c80"
    building_to_sectors = "5f4fec587b38705fff493dc6"
    failure_probability = "5f4e6e85ef0df52132b9f5c9"

    capital_shocks.set_parameter("result_name", "sector_shocks")

    capital_shocks.load_remote_input_dataset("buildings", building_inventory)
    capital_shocks.load_remote_input_dataset("buildings_to_sectors", building_to_sectors)
    capital_shocks.load_remote_input_dataset("failure_probability", failure_probability)
    capital_shocks.run_analysis()


if __name__ == '__main__':
    run_base_analysis()
