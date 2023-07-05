import numpy as np
import pandas as pd


def power_net_demand_computation(housing_alloc_data_file, mapping_data_file, prefix):
    """
    Calculates ratio of population served by each demand node in the power system

    Parameters
    ----------
    housing_alloc_data_file : str
    mapping_data_file : str
    prefix : str

    Returns
    -------

    """
    print(prefix, ': calculating ratio of population served by each node')
    housing_alloc_data = pd.read_csv(housing_alloc_data_file, low_memory=False)
    mapping_data = pd.read_csv(mapping_data_file, low_memory=False)
    node_list = list(mapping_data['node_guid'].unique())

    total_num_bldg = mapping_data.shape[0]
    print('Number of buildings:', total_num_bldg)
    total_num_hh = housing_alloc_data[~(pd.isna(housing_alloc_data['guid']))].shape[0]
    print('Number of housing units allocated to a building:', total_num_hh)
    total_population = 0

    cols = ['guid', 'serv_bldg', 'serv_hh', 'serv_pop']  # , 'demand_bldg', 'demand_hh','demand_pop']
    node_served_pop_ratio = pd.DataFrame(columns=cols)
    for node_guid in node_list:
        served_buildings = mapping_data[mapping_data['node_guid'] == node_guid]
        total_served_buildings = served_buildings.shape[0]
        total_hh = 0
        total_pop = 0
        for _, bldg in served_buildings.iterrows():
            hh_dict = housing_alloc_data[housing_alloc_data['guid'] == bldg['bldg_guid']]
            total_hh += hh_dict.shape[0]
            total_pop_bldg = 0
            for _, hh in hh_dict.iterrows():
                total_pop_bldg += hh['numprec'] if ~np.isnan(hh['numprec']) else 0
            total_pop += total_pop_bldg
        total_population += total_pop

        values = [node_guid, total_served_buildings, total_hh, total_pop]
        node_served_pop_ratio = node_served_pop_ratio.append(dict(zip(cols, values)), ignore_index=True)

    print('Total population:', total_population)
    node_served_pop_ratio['ratio_bldg'] = node_served_pop_ratio['serv_bldg'] / total_num_bldg
    node_served_pop_ratio['ratio_hh'] = node_served_pop_ratio['serv_hh'] / total_num_hh
    node_served_pop_ratio['ratio_pop'] = node_served_pop_ratio['serv_pop'] / total_population

    node_served_pop_ratio.to_csv(prefix + '_node_served_pop_ratio.csv', index=False)


