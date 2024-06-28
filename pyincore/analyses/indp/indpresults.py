# Copyright (c) 2023 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from pyincore.analyses.indp.indpcomponents import INDPComponents
import os


class INDPResults:
    """
    This class saves INDP results including actions, costs, run time, and components

    Attributes
    ----------
    results : dict
        Dictionary containing INDP results including actions, costs, run time, and components
    layers : list
        List of layers in the analysis
    results_layer : int
        Dictionary containing INDP results for each layer including actions, costs, run time, and components
    """

    cost_types = [
        "Space Prep",
        "Arc",
        "Node",
        "Over Supply",
        "Under Supply",
        "Flow",
        "Total",
        "Under Supply Perc",
    ]

    def __init__(self, layers=None):
        if layers is None:
            layers = []
        self.results = {}
        self.layers = layers
        self.results_layer = {layer: {} for layer in layers}

    def __len__(self):
        return len(self.results)

    def __getitem__(self, index):
        return self.results[index]

    def extend(self, indp_result, t_offset=0, t_start=0, t_end=0):
        """
        This function extends the results to accommodate a new time step.

        Parameters
        ----------
        indp_result : :class:`~INDPResults`
            The current :class:`~INDPResults` object before extension
        t_offset : int
            The number of time steps that the current results should be shifted forward. The default is 0.
        t_start : int
            The starting time step. The default is 0.
        t_end : int
            The ending time step. The default is 0.

        Returns
        -------
        None.

        """
        if t_end == 0:
            t_end = len(indp_result)
        for new_t, t in zip(
            [x + t_offset for x in range(t_end - t_start)],
            [y + t_start for y in range(t_end - t_start)],
        ):
            self.results[new_t] = indp_result.results[t]
        if self.layers:
            if t_end == 0:
                t_end = len(indp_result[self.layers[0]])
            for layer in indp_result.results_layer.keys():
                for new_t, t in zip(
                    [x + t_offset for x in range(t_end - t_start)],
                    [y + t_start for y in range(t_end - t_start)],
                ):
                    self.results_layer[layer][new_t] = indp_result.results_layer[layer][
                        t
                    ]

    def add_cost(self, t, cost_type, cost, cost_layer=None):
        """
        This function adds cost values to the results.

        Parameters
        ----------
        t : int
            The time steps to which the costs should be added
        cost_type : str
            The cost types that is added. The options are: "Space Prep", "Arc", "Node", "Over Supply", "Under Supply",
            "Flow", "Total", "Under Supply Perc"
        cost : float
            The cost value that is added
        cost_layer : dict
            The cost value that is added for each layer. The default is None, which adds no value for layers.

        Returns
        -------
        None.

        """
        if cost_layer is None:
            cost_layer = {}
        if t not in self.results:
            self.results[t] = {
                "costs": {
                    "Space Prep": 0.0,
                    "Arc": 0.0,
                    "Node": 0.0,
                    "Over Supply": 0.0,
                    "Under Supply": 0.0,
                    "Under Supply Perc": 0.0,
                    "Flow": 0.0,
                    "Total": 0.0,
                },
                "actions": [],
                "gc_size": 0,
                "num_components": 0,
                "components": INDPComponents(),
                "run_time": 0.0,
            }
        self.results[t]["costs"][cost_type] = cost
        if self.layers:
            for layer in cost_layer.keys():
                if t not in self.results_layer[layer]:
                    self.results_layer[layer][t] = {
                        "costs": {
                            "Space Prep": 0.0,
                            "Arc": 0.0,
                            "Node": 0.0,
                            "Over Supply": 0.0,
                            "Under Supply": 0.0,
                            "Under Supply Perc": 0.0,
                            "Flow": 0.0,
                            "Total": 0.0,
                        },
                        "actions": [],
                        "gc_size": 0,
                        "num_components": 0,
                        "components": INDPComponents(),
                        "run_time": 0.0,
                    }
                self.results_layer[layer][t]["costs"][cost_type] = cost_layer[layer]

    def add_run_time(self, t, run_time, save_layer=True):
        """
        This function adds run time to the results.

        Parameters
        ----------
        t : int
            The time steps to which the run time should be added
        run_time : float
            The run time that is added
        save_layer : bool
            If the run time should be added for each layer. The default is True.

        Returns
        -------
        None.

        """
        if t not in self.results:
            self.results[t] = {
                "costs": {
                    "Space Prep": 0.0,
                    "Arc": 0.0,
                    "Node": 0.0,
                    "Over Supply": 0.0,
                    "Under Supply": 0.0,
                    "Under Supply Perc": 0.0,
                    "Flow": 0.0,
                    "Total": 0.0,
                },
                "actions": [],
                "gc_size": 0,
                "num_components": 0,
                "components": INDPComponents(),
                "run_time": 0.0,
            }
        self.results[t]["run_time"] = run_time
        if self.layers and save_layer:
            for layer in self.layers:
                if t not in self.results_layer[layer]:
                    self.results_layer[layer][t] = {
                        "costs": {
                            "Space Prep": 0.0,
                            "Arc": 0.0,
                            "Node": 0.0,
                            "Over Supply": 0.0,
                            "Under Supply": 0.0,
                            "Under Supply Perc": 0.0,
                            "Flow": 0.0,
                            "Total": 0.0,
                        },
                        "actions": [],
                        "gc_size": 0,
                        "num_components": 0,
                        "components": INDPComponents(),
                        "run_time": 0.0,
                    }
                self.results_layer[layer][t]["run_time"] = run_time

    def add_action(self, t, action, save_layer=True):
        """
        This function adds restoration actions to the results.

        Parameters
        ----------
        t : int
            The time steps to which the actions should be added
        action : list
            List of actions that are added
        save_layer : bool
            If the actions should be added for each layer. The default is True.

        Returns
        -------
        None.

        """
        if t not in self.results:
            self.results[t] = {
                "costs": {
                    "Space Prep": 0.0,
                    "Arc": 0.0,
                    "Node": 0.0,
                    "Over Supply": 0.0,
                    "Under Supply": 0.0,
                    "Under Supply Perc": 0.0,
                    "Flow": 0.0,
                    "Total": 0.0,
                },
                "actions": [],
                "gc_size": 0,
                "num_components": 0,
                "components": INDPComponents(),
                "run_time": 0.0,
            }
        self.results[t]["actions"].append(action)
        if self.layers and save_layer:
            action_layer = int(action[-1])
            if t not in self.results_layer[action_layer]:
                self.results_layer[action_layer][t] = {
                    "costs": {
                        "Space Prep": 0.0,
                        "Arc": 0.0,
                        "Node": 0.0,
                        "Over Supply": 0.0,
                        "Under Supply": 0.0,
                        "Under Supply Perc": 0.0,
                        "Flow": 0.0,
                        "Total": 0.0,
                    },
                    "actions": [],
                    "gc_size": 0,
                    "num_components": 0,
                    "components": INDPComponents(),
                    "run_time": 0.0,
                }
            self.results_layer[action_layer][t]["actions"].append(action)

    def add_gc_size(self, t, gc_size):
        """
        This function adds the giant component size to the results

        Parameters
        ----------
        t : int
            The time steps to which the giant component size should be added
        gc_size : int
            The giant component size that is added

        Returns
        -------
        None.

        """
        if t not in self.results:
            self.results[t] = {
                "costs": {
                    "Space Prep": 0.0,
                    "Arc": 0.0,
                    "Node": 0.0,
                    "Over Supply": 0.0,
                    "Under Supply": 0.0,
                    "Under Supply Perc": 0.0,
                    "Flow": 0.0,
                    "Total": 0.0,
                },
                "actions": [],
                "gc_size": 0,
                "num_components": 0,
                "components": INDPComponents(),
                "run_time": 0.0,
            }
        self.results[t]["gc_size"] = gc_size

    def add_num_components(self, t, num_components):
        """
        This function adds the number of components to the results

        Parameters
        ----------
        t : int
            The time steps to which the number of components should be added
        num_components : int
            The number of components that is added

        Returns
        -------
        None.

        """
        if t not in self.results:
            self.results[t] = {
                "costs": {
                    "Space Prep": 0.0,
                    "Arc": 0.0,
                    "Node": 0.0,
                    "Over Supply": 0.0,
                    "Under Supply": 0.0,
                    "Under Supply Perc": 0.0,
                    "Flow": 0.0,
                    "Total": 0.0,
                },
                "actions": [],
                "gc_size": 0,
                "num_components": 0,
                "components": INDPComponents(),
                "run_time": 0.0,
            }
        self.results[t]["num_components"] = num_components

    def add_components(self, t, components):
        """
        This function adds the components to the results

        Parameters
        ----------
        t : int
            The time steps to which the number of components should be added
        components : list
            The list of components that is added

        Returns
        -------
        None.

        """
        if t not in self.results:
            self.results[t] = {
                "costs": {
                    "Space Prep": 0.0,
                    "Arc": 0.0,
                    "Node": 0.0,
                    "Over Supply": 0.0,
                    "Under Supply": 0.0,
                    "Under Supply Perc": 0.0,
                    "Flow": 0.0,
                    "Total": 0.0,
                },
                "actions": [],
                "gc_size": 0,
                "num_components": 0,
                "components": INDPComponents(),
                "run_time": 0.0,
            }
        self.results[t]["components"] = components
        self.add_num_components(t, components.num_components)
        self.add_gc_size(t, components.gc_size)

    def to_csv_layer(self, out_dir, sample_num=1, suffix=""):
        """
        This function writes the results to file for each layer. The file for each layer are distinguished by "_L" +
        the layer number.

        Parameters
        ----------
        out_dir : str
            Output directory to which the results should be written.
        sample_num : int
            The sample number corresponding to the results, The default is 1.
        suffix : str
            The suffix of the file that is being written. The default is "".

        Returns
        -------
        None.

        """
        for layer in self.layers:
            action_file = (
                out_dir
                + "/actions_"
                + str(sample_num)
                + "_L"
                + str(layer)
                + "_"
                + suffix
                + ".csv"
            )
            costs_file = (
                out_dir
                + "/costs_"
                + str(sample_num)
                + "_L"
                + str(layer)
                + "_"
                + suffix
                + ".csv"
            )
            run_time_file = (
                out_dir
                + "/run_time_"
                + str(sample_num)
                + "_L"
                + str(layer)
                + "_"
                + suffix
                + ".csv"
            )
            with open(action_file, "w") as f:
                f.write("t,action\n")
                for t in self.results_layer[layer]:
                    for a in self.results_layer[layer][t]["actions"]:
                        f.write(str(t) + "," + a + "\n")
            with open(run_time_file, "w") as f:
                f.write("t,run_time\n")
                for t in self.results_layer[layer]:
                    f.write(
                        str(t)
                        + ","
                        + str(self.results_layer[layer][t]["run_time"])
                        + "\n"
                    )
            with open(costs_file, "w") as f:
                f.write(
                    "t,Space Prep,Arc,Node,Over Supply,Under Supply,Flow,Total,Under Supply Perc\n"
                )
                for t in self.results_layer[layer]:
                    costs = self.results_layer[layer][t]["costs"]
                    f.write(
                        str(t)
                        + ","
                        + str(costs["Space Prep"])
                        + ","
                        + str(costs["Arc"])
                        + ","
                        + str(costs["Node"])
                        + ","
                        + str(costs["Over Supply"])
                        + ","
                        + str(costs["Under Supply"])
                        + ","
                        + str(costs["Flow"])
                        + ","
                        + str(costs["Total"])
                        + ","
                        + str(costs["Under Supply Perc"])
                        + "\n"
                    )

    @classmethod
    def from_csv(clss, out_dir, sample_num=1, suffix=""):
        """
        This function reads the results from file.

        Parameters
        ----------
        out_dir : str
            Output directory from which the results should be read
        sample_num : int
            The sample number corresponding to the results, The default is 1.
        suffix : str
            The suffix of the file that is being read. The default is "".

        Returns
        -------
        indp_result: :class:`~INDPResults`
            The :class:`~INDPResults` object containing the read results

        """
        action_file = out_dir + "/actions_" + str(sample_num) + "_" + suffix + ".csv"
        costs_file = out_dir + "/costs_" + str(sample_num) + "_" + suffix + ".csv"
        # perc_file = out_dir + "/percolation_" + str(sample_num) + "_" + suffix + ".csv"
        # comp_file = out_dir + "/components_" + str(sample_num) + "_" + suffix + ".csv"
        run_time_file = out_dir + "/run_time_" + str(sample_num) + "_" + suffix + ".csv"
        indp_result = INDPResults()
        if os.path.isfile(
            action_file
        ):  # ..todo: component-related results are not currently added to the results.
            with open(action_file) as f:
                lines = f.readlines()[1:]
                for line in lines:
                    data = line.strip().split(",")
                    t = int(data[0])
                    action = str.strip(data[1])
                    indp_result.add_action(t, action)
            with open(costs_file) as f:
                lines = f.readlines()
                cost_types = lines[0].strip().split(",")[1:]
                for line in lines[1:]:
                    data = line.strip().split(",")
                    t = int(data[0])
                    costs = data[1:]
                    for ct in range(len(cost_types)):
                        indp_result.add_cost(t, cost_types[ct], float(costs[ct]))
            with open(run_time_file) as f:
                lines = f.readlines()
                for line in lines[1:]:
                    data = line.strip().split(",")
                    t = int(data[0])
                    run_time = data[1]
                    indp_result.add_run_time(t, run_time)
            # with open(perc_file) as f:
            #    lines=f.readlines()[1:]
            #    for line in lines:
            #        data=string.split(str.strip(line),",")
            #        t=int(data[0])
            #        indp_result.add_gc_size(t,int(data[1]))
            #        indp_result.add_num_components(t,int(data[2]))
            # with open(comp_file) as f:
            #    lines=f.readlines()[1:]
            #    for line in lines:
            #        data=string.split(str.strip(line),",")
            #        t=int(data[0])
            #        comps=data[1:]
            #        if comps[0]!='':
            #            indp_result.add_components(t,INDPComponents.from_csv_string(comps))
            #        else:
            #            print("Caution: No component.")
        else:
            raise ValueError("File does not exist: " + action_file)
        return indp_result
