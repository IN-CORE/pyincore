# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from pyincore.analyses.bridgedamage import BridgeUtil


def test_bridge_damage_util():
    assert BridgeUtil.BRIDGE_FRAGILITY_KEYS == {
        "elastomeric bearing retrofit fragility id code": [
            "Elastomeric Bearing", "eb"],
        "steel jacket retrofit fragility id code": ["Steel Jacket", "sj"],
        "restrainer cables retrofit fragility id code": ["Restrainer Cables",
                                                         "rc"],
        "seat extender retrofit fragility id code": ["Seat Extender", "se"],
        "shear key retrofit fragility id code": ["Shear Key", "sk"],
        "non-retrofit fragility id code": ["as built", "none"],
        "non-retrofit inundationdepth fragility id code": ["as built", "none"]
    }

    assert BridgeUtil.DEFAULT_FRAGILITY_KEY == "Non-Retrofit Fragility ID Code"
    assert BridgeUtil.DEFAULT_TSUNAMI_HMAX_FRAGILITY_KEY == "Non-Retrofit inundationDepth Fragility ID Code"


def test_get_retrofit_cost():
    assert BridgeUtil.get_retrofit_cost(BridgeUtil.DEFAULT_FRAGILITY_KEY) == 0.0


def test_get_retrofit_type():
    assert BridgeUtil.get_retrofit_type(BridgeUtil.DEFAULT_FRAGILITY_KEY) == "as built"


def test_get_retrofit_code():
    assert BridgeUtil.get_retrofit_code(BridgeUtil.DEFAULT_FRAGILITY_KEY) == "none"
