# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
# EPN_Recovery_UW_GDAL.py
# Shuoqi Wang
# Department of Civil and Environmental Engineering
# University of Washington
# Created on: 2018-06-20
# Last Updated on: 2018-07-24
# ----------------------------------------------------------------------
# Import packages and set environment parameters
import sys
import os
import numpy
import fiona
from rasterstats import zonal_stats
import pandas as pd
import shutil

from pyincore import InsecureIncoreClient, HazardService, FragilityService, DataService
from pyincore import GeoUtil, AnalysisUtil


class EpnRecoveryModel:
    def __init__(self, client, boundary_id='', wind_id='', surge_id='', rain_id='', hzd_wind=False, hzd_surge=False, hzd_rain=False):
        # boundary: parcel and zip code bounday shapefiles
        # wind: hurricane hazard raster
        #   Maximum sustained wind speed (in meters per second).
        #   That is, the 1-minute wind speed at 10m above ground.
        #   Not the 3-second gust used in ASCE7
        # surge: inland inundation level above ground (in meters) raster
        # rain: maximum daily total rainfall (in millimeters) raster
        # header: column name which stores identifiers for the boundary data

        # Create Hazard and Fragility service
        self.hazardsvc = HazardService(client)
        self.fragilitysvc = FragilityService(client)
        self.datasetsvc = DataService(client)
        self.boundary_id = boundary_id
        self.wind_id = wind_id
        self.surge_id = surge_id
        self.rain_id = rain_id
        unique_fld = "guid"

        wind_on = False
        surge_on = False
        rain_on = False
        hzd_number = 0

        if hzd_wind:
            hzd_number += 1
        if hzd_surge:
            hzd_number += 1
        if hzd_rain:
            hzd_number += 1

        # check if the dataset provided
        if len(wind_id) > 0:
            wind_on = True
        if len(surge_id) > 0:
            surge_on = True
        if len(rain_id) > 0:
            rain_on = True

        # store shpefiles in the tmp directory
        # store boundary shapefile
        boundary_shp_name = self.datasetsvc.get_dataset_blob(boundary_id)
        tmpdir, tail = os.path.split(boundary_shp_name)
        boundary_path = os.path.join(boundary_shp_name, tail) + ".shp"

        # store wind geotif
        wind_name = self.datasetsvc.get_dataset_blob(wind_id)
        tmpdir, tail = os.path.split(wind_name)
        wind_path = os.path.join(wind_name, tail) + ".tif"

        # store surge geotif
        surge_name = self.datasetsvc.get_dataset_blob(surge_id)
        tmpdir, tail = os.path.split(surge_name)
        surge_path = os.path.join(surge_name, tail) + ".tif"

        # store wind geotif
        rain_name = self.datasetsvc.get_dataset_blob(rain_id)
        tmpdir, tail = os.path.split(rain_name)
        rain_path = os.path.join(rain_name, tail) + ".tif"

        # check if the hazard dataset and fragility relationship
        if hzd_wind:
            if wind_on == False:
                sys.exit("Wind hazard can't be applied since there is no rain dataset")
        if hzd_surge:
            if surge_on == False:
                sys.exit("Surge hazard can't be applied since there is no rain dataset")
        if hzd_rain:
            if rain_on == False:
                sys.exit("Rain hazard can't be applied since there is no rain dataset")

        # ds = ogr.Open(boundary_path, 0)
        # lyr = ds.GetLayer(0)
        name = []
        id = []
        i = 0

        boundary = fiona.open(boundary_path)
        for poly in boundary:
            name.append(poly['properties'][unique_fld])
            id.append(i)
            i += 1
        bound_table = {'guid': name, 'ID': id}
        df_bound = pd.DataFrame(bound_table)

        if rain_on:
            stats = zonal_stats(boundary_path, wind_path, stats='mean')
            h_w = pd.DataFrame(stats)
            h_w['ID'] = h_w.index.values
            h_w.columns = ['Wind_ms', 'ID']
            output = h_w


        # Calculate maximum storm surge level within each zip code boundary
        # if surge != "NA":
        if surge_on:
            stats = zonal_stats(boundary_path, surge_path, stats='mean')
            h_s = pd.DataFrame(stats)
            h_s['ID'] = h_s.index.values
            h_s.columns = ['Surge_m', 'ID']
            if wind_on:
                h_ws = pd.merge(h_w, h_s, on='ID')
                output = h_ws
            else:
                output = h_s


        # Calculate maximum rainfall level within each zip code boundary
        # The rainfall data is the maximum 24-hour total rainfall after landfall
        # of the hurricane.
        # if rain != "NA":
        if rain_on:
            stats = zonal_stats(boundary_path, rain_path, stats='mean')
            h_r = pd.DataFrame(stats)
            h_r['ID'] = h_r.index.values
            h_r.columns = ['Rain_mm', 'ID']
            if wind_on:
                if surge_on:
                    h_wsr = pd.merge(h_ws, h_r, on='ID')
                    output = h_wsr
                else:
                    h_wr = pd.merge(h_w, h_r, on='ID')
                    output = h_wr
            else:
                if surge_on:
                    h_sr = pd.merge(h_s, h_r, on='ID')
                    output = h_sr
                else:
                    output = h_r


        # Remove Inf and -Inf values by setting them to NaN
        output = output.replace(-numpy.inf, numpy.nan)
        output = output.replace(numpy.inf, numpy.nan)

        # ----------------------------------------------------------------------
        # Fragility Calculation
        #
        # The fragility is the conditional probability of inoperability X(t) due
        # to the level of the hurricane hazard at time t=0 (landfall assumed).
        # X(t=0)=X0 is characterized by a logistic regression model.
        #
        # There are multiple models based upon the three hazards of wind speed,
        # storm surge inundation and rainfall. The user has the option of making
        # the selection of the fragility function. The fragility function for
        # the wind speed uses the sustained 1-minute speed, rather than the
        # 3-sec gust.
        #
        # It represents the system at the zipcode level.
        # ----------------------------------------------------------------------

        # # Take user inputs of number of hazards and hazard types
        # hazard = input("Please type the hazard(s) you would like the "
        #                    "fragility calculation to be based on.\n"
        #                    "Choose from Wind, Surge, or Rain. "
        #                    "Combination of two or three hazards is also allowed"
        #                    " (separate hazards with single space)\n")

        # Select the proper fragility function to use based on user input
        if hzd_number == 0:
            sys.exit("No hazard was selected")

        if hzd_number == 1:
            if hzd_wind:
                h = output['Wind_ms']
                output['X0'] = numpy.exp(-4.583 + 0.187 * h) / (
                        1 + numpy.exp(-4.583 + 0.187 * h))
            elif hzd_surge:
                h = output["Surge_m"]
                output['X0'] = numpy.exp(-4 + 1.18 * h) / (
                        1 + numpy.exp(-4 + 1.18 * h))
            elif hzd_rain:
                h = output["Rain_mm"]
                output['X0'] = numpy.exp(-4 + 0.011 * h) / (
                        1 + numpy.exp(-4 + 0.011 * h))
            else:
                sys.exit("Hazard input error")

        if hzd_number == 2:
            if hzd_wind and hzd_rain:
                h1 = output["Wind_ms"]
                h2 = output["Rain_mm"]
                output['X0'] = numpy.exp(-3.746 + 0.117 * h1 + 0.002 * h2) / (
                        1 + numpy.exp(-3.746 + 0.117 * h1 + 0.002 * h2))
            elif hzd_wind and hzd_surge:
                h1 = output["Wind_ms"]
                h2 = output["Surge_m"]
                output['X0'] = numpy.exp(-5.168 + 0.196 * h1 + 0.104 * h2) / (
                        1 + numpy.exp(-5.168 + 0.196 * h1 + 0.104 * h2))
            elif hzd_surge and hzd_rain:
                h1 = output["Surge_m"]
                h2 = output["Rain_mm"]
                output['X0'] = numpy.exp(-2.796 + 0.520 * h1 + 0.006 * h2) / (
                        1 + numpy.exp(-2.796 + 0.520 * h1 + 0.006 * h2))
            else:
                sys.exit("Hazard input error")

        if hzd_number == 3:
            if hzd_wind and hzd_surge and hzd_rain:
                h1 = output["Wind_ms"]
                h2 = output["Surge_m"]
                h3 = output["Rain_mm"]
                output['X0'] = numpy.exp(-4.956 + 0.156 * h1 + 0.043 * h2 +
                                         0.004 * h3) / (
                        1 + numpy.exp(-4.956 + 0.156 * h1 + 0.043 * h2 +
                                     0.004 * h3))
            else:
                sys.exit("Hazard input error")

        # ----------------------------------------------------------------------
        # Omega Calculation
        #
        # The fragiliy function is the time t=0 value of the inoperability X(t)
        # over time after landfall. X(t) also represents power outages. The X(t)
        # function is modeled here as a single degree of freedom model with
        # parameters omega and time to recovery, 'tr' in days.
        #
        # The next calculation is for the omega value, then for the 'tr' value.
        #
        # If the user wants the X(t) value for each day, the program will
        # supply. otherwise, it will return the 'tr' value only.
        # ----------------------------------------------------------------------
        # Calculate omega using peak outage 'X0'
        output['Omega'] = 2.561 - 2.128 * output['X0']

        # ----------------------------------------------------------------------
        # tr Calculation
        # ----------------------------------------------------------------------
        # Calculate 'tr' using 'Omega'
        output['tr'] = numpy.exp(3.062 - 1.092 * output['Omega'])

        # Find maximum tr value for each affected zip code
        n = numpy.ceil(numpy.max(output['tr']))

        # One column is created for each day, e.g. Day2, where the estimated
        # power outage for each zip code on that day is stored

        i = 0
        while i <= n:
            fieldName = "Day" + str(i)
            x0 = output['X0']
            w = output['Omega']
            output[fieldName] = self.getxt(x0, w, i)
            i += 1

        # Write csv table to file
        result = pd.merge(df_bound, output, on='ID')
        out_csv = os.path.join(tmpdir, 'result.csv')
        result.to_csv(out_csv)

        csv_dataset_id = self.update_csv_dataset(out_csv, client)

        print(csv_dataset_id)
        boundary.close()
        shutil.rmtree(tmpdir)

    def update_csv_dataset(self, out_csv, client):
        # create data set and post to dataservice
        outdict = {}
        outdict["sourceDataset"] = self.boundary_id
        outdict["title"] = 'EPN Recovery'
        outdict["creator"] = client.headers.get("X-Credential-Username")
        outdict["format"] = 'table'
        outdict['dataType'] = 'incore:EPNRecoveryVer1'

        dataset_json = self.datasetsvc.create_dataset(outdict)
        dataset_id = dataset_json["id"]

        self.datasetsvc.add_files_to_dataset(dataset_id, [out_csv])

        return dataset_id

    # ----------------------------------------------------------------------
    # Daily Power Outage 'Xt' Calculation
    # ----------------------------------------------------------------------
    # Calculate outage for each day 'i' where 'i < maxtf' using
    # defined 'getxt' function
    def getxt(self, x0, w, t):
        """
            Summary
            -------
            Calculate power outage fraction for each zone on day t after
            hurricane landfall (t = 0 at landfall).

            Parameters
            ----------
            x0 : float
                The peak power outage fraction at hurricane landfall.
            w : float
                Parameters for the recovery function.
            t : int
                The number of days after landfall.

            Returns
            -------
            float
                Power outage fraction for each zone on day t.

        """
        z = 1.001
        x0dot = 0
        alpha = w * z
        beta = w * numpy.sqrt(z ** 2 - 1)
        term1 = (((alpha + beta) * x0 + x0dot) / (2 * beta)) * \
                numpy.exp(-(alpha - beta) * t)
        term2 = (((beta - alpha) * x0 - x0dot) / (2 * beta)) * \
                numpy.exp(-(alpha + beta) * t)

        return term1 + term2