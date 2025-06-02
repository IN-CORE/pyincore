from typing import Tuple, List, Dict

import numpy as np
import os
import pandas as pd

from pyincore import globals as pyglobals
from pyincore.client import IncoreClient
from pyincore.analyses.core_cge_ml import CoreCGEML
from pyincore.utils import parse_coeff, parse_base_vals

logger = pyglobals.LOGGER


class MMSACGE(CoreCGEML):
    DDS_coefficients_file = "DDS_coefficients.csv"
    DY_coefficients_file = "DY_coefficients.csv"
    MIGT_coefficients_file = "MIGT_coefficients.csv"
    DFFD_coefficients_file = "DFFD_coefficients.csv"

    DS_base_val_file = "DS_base_val.csv"
    GI_base_val_file = "GI_base_val.csv"
    HH_base_val_file = "HH_base_val.csv"
    FD_base_val_file = "FD_base_val.csv"

    Base_KAP_file = "baseKAP.csv"

    base_file_path = os.path.join(
        pyglobals.PYINCORE_PACKAGE_HOME, "analyses", "mmsacge"
    )

    def __init__(self, incore_client: IncoreClient):
        sectors, base_cap_factors, base_cap, model_coeffs = self.parse_files()
        self.base_cap_factors = base_cap_factors
        self.base_cap = base_cap
        self.model_coeffs = model_coeffs
        super(MMSACGE, self).__init__(incore_client, sectors)

    def get_spec(self):
        return {
            "name": "mmsa-shelby-cge-ml",
            "description": "CGE ML model for MMSA Shelby County.",
            "input_parameters": [
                {
                    "id": "domestic_supply_fname",
                    "required": False,
                    "description": "Name of the domestic supply output file with extension",
                    "type": str,
                },
                {
                    "id": "gross_income_fname",
                    "required": False,
                    "description": "Name of gross income output file with extension",
                    "type": str,
                },
                {
                    "id": "household_count_fname",
                    "required": False,
                    "description": "Name of the household count output file with extension",
                    "type": str,
                },
                {
                    "id": "pre_factor_demand_fname",
                    "required": False,
                    "description": "Name of the pre-factor demand output file with extension",
                    "type": str,
                },
                {
                    "id": "post_factor_demand_fname",
                    "required": False,
                    "description": "Name of the post-factor demand output file with extension",
                    "type": str,
                },
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

    def parse_files(
        self,
    ) -> Tuple[Dict[str, List[str]], np.ndarray, np.ndarray, Dict[str, np.ndarray]]:
        """parse_files Utility function to parse the input files

        Returns
        -------
        Tuple[Dict[str, List[str]], np.ndarray, np.ndarray, Dict[str, np.ndarray]]
            Returns a tuple containing the following:
            1. sectors: Dictionary containing the sectors for each factor
            2. base_cap_factors: List of numpy arrays containing the base capital for each factor
            3. base_cap: Numpy array containing the base capital
            4. model_coeffs: Dictionary containing the model coefficients for each factor
        """
        logger.info("Parsing input files...")
        model_filenames = {
            "ds": os.path.join(
                self.base_file_path,
                self.DDS_coefficients_file,
            )
        }
        model_coeffs, sectors, base_cap_sector_ordering = parse_coeff(model_filenames)
        filenames = [
            os.path.join(
                self.base_file_path,
                self.DS_base_val_file,
            ),
            os.path.join(
                self.base_file_path,
                self.GI_base_val_file,
            ),
            os.path.join(
                self.base_file_path,
                self.HH_base_val_file,
            ),
            os.path.join(
                self.base_file_path,
                self.FD_base_val_file,
            ),
            os.path.join(
                self.base_file_path,
                self.Base_KAP_file,
            ),
        ]

        base_cap_factors, base_cap = parse_base_vals(
            filenames, sectors["ds"], base_cap_sector_ordering
        )
        logger.info("Parsing input files completed.")

        return base_cap_sector_ordering, base_cap_factors, base_cap, model_coeffs

    def run_analysis(self) -> None:
        logger.info("Running MMSA CGE model...")
        sector_shocks = pd.read_csv(
            self.get_input_dataset("sector_shocks").get_file_path("csv")
        )
        # arrange the capital shocks in the same order as the sectors
        shocks = []
        for sector in self.sectors["ds"]:
            if sector.lower() not in [v.lower() for v in sector_shocks["sector"]]:
                raise ValueError(
                    f"Sector {sector} not found in the sector shocks file. Please make sure you have used the correct capital shocks"
                )
            shocks.append(
                sector_shocks.loc[sector_shocks["sector"] == sector.upper()]["shock"]
            )
        capital_shocks = np.array(shocks, dtype=np.float32).reshape(1, -1)
        super().run_core_cge_ml(
            self.base_cap,
            capital_shocks,
            self.model_coeffs,
            self.base_cap_factors[:1],  # need to remove this slice for full release
        )
        logger.info("Running MMSA CGE model completed.")
