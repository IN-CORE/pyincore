# Copyright (c) 2023 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import string


class INDPComponents:
    """
    This class stores components of a network

    Attributes
    ----------
    components : list
        List of components of the network
    num_components : int
        Number of components of the network
    gc_size : int
        Size of the largest component of the network
    """

    def __init__(self):
        self.components = []
        self.num_components = 0
        self.gc_size = 0

    def add_component(self, members, excess_supply):
        """
        This function adds a components

        Parameters
        ----------
        members : list
            List of nodes in the component
        excess_supply : float
            Excess supply within the component

        Returns
        -------
        None.

        """
        self.components.append((members, excess_supply))

    def to_csv_string(self):
        """
        Convert the list of components to a string

        Returns
        -------
            : str
            List of components as a string

        """
        comp_strings = []
        for c in self.components:
            comp_string = "/".join(c[0])
            comp_string += ":" + str(c[1])
            comp_strings.append(comp_string)
        return ",".join(comp_strings)

    @classmethod
    def calculate_components(clss, m, net, t=0, layers=None):
        """
        Find the components and the corresponding excess supply

        Parameters
        ----------
        m : gurobi.Model
            The object containing the solved optimization problem.
        net : networkx.DiGraph
            The networkx graph object that stores node, arc, and interdependency information
        t : int
            Time step. The default is zero.
        layers : list
            List of layers in the analysis

        Returns
        -------
        indp_components : :class:`~INDPComponents`
            The object containing the components

        """
        if layers is None:
            layers = [1, 2, 3]
        indp_components = INDPComponents()
        components = net.get_clusters(layers[0])
        indp_components.num_components = len(components)
        indp_components.gc_size = net.gc_size(layers[0])
        for c in components:
            total_excess_supply = 0.0
            members = []
            for n in c:
                members.append(str(n[0]) + "." + str(n[1]))
                excess_supply = 0.0
                excess_supply += m.getVarByName("delta+_" + str(n) + "," + str(t)).x
                excess_supply += -m.getVarByName("delta-_" + str(n) + "," + str(t)).x
                total_excess_supply += excess_supply
            indp_components.add_component(members, total_excess_supply)
        return indp_components

    @classmethod
    def from_csv_string(clss, csv_string):
        """
        This functions reads the components data from a string as a :class:`~INDPComponents` object

        Parameters
        ----------
        csv_string : str
            The string containing the component data

        Returns
        -------
        indp_components : :class:`~INDPComponents`
            The object containing the components

        """
        indp_components = INDPComponents()
        comps = csv_string
        for comp in comps:
            data = string.split(comp, ":")
            members = string.split(data[0], "/")
            supp = str.strip(data[1])
            indp_components.add_component(members, float(supp))
        return indp_components
