# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import requests
import numpy as np
import pandas as pd
from pyincore import BaseAnalysis
from pyincore.analyses.housingrecovery.housingrecoveryutil import HousingRecoveryUtil


class HousingRecovery(BaseAnalysis):
    """ The analysis predicts building values and value changes over time following a disaster event.
    The model is calibrated with respect to demographics, parcel data, and building value trajectories
    following Hurricane Ike (2008) in Galveston, Texas. The model predicts building value at the parcel
    level for 8 years of observation. The models rely on Census (Decennial or American Community Survey, ACS)
    and parcel data immediately prior to the disaster event (year -1) as inputs for prediction.

    The Galveston, TX example makes use of 2010 Decennial Census and Galveston County Appraisal District (GCAD) tax assessor data and outputs from other analysis (i.e., Building Damage, Housing Unit Allocation, Population Dislocation) .

    The CSV outputs of the building values for the 6 years following the disaster event (with year 0 being the impact year).

    Contributors
        | Science: Wayne Day, Sarah Hamideh
        | Implementation: Michal Ondrejcek, Santiago Núñez-Corrales, and NCSA IN-CORE Dev Team

    Related publications
        Hamideh, S., Peacock, W. G., & Van Zandt, S. (2018). Housing recovery after disasters: Primary versus
        seasonal/vacation housing markets in coastal communities. Natural Hazards Review.

    Args:
        incore_client (IncoreClient): Service authentication.

    """
    def __init__(self, incore_client):
        super(HousingRecovery, self).__init__(incore_client)

    def get_spec(self):
        return {
            "name":"housing-recovery",
            "description":"Housing Recovery Analysis",
            "input_parameters": [
                {
                   "id":"result_name",
                   "required": True,
                   "description":"Result CSV dataset name",
                   "type": str
                }
            ],
            "input_datasets": [
                # {
                #    "id":"building_dmg",
                #    "required": True,
                #    "description":"Structural building damage",
                #    "type": ["ergo:buildingDamageVer6"],
                # },
                {
                   "id":"population_dislocation",
                   "required": True,
                   "description":"Population Dislocation aggregated to the block group level",
                   "type": ["incore:popDislocation"]
                },
                {
                   "id": "building_area",
                   "required": True,
                   "description": "Building square footage, temporary",
                   "type": ["incore:buildingInventoryArea"]
                },
                {
                   "id":"census_block_groups_data",
                   "required": True,
                   "description":"Census ACS data, 2010 5yr data for block groups available at IPUMS NHGIS"
                                 "web site.",
                   "type": ["incore:censusBlockGroupsData"]
                },
                {
                   "id":"census_appraisal_data",
                   "required": False,
                   "description":"Census data, 2010 Decennial Census"
                                  "District (GCAD) Census data",
                   "type": ["incore:censusAppraisalData"]
                }
            ],
           "output_datasets": [
                {
                   "id":"result",
                   "description":"A csv file with the building values for the 6 years following the disaster"
                                  "event (with year 0 being the impact year)",
                   "type":"incore:buildingValues"
                }
            ]
        }

    def run(self):
        """Merges Building damage, Population dislocation and Census data

        Returns:
            bool: True if successful, False otherwise

        """
        # Get desired result name
        result_name = self.get_parameter("result_name")

        # Datasets
        # bldg_dmg_df = self.get_input_dataset("building_dmg").get_dataframe_from_csv(low_memory=False)
        pd_df = self.get_input_dataset("population_dislocation").get_dataframe_from_csv(low_memory=False)

        addl_structure_info_df = self.get_input_dataset("building_area").get_dataframe_from_csv(low_memory=False)
        bg_mhhinc_df = self.get_input_dataset("census_block_groups_data").get_dataframe_from_csv(low_memory=False)
        vac_status = self.get_input_dataset("census_appraisal_data").get_json_reader()

        # Calculate the percent vacation or seasonal housing of all housing units within a census tract
        vac_status_df = self.get_vac_season_housing(vac_status)
        # print(vac_status_df.head(len(vac_status_df.index)))

        # Almost 12,670 of 32,501 housing units are considered vacant. 13 of these are actually not vacant,
        # but are not assinged as renter- or owner-occupied.
        #
        # Assumption: Where ownershp is "missing", let vacancy codes 0/3/4 be considered owner-occupied,
        # and 1/2/5/6/7 be considered renter-occupied. It is uncertain whether vacancy codes 3,4,5,6,7 will
        # become owner- or renter-occupied or primarily one or the other.

        # create ownership dummy variable from pd_df.ownership
        pd_df["d_ownerocc"] = np.where(pd_df["ownershp"] == 1, 1,
                              np.where(pd_df["ownershp"] == 2, 0,
                              np.where(pd_df["ownershp"].isnull() & pd_df["vacancy"] == 0, 1,
                              np.where(pd_df["ownershp"].isnull() & pd_df["vacancy"] == 3, 1,
                              np.where(pd_df["ownershp"].isnull() & pd_df["vacancy"] == 4, 1,
                              np.where(pd_df["ownershp"].isnull() & pd_df["vacancy"] == 1, 0,
                              np.where(pd_df["ownershp"].isnull() & pd_df["vacancy"] == 2, 0,
                              np.where(pd_df["ownershp"].isnull() & pd_df["vacancy"] == 5, 0,
                              np.where(pd_df["ownershp"].isnull() & pd_df["vacancy"] == 6, 0,
                              np.where(pd_df["ownershp"].isnull() & pd_df["vacancy"] == 7, 0, np.nan))))))))))

        # from the population dislocation result dataset, keep only parcels with 1 building
        building_level = pd_df.loc[(pd_df.bldgobs == 1)]
        single_family = building_level.loc[(building_level.d_sf == 1)]
        # single_family.drop("Unnamed: 0", axis=1, inplace=True)

        # Identify housing submarkets
        # In Galveston
        # - Urban Core is the considered the primary housing market.
        # - Galveston Island and Bolivar Island both have seasonal/vacation housing markets for secondary
        #   homes or vacation rentals. Bolivar Island is considered vacation  entirely.

        # lists of census tracts according to Hamideh et al 2018
        hru = HousingRecoveryUtil()
        # urban_core_tracts = hru.urban_core_tracts
        # galveston_island_vacation_tracts_east = hru.galveston_island_vacation_tracts_east
        # galveston_island_vacation_tracts_west = hru.galveston_island_vacation_tracts_west
        # bolivar_island_vacation_tracts = hru.bolivar_island_vacation_tracts
        #
        # For application in other communities, a seasonal/vacation submarket is determined
        # when the percentage of homes designated as "For seasonal, recreational, or occasional use" within
        # a Census Tract is greater than or equal to 50 percent using Census ACS 5-year data.

        # keep only observations located in urban core, galveston island vacation, and
        # bolivar island vacation census tracts
        # urban_core_sf = single_family.loc[(single_family.tractid.isin(urban_core_tracts))]
        # galveston_island_vacation_east_sf = single_family.loc[(single_family.tractid.isin(galveston_island_vacation_tracts_east))]
        # galveston_island_vacation_west_sf = single_family.loc[(single_family.tractid.isin(galveston_island_vacation_tracts_west))]
        # bolivar_island_vacation_sf = single_family.loc[(single_family.tractid.isin(bolivar_island_vacation_tracts))]

        # create studyarea variable for each study area
        # urban_core_sf.loc[:, "studyarea_code_orig"] = 2
        # urban_core_sf.loc[:, "studyarea_desc_orig"] = "Galveston - Urban Core"
        #
        # galveston_island_vacation_east_sf.loc["studyarea_code_orig"] = 1
        # galveston_island_vacation_east_sf.loc["studyarea_desc_orig"] = "Galveston - East End"
        # galveston_island_vacation_west_sf.loc["studyarea_code_orig"] = 3
        # galveston_island_vacation_west_sf.loc["studyarea_desc_orig"] = "Galveston - West End"
        # bolivar_island_vacation_sf.loc["studyarea_code_orig"] = 3
        # bolivar_island_vacation_sf.loc["studyarea_desc_orig"] = "Bolivar Island Vacation"
        #
        # # append study area dataframes together
        # studyarea_sf = urban_core_sf.append(galveston_island_vacation_east_sf, ignore_index=True).\
        #     append(galveston_island_vacation_west_sf, ignore_index=True).\
        #     append(bolivar_island_vacation_sf, ignore_index=True)

        # show relevant data from population dislocation result
        # print(studyarea_sf[["guid", "addrptid", "strctid", "tractid", "studyarea_code_orig", "studyarea_desc_orig",
        #               "DS_0", "DS_1", "DS_2", "DS_3", "rploss_0", "rploss_1", "rploss_2", "rploss_3",
        #               "bgid", "d_ownerocc","pblackbg", "phispbg","d_sf"]].head())
        # add tractid variable
        # print(vac_status_df)
        # urban_core_sf["tractid"] = vac_status_df.state.str.cat(others=[vac_status_df.county, vac_status_df.tract])

        # print(vac_status_df.head())
        # print(vac_status_df.describe())

        # Read in & clean block group level median household income
        bg_mhhinc_df["mhhinck"] = bg_mhhinc_df["mhhinc"] / 1000
        # print(bg_mhhinc_df.head())

        # Read in & clean additional building information, NOTE add to building inventory
        # Create structure id for merging data
        addl_structure_info_df["strctid"] = addl_structure_info_df["xref"].apply(lambda x : "XREF"+x)
        # print(addl_structure_info_df["strctid"].describe())

        # show list of columns in dataframe
        # print(addl_structure_info_df.head())

        # Merge population dislocation result, Hamideh et al (2018) dataset, and seasonal/vacation
        # housing Census ACS data datasets

        # Galveston
        # hse_recov_df = studyarea_sf

        hse_recov_df = single_family
        hse_recov_df =  self.merge_add_inv(hse_recov_df, addl_structure_info_df)
        # print(hse_recov_df["strctid"].describe())
        # 16,495 of 23,285

        # merge with seasonal/vacation housing Census ACS data
        hse_recov_df = self.merge_seasonal_data(hse_recov_df, vac_status_df)

        # show list of columns in dataframe
        # print(hse_recov_df.columns)
        # print(hse_recov_df.head(len(hse_recov_df.index)))

        # merge with BG median HH income
        hse_recov_df = self.merge_block_data(hse_recov_df, bg_mhhinc_df)

        hse_recov_df["FIPScounty"] = hse_recov_df["FIPScounty"].astype(str)
        # print(hse_recov_df["FIPScounty"].describe())

        # generate minority variable
        hse_recov_df["pminoritybg"] = hse_recov_df["phispbg"] + hse_recov_df["pblackbg"]

        # Estimate value_loss for each parcel based on parameters from Bai, Hueste, & Gardoni (2009)
        hse_recov_value_loss = self.value_loss(hse_recov_df)

        print(hse_recov_value_loss[["strctid", "bv_2008", "DS_0", "DS_1", "DS_2", "DS_3", "rploss_0", "rploss_1", "rploss_2", "rploss_3", "value_loss","dmg"]].head())
        # compare value_loss and dmg
        print(hse_recov_value_loss[["dmg", "value_loss", "DS_0", "DS_1", "DS_2", "DS_3", "rploss_0", "rploss_1", "rploss_2", "rploss_3"]].describe())
        print(hse_recov_value_loss[["strctid", "value_loss", "effyrbuilt", "sqmeter", "d_ownerocc", "bgid", "mhhinck", "pminoritybg", "tractid", "pvacationct", "d_vacationct"]].head())

        # 6.2 Chained analysis
        # The models presented in this section are based on models developed in Hamideh et al (2018).
        # The modifications from the original models include (1) combining non-Hispanic Black and Hispanic block
        # group percentages into a minority block group percentage variable, and (2) having both parcel and block
        # group level intercepts. The original model only had parcel level intercepts. Considering that multiple
        # levels of data are used (parcel and block group), it is appropriate to have both levels of intercepts.

        print("finished")

        # Estimation

        # Predict building value
        # Predict building value for years -1 to +6. year -1 is the year before the storm, year 0 is the year of the storm,
        # and years +1 to +6 are the years after the storm.

        # input base year
        baseyear = 2010

        # Baseyear is used to calculate improvement age which is required input
        # The base year of the analysis is 2010. 2010 GCAD data and 2010 Census data are used in teh chained analsysis.
        # This does present some challenges in interpretting results as 2010 data are collected after Ike and are subject to Ike impacts.
        # It is best practice to have tax assessor and Census data prior to the disaster event, ideally the year before.

        # by year, predict building value for years -1 to 6
        # DO NOT CHANGE. The model specifically predicts from -1 to 6.

        years = [-1, 0, 1, 2, 3, 4, 5, 6]
        # B_PHM_dmg_years = np.fromiter(hru.B_PHM_dmg_year.keys(), dtype=int)
        # # values = np.fromiter(hru.B_PHM_dmg_year.values(), dtype=float)
        # print(B_PHM_dmg_years)
        # # print(values)
        # hse_recov_vl0 = np.empty((hse_recov_value_loss.shape[0], len(B_PHM_dmg_years)))
        # hse_recov_vl0[:] = np.NaN
        # print(hse_recov_vl0.shape)
        #
        # tmp = baseyear - hse_recov_value_loss["effyrbuilt"] + (-1) + 1

        # # yrbuilt = hse_recov_value_loss["effyrbuilt"][:, np.newaxis]
        # hse_recov_vl0 = hru.B_PHM_age * (hse_recov_vl0 - yrbuilt[:, np.newaxis])
        # # hse_recov_vl0[1,:] = baseyear - hse_recov_value_loss["effyrbuilt"] + years + 1
        # print(hse_recov_vl0)
        #
        #
        # years_str = ["p_bv_yr{0}".format(year) for year in years]
        # print(years_str)
        # hse_recov_vl = pd.DataFrame(np.empty((hse_recov_value_loss.shape[0], len(years))), columns=years_str)
        # hse_recov_vl[:] = np.NaN
        # print(hse_recov_vl.head(5))
        #
        # tmp = baseyear - hse_recov_value_loss["effyrbuilt"] + (-1) + 1
        # print(tmp)
        # tmp2 = hru.B_PHM_intercept + \
        #        hru.B_PHM_year[-1] + \
        #        hru.B_PHM_age * tmp + \
        #        hru.B_PHM_sqm * hse_recov_value_loss["sqmeter"] + \
        #        hru.B_PHM_dmg_year[-1] * hse_recov_value_loss["value_loss"] + \
        #        hru.B_PHM_own_year[-1] * hse_recov_value_loss["d_ownerocc"] + \
        #        hru.B_PHM_inc_year[-1] * hse_recov_value_loss["mhhinck"] + \
        #        hru.B_PHM_min_year[-1] * hse_recov_value_loss["pminoritybg"]
        # print(tmp2)

        # print(hse_recov_value_loss["d_vacationct"])
        # hse_recov_vl["p_bv_yr-1"] = np.where(hse_recov_value_loss["d_vacationct"] == 0,
        #                                      np.exp(tmp2),
        #                                      hse_recov_vl["p_bv_yr-1"])
        # print(hse_recov_vl["p_bv_yr-1"].head(5))

        print(hse_recov_value_loss["d_vacationct"])

        coef_fin = self.assemble_phm_coefs(years, hse_recov_value_loss, vacation_pct)
        print(coef_fin.shape)
