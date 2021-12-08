# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import os

import pandas as pd

from pyincore.analyses.indp.infrastructureutil import InfrastructureUtil
from pyincore.analyses.indp.indpresults import INDPResults


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
                            # assuming a 4-person crew per HAZUS
                            rep_time = (rep_rate['break'] * reptime_func_arc['# Fixed Breaks/Day/Worker'] +
                                        rep_rate['leak'] * reptime_func_arc[
                                            '# Fixed Leaks/Day/Worker']) * pipe_length / 4
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
        interdep_net = InfrastructureUtil.load_infrastructure_array_format_extended(base_dir=base_dir,
                                                                                    cost_scale=cost_scale,
                                                                                    extra_commodity=extra_commodity)
        return interdep_net

    @staticmethod
    def save_indp_model_to_file(model, out_model_dir, t, layer=0, suffix=''):
        """
        This function saves Gurobi optimization model to file.

        Parameters
        ----------
        model : gurobipy.Model
            Gurobi optimization model
        out_model_dir : str
            Directory to which the models should be written
        t : int
            The time step corresponding to the model
        layer : int
            The layer number corresponding to the model. The default is 0, which means the model includes all layers in
            the analysis
        suffix : str
            The suffix that should be added to files when saved. The default is ''.
        Returns
        -------
        None.

        """
        if not os.path.exists(out_model_dir):
            os.makedirs(out_model_dir)
        # Write models to file
        l_name = "/Model_t%d_l%d_%s.lp" % (t, layer, suffix)
        model.write(out_model_dir + l_name)
        model.update()
        # Write solution to file
        s_name = "/Solution_t%d_l%d_%s.txt" % (t, layer, suffix)
        file_id = open(out_model_dir + s_name, 'w')
        for vv in model.getVars():
            file_id.write('%s %g\n' % (vv.varName, vv.x))
        file_id.write('Obj: %g' % model.objVal)
        file_id.close()

    @staticmethod
    def apply_recovery(N, indp_results, t):
        """
        This function applies the restoration decisions (solution of INDP) to a Gurobi model by changing the state of
        repaired elements to functional

        Parameters
        ----------
        N : :class:`~infrastructure.InfrastructureNetwork`
            The model of the interdependent network.
        indp_results : INDPResults
            A :class:`~indputils.INDPResults` object containing the optimal restoration decisions.
        t : int
            The time step to which the results should apply.

        Returns
        -------
        None.

        """
        for action in indp_results[t]['actions']:
            if "/" in action:
                # Edge recovery action.
                data = action.split("/")
                src = tuple([int(x) for x in data[0].split(".")])
                dst = tuple([int(x) for x in data[1].split(".")])
                N.G[src][dst]['data']['inf_data'].functionality = 1.0
            else:
                # Node recovery action.
                node = tuple([int(x) for x in action.split(".")])
                # print "Applying recovery:",node
                N.G.nodes[node]['data']['inf_data'].repaired = 1.0
                N.G.nodes[node]['data']['inf_data'].functionality = 1.0

    @staticmethod
    def collect_results(m, controlled_layers, T, n_hat, n_hat_prime, a_hat_prime, S, coloc=True):
        """
        This function computes the results (actions and costs) of the optimal results and writes them to a
        :class:`~indputils.INDPResults` object.

        Parameters
        ----------
        m : gurobi.Model
            The object containing the solved optimization problem.
        controlled_layers : list
            Layer IDs that can be recovered in this optimization.
        T : int
            Number of time steps in the optimization (T=1 for iINDP, and T>=1 for td-INDP).
        n_hat : list
            List of Damaged nodes in the whole networks.
        n_hat_prime : list
            List of damaged nodes in controlled networks.
        a_hat_prime : list
            List of damaged arcs in controlled networks.
        S : list
            List of geographical sites.
        coloc : bool, optional
            If false, exclude geographical interdependency from the results. The default is True.

        Returns
        -------
        indp_results : INDPResults
        A :class:`~indputils.INDPResults` object containing the optimal restoration decisions.

        """
        layers = controlled_layers
        indp_results = INDPResults(layers)
        # compute total demand of all layers and each layer
        total_demand = 0.0
        total_demand_layer = {layer: 0.0 for layer in layers}
        for n, d in n_hat.nodes(data=True):
            demand_value = d['data']['inf_data'].demand
            if demand_value < 0:
                total_demand += demand_value
                total_demand_layer[n[1]] += demand_value
        for t in range(T):
            node_cost = 0.0
            arc_cost = 0.0
            flow_cost = 0.0
            over_supp_cost = 0.0
            under_supp_cost = 0.0
            under_supp = 0.0
            space_prep_cost = 0.0
            node_cost_layer = {layer: 0.0 for layer in layers}
            arc_cost_layer = {layer: 0.0 for layer in layers}
            flow_cost_layer = {layer: 0.0 for layer in layers}
            over_supp_cost_layer = {layer: 0.0 for layer in layers}
            under_supp_cost_layer = {layer: 0.0 for layer in layers}
            under_supp_layer = {layer: 0.0 for layer in layers}
            space_prep_cost_layer = {layer: 0.0 for layer in layers}  # !!! populate this for each layer
            # Record node recovery actions.
            for n, d in n_hat_prime:
                node_var = 'w_tilde_' + str(n) + "," + str(t)
                if T == 1:
                    node_var = 'w_' + str(n) + "," + str(t)
                if round(m.getVarByName(node_var).x) == 1:
                    action = str(n[0]) + "." + str(n[1])
                    indp_results.add_action(t, action)
            # Record edge recovery actions.
            for u, v, a in a_hat_prime:
                arc_var = 'y_tilde_' + str(u) + "," + str(v) + "," + str(t)
                if T == 1:
                    arc_var = 'y_' + str(u) + "," + str(v) + "," + str(t)
                if round(m.getVarByName(arc_var).x) == 1:
                    action = str(u[0]) + "." + str(u[1]) + "/" + str(v[0]) + "." + str(v[1])
                    indp_results.add_action(t, action)
            # Calculate space preparation costs.
            if coloc:
                for s in S:
                    space_prep_cost += s.cost * m.getVarByName('z_' + str(s.id) + "," + str(t)).x
            indp_results.add_cost(t, "Space Prep", space_prep_cost, space_prep_cost_layer)
            # Calculate arc preparation costs.
            for u, v, a in a_hat_prime:
                arc_var = 'y_tilde_' + str(u) + "," + str(v) + "," + str(t)
                if T == 1:
                    arc_var = 'y_' + str(u) + "," + str(v) + "," + str(t)
                arc_cost += (a['data']['inf_data'].reconstruction_cost / 2.0) * m.getVarByName(arc_var).x
                arc_cost_layer[u[1]] += (a['data']['inf_data'].reconstruction_cost / 2.0) * m.getVarByName(arc_var).x
            indp_results.add_cost(t, "Arc", arc_cost, arc_cost_layer)
            # Calculate node preparation costs.
            for n, d in n_hat_prime:
                node_var = 'w_tilde_' + str(n) + "," + str(t)
                if T == 1:
                    node_var = 'w_' + str(n) + "," + str(t)
                node_cost += d['data']['inf_data'].reconstruction_cost * m.getVarByName(node_var).x
                node_cost_layer[n[1]] += d['data']['inf_data'].reconstruction_cost * m.getVarByName(node_var).x
            indp_results.add_cost(t, "Node", node_cost, node_cost_layer)
            # Calculate under/oversupply costs.
            for n, d in n_hat.nodes(data=True):
                over_supp_cost += d['data']['inf_data'].oversupply_penalty * m.getVarByName(
                    'delta+_' + str(n) + "," + str(t)).x
                over_supp_cost_layer[n[1]] += d['data']['inf_data'].oversupply_penalty * m.getVarByName(
                    'delta+_' + str(n) + "," + str(t)).x
                under_supp += m.getVarByName('delta-_' + str(n) + "," + str(t)).x
                under_supp_layer[n[1]] += m.getVarByName('delta-_' + str(n) + "," + str(t)).x / total_demand_layer[n[1]]
                under_supp_cost += d['data']['inf_data'].undersupply_penalty * m.getVarByName(
                    'delta-_' + str(n) + "," + str(t)).x
                under_supp_cost_layer[n[1]] += d['data']['inf_data'].undersupply_penalty * m.getVarByName(
                    'delta-_' + str(n) + "," + str(t)).x
            indp_results.add_cost(t, "Over Supply", over_supp_cost, over_supp_cost_layer)
            indp_results.add_cost(t, "Under Supply", under_supp_cost, under_supp_cost_layer)
            indp_results.add_cost(t, "Under Supply Perc", under_supp / total_demand, under_supp_layer)
            # Calculate flow costs.
            for u, v, a in n_hat.edges(data=True):
                flow_cost += a['data']['inf_data'].flow_cost * m.getVarByName(
                    'x_' + str(u) + "," + str(v) + "," + str(t)).x
                flow_cost_layer[u[1]] += a['data']['inf_data'].flow_cost * m.getVarByName(
                    'x_' + str(u) + "," + str(v) + "," + str(t)).x
            indp_results.add_cost(t, "Flow", flow_cost, flow_cost_layer)
            # Calculate total costs.
            total_lyr = {}
            total_nd_lyr = {}
            for layer in layers:
                total_lyr[layer] = flow_cost_layer[layer] + arc_cost_layer[layer] + node_cost_layer[layer] + \
                                   over_supp_cost_layer[layer] + under_supp_cost_layer[layer] + space_prep_cost_layer[
                                       layer]
                total_nd_lyr[layer] = space_prep_cost_layer[layer] + arc_cost_layer[layer] + flow_cost +  \
                    node_cost_layer[layer]
            indp_results.add_cost(t, "Total",
                                  flow_cost + arc_cost + node_cost + over_supp_cost + under_supp_cost + space_prep_cost,
                                  total_lyr)
            indp_results.add_cost(t, "Total no disconnection", space_prep_cost + arc_cost + flow_cost + node_cost,
                                  total_nd_lyr)
        return indp_results

    @staticmethod
    def collect_solution_pool(m, T, n_hat_prime, a_hat_prime):
        """
        This function collects the result (list of repaired nodes and arcs) for all feasible solutions in the
        solution pool.

        Parameters
        ----------
        m : gurobi.Model
            The object containing the solved optimization problem.
        T : int
            Number of time steps in the optimization (T=1 for iINDP, and T>=1 for td-INDP).
        n_hat_prime : list
            List of damaged nodes in controlled networks.
        a_hat_prime : list
            List of damaged arcs in controlled networks.

        Returns
        -------
        sol_pool_results : dict
        A dictionary containing one dictionary per solution that contains list of repaired node and arcs in the
        solution.

        """
        sol_pool_results = {}
        current_sol_count = 0
        for sol in range(m.SolCount):
            m.setParam('SolutionNumber', sol)
            # print(m.PoolObjVal)
            sol_pool_results[sol] = {'nodes': [], 'arcs': []}
            for t in range(T):
                # Record node recovery actions.
                for n, d in n_hat_prime:
                    node_var = 'w_tilde_' + str(n) + "," + str(t)
                    if T == 1:
                        node_var = 'w_' + str(n) + "," + str(t)
                    if round(m.getVarByName(node_var).xn) == 1:
                        sol_pool_results[sol]['nodes'].append(n)
                # Record edge recovery actions.
                for u, v, a in a_hat_prime:
                    arc_var = 'y_tilde_' + str(u) + "," + str(v) + "," + str(t)
                    if T == 1:
                        arc_var = 'y_' + str(u) + "," + str(v) + "," + str(t)
                    if round(m.getVarByName(arc_var).x) == 1:
                        sol_pool_results[sol]['arcs'].append((u, v))
            if sol > 0 and sol_pool_results[sol] == sol_pool_results[current_sol_count]:
                del sol_pool_results[sol]
            elif sol > 0:
                current_sol_count = sol
        return sol_pool_results
