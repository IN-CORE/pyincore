from typing import Tuple, List, Dict

import pandas as pd
import numpy as np

from pyincore import globals as pyglobals

logger = pyglobals.LOGGER


class CGEMLFileUtil:
    "Utility class to parse the input files for the CGE-ML model"

    @staticmethod
    def parse_coeff(
        filenames: Dict[str, str]
    ) -> Tuple[Dict[str, np.ndarray], Dict[str, List[str]], Dict[str, List[str]]]:
        """parse_coeff Function to parse the model coefficients.

        Parameters
        ----------
        filenames : Dict[str, str]
            Dictionary containing the factor name and the path to the coefficient file

        Returns
        -------
        Tuple[Dict[str, np.ndarray], Dict[str, List[str]], Dict[str, List[str]]]
            Tuple containing three dictionaries. The first dictionary contains the model coefficients for
            each factor, the second dictionary contains the sectors for each factor, and the third dictionary
            contains the order of the sectors for each factor for models.
        """

        model_coeffs: Dict[str, np.ndarray] = {}
        sectors: Dict[str, List[str]] = {}
        base_cap_sector_order: Dict[str, List[str]] = {}

        for factor, filename in filenames.items():
            logger.info(f"Parsing {filename}")
            model_coeff_df: pd.DataFrame = pd.read_csv(filename)
            sectors[factor] = list(model_coeff_df.columns[5:])
            base_cap_sector_order[factor] = [
                s.split(" ")[-1].upper() for s in list(model_coeff_df["Model_Name"])[1:]
            ]
            model_coeffs[factor] = np.float64(
                model_coeff_df[model_coeff_df.columns[4:]].to_numpy()[1:, :]
            )  # skip the first row as it contains the total value model and its not needed in output
            # logger.info(f"factor: {factor} - model_coeff shape: {model_coeffs[factor].shape}")

        return model_coeffs, sectors, base_cap_sector_order

    @staticmethod
    def parse_csv(file_name: str, sectors: List[str]) -> np.ndarray:
        """parse_csv Utility function to parse the csv files

        Parameters
        ----------
        file_name : str
            Path to the csv file

        Returns
        -------
        np.ndarray
            Numpy array containing the data from the csv file
        """

        logger.info(f"Parsing {file_name}")
        df = pd.read_csv(file_name)

        col_name = df.columns[1]
        val_col = df.columns[2]

        # Convert 'sectors' column to categorical with the desired order
        df[col_name] = pd.Categorical(df[col_name], categories=sectors, ordered=True)

        # Sort the DataFrame based on the 'names' column
        df = df.sort_values(by=col_name)

        return np.array(df[val_col], dtype=np.float64)

    @staticmethod
    def parse_base_vals(
        filenames: List[str],
        ds_sectors: List[str],
        base_cap_sector_order: Dict[str, List[str]],
    ) -> Tuple[List[np.ndarray], np.ndarray]:
        """parse_base_vals parse_base_vals will parse the base values from the input file and return them as numpy arrays

        Parameters
        ----------
        filenames : List[str]
            Paths to the .csv files containing the base values. It has to be organized this order, starting from:
            1. Domestic Supply
            2. Gross Income
            3. Household Count
            4. Factor Demand
            5. Base Capital

        Returns
        -------

        Tuple[np.ndarray, np.ndarray]
            Tuple containing two numpy arrays. The first array is the base capital for different factors and the second is the base capital
        """

        base_cap_factors: List[np.ndarray] = []
        base_cap: np.ndarray = CGEMLFileUtil.parse_csv(
            filenames[-1], ds_sectors
        ).reshape(
            1, -1
        )  # 1 x K array K = number of sectors in the model
        # logger.info(f"base_cap shape: {base_cap.shape}")

        for filename, sector_order in zip(
            filenames[:-1], base_cap_sector_order.values()
        ):
            base_cap_factors.append(
                CGEMLFileUtil.parse_csv(filename, sector_order).reshape(-1, 1)
            )  # k_i x 1 array k_i = number of sectors k for a factor i
            # logger.info(f"{os.path.basename(filename)} shape: {base_cap_factors[-1].shape}")

        return base_cap_factors, base_cap

    @staticmethod
    def parse_files(
        model_filenames: Dict[str, str], filenames: List[str]
    ) -> Tuple[Dict[str, List[str]], np.ndarray, np.ndarray, Dict[str, np.ndarray]]:
        """parse_files Utility function to parse the input files

        Parameters
        ----------
        model_filenames : Dict[str, str]
            Dictionary containing the factor name and the path to the coefficient file
        filenames : List[str]
            Paths to the .csv files containing the base values. It has to be organized this order, starting from:
                1. Domestic Supply
                2. Gross Income
                3. Household Count
                4. Factor Demand
                5. Base Capital

        Returns
        -------
        Tuple[Dict[str, List[str]], np.ndarray, np.ndarray, Dict[str, np.ndarray]]
            Returns a tuple containing the following:
            1. sectors: Dictionary containing the sectors for each factor
            2. base_cap_factors: List of numpy arrays containing the base capital for each factor
            3. base_cap: Numpy array containing the base capital
            4. model_coeffs: Dictionary containing the model coefficients for each factor
            5. sectors["ds"]: List of sectors for the domestic supply
        """
        logger.info("Parsing input files...")

        model_coeffs, sectors, base_cap_sector_ordering = CGEMLFileUtil.parse_coeff(
            model_filenames
        )

        base_cap_factors, base_cap = CGEMLFileUtil.parse_base_vals(
            filenames, sectors["ds"], base_cap_sector_ordering
        )
        logger.info("Parsing input files completed.")

        return (
            base_cap_sector_ordering,
            base_cap_factors,
            base_cap,
            model_coeffs,
            sectors["ds"],
        )
