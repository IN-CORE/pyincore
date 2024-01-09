from typing import Tuple, List, Dict

import numpy as np
import os
import pandas as pd

from pyincore import globals as pyglobals
from pyincore.client import IncoreClient
from pyincore.analyses.core_cge_ml import CoreCGEML

logger = pyglobals.LOGGER


class MMSACGE(CoreCGEML):
    def __init__(self, incore_client: IncoreClient):
        sectors, base_cap_factors, base_cap, model_coeffs = self.parse_files()
        self.base_cap_factors = base_cap_factors
        self.base_cap = base_cap
        self.model_coeffs = model_coeffs
        super(MMSACGE, self).__init__(incore_client, sectors)

    def get_spec(self):
        return {
            'name': 'mmsa-shelby-cge-ml',
            'description': 'CGE ML model for MMSA Shelby County.',
            'input_parameters': [],
            'input_datasets': [
                {
                    'id': 'sector_shocks',
                    'required': True,
                    'description': 'Aggregation of building functionality states to capital shocks per sector',
                    'type': ['incore:capitalShocks']
                }
            ],
            'output_datasets': [
                {
                    'id': 'domestic-supply',
                    'parent_type': '',
                    'description': 'CSV file of resulting domestic supply',
                    'type': 'incore:Employment'
                },
                {
                    'id': 'gross-income',
                    'parent_type': '',
                    'description': 'CSV file of resulting gross income',
                    'type': 'incore:Employment'
                },
                {
                    'id': 'pre-disaster-factor-demand',
                    'parent_type': '',
                    'description': 'CSV file of factor demand before disaster',
                    'type': 'incore:FactorDemand'
                },
                {
                    'id': 'post-disaster-factor-demand',
                    'parent_type': '',
                    'description': 'CSV file of resulting factor-demand',
                    'type': 'incore:FactorDemand'
                },
                {
                    'id': 'household-count',
                    'parent_type': '',
                    'description': 'CSV file of household count',
                    'type': 'incore:HouseholdCount'
                }
            ]
        }

    def parse_base_vals(self, file_name: str) -> Tuple[List[np.ndarray], np.ndarray]:
        """parse_base_vals parse_base_vals will parse the base values from the input file and return them as numpy arrays

        Parameters
        ----------
        file_name : str
            Path to the .xlsx file containing the base values. It has to be organized in sheets starting from:
            1. Description
            2. Domestic Supply
            3. Gross Income
            4. Household Count
            5. Factor Demand
            6. Base Capital

        Returns
        -------
        Tuple[np.ndarray, np.ndarray]
            Tuple containing two numpy arrays. The first array is the base capital for different factors and the second is the base capital
        """
        logger.info(f"Parsing {file_name}")
        base_caps = pd.read_excel(file_name, sheet_name=[1, 2, 3, 4, 5])
        base_cap_factors: List[np.ndarray] = []
        base_cap: np.ndarray = np.array(base_caps[5]["baseKAP"]).reshape(
            1, -1
        )  # 1 x K array K = number of sectors in the model

        for i in range(1, 5):
            base_cap_factors.append(
                np.array(base_caps[i][0]).reshape(-1, 1)
            )  # k_i x 1 array k_i = number of sectors k for a factor i

        return base_cap_factors, base_cap

    def parse_coeff(
        self,
        filenames: Dict[str, str]
    ) -> Tuple[Dict[str, np.ndarray], Dict[str, List[str]]]:
        """parse_coeff Function to parse the model coefficients.

        Parameters
        ----------
        filenames : Dict[str, str]
            Dictionary containing the factor name and the path to the coefficient file

        Returns
        -------
        Tuple[Dict[str, np.ndarray], Dict[str, List[str]]]
            Tuple containing two dictionaries. The first dictionary contains the model coefficients for each factor and the second dictionary contains the sectors for each factor
        """
        model_coeffs: Dict[str, np.ndarray] = {}
        sectors: Dict[str, List[str]] = {}
        for factor, filename in filenames.items():
            logger.info(f"Parsing {filename}")
            model_coeff_df: pd.DataFrame = pd.read_csv(filename)
            sectors[factor] = list(model_coeff_df.columns[5:])
            model_coeffs[factor] = model_coeff_df[
                model_coeff_df.columns[4:]
            ].to_numpy()[
                1:, :
            ]  # skip the first row as it contains the total value model and its not needed in output

        return model_coeffs, sectors

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
        base_cap_factors, base_cap = self.parse_base_vals(os.path.join(pyglobals.PYINCORE_PACKAGE_HOME, "analyses", "mmsacge", "base_val_shelby_MMSA.xlsx"))
        model_filenames = {"ds": os.path.join(pyglobals.PYINCORE_PACKAGE_HOME, "analyses", "mmsacge", "DDS_coefficients.csv")}
        model_coeffs, sectors = self.parse_coeff(model_filenames)
        logger.info("Parsing input files completed.")
        
        return sectors, base_cap_factors, base_cap, model_coeffs

    def run_analysis(self) -> None:
        logger.info("Running MMSA CGE model...")
        sector_shocks = pd.read_csv(
            self.get_input_dataset("sector_shocks").get_file_path("csv")
        )
        # arrange the capital shocks in the same order as the sectors
        shocks = []
        for sector in self.sectors["ds"]:
            shocks.append(
                sector_shocks.loc[sector_shocks["sector"] == sector.upper()]["shock"]
            )
        capital_shocks = np.array(shocks).reshape(1, -1)
        super().run_core_cge_ml(
            self.base_cap, capital_shocks, self.model_coeffs, self.base_cap_factors[:1] # need to remove this slice for full release
        )
        logger.info("Running MMSA CGE model completed.")
