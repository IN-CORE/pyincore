from typing import Tuple, List, Dict

import pandas as pd
import numpy as np

from pyincore import globals as pyglobals

logger = pyglobals.LOGGER
from pprint import pprint


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
        base_cap_sector_order[factor] = [s.split(" ")[-1].upper() for s in list(model_coeff_df["Model_Name"])[1:]]
        model_coeffs[factor] = np.float32(model_coeff_df[model_coeff_df.columns[4:]].to_numpy()[
            1:, :
        ])  # skip the first row as it contains the total value model and its not needed in output

    return model_coeffs, sectors, base_cap_sector_order


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
        
    return np.array(df[val_col], dtype= np.float32)


def parse_base_vals(
    filenames: List[str], ds_sectors: List[str], base_cap_sector_order: Dict[str, List[str]]
) -> Tuple[List[np.ndarray], np.ndarray]:
    """parse_base_vals parse_base_vals will parse the base values from the input file and return them as numpy arrays

    Parameters
    ----------
    file_name : str
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
    base_cap: np.ndarray = parse_csv(filenames[-1], ds_sectors).reshape(
        1, -1
    )  # 1 x K array K = number of sectors in the model

    for filename, sector_order in zip(filenames[:-1], base_cap_sector_order.values()):
        base_cap_factors.append(
            parse_csv(filename, sector_order).reshape(-1, 1)
        )  # k_i x 1 array k_i = number of sectors k for a factor i

    return base_cap_factors, base_cap