# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from deprecated.sphinx import deprecated

from pyincore.analyses.buildingnonstructuraldamage.buildingnonstructuraldamage import (
    BuildingNonStructDamage,
)


@deprecated(
    version="1.19.0",
    reason="This class will be deprecated soon. Use BuildingNonStructDamage instead.",
)
class NonStructBuildingDamage:
    def __init__(self, incore_client):
        self._delegate = BuildingNonStructDamage(incore_client)

    def __getattr__(self, name):
        """
        Delegate attribute access to the BuildingNonStructDamage instance.
        """
        return getattr(self._delegate, name)
