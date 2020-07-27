from pyincore import BaseAnalysis
import pandas as pd
import numpy as np


class JoplinCapitalShocks(BaseAnalysis):
    """Capital stock shocks for an individual building is equal to the functionality probability multiplied by value
     of the building. This gives us the capital stock loss in the immediate aftermath of a natural disaster
     for a single building. We aggregate each of these individual losses to their associated economic sector
     to calculate the total capital stock lost for that sector. However, the capital stock shocks that are
     used as inputs into the CGE model are scalars for embodying the percent of capital stock remaining.
     we get this by dividing the total capital stock remaining by the total capital stock
     before the natural disaster."

    Args:
        incore_client (IncoreClient): Service authentication.

    """

    def __init__(self, incore_client):
        super(JoplinCapitalShocks, self).__init__(incore_client)

    def get_spec(self):
        return {
            'name': 'Joplin-small-calibrated',
            'description': 'Capital Shocks generation for Joplin cge model.',
            'input_parameters': [],
            'input_datasets': [
                {
                    'id': 'building_inventory',
                    'required': True,
                    'description': 'Failure probability of buildings.',
                    'type': ['incore:buildingInventory']
                },
                {
                    'id': 'failure_probability',
                    'required': True,
                    'description': 'Failure probability of buildings.',
                    'type': ['incore:failureProbability']
                }
            ],
            'output_datasets': [
                {
                    'id': 'sector_shocks',
                    'required': True,
                    'description': 'Aggregation of building functionality states to capital shocks per sector',
                    'type': ['incore:JoplinCGEshocks']
                }
            ]
        }

    def run(self):
        building_inventory = \
            pd.read_csv(self.get_input_dataset("building_inventory").get_file_path('csv'), index_col=0)
        failure_probability = \
            pd.read_csv(self.get_input_dataset("failure_probability").get_file_path('csv'), index_col=0)

        inventory_failure = pd.merge(building_inventory, failure_probability, on='guid')

        inventory_failure['cap_rem'] = inventory_failure.appr_bldg * (
                    1 - inventory_failure.failure_probability_retrofit1)

        goods = inventory_failure.loc[(inventory_failure['sector'] == 'GOODS')]
        hs1 = inventory_failure.loc[(inventory_failure['sector'] == 'HS1')]
        hs2 = inventory_failure.loc[(inventory_failure['sector'] == 'HS2')]
        hs3 = inventory_failure.loc[(inventory_failure['sector'] == 'HS3')]
        other = inventory_failure.loc[(inventory_failure['sector'] == 'OTHER')]
        trade = inventory_failure.loc[(inventory_failure['sector'] == 'TRADE')]

        # sector_cap = inventory_failure.groupby('sector')['cap_rem'].sum()

        goods_cap = goods['cap_rem'].sum()
        goods_total = goods['appr_bldg'].sum()
        goods_shock = np.divide(goods_cap, goods_total)

        hs1_cap = hs1['cap_rem'].sum()
        hs1_total = hs1['appr_bldg'].sum()
        hs1_shock = np.divide(hs1_cap, hs1_total)

        hs2_cap = hs2['cap_rem'].sum()
        hs2_total = hs2['appr_bldg'].sum()
        hs2_shock = np.divide(hs2_cap, hs2_total)

        hs3_cap = hs3['cap_rem'].sum()
        hs3_total = hs3['appr_bldg'].sum()
        hs3_shock = np.divide(hs3_cap, hs3_total)

        other_cap = other['cap_rem'].sum()
        other_total = other['appr_bldg'].sum()
        other_shock = np.divide(other_cap, other_total)

        trade_cap = trade['cap_rem'].sum()
        trade_total = trade['appr_bldg'].sum()
        trade_shock = np.divide(trade_cap, trade_total)

        sectors = ['GOODS', 'HS1', 'HS2', 'HS3', 'OTHER', 'TRADE']
        shocks = [goods_shock, hs1_shock, hs2_shock, hs3_shock, other_shock, trade_shock]

        sector_shocks_dict = {'sectors': sectors, 'shocks': shocks}
        sector_shocks = pd.DataFrame.from_dict(sector_shocks_dict)
        self.set_result_csv_data("sector_shocks", sector_shocks, name="sector_shocks.csv", source="dataframe")

        return True