# Primary Housing Market (PHM)
        d_vac_np = np.tile(hse_recov_value_loss["d_vacationct"], (8, 1)).T
        print(d_vac_np)
        print(np.exp(coef_fin))
        hse_recov_vl = np.where(d_vac_np == 0, np.exp(coef_fin), coef_fin)
        print(hse_recov_vl)

        exit(1)

        for year in years:
            # Primary Housing Market (PHM)
            hse_recov_value_loss["p_bv_yr{0}".format(year)] = np.NaN
            # hse_recov_value_loss["p_bv_yr{0}".format(year)] = np.where(hse_recov_value_loss["d_vacationct"] == 0, np.exp(hru.B_PHM_intercept + hru.B_PHM_year[year] + hru.B_PHM_age * (baseyear - hse_recov_value_loss["effyrbuilt"] + year + 1) + hru.B_PHM_sqm * hse_recov_value_loss["sqmeter"] + hru.B_PHM_dmg_year[year] * hse_recov_value_loss["value_loss"] + hru.B_PHM_own_year[year] * hse_recov_value_loss["d_ownerocc"] + hru.B_PHM_inc_year[year] * hse_recov_value_loss["mhhinck"] + hru.B_PHM_min_year[year] * hse_recov_value_loss["pminoritybg"]), hse_recov_value_loss["p_bv_yr{0}".format(year)])

            # Seasonal/Vacation housing market (SVHM)
            # hse_recov_value_loss["p_bv_yr{0}".format(year)] = np.where(hse_recov_value_loss["d_vacationct"] == 1, np.exp(hru.B_SVHM_intercept + hru.B_SVHM_year[year] + hru.B_SVHM_age * (baseyear - hse_recov_value_loss["effyrbuilt"] + year + 1) + hru.B_SVHM_sqm * hse_recov_value_loss["sqmeter"] + hru.B_SVHM_dmg_year[year] * hse_recov_value_loss["value_loss"] + hru.B_SVHM_own_year[year] * hse_recov_value_loss["d_ownerocc"] + hru.B_SVHM_inc_year[year] * hse_recov_value_loss["mhhinck"]), hse_recov_value_loss["p_bv_yr{0}".format(year)])

            # calculate building value index for years 0 to 7
            # for year in years:
            #     hse_recov_value_loss["index_yr{0}".format(year)] = hse_recov_value_loss["p_bv_yr{0}".format(year)] / hse_recov_value_loss["p_bv_yr-1"]

            print("finished")

            print(hse_recov_value_loss[["strctid", "effyrbuilt", "sqmeter", "d_ownerocc", "bgid", "mhhinck", "pminoritybg", "tractid", "pvacationct", "d_vacationct", "value_loss", "dmg", "bv_2008", "bv_2010", "p_bv_yr-1", "p_bv_yr0", "p_bv_yr1", "p_bv_yr2", "p_bv_yr3", "p_bv_yr4", "p_bv_yr5", "p_bv_yr6", "index_yr-1", "index_yr0", "index_yr1", "index_yr2", "index_yr3", "index_yr4", "index_yr5", "index_yr6"]].head())
            exit(1)
            # 6.2 Aggregate building values
            # 6.2 rename columns prior to aggregation

            # count how many negative years are in the years list, to be used for adjusting column names
            neg_count = len(list(filter(lambda x: (x < 0), years)))
            print(neg_count)

            # Reversing year order using slicing technique
            years_reverse = years
            years_reverse = years_reverse[::-1]
            print(years_reverse)

            # rename column names to range from 0 to n.
            # In prior versions of this code, observations with negative suffix values were
            #### dropping from dataframe after reshaping. This fixes that.

            for year in years_reverse:
            # chained data and estimates
                hse_recov_value_loss.rename(columns={"p_bv_yr{0}".format(year): "p_bv_yr{0}".format(year + neg_count), "index_yr{0}".format(year): "index_yr{0}".format(year + neg_count)}, inplace=True)

            print("finished")

            # a better solution would be to figure out how to not rename columns when reshaping, or find a different reshaping method

            ###### **6.2 using chained data and estimates**

            # reshape dataframe from wide to long
            hse_recov_value_loss_reshaped = pd.wide_to_long(hse_recov_value_loss, ["p_bv_yr", "index_yr"], i="strctid", j="year")

            # shift dataframe multiindex to columns
            hse_recov_value_loss_reshaped.reset_index(inplace=True)

            # sort dataframe
            hse_recov_value_loss_reshaped.sort_values(by=["strctid", "year"], inplace=True)

            # adjust year column to oringal -n to +n range by subtracting neg_count
            hse_recov_value_loss_reshaped["year"] = hse_recov_value_loss_reshaped["year"] - neg_count

            # display
            print(hse_recov_value_loss_reshaped[["strctid", "d_vacationct", "year", "p_bv_yr", "index_yr"]].head(5))

            # aggregate building values by year
            hse_recov_value_loss_collapse = hse_recov_value_loss_reshaped.groupby(["d_vacationct", "year"]).aggregate({"p_bv_yr": np.sum})
            hse_recov_value_loss_collapse.reset_index(inplace=True)
            hse_recov_value_loss_collapse.style.format({"p_bv_yr": "{:>,.0f}"})

            # hse_recov_value_loss_collapse.plot.line(x="year", y="p_bv_yr", grid=True)
            # plt.plot(hse_recov_value_loss_collapse.year, hse_recov_value_loss_collapse.p_bv_yr)
            # plt.title("Aggregate building values by year (chained)")
            # plt.xlabel("Year")
            # plt.ylabel("Aggregate building value")
            #
            # plt.grid(True)
            # plt.show()

            # 6.3 Read in & clean Hamideh et al (2018) dataset
            # Read in Hamideh et al.(2018) dataset for exact replication.
            #
            # read in dataset
            hametal2018_df = pd.read_csv("HAMETAL2018_2_cleandata_2022-01-07_incoreinput_nolabel.csv")

            # Create structure id for merging data
            hametal2018_df["strctid"] = hametal2018_df["xref"].apply( lambda x: "XREF" + x)

            # show list of columns in dataframe
            print(hametal2018_df.columns)

            # how many observations are there in the dataframe
            print(hametal2018_df.strctid.describe())

            crosstab = pd.crosstab(index=hametal2018_df["studyarea_code_orig"], columns=hametal2018_df["studyarea_desc_orig"], margins=True)
            print(crosstab)

            # 6.3.X required variables for replicating Hamideh et al 2018**

            # relevent data from dataset
            hametal2018_df[["strctid", "bv_2008", "dmg", "effyrbuilt", "squarefootage", "sqmeter", "own_2008", "bgfipsfull", "mhhinck", "his_pct", "blk_pct", "censustractid", "studyarea_code_orig", "studyarea_desc_orig"]].head()

            # Model Coefficients as in Hamideh et al (2018)
            # The models here are as they were originally in Hamideh et al.(2018)

            # 6.2.X Urban Core (GUC) model coefficients

            # 6.3 Estimation
            hametal2018_dmg = hametal2018_df.copy(deep=True)
            print("dataframe copied")

            crosstab = pd.crosstab(index=hametal2018_dmg["studyarea_code_orig"], columns=hametal2018_dmg["studyarea_desc_orig"], margins=True)
            print(crosstab)

            # input baseyear
            baseyear = 2008

            # baseyear is used to calculate improvement age which is required input
            # the base year of the analysis is 2008 using 2008 GCAD data which represents improvement valuation before Hurricane Ike impacts.
            # for other disaster events, the baseyear needs to be set to the tax assessment year representing pre-disaster building values.

            # by year, predict building value for years -1 to 6
            # DO NOT CHANGE. The model specifically predicts from -1 to 6.
            years = [-1, 0, 1, 2, 3, 4, 5, 6]

            for year in years:
                # Galveston Urban Core (GUC)
                hametal2018_dmg["p_bv_yr{0}".format(year)] = np.NaN
            hametal2018_dmg["p_bv_yr{0}".format(year)] = np.where(hametal2018_dmg["studyarea_code_orig"] == 2, np.exp(hru.B_GUC_intercept + hru.B_GUC_year[year] + hru.B_GUC_age * (baseyear - hametal2018_dmg["effyrbuilt"] + year + 1) + hru.B_GUC_sqm * hametal2018_dmg["sqmeter"] + hru.B_GUC_dmg_year[year] * hametal2018_dmg["dmg"] + hru.B_GUC_own_year[year] * hametal2018_dmg["own_2008"] + hru.B_GUC_inc_year[year] * hametal2018_dmg["mhhinck"] + hru.B_GUC_his_year[year] * hametal2018_dmg["his_pct"] + hru.B_GUC_blk_year[year] * hametal2018_dmg["blk_pct"]), hametal2018_dmg["p_bv_yr{0}".format(year)])

            # Galveston Island Vacation (GIC)
            hametal2018_dmg["p_bv_yr{0}".format(year)] = np.where(
                (hametal2018_dmg["studyarea_code_orig"] == 1) | (hametal2018_dmg["studyarea_code_orig"] == 3), np.exp(hru.B_GIV_intercept + hru.B_GIV_year[year] + hru.B_GIV_age * (baseyear - hametal2018_dmg["effyrbuilt"] + year + 1) + hru.B_GIV_sqm * hametal2018_dmg["sqmeter"] + hru.B_GIV_dmg_year[year] * hametal2018_dmg["dmg"] + hru.B_GIV_own_year[year] * hametal2018_dmg["own_2008"] + hru.B_GIV_inc_year[year] * hametal2018_dmg["mhhinck"] + hru.B_GIV_his_year[year] * hametal2018_dmg["his_pct"] + hru.B_GIV_blk_year[year] * hametal2018_dmg["blk_pct"]), hametal2018_dmg["p_bv_yr{0}".format(year)])

            # Bolivar Island Vacation (BIV)
            hametal2018_dmg["p_bv_yr{0}".format(year)] = np.where(hametal2018_dmg["studyarea_code_orig"] == 4, np.exp(hru.B_BIV_intercept + hru.B_BIV_year[year] + hru.B_BIV_age * (baseyear - hametal2018_dmg["effyrbuilt"] + year + 1) + hru.B_BIV_sqm * hametal2018_dmg["sqmeter"] + hru.B_BIV_dmg_year[year] * hametal2018_dmg["dmg"] + hru.B_BIV_own_year[year] * hametal2018_dmg["own_2008"] + hru.B_BIV_inc_year[year] * hametal2018_dmg["mhhinck"] + hru.B_BIV_his_year[year] * hametal2018_dmg["his_pct"] + hru.B_BIV_blk_year[year] * hametal2018_dmg["blk_pct"]), hametal2018_dmg["p_bv_yr{0}".format(year)])

            # calculate building value index for years 0 to 7
            for year in years:
                hametal2018_dmg["index_yr{0}".format(year)] = hametal2018_dmg["p_bv_yr{0}".format(year)] / hametal2018_dmg["p_bv_yr-1"]

            print("finished")

            print(hametal2018_dmg[["strctid", "studyarea_code_orig", "studyarea_desc_orig", "effyrbuilt", "sqmeter", "own_2008", "mhhinck", "his_pct", "blk_pct", "bv_2008", "dmg", "p_bv_yr-1", "p_bv_yr0", "p_bv_yr1", "p_bv_yr2", "p_bv_yr3", "p_bv_yr4", "p_bv_yr5", "p_bv_yr6", "index_yr-1", "index_yr0", "index_yr1", "index_yr2", "index_yr3", "index_yr4", "index_yr5", "index_yr6"]].head(5))

            # Aggregate building values
            # rename columns prior to aggregation
            # count how many negative years are in the years list, to be used for adjusting column names
            neg_count = len(list(filter(lambda x: (x < 0), years)))
            print(neg_count)

            # Reversing year order using slicing technique
            years_reverse = years
            years_reverse = years_reverse[::-1]
            print(years_reverse)

            # rename column names to range from 0 to n.
            # In prior versions of this code, observations with negative suffix values were
            # dropping from dataframe after reshaping. This fixes that.

            # hamideh et al 2018 data and estimates
            for year in years_reverse:
                hametal2018_dmg.rename(columns={"p_bv_yr{0}".format(year): "p_bv_yr{0}".format(year + neg_count), "index_yr{0}".format(year): "index_yr{0}".format(year + neg_count)}, inplace=True)

            print("finished")

        return True

    def get_vac_season_housing(self, vacation_status):
        """ Calculate the percent vacation or seasonal housing of all housing units within a census tract and
        add dummy variable for census tract as a seasonal/vacation housing submarket.
.
        Args:
            vacation_status (obj): Seasonal/vacation housing Census ACS data from json reader.

        Returns:
            pd.DataFrame: Seasonal/vacation housing data.

        """
        vac_status = pd.DataFrame(vacation_status[1:], columns=vacation_status[0])

        vac_status["B25004_006E"] = vac_status["B25004_006E"].astype(int)
        vac_status["B25004_006M"] = vac_status["B25004_006M"].astype(int)
        vac_status["B25002_001E"] = vac_status["B25002_001E"].astype(int)
        vac_status["B25002_001M"] = vac_status["B25002_001M"].astype(int)

        # Calculate the percent vacation or seasonal housing of all housing units within a census tract
        vac_status["pvacationct_moe"] = vac_status["B25004_006E"] / vac_status["B25002_001E"]
        vac_status["pvacationct"] = 100 * vac_status["pvacationct_moe"]
        vac_status["pvacationct_moe"] = vac_status["pvacationct_moe"] ** 2 * vac_status["B25002_001M"] ** 2
        vac_status["pvacationct_moe"] = vac_status["B25004_006M"]**2 - vac_status["pvacationct_moe"]
        vac_status["pvacationct_moe"] = 100 * (1 / vac_status["B25002_001E"]) * vac_status["pvacationct_moe"]**0.5

        # dummy variable for census tract as a seasonal/vacation housing submarket
        vac_status["d_vacationct"] = np.where(vac_status["pvacationct"] >= 50, 1, 0)

        vac_status.sort_values(by="pvacationct", inplace=True, ascending=False)

        return vac_status.copy(deep=True)

    def merge_add_inv(self, hse_rec, addl_struct):
        """Merge study area and additional structure information
.
        Args:
            hse_rec (pd.DataFrame):  Area inventory
            addl_struct (pd.DataFrame):  Additional infrastructure inventory.

        Returns:
            pd.DataFrame: Final merge of two inventories

        """
        hse_rec_merged =  pd.merge(hse_rec, addl_struct, on="strctid", how="inner")
        return hse_rec_merged

    def merge_seasonal_data(self, hse_rec, vac_status):
        """ Merge study area and with seasonal/vacation housing Census ACS data
.
        Args:
            hse_rec (pd.DataFrame): Area inventory.
            vac_status (pd.DataFrame): Seasonal/vacation housing Census ACS data.

        Returns:
            pd.DataFrame: Final merge of two inventories

        """
        hse_rec["tractid"] = hse_rec["tractid"].astype(str)
        # add county and state to trac to match hse_rec tracid (Galveston - 723900 to 48167723900)
        vac_status["tractid"] = vac_status["state"].astype(str) + vac_status["county"].astype(str) + \
                                vac_status["tract"].astype(str)

        hse_rec_merged =  pd.merge(hse_rec, vac_status, on="tractid", how="inner")
        return hse_rec_merged

    def merge_block_data(self, hse_rec, bg_mhhinc):
        """ Merge block group level median household income
.
        Args:
            hse_rec (pd.DataFrame):  Area inventory
            bg_mhhinc (pd.DataFrame):  Block data.

        Returns:
            pd.DataFrame: Final merge of two inventories

        """
        hse_rec_merged = pd.merge(hse_rec, bg_mhhinc, left_on="bgidstr", right_on="bgidstr", how="inner")
        return hse_rec_merged

    def value_loss(self, hse_rec):
        """ Estimate value_loss for each parcel based on parameters from Bai, Hueste, & Gardoni (2009)
    .
        Args:
            hse_rec (pd.DataFrame):  Area inventory

        Returns:
            pd.DataFrame: Inventory with value losses

            """
        hse_rec["value_loss"] = 100 * (hse_rec["DS_0"] * hse_rec["rploss_0"] +
                                       hse_rec["DS_1"] * hse_rec["rploss_1"] +
                                       hse_rec["DS_2"] * hse_rec["rploss_2"] +
                                       hse_rec["DS_3"] * hse_rec["rploss_3"])
        return hse_rec

    def assemble_phm_coefs(self, dmg_years, hse_rec):
        """ Assemble Primary Housing Market (PHM) data for full inventory and all damage-related years.
    .
        Args:
            dmg_years (list): A list of damage years such as [-1, 0, 1, 2, 3, 4, 5, 6]
            hse_rec (pd.DataFrame):  Area inventory including losses

        Returns:
            pd.DataFrame: Final coefficients for all damage years

        """
        hru = HousingRecoveryUtil()

        dmg_years = np.array(dmg_years)
        dmg_years_size = len(dmg_years)

        coef_fin = np.empty((hse_rec.shape[0], dmg_years_size))
        coef_fin[:] = hru.B_PHM_intercept + np.fromiter(hru.B_PHM_year.values(), dtype=float)

        # adjust build year year with damage years
        yrbl_all = np.empty((hse_rec.shape[0], dmg_years_size))
        yrbl_all[:] = hru.BASEYEAR + dmg_years + 1
        yrbuilt = hru.B_PHM_age * (yrbl_all - hse_rec["effyrbuilt"].to_numpy()[:, np.newaxis])

        # square meters, use vector (1x8) with B_PHM_sqm
        sqmeter = np.full((1, dmg_years_size), hru.B_PHM_sqm) * hse_rec["sqmeter"].to_numpy()[:, np.newaxis]

        valloss = np.fromiter(hru.B_PHM_dmg_year.values(), dtype=float) + hse_rec["value_loss"].to_numpy()[:, np.newaxis]
        d_owner = np.fromiter(hru.B_PHM_own_year.values(), dtype=float) + hse_rec["d_ownerocc"].to_numpy()[:, np.newaxis]
        mhhinck = np.fromiter(hru.B_PHM_inc_year.values(), dtype=float) + hse_rec["mhhinck"].to_numpy()[:, np.newaxis]
        pminrbg = np.fromiter(hru.B_PHM_min_year.values(), dtype=float) + hse_rec["pminoritybg"].to_numpy()[:, np.newaxis]

        coef_fin = coef_fin + yrbuilt + sqmeter + valloss + d_owner + mhhinck + pminrbg
        print("coef_fin")
        print(coef_fin)

        # vacation condition for all years
        d_vac_np = np.tile(hse_rec["d_vacationct"], (8, 1)).T
        # print(d_vac_np)

        hse_rec_fin = np.where(d_vac_np == 0, np.exp(coef_fin), coef_fin)
        print(hse_rec_fin)

        return hse_rec_fin

    def assemble_svhm_coefs(self, dmg_years, hse_rec):
        """ Assemble Seasonal/Vacation housing market (SVHM) data for full inventory and all damage-related years.
    .
        Args:
            dmg_years (list): A list of damage years such as [-1, 0, 1, 2, 3, 4, 5, 6]
            hse_rec (pd.DataFrame):  Area inventory including losses

        Returns:
            pd.DataFrame: Final coefficients for all damage years

        """
        hru = HousingRecoveryUtil()

        dmg_years = np.array(dmg_years)
        dmg_years_size = len(dmg_years)

        coef_fin = np.empty((hse_rec.shape[0], dmg_years_size))
        coef_fin[:] = hru.B_SVHM_intercept + np.fromiter(hru.B_SVHM_year.values(), dtype=float)

        # Seasonal/Vacation housing market (SVHM)
        # np.exp(
        # hru.B_SVHM_intercept + hru.B_SVHM_year[year] +
        # hru.B_SVHM_age * (baseyear - hse_recov_value_loss["effyrbuilt"] + year + 1) +
        # hru.B_SVHM_sqm * hse_recov_value_loss["sqmeter"] +
        # hru.B_SVHM_dmg_year[year] * hse_recov_value_loss["value_loss"] +
        # hru.B_SVHM_own_year[year] * hse_recov_value_loss["d_ownerocc"] +
        # hru.B_SVHM_inc_year[year] * hse_recov_value_loss["mhhinck"])

        # adjust build year year with damage years
        yrbl_all = np.empty((hse_rec.shape[0], dmg_years_size))
        yrbl_all[:] = hru.BASEYEAR + dmg_years + 1
        yrbuilt = hru.B_SVHM_age * (yrbl_all - hse_rec["effyrbuilt"].to_numpy()[:, np.newaxis])

        # square meters, use vector (1x8) with B_PHM_sqm
        sqmeter = np.full((1, dmg_years_size), hru.B_SVHM_sqm) * hse_rec["sqmeter"].to_numpy()[:, np.newaxis]

        valloss = np.fromiter(hru.SVHM_dmg_year.values(), dtype=float) + hse_rec["value_loss"].to_numpy()[:, np.newaxis]
        d_owner = np.fromiter(hru.SVHM_own_year.values(), dtype=float) + hse_rec["d_ownerocc"].to_numpy()[:, np.newaxis]
        mhhinck = np.fromiter(hru.SVHM_inc_year.values(), dtype=float) + hse_rec["mhhinck"].to_numpy()[:, np.newaxis]

        coef_fin = coef_fin + yrbuilt + sqmeter + valloss + d_owner + mhhinck
        print("coef_fin")
        print(coef_fin)

        # vacation condition for all years
        d_vac_np = np.tile(hse_rec["d_vacationct"], (8, 1)).T
        # print(d_vac_np)

        hse_rec_fin = np.where(d_vac_np == 1, np.exp(coef_fin), coef_fin)
        print(hse_rec_fin)

        return hse_rec_fin
