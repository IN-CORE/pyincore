# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import os

import pyomo.environ as pyo
from pyomo.core import value

from pyincore.analyses.indp.infrastructureutil import InfrastructureUtil
from pyincore.analyses.indp.indpresults import INDPResults
import pandas as pd

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

    # @staticmethod
    # def time_resource_usage_curves(power_arcs, power_nodes, water_arcs, water_nodes, pipeline_dmg, nodes_reptime_func,
    #                                nodes_damge_ratio, arcs_reptime_func,
    #                                arcs_damge_ratio, dmg_sce_data, sample_num):
    #     """
    #     This module calculates the repair time for nodes and arcs for the current scenario based on their damage
    #     state, and writes them to the input files of INDP. Currently, it is only compatible with NIST testbeds.
    #
    #     Args:
    #         power_arcs (dataframe):
    #         power_nodes (dataframe):
    #         water_arcs (dataframe):
    #         water_nodes (dataframe):
    #         pipeline_dmg (dataframe):
    #         nodes_reptime_func:
    #         nodes_damge_ratio:
    #         arcs_reptime_func:
    #         arcs_damge_ratio:
    #         dmg_sce_data:
    #         sample_num:
    #
    #     Returns:
    #         water_nodes:
    #         water_arcs:
    #         power_nodes:
    #         power_arcs:
    #
    #     """
    #     # TODO this is hardcoded?
    #     net_names = {'Water': 1, 'Power': 3}
    #
    #     for index, node_data in enumerate([water_nodes, power_nodes]):
    #         for v in node_data.iterrows():
    #             node_type = v[1]['utilfcltyc']
    #             node_id = int(v[1]['nodenwid'])
    #
    #             reptime_func_node = nodes_reptime_func[nodes_reptime_func['Type'] == node_type]
    #             dr_data = nodes_damge_ratio[nodes_damge_ratio['Type'] == node_type]
    #             rep_time = 0
    #             repair_cost = 0
    #             if not reptime_func_node.empty:
    #                 if index == 0:
    #                     node_name = '(' + str(node_id) + ',' + str(net_names["Water"]) + ')'
    #                 else:
    #                     node_name = '(' + str(node_id) + ',' + str(net_names["Power"]) + ')'
    #                 ds = dmg_sce_data[dmg_sce_data['name'] == node_name].iloc[0][sample_num + 1]
    #                 rep_time = reptime_func_node.iloc[0]['ds_' + ds + '_mean'] # we can use the 100% instead of mean
    #                 dr = dr_data.iloc[0]['dr_' + ds + '_be']
    #                 repair_cost = v[1]['q_ds_3'] * dr
    #             node_data.loc[v[0], 'p_time'] = rep_time if rep_time > 0 else 0
    #             node_data.loc[v[0], 'p_budget'] = repair_cost
    #             node_data.loc[v[0], 'q'] = repair_cost
    #
    #     for arc_data in [water_arcs, power_arcs]:
    #         for v in arc_data.iterrows():
    #             dmg_data_arc = pipeline_dmg[pipeline_dmg['guid'] == v[1]['guid']]
    #             rep_time = 0
    #             repair_cost = 0
    #             if not dmg_data_arc.empty:
    #                 if v[1]['diameter'] > 20:
    #                     reptime_func_arc = arcs_reptime_func[arcs_reptime_func['Type'] == '>20 in']
    #                     dr_data = arcs_damge_ratio[arcs_damge_ratio['Type'] == '>20 in']
    #                 else:
    #                     reptime_func_arc = arcs_reptime_func[arcs_reptime_func['Type'] == '<20 in']
    #                     dr_data = arcs_damge_ratio[arcs_damge_ratio['Type'] == '<20 in']
    #                 pipe_length = v[1]['length_km']
    #                 pipe_length_ft = v[1]['Length']
    #                 rep_rate = {'break': dmg_data_arc.iloc[0]['breakrate'],
    #                             'leak': dmg_data_arc.iloc[0]['leakrate']}
    #                 # assuming a 4-person crew per HAZUS
    #                 rep_time = (rep_rate['break'] * reptime_func_arc['# Fixed Breaks/Day/Worker'] +
    #                             rep_rate['leak'] * reptime_func_arc[
    #                                 '# Fixed Leaks/Day/Worker']) * pipe_length / 4
    #                 dr = {'break': dr_data.iloc[0]['break_be'], 'leak': dr_data.iloc[0]['leak_be']}
    #
    #                 num_20_ft_seg = pipe_length_ft / 20
    #                 num_breaks = rep_rate['break'] * pipe_length
    #                 if num_breaks > num_20_ft_seg:
    #                     repair_cost += v[1]['f_ds_3'] * dr['break']
    #                 else:
    #                     repair_cost += v[1]['f_ds_3'] / num_20_ft_seg * num_breaks * dr['break']
    #                 num_leaks = rep_rate['leak'] * pipe_length
    #                 if num_leaks > num_20_ft_seg:
    #                     repair_cost += v[1]['f_ds_3'] * dr['leak']
    #                 else:
    #                     repair_cost += v[1]['f_ds_3'] / num_20_ft_seg * num_leaks * dr['leak']
    #                 repair_cost = min(repair_cost, v[1]['f_ds_3'])
    #             arc_data.loc[v[0], 'h_time'] = float(rep_time)
    #             arc_data.loc[v[0], 'h_budget'] = repair_cost
    #             arc_data.loc[v[0], 'f'] = repair_cost
    #
    #     return water_nodes, water_arcs, power_nodes, power_arcs

    @staticmethod
    def time_resource_usage_curves(power_arcs, power_nodes, water_arcs, water_nodes, wf_restoration_time,
                                   wf_repair_cost_sample, pipeline_restoration_time, pipeline_repair_cost,
                                   epf_restoration_time, epf_repair_cost_sample):
        """
        This module calculates the repair time for nodes and arcs for the current scenario based on their damage
        state, and writes them to the input files of INDP. Currently, it is only compatible with NIST testbeds.

        Args:
            power_arcs (dataframe):
            power_nodes (dataframe):
            water_arcs (dataframe):
            water_nodes (dataframe):
            wf_restoration_time (dataframe):
            wf_repair_cost_sample (dataframe):
            pipeline_restoration_time (dataframe):
            pipeline_repair_cost (dataframe):
            epf_restoration_time (dataframe):
            epf_repair_cost_sample (dataframe):

        Returns:
            water_nodes:
            water_arcs:
            power_nodes:
            power_arcs:

        """
        water_nodes = water_nodes.merge(wf_repair_cost_sample, on='guid', how='left')
        water_nodes['p_time'] = 0
        water_nodes['p_budget'] = water_nodes['budget']
        water_nodes['p_budget'].fillna(0, inplace=True)
        water_nodes['q'] = water_nodes['repaircost']
        water_nodes['q'].fillna(0, inplace=True)

        power_nodes = power_nodes.merge(epf_repair_cost_sample, on='guid', how='left')
        power_nodes['p_time'] = 0
        power_nodes['p_budget'] = power_nodes['budget']
        power_nodes['p_budget'].fillna(0, inplace=True)
        power_nodes['q'] = power_nodes['repaircost']
        power_nodes['q'].fillna(0, inplace=True)

        water_arcs = water_arcs.merge(pipeline_repair_cost, on='guid', how='left')
        water_arcs['h_time'] = 0
        water_arcs['h_budget'] = water_arcs['budget'].astype(float)
        water_arcs['f'] = water_arcs['repaircost'].astype(float)

        return water_nodes, water_arcs, power_nodes, power_arcs

    @staticmethod
    def initialize_network(power_nodes, power_arcs, water_nodes, water_arcs, interdep, cost_scale=1.0,
                           extra_commodity=None):
        """
        This function initializes a :class:`~infrastructure.InfrastructureNetwork` object based on network data.

        Args:
            cost_scale (float): Scales the cost to improve efficiency. The default is 1.0:
            extra_commodity (dict): Dictionary of commodities other than the default one for each layer of the
            network. The default is 'None', which means that there is only one commodity per layer.

        Returns:
            interdep_net (class):`~infrastructure.InfrastructureNetwork` The object containing the network data.

        """
        interdep_net = InfrastructureUtil.load_infrastructure_array_format_extended(power_nodes,
                                                                                    power_arcs,
                                                                                    water_nodes,
                                                                                    water_arcs,
                                                                                    interdep,
                                                                                    cost_scale=cost_scale,
                                                                                    extra_commodity=extra_commodity)
        return interdep_net

    @staticmethod
    def save_indp_model_to_file(model, out_model_dir, t, layer=0, suffix=''):
        """
        This function saves pyomo optimization model to file.

        Parameters
        ----------
        model : Pyomo.Model
            Pyomo optimization model
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
        l_name = "/Model_t%d_l%d_%s.txt" % (t, layer, suffix)
        file_id = open(out_model_dir + l_name, 'w')
        model.pprint(ostream=file_id)
        file_id.close()
        # Write solution to file
        s_name = "/Solution_t%d_l%d_%s.txt" % (t, layer, suffix)
        file_id = open(out_model_dir + s_name, 'w')
        for vv in model.component_data_objects(pyo.Var):
            if vv.value:
                file_id.write('%s %g\n' % (str(vv), vv.value))
            else:
                file_id.write('%s NONE\n' % (str(vv)))
        file_id.write('Obj: %g' % value(model.Obj))
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
    def collect_results(model, controlled_layers, coloc=True):
        """
        This function computes the results (actions and costs) of the optimal results and writes them to a
        :class:`~indputils.INDPResults` object.

        Parameters
        ----------
        model : pyomo.model
            The object containing the the solved optimization problem.
        controlled_layers : list
            Layer IDs that can be recovered in this optimization.
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
        for n, d in model.n_hat.nodes(data=True):
            demand_value = d['data']['inf_data'].demand
            if demand_value < 0:
                total_demand += demand_value
                total_demand_layer[n[1]] += demand_value
        for t in range(model.T):
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
            for n in model.n_hat_prime_nodes:
                if model.T == 1:
                    node_state = model.w[n, t].value
                else:
                    node_state = model.w_tilde[n, t].value
                if node_state == 1:
                    action = str(n[0]) + "." + str(n[1])
                    indp_results.add_action(t, action)
            # Record edge recovery actions.
            for i, k, j, kb in model.a_hat_prime:
                if model.T == 1:
                    arc_state = model.y[i, k, j, kb, t].value
                else:
                    arc_state = model.y_tilde[i, k, j, kb, t].value
                if arc_state == 1:
                    action = str(i) + "." + str(k) + "/" + str(j) + "." + str(kb)
                    indp_results.add_action(t, action)
            # Calculate space preparation costs.
            if coloc:
                for s in model.S.value:
                    if model.z[s.id, t].value:
                        space_prep_cost += s.cost * model.z[s.id, t].value
            indp_results.add_cost(t, "Space Prep", space_prep_cost, space_prep_cost_layer)
            # Calculate arc preparation costs.
            for i, k, j, kb in model.a_hat_prime:
                a = model.n_hat[i, k][j, kb]['data']['inf_data']
                if model.T == 1:
                    arc_state = model.y[i, k, j, kb, t].value
                else:
                    arc_state = model.y_tilde[i, k, j, kb, t].value
                arc_cost += (a.reconstruction_cost / 2.0) * arc_state
                arc_cost_layer[k] += (a.reconstruction_cost / 2.0) * arc_state
            indp_results.add_cost(t, "Arc", arc_cost, arc_cost_layer)
            # Calculate node preparation costs.
            for n in model.n_hat_prime_nodes:
                d = model.n_hat.nodes[n]['data']['inf_data']
                if model.T == 1:
                    node_state = model.w[n, t].value
                else:
                    node_state = model.w_tilde[n, t].value
                node_cost += d.reconstruction_cost * node_state
                node_cost_layer[n[1]] += d.reconstruction_cost * node_state
            indp_results.add_cost(t, "Node", node_cost, node_cost_layer)
            # Calculate under/oversupply costs.
            for n, d in model.n_hat.nodes(data=True):
                over_supp_cost += d['data']['inf_data'].oversupply_penalty * model.delta_p[n, 'b', t].value
                over_supp_cost_layer[n[1]] += d['data']['inf_data'].oversupply_penalty * model.delta_p[n, 'b', t].value
                under_supp += model.delta_m[n, 'b', t].value
                under_supp_layer[n[1]] += model.delta_m[n, 'b', t].value / total_demand_layer[n[1]]
                under_supp_cost += d['data']['inf_data'].undersupply_penalty * model.delta_m[n, 'b', t].value
                under_supp_cost_layer[n[1]] += d['data']['inf_data'].undersupply_penalty * model.delta_m[
                    n, 'b', t].value
            indp_results.add_cost(t, "Over Supply", over_supp_cost, over_supp_cost_layer)
            indp_results.add_cost(t, "Under Supply", under_supp_cost, under_supp_cost_layer)
            indp_results.add_cost(t, "Under Supply Perc", under_supp / total_demand, under_supp_layer)
            # Calculate flow costs.
            for i, k, j, kb in model.a_hat:
                a = model.n_hat[i, k][j, kb]['data']['inf_data']
                flow_cost += a.flow_cost * model.x[i, k, j, kb, 'b', t].value
                flow_cost_layer[k] += a.flow_cost * model.x[i, k, j, kb, 'b', t].value
            indp_results.add_cost(t, "Flow", flow_cost, flow_cost_layer)
            # Calculate total costs.
            total_lyr = {}
            total_nd_lyr = {}
            for layer in layers:
                total_lyr[layer] = flow_cost_layer[layer] + arc_cost_layer[layer] + node_cost_layer[layer] + \
                                   over_supp_cost_layer[layer] + under_supp_cost_layer[layer] + \
                                   space_prep_cost_layer[layer]
                total_nd_lyr[layer] = space_prep_cost_layer[layer] + arc_cost_layer[layer] + flow_cost \
                                      + node_cost_layer[layer]
            indp_results.add_cost(t, "Total", flow_cost + arc_cost + node_cost + over_supp_cost + under_supp_cost +
                                  space_prep_cost, total_lyr)
            indp_results.add_cost(t, "Total no disconnection", space_prep_cost + arc_cost + flow_cost + node_cost,
                                  total_nd_lyr)
        return indp_results

    @staticmethod
    def initial_state_node_rule(model, i, k):
        return model.w[i, k, 0] == 0.0

    @staticmethod
    def initial_state_arc_rule(model, i, k, j, kb):
        return model.y[i, k, j, kb, 0] == 0.0

    @staticmethod
    def time_dependent_node_rule(model, i, k, t):
        if t > 0:
            return sum(model.w_tilde[i, k, t_p] for t_p in range(1, t + 1) if t > 0) >= model.w[i, k, t]
        else:
            return pyo.Constraint.Skip

    @staticmethod
    def time_dependent_arc_rule(model, i, k, j, kb, t):
        if t > 0:
            return sum(model.y_tilde[i, k, j, kb, t_p] for t_p in range(1, t + 1) if t > 0) >= model.y[i, k, j, kb, t]
        else:
            return pyo.Constraint.Skip

    @staticmethod
    def arc_equality_rule(model, i, k, j, kb, t):
        try:
            if model.T == 1:
                return model.y[i, k, j, kb, t] == model.y[j, kb, i, k, t]
            else:
                return model.y[i, k, j, kb, t] == model.y[j, kb, i, k, t], \
                       model.y_tilde[i, k, j, kb, t] == model.y_tilde[j, kb, i, k, t]
        except KeyError:
            return pyo.Constraint.Skip

    @staticmethod
    def flow_conserv_node_rule(model, i, k, layer, t):
        d = model.n_hat.nodes[(i, k)]
        out_flow_constr = 0
        in_flow_constr = 0
        demand_constr = 0
        for u, v, a in model.n_hat.out_edges((i, k), data=True):
            if layer == 'b' or layer in a['data']['inf_data'].extra_com.keys():
                out_flow_constr += model.x[u, v, layer, t]
        for u, v, a in model.n_hat.in_edges((i, k), data=True):
            if layer == 'b' or layer in a['data']['inf_data'].extra_com.keys():
                in_flow_constr += model.x[u, v, layer, t]
        if layer == 'b':
            demand_constr += d['data']['inf_data'].demand - model.delta_p[i, k, layer, t] \
                             + model.delta_m[i, k, layer, t]
        else:
            demand_constr += d['data']['inf_data'].extra_com[layer]['demand'] - model.delta_p[i, k, layer, t] + \
                             model.delta_m[i, k, layer, t]
        return out_flow_constr - in_flow_constr == demand_constr

    @staticmethod
    def flow_in_functionality_rule(model, i, k, j, kb, t):
        if not model.functionality:
            interdep_nodes_list = model.interdep_nodes.keys()  # Interdependent nodes with a damaged dependee node
        else:
            interdep_nodes_list = model.interdep_nodes[t].keys()  # Interdependent nodes with a damaged dependee node
        a = model.n_hat[i, k][j, kb]['data']['inf_data']
        lhs = model.x[i, k, j, kb, 'b', t]
        for layer in a.extra_com.keys():
            lhs += model.x[i, k, j, kb, layer, t]
        if ((i, k) in model.n_hat_prime_nodes) | ((i, k) in interdep_nodes_list):
            return lhs <= a.capacity * model.w[i, k, t]
        else:
            return lhs <= a.capacity * model.N.G.nodes[(i, k)]['data']['inf_data'].functionality

    @staticmethod
    def flow_out_functionality_rule(model, i, k, j, kb, t):
        if not model.functionality:
            interdep_nodes_list = model.interdep_nodes.keys()  # Interdependent nodes with a damaged dependee node
        else:
            interdep_nodes_list = model.interdep_nodes[t].keys()  # Interdependent nodes with a damaged dependee node
        a = model.n_hat[i, k][j, kb]['data']['inf_data']
        lhs = model.x[i, k, j, kb, 'b', t]
        for layer in a.extra_com.keys():
            lhs += model.x[i, k, j, kb, layer, t]
        if ((j, kb) in model.n_hat_prime_nodes) | ((j, kb) in interdep_nodes_list):
            return lhs <= a.capacity * model.w[j, kb, t]
        else:
            return lhs <= a.capacity * model.N.G.nodes[(j, kb)]['data']['inf_data'].functionality

    @staticmethod
    def flow_arc_functionality_rule(model, i, k, j, kb, t):
        if not model.functionality:
            interdep_nodes_list = model.interdep_nodes.keys()  # Interdependent nodes with a damaged dependee node
        else:
            interdep_nodes_list = model.interdep_nodes[t].keys()  # Interdependent nodes with a damaged dependee node
        a = model.n_hat[i, k][j, kb]['data']['inf_data']
        lhs = model.x[i, k, j, kb, 'b', t]
        for layer in a.extra_com.keys():
            lhs += model.x[i, k, j, kb, layer, t]
        if (i, k, j, kb) in model.a_hat_prime:
            return lhs <= a.capacity * model.y[i, k, j, kb, t]
        else:
            return lhs <= a.capacity * model.N.G[(i, k)][(j, kb)]['data']['inf_data'].functionality

    @staticmethod
    def resource_rule(model, rc, t):
        resource_dict = model.v_r[rc]
        is_sep_res = False
        if isinstance(resource_dict, int):
            total_resource = resource_dict
        else:
            is_sep_res = True
            total_resource = sum([lval for _, lval in resource_dict.items()])
            assert len(resource_dict.keys()) == len(model.layers), "The number of resource  values does not match the \
                                                                    number of layers."
        resource_left_constr = 0
        if is_sep_res:
            res_left_constr_sep = {key: 0 for key in resource_dict.keys()}
        for i, k, j, kb in model.a_hat_prime:
            a = model.n_hat[i, k][j, kb]['data']['inf_data']
            idx_lyr = a.layer
            res_use = 0.5 * a.resource_usage['h_' + rc]
            if model.T == 1:
                resource_left_constr += res_use * model.y[i, k, j, kb, t]
                if is_sep_res:
                    res_left_constr_sep[idx_lyr] += res_use * model.y[i, k, j, kb, t]
            else:
                resource_left_constr += res_use * model.y_tilde[i, k, j, kb, t]
                if is_sep_res:
                    res_left_constr_sep[idx_lyr] += res_use * model.y_tilde[i, k, j, kb, t]
        for n in model.n_hat_prime_nodes:
            idx_lyr = n[1]
            d = model.n_hat.nodes[n]['data']['inf_data']
            res_use = d.resource_usage['p_' + rc]
            if model.T == 1:
                resource_left_constr += res_use * model.w[n, t]
                if is_sep_res:
                    res_left_constr_sep[idx_lyr] += res_use * model.w[n, t]
            else:
                resource_left_constr += res_use * model.w_tilde[n, t]
                if is_sep_res:
                    res_left_constr_sep[idx_lyr] += res_use * model.w_tilde[n, t]
        if not isinstance(resource_left_constr, int):
            if not is_sep_res:
                return resource_left_constr <= total_resource
            else:
                return resource_left_constr <= total_resource, [res_left_constr_sep[key] <= lval for key, lval in
                                                                resource_dict]
        else:
            return pyo.Constraint.Skip

    @staticmethod
    def interdependency_rule(model, i, k, t):
        if not model.functionality:
            if (i, k) in model.interdep_nodes:
                interdep_l_constr = 0
                interdep_r_constr = 0
                for interdep in model.interdep_nodes[(i, k)]:
                    src = interdep[0]
                    gamma = interdep[1]
                    if not model.n_hat.has_node(src):
                        interdep_l_constr += 0
                    else:
                        interdep_l_constr += model.w[src, t] * gamma
                interdep_r_constr += model.w[i, k, t]
                return interdep_l_constr >= interdep_r_constr
        else:
            if (i, k) in model.interdep_nodes[t]:
                # print interdep_nodes[t]
                interdep_l_constr = 0
                interdep_r_constr = 0
                for interdep in model.interdep_nodes[t][(i, k)]:
                    src = interdep[0]
                    gamma = interdep[1]
                    if not model.n_hat.has_node(src):
                        print("Forcing", str((i, k)), "to be 0 (dep. on", str(src), ")")
                        interdep_l_constr += 0
                    else:
                        interdep_l_constr += model.w[src, t] * gamma
                interdep_r_constr += model.w[i, k, t]
                return interdep_l_constr >= interdep_r_constr
        return pyo.Constraint.Skip

    @staticmethod
    def node_geographic_space_rule(model, s, i, k, t):
        d = model.n_hat.nodes[(i, k)]['data']['inf_data']
        if d.in_space(s):
            if model.T == 1:
                return model.w[(i, k), t] * d.in_space(s) <= model.z[s, t]
            else:
                return model.w_tilde[(i, k), t] * d.in_space(s) <= model.z[s, t]
        return pyo.Constraint.Skip

    @staticmethod
    def arc_geographic_space_rule(model, s, i, k, j, kb, t):
        a = model.n_hat[i, k][j, kb]['data']['inf_data']
        if a.in_space(s):
            if model.T == 1:
                return model.y[i, k, j, kb, t] * a.in_space(s) <= model.z[s, t]
            else:
                return model.y_tilde[i, k, j, kb, t] * a.in_space(s) <= model.z[s, t]
        return pyo.Constraint.Skip

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
