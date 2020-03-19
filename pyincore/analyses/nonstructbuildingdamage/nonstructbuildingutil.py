    # Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import collections

class NonStructBuildingUtil:
    """Utility methods for the non-structural building damage analysis."""
    BUILDING_FRAGILITY_KEYSBUILDING_FRAGILITY_KEYS = {
        "drift-sensitive fragility id code": ["Drift Sensitive", "DS"],
        "parametric non-retrofit fragility id code": ["Parametric Non-Retrofit", "PNR"],
        "acceleration-sensitive fragility id code": ["Acceleration Sensitive", "AS"],
        "non-retrofit fragility id code": ["as built", "none"]
    }

    DEFAULT_FRAGILITY_KEY_DS = "Drift-Sensitive Fragility ID Code"
    DEFAULT_FRAGILITY_KEY_AS = "Acceleration-Sensitive Fragility ID Code"

    @staticmethod
    def get_hazard_demand_type(building, fragility_set, hazard_type):
        """Get hazard demand type.

        Args:
            building (obj): A JSON mapping of a geometric object from the inventory: current building.
            fragility_set (obj): A JSON description of fragility applicable to the bridge.
            hazard_type (str): A hazard type such as earthquake, tsunami etc.

        Returns:
            str: A hazard demand type.

        """
        fragility_hazard_type = fragility_set.demand_type.lower()
        hazard_demand_type = fragility_hazard_type

        if hazard_type.lower() == "earthquake":
            num_stories = building['properties']['no_stories']
            building_period = fragility_set[0].get_building_period(num_stories)

            if fragility_hazard_type.endswith(
                    'sa') and fragility_hazard_type != 'sa':
                # This fixes a bug where demand type is in a format similar to 1.0 Sec Sa
                if len(fragility_hazard_type.split()) > 2:
                    building_period = fragility_hazard_type.split()[0]
                    fragility_hazard_type = "Sa"

            hazard_demand_type = fragility_hazard_type

            # This handles the case where some fragilities only specify Sa, others a specific period of Sa
            if not hazard_demand_type.endswith('pga'):
                hazard_demand_type = str(
                    building_period) + " " + fragility_hazard_type

        return hazard_demand_type

    @staticmethod
    def adjust_damage_for_liquefaction(limit_state_probabilities, ground_failure_probabilities):
        """Adjusts building damage probability based on liquefaction ground failure probability
        with the liq_dmg, we know that it is 3 values, the first two are the same.
        The 3rd might be different.
        We always want to apply the first two to all damage states except the highest.

        Args:
            limit_state_probabilities (obj): Limit state probabilities.
            ground_failure_probabilities (list): Ground failure probabilities.

        Returns:
            OrderedDict: Adjusted limit state probability.

        """
        keys = list(limit_state_probabilities.keys())
        adjusted_limit_state_probabilities = collections.OrderedDict()

        for i in range(len(keys)):
            # check and see...if we are trying to use the last ground failure
            # number for something other than the
            # last limit-state-probability, then we should use the
            # second-to-last probability of ground failure instead.

            if i > len(ground_failure_probabilities) -1:
                prob_ground_failure = ground_failure_probabilities[len(ground_failure_probabilities)-2]
            else:
                prob_ground_failure = ground_failure_probabilities[i]

            adjusted_limit_state_probabilities[keys[i]] = limit_state_probabilities[keys[i]] + prob_ground_failure \
                                                - limit_state_probabilities[keys[i]] * prob_ground_failure

        # the final one is the last of limitStates should match with the last of ground failures
        j = len(limit_state_probabilities) - 1
        prob_ground_failure = ground_failure_probabilities[-1]
        adjusted_limit_state_probabilities[keys[j]] = limit_state_probabilities[keys[j]] + prob_ground_failure \
                                            - limit_state_probabilities[keys[j]] * prob_ground_failure

        return adjusted_limit_state_probabilities