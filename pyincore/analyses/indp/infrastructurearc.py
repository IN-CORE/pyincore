# Copyright (c) 2023 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


class InfrastructureArc(object):
    """
    This class models an arc in an infrastructure network

    Attributes
    ----------
    source : int
        Start (or head) node id
    dest : int
        End (or tail) node id
    layer : int
        The id of the layer of the network to which the arc belong
    failure_probability : float
        Failure probability of the arc
    functionality : bool
        Functionality state of the node
    repaired : bool
        If the arc is repaired or not
    flow_cost : float
        Unit cost of sending the main commodity through the arc
    reconstruction_cost : float
        Reconstruction cost of the arc
    capacity : float
        Maximum volume of the commodities that the arc can carry
    space : int
        The id of the geographical space where the arc is
    resource_usage : dict
        The dictionary that shows how many resource (of each resource type) is employed to repair the arc
    extra_com : dict
        The dictionary that shows flow_cost corresponding to commodities other than the main commodity
    is_interdep : bool
        If arc represent a normal arc (that carry commodity within a single layer) or physical interdependency between
        nodes from different layers
    """

    def __init__(self, source, dest, layer, is_interdep=False):
        self.source = source
        self.dest = dest
        self.layer = layer
        self.failure_probability = 0.0
        self.functionality = 1.0
        self.repaired = 1.0
        self.flow_cost = 0.0
        self.reconstruction_cost = 0.0
        self.resource_usage = {}
        self.capacity = 0.0
        self.space = 0
        self.extra_com = {}
        self.is_interdep = is_interdep

    def set_extra_commodity(self, extra_commodity):
        """
        This function initialize the dictionary for the extra commodities

        Parameters
        ----------
        extra_commodity : list
            List of extra commodities

        Returns
        -------
        None.

        """
        for ec in extra_commodity:
            self.extra_com[ec] = {"flow_cost": 0}

    def set_resource_usage(self, resource_names):
        """
        This function initialize the dictionary for resource usage per all resource types in the analysis

        Parameters
        ----------
        resource_names : list
            List of resource types

        Returns
        -------
        None.

        """
        for rc in resource_names:
            self.resource_usage[rc] = 0

    def in_space(self, space_id):
        """
        This function checks if the arc is in a given space or not

        Parameters
        ----------
        space_id :
            The id of the space that is checked

        Returns
        -------
            : bool
            Returns 1 if the arc is in the space, and 0 otherwise.
        """
        if self.space == space_id:
            return 1
        else:
            return 0
