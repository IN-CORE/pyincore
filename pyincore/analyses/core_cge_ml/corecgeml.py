""" Core CGE ML """
from typing import List
from collections import defaultdict
import numpy as np
import pandas as pd

from pyincore import BaseAnalysis
from pyincore import globals as pyglobals

logger = pyglobals.LOGGER


class CoreCGEML(BaseAnalysis):
    """Core CGE ML"""

    def __init__(
        self,
        incore_client,
        ds_sector_list: list[str],
        hh_sector_list: list[str],
        fd_sector_list: list[str],
    ):
        super(CoreCGEML, self).__init__(incore_client)

        self.factors = [
            "domestic_supply",
            "gross_income",
            "household_count",
            "factor_demand",
        ]
        self.ds_sectors = ds_sector_list
        self.hh_sectors = hh_sector_list
        self.fd_sectors = fd_sector_list
        self.labor_groups = ["L1", "L2", "L3"]

    def construct_output(self, predictions: dict) -> tuple:
        """construct_output will construct the output in the format required by the pyincore.
        The output will be a tuple of 5 elements. Each element will be a dictionary according to the following format:
        - Domestic Supply:
            Sectors: list of domestic supply sectors
            DS0: domestic supply values before disaster
            DSL: domestic supply values after disaster
        - Gross Income:
            Household Group: list of houshold sectors
            Y0: Household income before disaster
            YL: Household income after disaster
        - Household Count:
            Household Group: list of houshold sectors
            HH0: Household count before disaster
            HHL: Household count after disaster
        - Pre-Disaster Factor Demand:
            Labor Group: list of labor groups
            sector1:
            sector2:
            .
            .
            .
            sectorN:
        - Post-Disaster Factor Demand:
            Labor Group: list of labor groups
            sector1:
            sector2:
            .
            .
            .
            sectorN:

        Parameters
        ----------
        predictions : dict
            This is a dictionary with keys as factors and values as a dictionary with keys "before" and "after".

        Returns
        -------
        tuple
            A tuple of 5 dictionaries.
        """
        ds = {
            "Sectors": self.ds_sectors,
            "DS0": predictions["domestic_supply"]["before"],
            "DSL": predictions["domestic_supply"]["after"],
        }
        gi = {
            "Household Group": self.hh_sectors,
            "Y0": predictions["gross_income"]["before"],
            "YL": predictions["gross_income"]["after"],
        }
        hh = {
            "Household Group": self.hh_sectors,
            "HH0": predictions["household_count"]["before"],
            "HHL": predictions["household_count"]["after"],
        }

        prefd = {
            "Labor Group": self.labor_groups,
        }
        postfd = {
            "Labor Group": self.labor_groups,
        }

        temp_prefd = defaultdict(list)
        temp_postfd = defaultdict(list)
        for i, fd_sector in enumerate(self.fd_sectors):
            sector, grp = fd_sector.split("_")
            temp_prefd[sector].push((grp, predictions["factor_demand"]["before"][i]))
            temp_postfd[sector].push((grp, predictions["factor_demand"]["after"][i]))

        for sector in temp_prefd.keys():
            prefd[sector] = [
                x[1] for x in sorted(temp_prefd[sector], key=lambda x: x[0])
            ]
            postfd[sector] = [
                x[1] for x in sorted(temp_postfd[sector], key=lambda x: x[0])
            ]

        return ds, gi, hh, prefd, postfd

    def run_core_cge_ml(
        self,
        base_cap: np.ndarray,
        capital_shocks: np.ndarray,
        model_coeffs: List[np.ndarray],
        base_cap_factors: List[np.ndarray],
    ) -> None:
        """run_core_cge_ml will use the model coefficients to predict the change in capital stock for each sector.
        The predicted change will then be added to base_cap_factors to get the final capital stock for each sector after a disaster.
        The model requires capital stock loss in dollar amount, hence the base_cap will be used to calculate the loss in dollar amount.
        The capital_shocks is the percentage of capital stock that remains and hence to get the loss we use 1 - capital_shocks.

        Some variables for parameters:
        - n: number of factors
        - m_i: number of sectors (including subsectors) for factor i.
        - K: number of sectors (including subsectors) for input to model.
        - l_i: number of coefficients for a model for factor i.

        The length of model_coeffs == length of base_cap_factors == n.

        #TODO: Add detail about the length of base_cap being equal to K and l_i. Meaning K == l_i for i = 1, 2, ..., n.

        Parameters
        ----------
        base_cap : (K x 1) np.ndarray
            This is the base capital for each sector in dollar amount in Millions. This is a (K, 1) array with K elements.
            The shape should match the shape of capital_shocks.
        capital_shocks : (K x 1) np.ndarray
            This is the capital shock for each sector in percentage. This is a (K, 1) array with K elements.
        model_coeffs : List[np.ndarray]
            This is a list of 2D arrays with shape [n, (m_i, l_i)]. Each entry in the list corresponds to a factor and each factor has m_i number of models.
            It is assumed that the intercept term is included in the model coefficients and is at the 0th column.
        base_cap_factors : List[np.ndarray]
            This is a list of 1D array with each entry corresponding to a factor representing its base capital by sectors.
            This is the base capital for each sector for a given factor.
            The list would look like [(m_1, 1), (m_2, 1), ..., (m_n, 1)].
        """

        # check if the shape of base_cap and capital_shocks match
        if base_cap.shape != capital_shocks.shape:
            raise ValueError("The shape of base_cap and capital_shocks do not match.")

        # Convert capital_shocks to capital percent loss and then to capital loss in dollar amount
        capital_loss = (1 - capital_shocks) * base_cap

        # add a bias term to the capital loss with value 1
        capital_loss = np.hstack((np.ones((1, 1)), capital_loss)).reshape(1, -1)

        assert (
            capital_loss.shape[1] == model_coeffs[0].shape[1]
        ), "The number of columns in capital_loss and model_coeffs[0] do not match. required shape [{},{}], observed shape [{},{}]".format(
            1, model_coeffs[0].shape[1], capital_loss.shape[0], capital_loss.shape[1]
        )

        assert len(model_coeffs) == len(
            base_cap_factors
        ), "The length of model_coeffs and base_cap_factors do not match. required length {}, observed length {}".format(
            len(model_coeffs), len(base_cap_factors)
        )

        predictions = {}
        for factor, factor_base_cap_before, factor_model_coeff in zip(
            self.factor, base_cap_factors, model_coeffs
        ):
            # multiply the capital loss with the model coefficients
            factor_capital_loss = capital_loss.dot(factor_model_coeff.T).T

            assert (
                factor_capital_loss[1:, :].shape == factor_base_cap_before.shape
            ), "Number of sectors in models and base_cap_factors do not match. required shape {}, observed shape {}".format(
                factor_capital_loss[1:, :].shape, factor_base_cap_before.shape
            )
            # add the predicted change in capital stock to the base_cap_factors
            factor_base_cap_after = factor_base_cap_before + factor_capital_loss[1:, :]

            predictions[factor] = {
                "before": np.squeeze(factor_base_cap_before).tolist(),
                "after": np.squeeze(factor_base_cap_after).tolist(),
            }

        ds, gi, hh, prefd, postfd = self.construct_output(predictions)

        self.set_result_csv_data(
            "domestic-supply",
            pd.DataFrame(ds),
            name="domestic-supply",
            source="dataframe",
        )
        self.set_result_csv_data(
            "pre-disaster-factor-demand",
            pd.DataFrame(prefd),
            name="pre-disaster-factor-demand",
            source="dataframe",
        )
        self.set_result_csv_data(
            "post-disaster-factor-demand",
            pd.DataFrame(postfd),
            name="post-disaster-factor-demand",
            source="dataframe",
        )
        self.set_result_csv_data(
            "gross-income", pd.DataFrame(gi), name="gross-income", source="dataframe"
        )
        self.set_result_csv_data(
            "household-count",
            pd.DataFrame(hh),
            name="household-count",
            source="dataframe",
        )
