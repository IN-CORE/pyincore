"""pyincore.analyses.epfdamage.epfutil

Copyright (c) 2017 University of Illinois and others.  All rights reserved.
This program and the accompanying materials are made available under the
terms of the BSD-3-Clause which accompanies this distribution,
and is available at https://opensource.org/licenses/BSD-3-Clause

"""


class EpfUtil:
    """Utility methods for the electric power facility damage analysis."""
    DEFAULT_FRAGILITY_KEY = "Non-Retrofit Fragility ID Code"

    @staticmethod
    def get_hazard_demand_type(fragility_set, hazard_type):
        """Run analysis for single epf (facility).

        Args:
            fragility_set (obj): Fragility set applied to the facility.
            hazard_type (obj): A single epf from input inventory set.

        Returns:
            obj: A string with hazard demand_type.

        """
        fragility_hazard_type = fragility_set['demandType'].lower()
        hazard_demand_type = fragility_hazard_type

        if hazard_type.lower() == "earthquake":
            hazard_demand_type = fragility_hazard_type

        return hazard_demand_type
