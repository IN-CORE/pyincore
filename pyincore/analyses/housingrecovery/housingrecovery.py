# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import requests
import numpy as np
import pandas as pd
from pyincore import BaseAnalysis


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
                {
                   "id":"building_dmg",
                   "required": True,
                   "description":"Structural building damage",
                   "type": ["ergo:buildingDamageVer6"],
                },
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
                   "description":"Census ACS data, 2010 5yr data for block groups available at IPUMS NHGIS "
                                 "web site.",
                   "type": ["incore:censusBlockGroupsData"]
                },
                {
                   "id":"census_appraisal_data",
                   "required": False,
                   "description":"Census tax data, 2010 Decennial Census and Galveston County Appraisal"
                                  "District (GCAD) tax assessor data",
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
        bldg_dmg_df = self.get_input_dataset("building_dmg").get_dataframe_from_csv(low_memory=False)
        pd_df = self.get_input_dataset("population_dislocation").get_dataframe_from_csv(low_memory=False)
        census_appraisal = self.get_input_dataset("census_appraisal_data").get_json_reader()

        print(census_appraisal)

        # Show list of column names in DataFrame.
        print(pd_df.columns)
        # How many observations are in the DataFrame?
        print(pd_df.guid.describe())
        # How many unique address point ids and structure ids are there in the population dislocation output file?
        print(pd_df.columns)
        print(pd_df[["addrptid", "strctid"]].describe())

        # crosstab ownership and vacancy prior to creating owner-occupied dummy variable
        # Add .fillna() because .crosstab() won't include Nan as a value in tabulation
        crosstab = pd.crosstab(index=pd_df["vacancy"].fillna("missing"),
                               columns=pd_df["ownershp"].fillna("missing"),
                               margins=True, dropna=False)
        print(crosstab)

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
        print(pd_df.d_ownerocc.describe())

        crosstab = pd.crosstab(index=pd_df["vacancy"].fillna("missing"), columns=pd_df["d_ownerocc"].fillna("missing"), margins=True, dropna=False)
        print(crosstab)

        # from the population dislocation result dataset, keep only parcels with 1 building
        building_level = pd_df.loc[(pd_df.bldgobs == 1)]
        print("building_level")
        print(building_level.strctid.describe())
        # keep buildings that are single-family
        single_family = building_level.loc[(building_level.d_sf == 1)]
        print("single_family")
        print(single_family.strctid.describe())
        print(single_family)

        # single_family.drop("Unnamed: 0", axis=1, inplace=True)
        print(single_family.columns)

        # Identify housing submarkets
        # In Galveston
        # - Urban Core is the considered the primary housing market. This is where those who live and work
        #   in Galveston year round reside.
        # - Galveston Island and Bolivar Island both have seasonal/vacation housing markets for secondary
        #   homes or vacation rentals. Bolivar Island is considered vacation  entirely.
        #
        # lists of census tracts according to Hamideh et al 2018
        urban_core_tracts = [48167724000, 48167724200, 48167724300, 48167724400, 48167724500, 48167724600,
                             48167724700, 48167724800, 48167724900, 48167725000, 48167725100, 48167725200,
                             48167725300, 48167725400, 48167725500, 48167725600, 48167725700, 48167725800,
                             48167725900]
        galveston_island_vacation_tracts_east = [48167724100]
        galveston_island_vacation_tracts_west = [48167726000, 48167726100]
        bolivar_island_vacation_tracts = [48167723900 ]
        #
        # For application in other communities, a seasonal/vacation submarket is determined
        # when the percentage of homes designated as "For seasonal, recreational, or occasional use" within
        # a Census Tract is greater than or equal to 50 percent using Census ACS 5-year data.

        # keep only observations located in urban core, galveston island vacation, and
        # bolivar island vacation census tracts
        urban_core_sf = single_family.loc[(single_family.tractid.isin(urban_core_tracts))]
        galveston_island_vacation_east_sf = single_family.loc[(single_family.tractid.isin(galveston_island_vacation_tracts_east))]
        galveston_island_vacation_west_sf = single_family.loc[(single_family.tractid.isin(galveston_island_vacation_tracts_west))]
        bolivar_island_vacation_sf = single_family.loc[(single_family.tractid.isin(bolivar_island_vacation_tracts))]

        # create studyarea variable for each study area
        urban_core_sf.loc[:, "studyarea_code_orig"] = 2
        urban_core_sf.loc[:, "studyarea_desc_orig"] = "Galveston - Urban Core"

        galveston_island_vacation_east_sf.loc[:, "studyarea_code_orig"] = 1
        galveston_island_vacation_east_sf.loc[:, "studyarea_desc_orig"] = "Galveston - East End"
        galveston_island_vacation_west_sf.loc[:, "studyarea_code_orig"] = 3
        galveston_island_vacation_west_sf.loc[:, "studyarea_desc_orig"] = "Galveston - West End"
        bolivar_island_vacation_sf.loc[:, "studyarea_code_orig"] = 3
        bolivar_island_vacation_sf.loc[:, "studyarea_desc_orig"] = "Bolivar Island Vacation"

        # append study area dataframes together
        studyarea_sf = urban_core_sf.append(galveston_island_vacation_east_sf, ignore_index=True).\
            append(galveston_island_vacation_west_sf, ignore_index=True).\
            append(bolivar_island_vacation_sf, ignore_index=True)
        print(studyarea_sf.strctid.describe())

        print(studyarea_sf["studyarea_code_orig"].value_counts())

        crosstab = pd.crosstab(index=studyarea_sf["studyarea_code_orig"], 
                               columns=studyarea_sf["studyarea_desc_orig"],
                               margins=True)
        print(crosstab)

        # show relevant data from population dislocation result
        print(studyarea_sf[["guid", "addrptid", "strctid", "tractid", "studyarea_code_orig", "studyarea_desc_orig",
                      "DS_0", "DS_1", "DS_2", "DS_3", "rploss_0", "rploss_1", "rploss_2", "rploss_3",
                      "bgid", "d_ownerocc","pblackbg", "phispbg","d_sf"]].head())

        return True
