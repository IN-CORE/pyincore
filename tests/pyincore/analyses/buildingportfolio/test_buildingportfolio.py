# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


from pyincore.analyses.buildingportfolio.recovery import BuildingPortfolioRecoveryAnalysis
from pyincore import IncoreClient
import pyincore.globals as pyglobals

if __name__ == "__main__":
    cred = None
    try:
        client = IncoreClient(pyglobals.INCORE_API_PROD_URL)
        bldg_data_dataset = "5c756966c11bb369a33a0b0a"
        occupancy_dataset = "5c7569f9c11bb369a33a0b16"
        bldg_damage_dataset = "5c756a2fc11bb369a33a0b22"
        mean_repair_dataset = "5c756ac5c11bb369a33a0b34"
        utility_dataset = "5c756af4c11bb369a33a0b40"
        utility_partial_dataset = "5c756b1ec11bb369a33a0b4c"
        coefFL_dataset = "5c756b56c11bb369a33a0b58"

        bldg_portfolio_recovery = BuildingPortfolioRecoveryAnalysis(client)
        bldg_portfolio_recovery.set_parameter("uncertainty", True)
        bldg_portfolio_recovery.set_parameter("sample_size", 35)  # default none. Gets size form input dataset
        bldg_portfolio_recovery.set_parameter("random_sample_size", 50)  # default 10000
        bldg_portfolio_recovery.set_parameter("no_of_weeks", 100)  # default 250
        bldg_portfolio_recovery.set_parameter("num_cpu", 1)

        bldg_portfolio_recovery.load_remote_input_dataset("building_data", bldg_data_dataset)
        bldg_portfolio_recovery.load_remote_input_dataset("occupancy_mapping", occupancy_dataset)
        bldg_portfolio_recovery.load_remote_input_dataset("building_damage", bldg_damage_dataset)
        bldg_portfolio_recovery.load_remote_input_dataset("dmg_ratios", mean_repair_dataset)
        bldg_portfolio_recovery.load_remote_input_dataset("utility", utility_dataset)
        bldg_portfolio_recovery.load_remote_input_dataset("utility_partial", utility_partial_dataset)
        bldg_portfolio_recovery.load_remote_input_dataset("coefFL", coefFL_dataset)

        bldg_portfolio_recovery.run_analysis()
        bldg_portfolio_recovery.get_output_dataset("result").get_dataframe_from_csv().head()

    except EnvironmentError:
        raise
        # traceback.print_exc()
