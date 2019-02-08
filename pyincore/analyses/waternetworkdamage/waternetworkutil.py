"""

Copyright (c) 2019 University of Illinois and others.  All rights reserved.
This program and the accompanying materials are made available under the
terms of the Mozilla Public License v2.0 which accompanies this distribution,
and is available at https://www.mozilla.org/en-US/MPL/2.0/

"""

class WaterNetworkUtil:

    @staticmethod
    def convert_result_unit(result_unit, result):
        """
        convert result unit from ft to meter
        Args:
            result_unit: the unit of the result to be converted
            result: converted number

        Returns:

        """
        # convert to 1/m
        if result_unit.lower() == "repairs/1000ft":
            result =  result * (3.28 / 1000)

        return result