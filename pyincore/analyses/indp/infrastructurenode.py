# Copyright (c) 2023 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


class InfrastructureNode(object):
    """
    This class models a node in an infrastructure network

    Attributes
    ----------
    id : int
        Node id
    net_id : int
        The id of the layer of the network to which the node belong
    local_id : int
        Local node id
    failure_probability : float
        Failure probability of the node
    functionality : bool
        Functionality state of the node
    repaired : bool
        If the node is repaired or not
    reconstruction_cost : float
        Reconstruction cost of the node
    oversupply_penalty : float
        Penalty per supply unit  of the main commodity that is not used for the the node
    undersupply_penalty : float
        Penalty per demand unit  of the main commodity that is not satisfied for the the node
    demand : float
        Demand or supply value of the main commodity assigned to the node
    space : int
        The id of the geographical space where the node is
    resource_usage : dict
        The dictionary that shows how many resource (of each resource type) is employed to repair the node
    extra_com : dict
        The dictionary that shows demand, oversupply_penalty, and undersupply_penalty corresponding to commodities
        other than the main commodity
    """

    def __init__(self, id, net_id, local_id=""):
        self.id = id
        self.net_id = net_id
        if local_id == "":
            self.local_id = id
        self.local_id = local_id
        self.failure_probability = 0.0
        self.functionality = 1.0
        self.repaired = 1.0
        self.reconstruction_cost = 0.0
        self.oversupply_penalty = 0.0
        self.undersupply_penalty = 0.0
        self.demand = 0.0
        self.space = 0
        self.resource_usage = {}
        self.extra_com = {}

    def set_failure_probability(self, failure_probability):
        """
        This function sets the failure probability of the node

        Parameters
        ----------
        failure_probability : float
            Assigned failure probability of node

        Returns
        -------
        None.

        """
        self.failure_probability = failure_probability

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
        for m in extra_commodity:
            self.extra_com[m] = {
                "demand": 0,
                "oversupply_penalty": 0,
                "undersupply_penalty": 0,
            }

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
        This function checks if the node is in a given space or not

        Parameters
        ----------
        space_id :
            The id of the space that is checked

        Returns
        -------
            : bool
            Returns 1 if the node is in the space, and 0 otherwise.
        """
        if self.space == space_id:
            return 1
        else:
            return 0
