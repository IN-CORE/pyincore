# Copyright (c) 2023 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


class InfrastructureSpace(object):
    """
    This class models a geographical space.

    Attributes
    ----------
    id : int
        The id of the space
    cost : float
        The cost of preparing the space for a repair action
    """

    def __init__(self, id, cost):
        self.id = id
        self.cost = cost
