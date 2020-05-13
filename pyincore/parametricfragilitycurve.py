# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import math

from pyincore.dfr3curve import DFR3Curve


class ParametricFragilityCurve(DFR3Curve):

    def __init__(self, curve_parameters):
        # TODO: not sure if i need to define a class of parameters with "name", "unit", "coefficient" and
        #  "interceptTermDefault" as fixed fields; is it going to be over complicated?
        self.parameters = curve_parameters['parameters']
        self.curve_type = curve_parameters['curveType']

        super(ParametricFragilityCurve, self).__init__(curve_parameters)

    def calculate_logit_limit_state_probability(self, hazard, constant=1, fc=33.78, fy=459.436160679934, ebl=-3.22,
                                                ebt=-2.3, fbl=-1.56, fbt=0.99, pass_stf=21.545, act_stf=177795,
                                                rot_stf=175000, trns_stf=222245, damp=0.045, abt_gp_l1=38.1,
                                                abt_gp_l2=38.1, hng_gp_l1=25.4, hng_gp_l2=25.4, spn_ln=13950,
                                                col_ht=4070, width=6350, **kwargs):
        """

        Args:
            hazard: intercept terms. Unit: g
            constant: intercept terms
            fc: intercept terms. Unit: MPa
            fy: intercept terms. Unit: MPa
            ebl: intercept terms
            ebt: intercept terms
            fbl: intercept terms
            fbt: intercept terms
            pass_stf: intercept terms. Unit: N/mm/mm
            act_stf: intercept terms. Unit: N/pile
            rot_stf: intercept terms. Unit: N/mm/pile
            trns_stf: intercept terms
            damp: intercept terms
            abt_gp_l1: intercept terms
            abt_gp_l2: intercept terms
            hng_gp_l1: intercept terms
            hng_gp_l2: intercept terms
            spn_ln: intercept terms
            col_ht: intercept terms
            width: intercept terms
            **kwargs: in case other logit curve with other parameters and coefficient other than the above 19 has
            been defined

        Returns: pf (DS) = exp(X*theta')/(1+exp(X*theta'));
        example: pf(DS) = EXP(1 * A0 + log(PGA) * A1 + A2*X2 + ...) / (1 + EXP(1 *A0 + log(PGA) * A1 + ...))
        """
        probability = float(0.0)

        # X*theta'
        cumulate_term = 0
        for parameter_set in self.parameters:
            name = parameter_set["name"].lower()
            coefficient = parameter_set["coefficient"]
            if name == "constant":
                cumulate_term += constant * coefficient
            elif name == "demand":
                cumulate_term += math.log(hazard) * coefficient
            elif name == "fc":
                cumulate_term += fc * coefficient
            elif name == "fy":
                cumulate_term += fy * coefficient
            elif name == "ebl":
                cumulate_term += math.log(ebl) * coefficient
            elif name == "ebt":
                cumulate_term += math.log(ebt) * coefficient
            elif name == "fbl":
                cumulate_term += math.log(fbl) * coefficient
            elif name == "fbt":
                cumulate_term += math.log(fbt) * coefficient
            elif name == "pass_stf":
                cumulate_term += pass_stf * coefficient
            elif name == "act_stf":
                cumulate_term += act_stf * coefficient
            elif name == "rot_stf":
                cumulate_term += rot_stf * coefficient
            elif name == "trns_stf":
                cumulate_term += trns_stf * coefficient
            elif name == "damp":
                cumulate_term += damp * coefficient
            elif name == "abt_gp_l1":
                cumulate_term += abt_gp_l1 * coefficient
            elif name == "abt_gp_l2":
                cumulate_term += abt_gp_l2 * coefficient
            elif name == "hng_gp_l1":
                cumulate_term += hng_gp_l1 * coefficient
            elif name == "hng_gp_l2":
                cumulate_term += hng_gp_l2 * coefficient
            elif name == "spn_ln":
                cumulate_term += spn_ln * coefficient
            elif name == "col_ht":
                cumulate_term += col_ht * coefficient
            elif name == "width":
                cumulate_term += width * coefficient
            else:
                # TODO deal with the kwargs
                pass

        probability = math.exp(cumulate_term) / (1 + math.exp(cumulate_term))

        return probability
