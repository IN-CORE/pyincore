# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


class PipelineUtil:
    """Utility methods for pipeline analysis"""

    DEFAULT_EQ_FRAGILITY_KEY = "pgv"
    LIQ_FRAGILITY_KEY = "pgd"
    DEFAULT_TSU_FRAGILITY_KEY = "Non-Retrofit inundationDepth Fragility ID Code"

    @staticmethod
    def convert_result_unit(result_unit: str, result: float):
        """Convert values between different units.

        Args:
            result_unit (str): Resulting unit.
            result (float): Input value.

        Returns:
            float: Converted value.

        """

        if result_unit.lower() == "repairs/km":
            return result
        elif result_unit.lower() == "repairs/1000ft":
            return result / 0.3048

        print("Result type was not found so we didn't change it.  For pipes, all results should convert from their "
              "unit type into Repairs per Kilometer for uniform results.  We found a result type of " + result_unit)
        return result

    @staticmethod
    def get_pipe_length(pipeline):
        """Get pipe length.

        Args:
            pipeline (obj): A JSON-like description of pipeline properties.

        Returns:
            float: Pipe length.

        """
        pipe_length = 0.0

        if 'pipelength' in pipeline['properties']:
            pipe_length = float(pipeline['properties']['pipelength'])
        elif 'length_km' in pipeline['properties']:
            pipe_length = float(pipeline['properties']['length_km'])
        elif 'length' in pipeline['properties']:
            pipe_length = float(pipeline['properties']['length'])
        else:
            print("Pipeline has no length attribute")

        return pipe_length

    @staticmethod
    def get_pipe_diameter(pipeline):
        """Get pipe diameter.

        Args:
            pipeline (obj): A JSON-like description of pipeline properties.

        Returns:
            float: Pipe diameter.

        """
        diameter = 0.0
        if 'diameter' in pipeline['properties']:
            diameter = float(pipeline['properties']['diameter'])

        return diameter
