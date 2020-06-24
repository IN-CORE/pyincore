# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


class BridgeUtil:
    """Utility methods for the bridge damage analysis."""
    BRIDGE_FRAGILITY_KEYS = {
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

    DEFAULT_FRAGILITY_KEY = "Non-Retrofit Fragility ID Code"
    DEFAULT_TSUNAMI_HMAX_FRAGILITY_KEY = "Non-Retrofit inundationDepth Fragility ID Code"

    @staticmethod
    def get_retrofit_cost(target_fragility_key):
        """Calculates retrofit cost estimate of a bridge.

        Args:
            target_fragility_key (str): Fragility key describing the type of fragility.

        Note:
            This function is not completed yet. Need real data example on the following variable
            private FeatureDataset bridgeRetrofitCostEstimate

        Returns:
            float: Retrofit cost estimate.

        """
        retrofit_cost = 0.0
        if target_fragility_key.lower() == BridgeUtil.DEFAULT_FRAGILITY_KEY.lower():
            return retrofit_cost
        else:
            retrofit_code = BridgeUtil.get_retrofit_code(target_fragility_key)
        return retrofit_cost

    @staticmethod
    def get_retrofit_type(target_fragility_key):
        """Get retrofit type by looking up BRIDGE_FRAGILITY_KEYS dictionary.

        Args:
            target_fragility_key (str): Fragility key describing the type of fragility.

        Returns:
            str: A retrofit type.

        """
        return BridgeUtil.BRIDGE_FRAGILITY_KEYS[target_fragility_key.lower()][
            0] \
            if target_fragility_key.lower() in BridgeUtil.BRIDGE_FRAGILITY_KEYS else "none"

    @staticmethod
    def get_retrofit_code(target_fragility_key):
        """Get retrofit code by looking up BRIDGE_FRAGILITY_KEYS dictionary.

        Args:
            target_fragility_key (str): Fragility key describing the type of fragility.

        Returns:
            str: A retrofit code.

        """
        return BridgeUtil.BRIDGE_FRAGILITY_KEYS[target_fragility_key.lower()][
            1] \
            if target_fragility_key.lower() in BridgeUtil.BRIDGE_FRAGILITY_KEYS else "none"
