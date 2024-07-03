# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


from pyincore.analyses.buyoutdecision import BuyoutDecision
from pyincore import IncoreClient
import pyincore.globals as pyglobals


def BuyoutDecisionTest():
    client = IncoreClient(pyglobals.INCORE_API_DEV_URL)

    past_building_damage_id = "6632d2605da5fd22b268511f"
    future_building_damage_id = "6632d45b5da5fd22b2685136"
    past_pop_dislocation_id = "6632d5205da5fd22b26878bb"

    hua_id = "64227016b18d026e7c80d2bc"

    buildings_id = "63ff69a96d3b2a308baaca12"

    fema_buyout_cap = 321291.600
    residential_archetypes = [1, 2, 3, 4, 5, 17]

    buyout_decision = BuyoutDecision(client)
    buyout_decision.set_parameter("fema_buyout_cap", fema_buyout_cap)
    buyout_decision.set_parameter("residential_archetypes", residential_archetypes)
    buyout_decision.set_parameter("result_name", "galveston_buyout")

    buyout_decision.load_remote_input_dataset("buildings", buildings_id)
    buyout_decision.load_remote_input_dataset("housing_unit_allocation", hua_id)
    buyout_decision.load_remote_input_dataset(
        "past_building_damage", past_building_damage_id
    )
    buyout_decision.load_remote_input_dataset(
        "future_building_damage", future_building_damage_id
    )
    buyout_decision.load_remote_input_dataset(
        "population_dislocation", past_pop_dislocation_id
    )

    buyout_decision.run_analysis()

    result = buyout_decision.get_output_dataset("result")
    result_df = result.get_dataframe_from_csv()
    print(result_df.head())
    print(len(result_df))


if __name__ == "__main__":
    BuyoutDecisionTest()
