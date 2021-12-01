# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from infrastructure import load_infrastructure_array_format_extended


class INDPUtil:

    @staticmethod
    def get_resource_suffix(params):
        """
        This function generates the part of the suffix of result folders that pertains to resource cap(s).

        Args:
            params (dict): Parameters that are needed to run the INDP optimization.

        Returns:
            out_dir_suffix_res (str): The part of the suffix of result folders that pertains to resource cap(s).

        """
        out_dir_suffix_res = ''
        for rc, val in params["V"].items():
            if isinstance(val, int):
                if rc != '':
                    out_dir_suffix_res += rc[0] + str(val)
                else:
                    out_dir_suffix_res += str(val)
            else:
                out_dir_suffix_res += rc[0] + str(sum([lval for _, lval in val.items()])) + '_fixed_layer_Cap'
        return out_dir_suffix_res

    @staticmethod
    def time_resource_usage_curves(base_dir, damage_dir, sample_num):
        """
        This module calculates the repair time for nodes and arcs for the current scenario based on their damage
        state, and writes them to the input files of INDP. Currently, it is only compatible with NIST testbeds.

        Args:
            damage_dir:
            sample_num:

        Returns:

        """
        files = [f for f in os.listdir(base_dir) if os.path.isfile(os.path.join(base_dir, f))]
        nodes_reptime_func = pd.read_csv(base_dir + 'repair_time_curves_nodes.csv')
        nodes_damge_ratio = pd.read_csv(base_dir + 'damage_ratio_nodes.csv')
        arcs_reptime_func = pd.read_csv(base_dir + 'repair_time_curves_arcs.csv')
        arcs_damge_ratio = pd.read_csv(base_dir + 'damage_ratio_arcs.csv')
        dmg_sce_data = pd.read_csv(damage_dir + 'Initial_node_ds.csv', delimiter=',')
        net_names = {'Water': 1, 'Power': 3}

        for file in files:
            fname = file[0:-4]
            if fname[-5:] == 'Nodes':
                with open(base_dir + file) as f:
                    node_data = pd.read_csv(f, delimiter=',')
                    for v in node_data.iterrows():
                        node_type = v[1]['utilfcltyc']
                        node_id = int(v[1]['nodenwid'])

                        reptime_func_node = nodes_reptime_func[nodes_reptime_func['Type'] == node_type]
                        dr_data = nodes_damge_ratio[nodes_damge_ratio['Type'] == node_type]
                        rep_time = 0
                        repair_cost = 0
                        if not reptime_func_node.empty:
                            node_name = '(' + str(node_id) + ',' + str(net_names[fname[:5]]) + ')'
                            ds = dmg_sce_data[dmg_sce_data['name'] == node_name].iloc[0][sample_num + 1]
                            rep_time = reptime_func_node.iloc[0]['ds_' + ds + '_mean']
                            # ..todo Add repair time uncertainty here
                            # rep_time = np.random.normal(reptime_func_node['ds_'+ds+'_mean'],
                            #                             reptime_func_node['ds_'+ds+'_sd'], 1)[0]

                            dr = dr_data.iloc[0]['dr_' + ds + '_be']
                            # ..todo Add damage ratio uncertainty here
                            # dr = np.random.uniform(dr_data.iloc[0]['dr_'+ds+'_min'],
                            #                       dr_data.iloc[0]['dr_'+ds+'_max'], 1)[0]
                            repair_cost = v[1]['q (complete DS)'] * dr
                        node_data.loc[v[0], 'p_time'] = rep_time if rep_time > 0 else 0
                        node_data.loc[v[0], 'p_budget'] = repair_cost
                        node_data.loc[v[0], 'q'] = repair_cost
                    node_data.to_csv(base_dir + file, index=False)

        for file in files:
            fname = file[0:-4]
            if fname[-4:] == 'Arcs':
                with open(base_dir + file) as f:
                    data = pd.read_csv(f, delimiter=',')
                    dmg_data_all = pd.read_csv(damage_dir + 'pipe_dmg.csv', delimiter=',')
                    for v in data.iterrows():
                        dmg_data_arc = dmg_data_all[dmg_data_all['guid'] == v[1]['guid']]
                        rep_time = 0
                        repair_cost = 0
                        if not dmg_data_arc.empty:
                            if v[1]['diameter'] > 20:
                                reptime_func_arc = arcs_reptime_func[arcs_reptime_func['Type'] == '>20 in']
                                dr_data = arcs_damge_ratio[arcs_damge_ratio['Type'] == '>20 in']
                            else:
                                reptime_func_arc = arcs_reptime_func[arcs_reptime_func['Type'] == '<20 in']
                                dr_data = arcs_damge_ratio[arcs_damge_ratio['Type'] == '<20 in']
                            pipe_length = v[1]['length_km']
                            pipe_length_ft = v[1]['Length']
                            rep_rate = {'break': dmg_data_arc.iloc[0]['breakrate'],
                                        'leak': dmg_data_arc.iloc[0]['leakrate']}
                            rep_time = (rep_rate['break'] * reptime_func_arc['# Fixed Breaks/Day/Worker'] + \
                                        rep_rate['leak'] * reptime_func_arc['# Fixed Leaks/Day/Worker']) * \
                                       pipe_length / 4  # assuming a 4-person crew per HAZUS
                            dr = {'break': dr_data.iloc[0]['break_be'], 'leak': dr_data.iloc[0]['leak_be']}
                            # ..todo Add repair cost uncertainty here
                            # dr = {'break': np.random.uniform(dr_data.iloc[0]['break_min'],
                            #                                  dr_data.iloc[0]['break_max'], 1)[0],
                            #       'leak': np.random.uniform(dr_data.iloc[0]['leak_min'],
                            #                                  dr_data.iloc[0]['leak_max'], 1)[0]}

                            num_20_ft_seg = pipe_length_ft / 20
                            num_breaks = rep_rate['break'] * pipe_length
                            if num_breaks > num_20_ft_seg:
                                repair_cost += v[1]['f (complete)'] * dr['break']
                            else:
                                repair_cost += v[1]['f (complete)'] / num_20_ft_seg * num_breaks * dr['break']
                            num_leaks = rep_rate['leak'] * pipe_length
                            if num_leaks > num_20_ft_seg:
                                repair_cost += v[1]['f (complete)'] * dr['leak']
                            else:
                                repair_cost += v[1]['f (complete)'] / num_20_ft_seg * num_leaks * dr['leak']
                            repair_cost = min(repair_cost, v[1]['f (complete)'])
                        data.loc[v[0], 'h_time'] = float(rep_time)
                        data.loc[v[0], 'h_budget'] = repair_cost
                        data.loc[v[0], 'f'] = repair_cost
                    data.to_csv(base_dir + file, index=False)

    @staticmethod
    def initialize_network(base_dir, cost_scale=1.0, extra_commodity=None):
        """
        This function initializes a :class:`~infrastructure.InfrastructureNetwork` object based on network data.

        Args:
            base_dir (str): Base directory of Shelby County data or synthetic networks.
            cost_scale (float): Scales the cost to improve efficiency. The default is 1.0:
            extra_commodity (dict): Dictionary of commodities other than the default one for each layer of the
            network. The default is 'None', which means that there is only one commodity per layer.

        Returns:
            interdep_net (class):`~infrastructure.InfrastructureNetwork` The object containing the network data.

        """
        interdep_net = load_infrastructure_array_format_extended(base_dir=base_dir, cost_scale=cost_scale,
                                                                 extra_commodity=extra_commodity)
        return interdep_net


