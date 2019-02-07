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