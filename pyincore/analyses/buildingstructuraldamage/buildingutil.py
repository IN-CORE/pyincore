# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


class BuildingUtil:
    """Utility methods for the building damage analysis."""
    DEFAULT_FRAGILITY_KEY = "Non-Retrofit Fragility ID Code"
    DEFAULT_TSUNAMI_HMAX_FRAGILITY_KEY = "Non-Retrofit Inundation Fragility ID Code"
    DEFAULT_TSUNAMI_MMAX_FRAGILITY_KEY = "Non-Retrofit MomentumFlux Fragility ID Code"
    DEFAULT_REPAIR_KEY = "Repair ID Code"
    BLDG_STORIES = "no_stories"
    PROPERTIES = "properties"
    BLDG_PERIOD = "period"
    GROUND_FAILURE_PROB = "groundFailureProb"
