# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from pyincore.analyses.buildingdamage import BuildingUtil


def test_building_damage_util():
    assert BuildingUtil.DEFAULT_FRAGILITY_KEY == "Non-Retrofit Fragility ID Code"
    assert BuildingUtil.DEFAULT_TSUNAMI_HMAX_FRAGILITY_KEY == "Non-Retrofit Inundation Fragility ID Code"
    assert BuildingUtil.DEFAULT_TSUNAMI_MMAX_FRAGILITY_KEY == "Non-Retrofit MomentumFlux Fragility ID Code"
    assert BuildingUtil.BLDG_STORIES == "no_stories"
    assert BuildingUtil.PROPERTIES == "properties"
    assert BuildingUtil.BLDG_PERIOD == "period"
