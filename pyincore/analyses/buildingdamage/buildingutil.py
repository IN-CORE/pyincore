# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import math


class BuildingUtil:
    """Utility methods for the building damage analysis."""
    DEFAULT_FRAGILITY_KEY = "Non-Retrofit Fragility ID Code"
    DEFAULT_TSUNAMI_HMAX_FRAGILITY_KEY = "Non-Retrofit Inundation Fragility ID Code"
    DEFAULT_TSUNAMI_MMAX_FRAGILITY_KEY = "Non-Retrofit MomentumFlux Fragility ID Code"

    @staticmethod
    def get_building_period(num_stories, fragility_set):
        """Get building period from the fragility curve.

        Args:
            num_stories (int): Number of building stories.
            fragility_set (obj): A JSON description of fragility applicable to the bridge.

        Returns:
            float: Building period.

        """
        period = 0.0

        fragility_curve = fragility_set['fragilityCurves'][0]

        fragility_class_name = fragility_curve['className']
        if fragility_class_name in ['edu.illinois.ncsa.incore.service.dfr3.models.PeriodStandardFragilityCurve',
                                    'edu.illinois.ncsa.incore.service.dfr3.models.PeriodBuildingFragilityCurve']:

            period_equation_type = fragility_curve['periodEqnType']
            if period_equation_type == 1:
                period = fragility_curve['periodParam0']
            elif period_equation_type == 2:
                period = fragility_curve['periodParam0'] * num_stories
            elif period_equation_type == 3:
                period = \
                    fragility_curve['periodParam1'] * math.pow(fragility_curve['periodParam0'] * num_stories,
                                                               fragility_curve['periodParam2'])

        return period

    @staticmethod
    def get_hazard_demand_type(building, fragility_set, hazard_type):
        """Get hazard demand type.

        Args:
            building (obj): A JSON mapping of a geometric object from the inventory: current building.
            fragility_set (obj): A JSON description of fragility applicable to the building.
            hazard_type (str): A hazard type such as earthquake, tsunami etc.

        Returns:
            str: A hazard demand type.

        """
        fragility_hazard_type = fragility_set['demandType'].lower()
        hazard_demand_type = fragility_hazard_type

        if hazard_type.lower() == "earthquake":
            num_stories = building['properties']['no_stories']
            building_period = BuildingUtil.get_building_period(num_stories, fragility_set)

            if fragility_hazard_type.endswith('sa') and fragility_hazard_type != 'sa':
                # This fixes a bug where demand type is in a format similar to 1.0 Sec Sa
                if len(fragility_hazard_type.split()) > 2:
                    building_period = fragility_hazard_type.split()[0]
                    fragility_hazard_type = "Sa"

            hazard_demand_type = fragility_hazard_type

            # This handles the case where some fragilities only specify Sa, others a specific period of Sa
            if not hazard_demand_type.endswith('pga'):
                hazard_demand_type = str(building_period) + " " + fragility_hazard_type
        elif hazard_type.lower() == "tsunami":
            if hazard_demand_type == "momentumflux":
                hazard_demand_type = "mmax"
            elif hazard_demand_type == "inundationdepth":
                hazard_demand_type = "hmax"

        return hazard_demand_type
