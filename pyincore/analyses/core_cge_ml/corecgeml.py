""" Core CGE ML """
from typing import List, Dict
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
        sectors: Dict[str, List[str]],
    ):
        super(CoreCGEML, self).__init__(incore_client)

        self.factors = [
            "domestic_supply",
            "gross_income",
            "household_count",
            "factor_demand",
        ]
        self.sectors = sectors
        self.labor_groups = ["L1", "L2", "L3"]

    def construct_output(self, predictions: dict) -> Dict[str, Dict[str, list]]:
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
        Dict[str, Dict[str, list]]
            A dictionary of 5 dictionaries.
        """
        constructed_outputs = {}
        if predictions.get("ds", None) is not None:
            constructed_outputs["ds"] = {
                "Sectors": self.sectors["ds"],
                "DS0": predictions["ds"]["before"],
                "DSL": predictions["ds"]["after"],
            }
        if predictions.get("gi", None) is not None:
            constructed_outputs["gi"] = {
                "Household Group": self.sectors["gi"],
                "Y0": predictions["gi"]["before"],
                "YL": predictions["gi"]["after"],
            }
        if predictions.get("hh", None) is not None:
            constructed_outputs["hh"] = {
                "Household Group": self.sectors["hh"],
                "HH0": predictions["hh"]["before"],
                "HHL": predictions["hh"]["after"],
            }
        if (
            predictions.get("prefd", None) is not None
            and predictions.get("postfd", None) is not None
        ):
            prefd = {
                "Labor Group": self.labor_groups,
            }
            postfd = {
                "Labor Group": self.labor_groups,
            }

            temp_prefd: Dict[str, list] = defaultdict(list)
            temp_postfd: Dict[str, list] = defaultdict(list)
            for i, fd_sector in enumerate(self.sectors["fd"]):
                sector, grp = fd_sector.split("_")
                temp_prefd[sector].push((grp, predictions["fd"]["before"][i]))
                temp_postfd[sector].push((grp, predictions["fd"]["after"][i]))

            for sector in temp_prefd.keys():
                prefd[sector] = [
                    x[1] for x in sorted(temp_prefd[sector], key=lambda x: x[0])
                ]
                postfd[sector] = [
                    x[1] for x in sorted(temp_postfd[sector], key=lambda x: x[0])
                ]

            constructed_outputs["prefd"] = prefd
            constructed_outputs["postfd"] = postfd

        return constructed_outputs

    def run_core_cge_ml(
        self,
        base_cap: np.ndarray,
        capital_shocks: np.ndarray,
        model_coeffs: Dict[str, np.ndarray],
        base_cap_factors: List[np.ndarray],
    ) -> None:
        """run_core_cge_ml will use the model coefficients to predict the change in capital stock for each sector.
        The predicted change will then be added to base_cap_factors to get the final capital stock for each sector after a disaster.
        The model requires capital stock loss in dollar amount, hence the base_cap will be used to calculate the loss in dollar amount.
        The capital_shocks is the percentage of capital stock that remains and hence to get the loss we use 1 - capital_shocks.

        Some variables for parameters:
        - n: number of factors
        - k_i: number of sectors (including subsectors) for factor i.
        - K: number of sectors (including subsectors) for input to model.
        - l_i: number of coefficients for a model for factor i.

        The length of model_coeffs == length of base_cap_factors == n.

        #TODO: Add detail about the length of base_cap being equal to K and l_i. Meaning K == l_i for i = 1, 2, ..., n.

        Parameters
        ----------
        base_cap : (1 X K) np.ndarray
           This is the base capital for each sector in dollar amount in Millions. This is a (1, K) array with K elements.
            The shape should match the shape of capital_shocks.
        capital_shocks : (1 X K) np.ndarray
            This is the capital shock for each sector in percentage. This is a (1, K) array with K elements.
        model_coeffs : Dict[str, np.ndarray]
            This is a dictionary of 2D arrays with shape [n, (k_i, l_i)]. Each entry in the dictionary corresponds to a factor and each factor has k_i number of models.
            It is assumed that the intercept term is included in the model coefficients and is at the 0th column.
        base_cap_factors : List[np.ndarray]
            This is a list of 1D array with each entry corresponding to a factor representing its base capital by sectors.
            This is the base capital for each sector for a given factor.
            The list would look like [(m_1, 1), (m_2, 1), ..., (m_n, 1)].
        """

        # check if the shape of base_cap and capital_shocks match
        if base_cap.shape != capital_shocks.shape:
            raise ValueError(
                "The shape of base_cap and capital_shocks do not match. Base Cap shape {}, Capital Shocks shape {}".format(
                    base_cap.shape, capital_shocks.shape
                )
            )

        # Convert capital_shocks to capital percent loss and then to capital loss in dollar amount
        capital_loss = (1 - capital_shocks) * base_cap

        # add a bias term to the capital loss with value 1 resulting in a shape of (1, 1+K)
        capital_loss = np.hstack((np.ones((1, 1)), capital_loss))

        assert len(model_coeffs) == len(
            base_cap_factors
        ), "The length of model_coeffs and base_cap_factors do not match. required length {}, observed length {}".format(
            len(model_coeffs), len(base_cap_factors)
        )

        predictions = {}
        for factor_base_cap_before, (factor, factor_model_coeff) in zip(
            base_cap_factors, model_coeffs.items()
        ):
            # multiply the capital loss with the model coefficients (k_i x 1) = (1, 1+K) . (k_i, l_i)
            factor_capital_loss: np.ndarray = capital_loss.dot(factor_model_coeff.T).T

            assert (
                factor_capital_loss.shape == factor_base_cap_before.shape
            ), "Number of sectors in models and base_cap_factors do not match. required shape {}, observed shape {}".format(
                factor_capital_loss[1:, :].shape, factor_base_cap_before.shape
            )
            # add the predicted change in capital stock to the base_cap_factors
            factor_base_cap_after: np.ndarray = (
                factor_base_cap_before + factor_capital_loss
            )

            predictions[factor] = {
                "before": np.squeeze(factor_base_cap_before).tolist(),
                "after": np.squeeze(factor_base_cap_after).tolist(),
            }

        constructed_outputs = self.construct_output(predictions)

        if constructed_outputs.get("ds", None) is not None:
            self.set_result_csv_data(
                "domestic-supply",
                pd.DataFrame(constructed_outputs["ds"]),
                name=self.get_parameter("domestic_supply_fname")
                if self.get_parameter("domestic_supply_fname") is not None
                else "domestic-supply",
                source="dataframe",
            )
        if constructed_outputs.get("gi", None) is not None:
            self.set_result_csv_data(
                "gross-income",
                pd.DataFrame(constructed_outputs["gi"]),
                name=self.get_parameter("gross_income_fname")
                if self.get_parameter("gross_income_fname") is not None
                else "gross-income",
                source="dataframe",
            )
        if constructed_outputs.get("hh", None) is not None:
            self.set_result_csv_data(
                "household-count",
                pd.DataFrame(constructed_outputs["hh"]),
                name=self.get_parameter("household_count_fname")
                if self.get_parameter("household_count_fname") is not None
                else "household-count",
                source="dataframe",
            )
        if constructed_outputs.get("prefd", None) is not None:
            self.set_result_csv_data(
                "pre-disaster-factor-demand",
                pd.DataFrame(constructed_outputs["prefd"]),
                name=self.get_parameter("pre_factor_demand_fname")
                if self.get_parameter("pre_factor_demand_fname") is not None
                else "pre-disaster-factor-demand",
                source="dataframe",
            )
        if constructed_outputs.get("postfd", None) is not None:
            self.set_result_csv_data(
                "post-disaster-factor-demand",
                pd.DataFrame(constructed_outputs["postfd"]),
                name=self.get_parameter("post_factor_demand_fname")
                if self.get_parameter("post_factor_demand_fname") is not None
                else "post-disaster-factor-demand",
                source="dataframe",
            )

        return True