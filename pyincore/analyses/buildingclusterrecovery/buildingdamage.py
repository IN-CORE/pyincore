# Copyright (c) 2018 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


class BuildingDamage(object):
    def __init__(
        self,
        distance_to_center,
        restricted_entry,
        restricted_use,
        reoccupancy,
        best_line_functionality,
        full_functionality,
    ):
        self.distance_to_center = distance_to_center
        self.restricted_entry = restricted_entry
        self.restricted_use = restricted_use
        self.reoccupancy = reoccupancy
        self.best_line_functionality = best_line_functionality
        self.full_functionality = full_functionality
