# Copyright (c) 2024 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import numpy as np
import os
import pandas as pd

from pyincore import globals as pyglobals
from pyincore.client import IncoreClient
from pyincore.analyses.core_cge_ml import CoreCGEML
from pyincore.utils.cge_ml_file_util import CGEMLFileUtil

logger = pyglobals.LOGGER


class MlEnabledCgeGalveston(CoreCGEML):
    model = "Machine Learning Enabled Computable General Equilibrium - Galveston"

    # Coefficients files
    DDS_coefficients_file = "DDS_coefficients.csv"
    DY_coefficients_file = "DY_coefficients.csv"
    MIGT_coefficients_file = "MIGT_coefficients.csv"
    DFFD_coefficients_file = "DFFD_coefficients.csv"

    # Base value files
    DS_base_val_file = "DS_base_val.csv"
    GI_base_val_file = "GI_base_val.csv"
    HH_base_val_file = "HH_base_val.csv"
    FD_base_val_file = "FD_base_val.csv"

    Base_KAP_file = "baseKAP.csv"

    base_file_path = os.path.join(
        pyglobals.PYINCORE_PACKAGE_HOME,
        "analyses",
        "mlenabledcgegalveston",
    )

    model_filenames = {
        "ds": os.path.join(
            base_file_path,
            DDS_coefficients_file,
        ),
        "dy": os.path.join(
            base_file_path,
            DY_coefficients_file,
        ),
        "migt": os.path.join(
            base_file_path,
            MIGT_coefficients_file,
        ),
        "dffd": os.path.join(
            base_file_path,
            DFFD_coefficients_file,
        ),
    }

    filenames = [
        os.path.join(
            base_file_path,
            DS_base_val_file,
        ),
        os.path.join(
            base_file_path,
            GI_base_val_file,
        ),
        os.path.join(
            base_file_path,
            HH_base_val_file,
        ),
        os.path.join(
            base_file_path,
            FD_base_val_file,
        ),
        os.path.join(
            base_file_path,
            Base_KAP_file,
        ),
    ]

    def __init__(self, incore_client: IncoreClient):
        (
            sectors,
            base_cap_factors,
            base_cap,
            model_coeffs,
            cap_shock_sectors,
        ) = CGEMLFileUtil.parse_files(self.model_filenames, self.filenames)
        self.base_cap_factors = base_cap_factors
        self.base_cap = base_cap
        self.model_coeffs = model_coeffs
        self.cap_shock_sectors = cap_shock_sectors
        super(MlEnabledCgeGalveston, self).__init__(
            incore_client, sectors, labor_groups=[f"L{gp}" for gp in range(1, 5)]
        )  # 4 labor groups

    def run(self) -> bool:
        """Executes the ML enabled CGE model for Galveston"""

        logger.info(f"Running {self.model} model...")
        sector_shocks = pd.read_csv(
            self.get_input_dataset("sector_shocks").get_file_path("csv")
        )
        # arrange the capital shocks in the same order as the sectors
        shocks = []

        for sector in self.cap_shock_sectors:
            if sector.upper() not in [v.upper() for v in sector_shocks["sector"]]:
                # special case for galveston: if a sector from base cap is not in the shocks, add a unit shock. (No Loss)
                shocks.append(1.0)
            else:
                shocks.append(
                    sector_shocks.loc[
                        sector_shocks["sector"] == sector.upper(), "shock"
                    ].iloc[0]
                )
        capital_shocks = np.array(shocks, dtype=np.float64).reshape(1, -1)
        # logger.info(f"capital_shocks shape: {capital_shocks.shape}")

        super().run_core_cge_ml(
            self.base_cap,
            capital_shocks,
            self.model_coeffs,
            self.base_cap_factors,
        )
        logger.info(f"Running {self.model} model completed.")

        return True

    def get_spec(self):
        return {
            "name": "Galveston-cge",
            "description": "CGE model for Galveston.",
            "input_parameters": [
                {
                    "id": "result_name",
                    "required": False,
                    "description": "Result CSV dataset name prefix",
                    "type": str,
                }
            ],
            "input_datasets": [
                {
                    "id": "sector_shocks",
                    "required": True,
                    "description": "Aggregation of building functionality states to capital shocks per sector",
                    "type": ["incore:capitalShocks"],
                }
            ],
            "output_datasets": [
                {
                    "id": "domestic-supply",
                    "parent_type": "",
                    "description": "CSV file of resulting domestic supply",
                    "type": "incore:Employment",
                },
                {
                    "id": "gross-income",
                    "parent_type": "",
                    "description": "CSV file of resulting gross income",
                    "type": "incore:Employment",
                },
                {
                    "id": "pre-disaster-factor-demand",
                    "parent_type": "",
                    "description": "CSV file of factor demand before disaster",
                    "type": "incore:FactorDemand",
                },
                {
                    "id": "post-disaster-factor-demand",
                    "parent_type": "",
                    "description": "CSV file of resulting factor-demand",
                    "type": "incore:FactorDemand",
                },
                {
                    "id": "household-count",
                    "parent_type": "",
                    "description": "CSV file of household count",
                    "type": "incore:HouseholdCount",
                },
            ],
        }
