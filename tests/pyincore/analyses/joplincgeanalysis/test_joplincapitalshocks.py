from pyincore import IncoreClient
from pyincore.analyses.joplincgeanalysis import JoplinCapitalShocks
import pyincore.globals as pyglobals


def run_base_analysis():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)
    joplin_capital_shocks = JoplinCapitalShocks(client)

    # Building inventory
    building_inventory = "5cdc7b585648c4048fb53062"
    failure_probability = "5cdc7b585648c4048fb53062"

    joplin_capital_shocks.load_remote_input_dataset("building_inventory", building_inventory)
    joplin_capital_shocks.load_remote_input_dataset("failure_probability", failure_probability)
    joplin_capital_shocks.run_analysis()


if __name__ == '__main__':
    run_base_analysis()
