class WaterNetworkUtil:

    @staticmethod
    def convert_result_unit(result_unit, result):
        # convert to 1/m
        if result_unit.lower() == "repairs/1000ft":
            result =  result * (3.28 / 1000)

        return result