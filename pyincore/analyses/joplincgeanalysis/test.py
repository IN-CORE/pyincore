import pandas as pd
import numpy as np

building_inventory = pd.read_csv("./joplin_building_inventory_econ.csv", index_col=0)
failure_probability = pd.read_csv("./Joplin_bldg_failure_retrofit.csv", index_col=0)

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

sector_shocks.to_csv("sector-shocks.csv", index=False)

# inventory_failure = pd.merge(building_inventory, failure_probability, on='guid')
#
# inventory_failure['cap_rem'] = inventory_failure.appr_bldg * (1 - inventory_failure.failure_probability_retrofit1)
#
# goods = inventory_failure.loc[(inventory_failure['sector'] == 'GOODS')]
# hs1 = inventory_failure.loc[(inventory_failure['sector'] == 'HS1')]
# hs2 = inventory_failure.loc[(inventory_failure['sector'] == 'HS2')]
# hs3 = inventory_failure.loc[(inventory_failure['sector'] == 'HS3')]
# other = inventory_failure.loc[(inventory_failure['sector'] == 'OTHER')]
# trade = inventory_failure.loc[(inventory_failure['sector'] == 'TRADE')]
#
# # sector_cap = inventory_failure.groupby('sector')['cap_rem'].sum()
#
# goods_cap = goods['cap_rem'].sum()
# goods_total = goods['appr_bldg'].sum()
# goods_shock = np.divide(goods_cap, goods_total)
#
# hs1_cap = hs1['cap_rem'].sum()
# hs1_total = hs1['appr_bldg'].sum()
# hs1_shock = np.divide(hs1_cap, hs1_total)
#
# hs2_cap = hs2['cap_rem'].sum()
# hs2_total = hs2['appr_bldg'].sum()
# hs2_shock = np.divide(hs2_cap, hs2_total)
#
# hs3_cap = hs3['cap_rem'].sum()
# hs3_total = hs3['appr_bldg'].sum()
# hs3_shock = np.divide(hs3_cap, hs3_total)
#
# other_cap = other['cap_rem'].sum()
# other_total = other['appr_bldg'].sum()
# other_shock = np.divide(other_cap, other_total)
#
# trade_cap = trade['cap_rem'].sum()
# trade_total = trade['appr_bldg'].sum()
# trade_shock = np.divide(trade_cap, trade_total)
#
# sector_shocks_dict = {'GOODS': [goods_shock], 'HS1': [hs1_shock],
#                       'HS2': [hs2_shock], 'HS3': [hs3_shock], 'OTHER': [other_shock], 'TRADE': [trade_shock]}
# sector_shocks = pd.DataFrame.from_dict(sector_shocks_dict)
#
# sector_shocks.to_csv("sector_shocks.csv", index=False)
