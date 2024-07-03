# Copyright (c) 2023 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from pyincore.analyses.indp.infrastructurearc import InfrastructureArc


class InfrastructureInterdepArc(InfrastructureArc):
    """
    This class models a physical interdependency between nodes from two different layers. This class inherits from
    :class:`InfrastructureArc`, where `source` attributes corresponds to the dependee node, and `dest` corresponds to
    the depender node. The depender node is non-functional if the corresponding dependee node is non-functional.

    Attributes
    ----------
    source_layer : int
        The id of the layer where the dependee node is
    dest_layer : int
        The id of the layer where the depender node is
    gamma : float
        The strength of the dependency, which is a number between 0 and 1.
    """

    def __init__(self, source, dest, source_layer, dest_layer, gamma):
        super(InfrastructureInterdepArc, self).__init__(
            source, dest, source_layer, True
        )
        self.source_layer = source_layer
        self.dest_layer = dest_layer
        self.gamma = gamma
