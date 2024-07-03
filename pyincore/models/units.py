# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


class Units:
    deg_to_rad = 0.0174533
    rad_to_deg = 57.2958

    ms_to_msec = 1
    msec_to_ms = 1
    ms_to_ins = 39.3701
    msec_to_ins = 39.3701
    ms_to_fts = 3.28084
    msec_to_fts = 3.28084
    ms_to_mph = 2.23694
    mps_to_mph = 2.23694
    msec_to_mph = 2.23694

    ins_to_msec = 0.0254
    ins_to_ms = 0.0254
    ins_to_fts = 0.0833333
    ins_to_mph = 0.0568182

    fts_to_msec = 0.3048
    fts_to_ms = 0.3048
    fts_to_ins = 12
    fts_to_mph = 0.681818

    mph_to_ins = 17.6
    mph_to_fts = 1.46667
    mph_to_ms = 0.44704
    mph_to_mps = 0.44704
    mph_to_msec = 0.44704

    m_to_cm = 100.0
    m_to_in = 39.3701
    m_to_ft = 3.28084

    in_to_cm = 2.54
    in_to_m = 0.0254
    in_to_ft = 0.0833333

    cm_to_m = 0.01
    cm_to_in = 0.3937
    cm_to_ft = 0.0328

    ft_to_cm = 30.48
    ft_to_in = 12
    ft_to_m = 0.3048

    hr_to_min = 60
    min_to_hr = 0.01666
    min_to_s = 60
    s_to_min = 0.01666
    hr_to_s = 3600
    s_to_hr = 0.00028

    @staticmethod
    def convert_hazard(hazard_value, original_demand_units, requested_demand_units):
        converted_hazard_value = hazard_value
        if original_demand_units.lower() != requested_demand_units.lower():
            conversion = (
                f"{original_demand_units.lower().replace('/', '')}_to_"
                f"{requested_demand_units.lower().replace('/', '')}"
            )
            try:
                conversion_value = getattr(Units, conversion)
                converted_hazard_value = conversion_value * hazard_value
            except AttributeError:
                raise ValueError(
                    f"We don't support the conversion from {original_demand_units} "
                    f"to {requested_demand_units}"
                )
        else:
            return converted_hazard_value

        return converted_hazard_value
