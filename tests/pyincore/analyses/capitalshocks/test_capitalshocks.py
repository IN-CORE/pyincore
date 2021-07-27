import pyincore.globals as pyglobals
from pyincore import IncoreClient
from pyincore.analyses.capitalshocks import CapitalShocks


def run_base_analysis():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)
    capital_shocks = CapitalShocks(client)

    # Building inventory
    building_inventory = "5f218e36114b783cb0b01833"
    building_to_sectors = "5f218fa47887544479c8629f"
    failure_probability = "5f21909b7887544479c862c6"

    capital_shocks.set_parameter("result_name", "sector_shocks")

    capital_shocks.load_remote_input_dataset("buildings", building_inventory)
    capital_shocks.load_remote_input_dataset("buildings_to_sectors", building_to_sectors)
    capital_shocks.load_remote_input_dataset("failure_probability", failure_probability)
    capital_shocks.run_analysis()


if __name__ == '__main__':
    run_base_analysis()
