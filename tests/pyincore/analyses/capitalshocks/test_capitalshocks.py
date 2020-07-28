from pyincore import IncoreClient
from pyincore.analyses.capitalshocks import CapitalShocks


def run_base_analysis():
    client = IncoreClient()
    joplin_capital_shocks = CapitalShocks(client)

    # Building inventory
    building_inventory = "5dbc8478b9219c06dd242c0d"
    building_to_sectors = "5f202d674620b643d787a5e7"
    failure_probability = "5f20347933b2700c110a3dd2"

    joplin_capital_shocks.load_remote_input_dataset("buildings", building_inventory)
    joplin_capital_shocks.load_remote_input_dataset("buildings_to_sectors", building_to_sectors)
    joplin_capital_shocks.load_remote_input_dataset("failure_probability", failure_probability)
    joplin_capital_shocks.run_analysis()


if __name__ == '__main__':
    run_base_analysis()
