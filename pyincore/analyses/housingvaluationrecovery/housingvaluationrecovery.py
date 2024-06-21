# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import numpy as np
import pandas as pd

from pyincore import BaseAnalysis
from pyincore.analyses.housingvaluationrecovery.housingvaluationrecoveryutil import (
    HousingValuationRecoveryUtil,
)


class HousingValuationRecovery(BaseAnalysis):
    """The analysis predicts building values and value changes over time following a disaster event.
    The model is calibrated with respect to demographics, parcel data, and building value trajectories
    following Hurricane Ike (2008) in Galveston, Texas. The model predicts building value at the parcel
    level for 8 years of observation. The models rely on Census (Decennial or American Community Survey, ACS)
    and parcel data immediately prior to the disaster event (year -1) as inputs for prediction.

    The Galveston, TX example makes use of 2010 Decennial Census and Galveston County Appraisal District (GCAD)
    tax assessor data and outputs from other analysis (i.e., Building Damage, Housing Unit Allocation,
    Population Dislocation) .

    The CSV outputs of the building values for the 6 years following the disaster event (with year 0 being
    the impact year).

    Contributors
        | Science: Wayne Day, Sarah Hamideh
        | Implementation: Michal Ondrejcek, Santiago Núñez-Corrales, and NCSA IN-CORE Dev Team

    Related publications
        Hamideh, S., Peacock, W. G., & Van Zandt, S. (2018). Housing valuation recovery after disasters: Primary versus
        seasonal/vacation housing markets in coastal communities. Natural Hazards Review.

    Args:
        incore_client (IncoreClient): Service authentication.

    """

    def __init__(self, incore_client):
        super(HousingValuationRecovery, self).__init__(incore_client)

    def get_spec(self):
        return {
            "name": "housing-valuation-recovery",
            "description": "Housing Valuation Recovery Analysis",
            "input_parameters": [
                {
                    "id": "base_year",
                    "required": False,
                    "description": "Base year is used to calculate improvement age. It needs to be set to the tax "
                    "assessment year representing pre-disaster building values. For example for GCAD "
                    "data which represents improvement valuation before Hurricane Ike impacts."
                    "Deafult 2008",
                    "type": int,
                },
                {
                    "id": "result_name",
                    "required": True,
                    "description": "Result CSV dataset name",
                    "type": str,
                },
            ],
            "input_datasets": [
                {
                    "id": "population_dislocation",
                    "required": True,
                    "description": "Population Dislocation aggregated to the block group level",
                    "type": ["incore:popDislocation"],
                },
                {
                    "id": "building_area",
                    "required": True,
                    "description": "Building square footage and damage. Damage is the actual building value loss "
                    "in percentage terms observed through the County Appraisal District (GCAD) data",
                    "type": ["incore:buildingInventoryArea"],
                },
                {
                    "id": "census_block_groups_data",
                    "required": True,
                    "description": "Census ACS data, 2010 5yr data for block groups available at IPUMS NHGIS "
                    "website.",
                    "type": ["incore:censusBlockGroupsData"],
                },
                {
                    "id": "census_appraisal_data",
                    "required": True,
                    "description": "Census data, 2010 Decennial Census District (GCAD) Census data",
                    "type": ["incore:censusAppraisalData"],
                },
            ],
            "output_datasets": [
                {
                    "id": "result",
                    "description": "A csv file with the building values for the 6 years following the disaster"
                    "event (year -1 denotes pre-impact conditions and 0 being the impact year). "
                    "Index year values represent building values against a base, pre-impact value.",
                    "type": "incore:buildingValues",
                }
            ],
        }

    def run(self):
        """Executes the housing valuation recovery analysis.

        Returns:
            bool: True if successful, False otherwise.

        """
        hru = HousingValuationRecoveryUtil()

        # Get base year
        self.base_year = self.get_parameter("base_year")
        if self.base_year is None:
            self.base_year = hru.BASEYEAR
        # Get desired result name
        result_name = self.get_parameter("result_name")

        # Datasets
        pop_disl = self.get_input_dataset(
            "population_dislocation"
        ).get_dataframe_from_csv(low_memory=False)
        addl_structure_info = self.get_input_dataset(
            "building_area"
        ).get_dataframe_from_csv(low_memory=False)
        bg_mhhinc = self.get_input_dataset(
            "census_block_groups_data"
        ).get_dataframe_from_csv(low_memory=False)

        # Census data
        vac_status = self.get_input_dataset(
            "census_appraisal_data"
        ).get_dataframe_from_csv(low_memory=False)

        # Calculate the percent vacation or seasonal housing of all housing units within a census tract
        vac_status = self.get_vac_season_housing(vac_status)

        # Get ownership by filtering vacancy codes
        pop_disl["d_ownerocc"] = self.get_owneship(pop_disl)

        # Keep only parcels with 1 building
        building_level = pop_disl.loc[(pop_disl.bldgobs == 1)]
        single_family = building_level.loc[(building_level.d_sf == 1)]

        # Read in and clean block group level median household income
        bg_mhhinc["mhhinck"] = bg_mhhinc["mhhinc"] / 1000

        # Read in and clean additional building information, NOTE add to building inventory
        # Create structure id for merging data
        addl_structure_info["strctid"] = addl_structure_info["xref"].apply(
            lambda x: "XREF" + x
        )
        hse_recov = self.merge_add_inv(single_family, addl_structure_info)

        # Merge with seasonal/vacation housing Census ACS data
        hse_recov = self.merge_seasonal_data(hse_recov, vac_status)

        # Merge with BG median HH income
        hse_recov = self.merge_block_data(hse_recov, bg_mhhinc)

        # Generate minority variable
        hse_recov["pminoritybg"] = hse_recov["phispbg"] + hse_recov["pblackbg"]

        # Estimate value_loss for each parcel based on parameters from Bai, Hueste, & Gardoni (2009)
        hse_recov = self.value_loss(hse_recov)

        # Primary Housing Market (PHM)
        hse_rec_phm = self.assemble_phm_coefs(hru, hse_recov)
        # Seasonal/Vacation housing market (SVHM)
        hse_rec_svhm = self.assemble_svhm_coefs(hru, hse_recov)

        d_vac_np = np.tile(hse_recov["d_vacationct"], (8, 1)).T
        # Vacation condition for all years

        hse_rec_fin = np.empty(hse_recov.shape)
        hse_rec_fin[:] = np.NaN
        hse_rec_fin = np.where(d_vac_np == 0, np.exp(hse_rec_phm), np.NaN)
        hse_rec_fin = np.where(d_vac_np == 1, np.exp(hse_rec_svhm), hse_rec_fin)

        # Index building values against a pre-impact (-1) value
        hse_rec_fin_index = hse_rec_fin / hse_rec_fin[:, 0:1]

        # Name columns, use list of damage years (range from -1 to n).
        bval_yr = ["bval_year_{0}".format(i) for i in hru.DMG_YEARS]
        index_yr = ["index_{0}".format(i) for i in hru.DMG_YEARS]

        hse_rec_fin1 = pd.DataFrame(hse_rec_fin, columns=bval_yr)
        hse_rec_fin2 = pd.DataFrame(hse_rec_fin_index, columns=index_yr)
        hse_recov = pd.concat([hse_recov, hse_rec_fin1, hse_rec_fin2], axis=1)

        columns_to_save = (
            ["guid", "d_vacationct", "mhhinck", "pminoritybg", "dmg", "value_loss"]
            + bval_yr
            + index_yr
        )
        self.set_result_csv_data(
            "result", hse_recov[columns_to_save], result_name, "dataframe"
        )

        return True

    def get_owneship(self, popd):
        """Filter ownership based on the vacancy codes
            Assumption:
            Where ownershp is "missing", let vacancy codes 0/3/4 be considered owner-occupied,
            and 1/2/5/6/7 be considered renter-occupied.
            It is uncertain whether vacancy codes 3,4,5,6,7 will become owner- or renter-occupied or primarily
            one or the other.
        .
            Args:
                popd (pd.DataFrame): Population dislocation results with ownership information.

            Returns:
                pd.DataFrame: Ownership data.

        """
        # Create ownership dummy variable from popd.ownership
        own = np.where(popd["ownershp"].isnull() & popd["vacancy"] == 7, 0, np.nan)
        own = np.where(popd["ownershp"].isnull() & popd["vacancy"] == 6, 0, own)
        own = np.where(popd["ownershp"].isnull() & popd["vacancy"] == 5, 0, own)
        own = np.where(popd["ownershp"].isnull() & popd["vacancy"] == 2, 0, own)
        own = np.where(popd["ownershp"].isnull() & popd["vacancy"] == 1, 0, own)
        own = np.where(popd["ownershp"].isnull() & popd["vacancy"] == 4, 1, own)
        own = np.where(popd["ownershp"].isnull() & popd["vacancy"] == 3, 1, own)
        own = np.where(popd["ownershp"].isnull() & popd["vacancy"] == 0, 1, own)
        own = np.where(popd["ownershp"] == 2, 0, own)
        own = np.where(popd["ownershp"] == 1, 1, own)

        return own

    def get_vac_season_housing(self, vac_status):
        """Calculate the percent vacation or seasonal housing of all housing units within a census tract and
                add dummy variable for census tract as a seasonal/vacation housing submarket.
        .
                Args:
                    vac_status (obj): Seasonal/vacation housing Census ACS data from json reader.

                Returns:
                    pd.DataFrame: Seasonal/vacation housing data.

        """
        vac_status["B25004_006E"] = vac_status["B25004_006E"].astype(int)
        vac_status["B25004_006M"] = vac_status["B25004_006M"].astype(int)
        vac_status["B25002_001E"] = vac_status["B25002_001E"].astype(int)
        vac_status["B25002_001M"] = vac_status["B25002_001M"].astype(int)

        # Calculate the percent vacation or seasonal housing of all housing units within a census tract
        vac_status["pvacationct_moe"] = (
            vac_status["B25004_006E"] / vac_status["B25002_001E"]
        )
        vac_status["pvacationct"] = 100 * vac_status["pvacationct_moe"]
        vac_status["pvacationct_moe"] = (
            vac_status["pvacationct_moe"] ** 2 * vac_status["B25002_001M"] ** 2
        )
        vac_status["pvacationct_moe"] = (
            vac_status["B25004_006M"] ** 2 - vac_status["pvacationct_moe"]
        )
        vac_status["pvacationct_moe"] = (
            100 * (1 / vac_status["B25002_001E"]) * vac_status["pvacationct_moe"] ** 0.5
        )

        # dummy variable for census tract as a seasonal/vacation housing submarket
        vac_status["d_vacationct"] = np.where(vac_status["pvacationct"] >= 50, 1, 0)

        vac_status.sort_values(by="pvacationct", inplace=True, ascending=False)

        return vac_status

    def merge_add_inv(self, hse_rec, addl_struct):
        """Merge study area and additional structure information.
        .
                Args:
                    hse_rec (pd.DataFrame):  Area inventory.
                    addl_struct (pd.DataFrame):  Additional infrastructure inventory.

                Returns:
                    pd.DataFrame: Final merge of two inventories.

        """
        hse_rec_merged = pd.merge(hse_rec, addl_struct, on="strctid", how="inner")
        return hse_rec_merged

    def merge_seasonal_data(self, hse_rec, vac_status):
        """Merge study area and with seasonal/vacation housing Census ACS data.
        .
                Args:
                    hse_rec (pd.DataFrame): Area inventory.
                    vac_status (pd.DataFrame): Seasonal/vacation housing Census ACS data.

                Returns:
                    pd.DataFrame: Final merge of two inventories.

        """
        hse_rec["tractid"] = hse_rec["tractid"].astype(str)
        # Add county and state to trac to match hse_rec tracid (Galveston - 723900 to 48167723900)
        vac_status["tractid"] = (
            vac_status["state"].astype(str)
            + vac_status["county"].astype(str)
            + vac_status["tract"].astype(str)
        )

        hse_rec_merged = pd.merge(
            hse_rec, vac_status, left_on="tractid", right_on="tractid", how="inner"
        )
        return hse_rec_merged

    def merge_block_data(self, hse_rec, bg_mhhinc):
        """Merge block group level median household income.
        .
                Args:
                    hse_rec (pd.DataFrame):  Area inventory.
                    bg_mhhinc (pd.DataFrame):  Block data.

                Returns:
                    pd.DataFrame: Final merge of two inventories.

        """
        hse_rec_merged = pd.merge(
            hse_rec, bg_mhhinc, left_on="bgidstr", right_on="bgidstr", how="inner"
        )
        return hse_rec_merged

    def value_loss(self, hse_rec):
        """Estimate value_loss for each parcel based on parameters from Bai, Hueste, & Gardoni (2009).
        .
            Args:
                hse_rec (pd.DataFrame):  Area inventory.

            Returns:
                pd.DataFrame: Inventory with value losses.

        """
        hse_rec["value_loss"] = 100 * (
            hse_rec["DS_0"] * hse_rec["rploss_0"]
            + hse_rec["DS_1"] * hse_rec["rploss_1"]
            + hse_rec["DS_2"] * hse_rec["rploss_2"]
            + hse_rec["DS_3"] * hse_rec["rploss_3"]
        )
        return hse_rec

    def assemble_phm_coefs(self, hru, hse_rec):
        """Assemble Primary Housing Market (PHM) data for full inventory and all damage-related years.
        .
            Args:
                hru (obj): Housing valuation recovery utility.
                hse_rec (pd.DataFrame):  Area inventory including losses.

            Returns:
                np.array: Final coefficients for all damage years.

        """
        dmg_years = np.array(hru.DMG_YEARS)
        dmg_years_size = len(hru.DMG_YEARS)

        coef_fin = np.empty((hse_rec.shape[0], dmg_years_size))
        coef_fin[:] = hru.B_PHM_intercept + np.fromiter(
            hru.B_PHM_year.values(), dtype=float
        )

        # Adjust build year year with damage years
        yrbl_all = np.empty((hse_rec.shape[0], dmg_years_size))
        yrbl_all[:] = self.base_year + dmg_years + 1
        yrbuilt = hru.B_PHM_age * (
            yrbl_all - hse_rec["effyrbuilt"].to_numpy()[:, np.newaxis]
        )

        # Square meters, use vector (1x8) with B_PHM_sqm
        sqmeter = (
            np.full((1, dmg_years_size), hru.B_PHM_sqm)
            * hse_rec["sqmeter"].to_numpy()[:, np.newaxis]
        )

        if "dmg" in hse_rec.columns:
            dmg_loss = (
                np.fromiter(hru.B_PHM_dmg_year.values(), dtype=float)
                * hse_rec["dmg"].to_numpy()[:, np.newaxis]
            )
        else:
            dmg_loss = (
                np.fromiter(hru.B_PHM_dmg_year.values(), dtype=float)
                * hse_rec["value_loss"].to_numpy()[:, np.newaxis]
            )
        d_owner = (
            np.fromiter(hru.B_PHM_own_year.values(), dtype=float)
            * hse_rec["d_ownerocc"].to_numpy()[:, np.newaxis]
        )
        mhhinck = (
            np.fromiter(hru.B_PHM_inc_year.values(), dtype=float)
            * hse_rec["mhhinck"].to_numpy()[:, np.newaxis]
        )
        pminrbg = (
            np.fromiter(hru.B_PHM_min_year.values(), dtype=float)
            * hse_rec["pminoritybg"].to_numpy()[:, np.newaxis]
        )

        return coef_fin + yrbuilt + sqmeter + d_owner + dmg_loss + mhhinck + pminrbg

    def assemble_svhm_coefs(self, hru, hse_rec):
        """Assemble Seasonal/Vacation housing market (SVHM) data for full inventory and all damage-related years.
        .
            Args:
                hru (obj): Housing valution recovery utility.
                hse_rec (pd.DataFrame):  Area inventory including losses.

            Returns:
                np.array: Final coefficients for all damage years.

        """
        dmg_years = np.array(hru.DMG_YEARS)
        dmg_years_size = len(hru.DMG_YEARS)

        coef_fin = np.empty((hse_rec.shape[0], dmg_years_size))
        coef_fin[:] = hru.B_SVHM_intercept + np.fromiter(
            hru.B_SVHM_year.values(), dtype=float
        )

        # Adjust build year year with damage years
        yrbl_all = np.empty((hse_rec.shape[0], dmg_years_size))
        yrbl_all[:] = self.base_year + dmg_years + 1
        yrbuilt = hru.B_SVHM_age * (
            yrbl_all - hse_rec["effyrbuilt"].to_numpy()[:, np.newaxis]
        )

        # Square meters, use vector (1x8) with B_PHM_sqm
        sqmeter = (
            np.full((1, dmg_years_size), hru.B_SVHM_sqm)
            * hse_rec["sqmeter"].to_numpy()[:, np.newaxis]
        )

        if "dmg" in hse_rec.columns:
            dmg_loss = (
                np.fromiter(hru.B_SVHM_dmg_year.values(), dtype=float)
                * hse_rec["dmg"].to_numpy()[:, np.newaxis]
            )
        else:
            dmg_loss = (
                np.fromiter(hru.B_SVHM_dmg_year.values(), dtype=float)
                * hse_rec["value_loss"].to_numpy()[:, np.newaxis]
            )
        d_owner = (
            np.fromiter(hru.B_SVHM_own_year.values(), dtype=float)
            * hse_rec["d_ownerocc"].to_numpy()[:, np.newaxis]
        )
        mhhinck = (
            np.fromiter(hru.B_SVHM_inc_year.values(), dtype=float)
            * hse_rec["mhhinck"].to_numpy()[:, np.newaxis]
        )

        return coef_fin + yrbuilt + sqmeter + dmg_loss + d_owner + mhhinck