def water_net_demand_computation(housing_alloc_data_file, mapping_data_file, prefix, arc_data):
    """
    Calculates ratio of population served by each demand node and supply nodes in the power system

    Parameters
    ----------
    housing_alloc_data_file : str
    mapping_data_file : str
    prefix : str
    arc_data : dict

    Returns
    -------

    """
    print(prefix, ': calculating ratio of population served by each node')
    housing_alloc_data = pd.read_csv(housing_alloc_data_file, low_memory=False)
    mapping_data = pd.read_csv(mapping_data_file, low_memory=False)
    edge_list = list(mapping_data['edge_guid'].unique())

    total_num_bldg = mapping_data.shape[0]
    print('Number of buildings:', total_num_bldg)
    total_num_hh = housing_alloc_data[~(pd.isna(housing_alloc_data['guid']))].shape[0]
    print('Number of housing units allocated to a building:', total_num_hh)
    total_population = 0

    demand_dict = {}
    # Dictionary keys are 'Pump_ID's (not 'nodenwid')
    supply_dict = {0: {'serv_bldg': 0, 'serv_hh': 0, 'serv_pop': 0},
                   1: {'serv_bldg': 0, 'serv_hh': 0, 'serv_pop': 0},
                   2: {'serv_bldg': 0, 'serv_hh': 0, 'serv_pop': 0},
                   3: {'serv_bldg': 0, 'serv_hh': 0, 'serv_pop': 0}}
    for e in edge_list:
        s_node = int(arc_data[arc_data['guid'] == e]['fromnode'])
        if s_node not in demand_dict.keys():
            demand_dict[s_node] = {'serv_bldg': 0, 'serv_hh': 0, 'serv_pop': 0}
        e_node = int(arc_data[arc_data['guid'] == e]['tonode'])
        if e_node not in demand_dict.keys():
            demand_dict[e_node] = {'serv_bldg': 0, 'serv_hh': 0, 'serv_pop': 0}

        bldgs = mapping_data[mapping_data['edge_guid'] == e]
        total_bldgs = bldgs.shape[0]
        demand_dict[s_node]['serv_bldg'] += total_bldgs / 2
        demand_dict[e_node]['serv_bldg'] += total_bldgs / 2

        total_hh = 0
        total_pop = 0
        for _, bldg in bldgs.iterrows():
            supply_dict[bldg['water_pump_ID']]['serv_bldg'] += 1
            hh_dict = housing_alloc_data[housing_alloc_data['guid'] == bldg['bldg_guid']]
            total_hh += hh_dict.shape[0]
            supply_dict[bldg['water_pump_ID']]['serv_hh'] += hh_dict.shape[0]

            total_pop_bldg = 0
            for _, hh in hh_dict.iterrows():
                total_pop_bldg += hh['numprec'] if ~np.isnan(hh['numprec']) else 0
            supply_dict[bldg['water_pump_ID']]['serv_pop'] += total_pop_bldg
            total_pop += total_pop_bldg
        demand_dict[s_node]['serv_hh'] += total_hh / 2
        demand_dict[e_node]['serv_hh'] += total_hh / 2
        demand_dict[s_node]['serv_pop'] += total_pop / 2
        demand_dict[e_node]['serv_pop'] += total_pop / 2
        total_population += total_pop

    # Waste water plant provide water for the whole city, other supply nodes are pumps that
    # provide pressured water (another type of commodity, and hence, a different set of demand values)
    supply_dict[0]['serv_bldg'] = total_num_bldg
    supply_dict[0]['serv_hh'] = total_num_hh
    supply_dict[0]['serv_pop'] = total_population

    cols = ['node', 'serv_bldg', 'serv_hh', 'serv_pop']  # , 'demand_bldg', 'demand_hh','demand_pop']
    demand_node_served_pop_ratio = pd.DataFrame(columns=cols)
    for n, val in demand_dict.items():
        values = [n, val['serv_bldg'], val['serv_hh'], val['serv_pop']]
        demand_node_served_pop_ratio = demand_node_served_pop_ratio.append(dict(zip(cols, values)), ignore_index=True)

    demand_node_served_pop_ratio['ratio_bldg'] = demand_node_served_pop_ratio['serv_bldg'] / total_num_bldg
    demand_node_served_pop_ratio['ratio_hh'] = demand_node_served_pop_ratio['serv_hh'] / total_num_hh
    demand_node_served_pop_ratio['ratio_pop'] = demand_node_served_pop_ratio['serv_pop'] / total_population

    demand_node_served_pop_ratio.to_csv(prefix + '_demand_node_served_pop_ratio.csv', index=False)

    supply_node_served_pop_ratio = pd.DataFrame(columns=cols)
    for n, val in supply_dict.items():
        values = [n, val['serv_bldg'], val['serv_hh'], val['serv_pop']]
        supply_node_served_pop_ratio = supply_node_served_pop_ratio.append(dict(zip(cols, values)), ignore_index=True)

    supply_node_served_pop_ratio['ratio_bldg'] = supply_node_served_pop_ratio['serv_bldg'] / total_num_bldg
    supply_node_served_pop_ratio['ratio_hh'] = supply_node_served_pop_ratio['serv_hh'] / total_num_hh
    supply_node_served_pop_ratio['ratio_pop'] = supply_node_served_pop_ratio['serv_pop'] / total_population

    supply_node_served_pop_ratio.to_csv(prefix + '_supply_node_served_pop_ratio.csv', index=False)
