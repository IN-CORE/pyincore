# Copyright (c) 2021 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import numpy as np


class JoplinEmpirRestorUtil:
    """Utility methods for the Joplin restoration analysis."""

    # Empirical coefficients mean and sigma for lognormal distribution
    FL_COEF = np.zeros((4, 4, 2), dtype=float)
    # initial functionality is FL1
    # target functionality is FL0
    FL_COEF[0, 0, :] = [5.90, 0.5]
    # other (for consistency)
    FL_COEF[1, 1, :] = [0.0, 1.0]
    FL_COEF[1, 2, :] = [0.0, 1.0]
    FL_COEF[1, 3, :] = [0.0, 1.0]

    # initial functionality is FL2
    # target functionality is FL0
    FL_COEF[1, 0, :] = [6.06, 0.32]
    # target functionality is FL1
    FL_COEF[1, 1, :] = [5.87, 0.35]
    # other (for consistency)
    FL_COEF[1, 2, :] = [0.0, 1.0]
    FL_COEF[1, 3, :] = [0.0, 1.0]

    # initial functionality is FL3
    # target functionality is FL0
    FL_COEF[2, 0, :] = [5.90, 0.60]
    # target functionality is FL1
    FL_COEF[2, 1, :] = [5.74, 0.55]
    # target functionality is FL2
    FL_COEF[2, 2, :] = [5.56, 0.46]
    # other (for consistency)
    FL_COEF[2, 3, :] = [0.0, 1.0]

    # initial functionality is FL4
    # target functionality is FL0
    FL_COEF[3, 0, :] = [6.60, 0.53]
    # target functionality is FL1
    FL_COEF[3, 1, :] = [6.39, 0.48]
    # target functionality is FL2
    FL_COEF[3, 2, :] = [6.49, 0.6]
    # target functionality is FL3
    FL_COEF[3, 3, :] = [6.13, 0.33]
