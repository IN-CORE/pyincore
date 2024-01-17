# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import math


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

    sa_pgv = "sapgv"
    pga_pgd = "pgapgd"
    pga_pga = "pgapga"
    sa_sa = "sasa"
    sa_sv = "sasv"
    sa_sd = "sasd"
    sd_sd = "sdsd"
    pgv_pgv = "pgvpgv"
    sv_sv = "svsv"

    units_percg = "%g"
    units_g = "g"

    # Metric
    units_m = "meters"
    units_m_abbr = "m"
    units_cm = "cm"
    units_cms = "cm/s"
    units_ins = "in/s"

    # Imperial
    units_in = "in"
    units_ft = "feet"
    units_ft_abbr = "ft"

    @staticmethod
    def convert_hazard(hazard_value, original_demand_units, requested_demand_units):
        converted_hazard_value = hazard_value
        if original_demand_units.lower() != requested_demand_units.lower():
            conversion = f"{original_demand_units.lower().replace('/', '')}_to_" \
                         f"{requested_demand_units.lower().replace('/', '')}"
            try:
                conversion_value = getattr(Units, conversion)
                converted_hazard_value = conversion_value * hazard_value
            except AttributeError:
                raise ValueError(f"We don't support the conversion from {original_demand_units} "
                                 f"to {requested_demand_units}")
        else:
            return converted_hazard_value

        return converted_hazard_value

    @staticmethod
    def convert_eq_hazard(hazard_value, from_unit, t, from_type, to_unit, to_type):
        if hazard_value is None:
            return None

        concat = from_type.lower() + to_type.lower()
        if concat == Units.sa_pgv.lower():
            pgv_from_sa = Units.convert_sa_to_pgv(hazard_value, from_unit)
            return Units.convert_eq_hazard_type(pgv_from_sa, Units.units_cms, 0.0, "PGV", to_unit, "PGV")
        elif concat == Units.pga_pga.lower():
            hazard_value = Units.get_correct_units_of_pga(hazard_value, from_unit, to_unit)
        elif concat == Units.sa_sa.lower():
            hazard_value = Units.get_correct_units_of_sa(hazard_value, from_unit, to_unit)
        elif concat == Units.sa_sd.lower():
            hazard_value = Units.convert_sa_to_sd(hazard_value, t, from_unit, to_unit)
        elif concat == Units.sa_sv.lower():
            hazard_value = Units.convert_sa_to_sv(hazard_value, t, from_unit, to_unit)
        elif concat == Units.sd_sd.lower():
            hazard_value = Units.get_correct_units_of_sd(hazard_value, from_unit, to_unit)
        elif concat == Units.pga_pgd.lower():
            hazard_value = Units.convert_pga_to_pgd(hazard_value, from_unit, to_unit)
        elif concat == Units.pgv_pgv.lower():
            hazard_value = Units.get_correct_units_of_pgv(hazard_value, from_unit, to_unit)
        elif concat == Units.sv_sv.lower():
            hazard_value = Units.get_correct_units_of_sv(hazard_value, from_unit, to_unit)

        if hazard_value is not None and not math.isnan(hazard_value):
            hazard_value = 0.0 if math.isinf(hazard_value) else hazard_value

        return hazard_value

    @staticmethod
    def convert_sa_to_pgv(sa_value, sa_unit):
        if sa_unit.lower() == Units.units_percg.lower():
            sa_value /= 100.0

        return ((386.4 * sa_value) / (2 * math.pi)) * 2.54 / 1.65

    @staticmethod
    def convert_pga_to_pgd(pga_value, pga_unit, pgd_unit):
        if pga_unit.lower() == Units.units_g.lower():
            pga_value *= 9.80
        elif pga_unit.lower() == Units.units_percg.lower():
            pga_value = pga_value * 9.8 / 100.0
        else:
            print("unknown units in converting PGA to PGD, returning base hazard value:", pga_value)
            return pga_value

        return Units.get_correct_units_of_pgd(Units._convert_pga_to_pgd_core(pga_value, 1.2, 0.5, 2.0), "m", pgd_unit)

    @staticmethod
    def _convert_pga_to_pgd_core(pga, s, t_c, t_d):
        return 0.025 * pga * s * t_c * t_d

    @staticmethod
    def convert_sa_to_sd(sa_value, t, sa_unit, sd_unit):
        sa_value = Units.get_correct_units_of_sa(sa_value, sa_unit, Units.units_g)
        return Units.get_correct_units_of_sd(sa_value * 9.78 * math.pow(t, 2) * 2.54, Units.units_cm, sd_unit)

    @staticmethod
    def convert_sa_to_sv(sa_value, t, sa_unit, sv_unit):
        sa_value = Units.get_correct_units_of_sa(sa_value, sa_unit, Units.units_g)
        return Units.get_correct_units_of_sv(sa_value * 9.8 * t / (2 * math.pi), Units.units_cms, sv_unit)

    @staticmethod
    def get_correct_units_of_sa(sa_value, from_unit, to_unit):
        if to_unit is not None and to_unit.lower() == from_unit.lower():
            return sa_value
        elif Units.units_g.lower() == to_unit.lower() and Units.units_percg.lower() == from_unit.lower():
            return sa_value / 100.0
        else:
            print("Unknown SA unit, returning unconverted sa value")
            return sa_value

    @staticmethod
    def get_correct_units_of_sd(sd_value, from_unit, to_unit):
        if to_unit is not None and to_unit.lower() == from_unit.lower():
            return sd_value
        elif Units.units_in.lower() == to_unit.lower() and Units.units_cm.lower() == from_unit.lower():
            return sd_value / 2.54
        elif Units.units_m_abbr.lower() == to_unit.lower() and Units.units_cm.lower() == from_unit.lower():
            return sd_value / 100.0
        elif Units.units_ft_abbr.lower() == to_unit.lower() and Units.units_cm.lower() == from_unit.lower():
            return sd_value / 30.48
        elif Units.units_cm.lower() == to_unit.lower() and Units.units_in.lower() == from_unit.lower():
            return sd_value * 2.54
        elif Units.units_m_abbr.lower() == to_unit.lower() and Units.units_in.lower() == from_unit.lower():
            return sd_value * 0.0254
        elif Units.units_ft_abbr.lower() == to_unit.lower() and Units.units_in.lower() == from_unit.lower():
            return sd_value / 12.0
        else:
            print("Unknown SD unit, returning unconverted sd_value value")
            return sd_value

    @staticmethod
    def get_correct_units_of_pga(pga_value, from_unit, to_unit):
        if to_unit is not None and to_unit.lower() == from_unit.lower():
            return pga_value
        elif to_unit.lower() == Units.units_g.lower() and from_unit.lower() == Units.units_percg.lower():
            return pga_value / 100.0
        else:
            print("Unknown PGA unit, returning unconverted pga value")
            return pga_value

    @staticmethod
    def get_correct_units_of_pgd(pgd_value, from_unit, to_unit):
        if from_unit is not None and from_unit.lower() == to_unit.lower():
            return pgd_value
        elif Units.units_m.lower() == from_unit.lower() or ("m".lower() == from_unit.lower() and Units.units_ft.lower()
                                                            == to_unit.lower()):
            return pgd_value * 3.2808399
        elif Units.units_m.lower() == from_unit.lower() or ("m".lower() == from_unit.lower() and
                                                            Units.units_cm.lower() == to_unit.lower()):
            return pgd_value * 100
        else:
            print("Unknown PGD unit, returning unconverted pgd value")
            return pgd_value

    @staticmethod
    def get_correct_units_of_sv(sv_value, from_unit, to_unit):
        if to_unit is not None and to_unit.lower() == from_unit.lower():
            return sv_value
        elif Units.units_ins.lower() == to_unit.lower() and Units.units_cms.lower() == from_unit.lower():
            return sv_value / 2.54
        elif Units.units_cms.lower() == to_unit.lower() and Units.units_ins.lower() == from_unit.lower():
            return sv_value * 2.54
        else:
            print("Unknown SV unit, returning unconverted sv value")
            return sv_value

    @staticmethod
    def get_correct_units_of_pgv(pgv_value, from_unit, to_unit):
        if to_unit is not None and to_unit.lower() == from_unit.lower():
            return pgv_value
        elif Units.units_ins.lower() == to_unit.lower() and Units.units_cms.lower() == from_unit.lower():
            return pgv_value / 2.54
        elif Units.units_cms.lower() == to_unit.lower() and Units.units_ins.lower() == from_unit.lower():
            return pgv_value * 2.54
        else:
            print("Unknown PGV unit, returning unconverted pgv value")
            return pgv_value

