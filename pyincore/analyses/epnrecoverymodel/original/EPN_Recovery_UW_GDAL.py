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
from osgeo import ogr
from rasterstats import zonal_stats
import pandas as pd

os.chdir("C:\Workspace-incore2\\analyses\\epnrecoverymodel\\original\\test_data\\gdal_test\\")

# Define parcel and zip code bounday shapefiles
# boundary = input("Please enter the name of the boundary "
#                    "shapefile\n")
# header = input("Please enter the header of the column which "
#                 "stores identifiers for the boundary data \n")
boundary = 'isaac_parish.shp'
header = 'NAME'

ds = ogr.Open(boundary, 0)
lyr = ds.GetLayer(0)
name = []
id = []
i = 0
for feat in lyr:
    name.append(feat.GetFieldAsString(header))
    id.append(feat.GetFID())
bound_table = {'Name': name, 'ID': id}
df_bound = pd.DataFrame(bound_table)

# Define hurricane hazard input data
# Maximum sustained wind speed (in meters per second)
# That is, the 1-minute wind speed at 10m above ground
# Not the 3-second gust used in ASCE7
# wind = input("Please enter the name of the wind speed raster "
#                  "(enter NA if no data available)\n")
#
# # inland inundation level above ground (in meters)
# surge = input("Please enter the name of the storm surge raster "
#                   "(enter NA if no data available)\n")
#
# # maximum daily total rainfall (in millimeters)
# rain = input("Please enter the name of the rainfall raster "
#                  "(enter NA if no data available)\n")
wind = 'isaac_hwind.tif'
surge = 'isaac_surge.tif'
rain = 'isaac_rainfall.tif'


# Calculate maximum sustained wind speed within each zip code boundary
# That is, the 1-minute wind speed at 10m above ground
# Not the 3-second gust used in ASCE7

if wind != "NA":
    stats = zonal_stats(boundary, wind, stats='mean')
    h_w = pd.DataFrame(stats)
    h_w['ID'] = h_w.index.values
    h_w.columns = ['Wind_ms', 'ID']
    output = h_w


# Calculate maximum storm surge level within each zip code boundary
if surge != "NA":
    stats = zonal_stats(boundary, surge, stats='mean')
    h_s = pd.DataFrame(stats)
    h_s['ID'] = h_s.index.values
    h_s.columns = ['Surge_m', 'ID']
    if wind != "NA":
        h_ws = pd.merge(h_w, h_s, on='ID')
        output = h_ws
    else:
        output = h_s


# Calculate maximum rainfall level within each zip code boundary
# The rainfall data is the maximum 24-hour total rainfall after landfall
# of the hurricane.
if rain != "NA":
    stats = zonal_stats(boundary, rain, stats='mean')
    h_r = pd.DataFrame(stats)
    h_r['ID'] = h_r.index.values
    h_r.columns = ['Rain_mm', 'ID']
    if wind != "NA":
        if surge != "NA":
            h_wsr = pd.merge(h_ws, h_r, on='ID')
            output = h_wsr
        else:
            h_wr = pd.merge(h_w, h_r, on='ID')
            output = h_wr
    else:
        if surge != "NA":
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

# Take user inputs of number of hazards and hazard types
hazard = input("Please type the hazard(s) you would like the "
                   "fragility calculation to be based on.\n"
                   "Choose from Wind, Surge, or Rain. "
                   "Combination of two or three hazards is also allowed"
                   " (separate hazards with single space)\n")

model = hazard.split()

# Select the proper fragility function to use based on user input
if len(model) == 1:
    if "Wind" in model:
        h = output['Wind_ms']
        output['X0'] = numpy.exp(-4.583 + 0.187 * h) / (
                1 + numpy.exp(-4.583 + 0.187 * h))
    elif "Surge" in model:
        h = output["Surge_m"]
        output['X0'] = numpy.exp(-4 + 1.18 * h) / (
                1 + numpy.exp(-4 + 1.18 * h))
    elif "Rain" in model:
        h = output["Rain_mm"]
        output['X0'] = numpy.exp(-4 + 0.011 * h) / (
                1 + numpy.exp(-4 + 0.011 * h))
    else:
        sys.exit("Input error")
elif len(model) == 2:
    if "Wind" in model and "Rain" in model:
        h1 = output["Wind_ms"]
        h2 = output["Rain_mm"]
        output['X0'] = numpy.exp(-3.746 + 0.117 * h1 + 0.002 * h2) / (
                1 + numpy.exp(-3.746 + 0.117 * h1 + 0.002 * h2))
    elif "Wind" in model and "Surge" in model:
        h1 = output["Wind_ms"]
        h2 = output["Surge_m"]
        output['X0'] = numpy.exp(-5.168 + 0.196 * h1 + 0.104 * h2) / (
                1 + numpy.exp(-5.168 + 0.196 * h1 + 0.104 * h2))
    elif "Surge" in model and "Rain" in model:
        h1 = output["Surge_m"]
        h2 = output["Rain_mm"]
        output['X0'] = numpy.exp(-2.796 + 0.520 * h1 + 0.006 * h2) / (
                1 + numpy.exp(-2.796 + 0.520 * h1 + 0.006 * h2))
    else:
        sys.exit("Input error")
elif len(model) == 3:
    if "Wind" in model and "Surge" in model and "Rain" in model:
        h1 = output["Wind_ms"]
        h2 = output["Surge_m"]
        h3 = output["Rain_mm"]
        output['X0'] = numpy.exp(-4.956 + 0.156 * h1 + 0.043 * h2 +
                                 0.004 * h3) / (
                1 + numpy.exp(-4.956 + 0.156 * h1 + 0.043 * h2 +
                             0.004 * h3))
    else:
        sys.exit("Input error")

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

# ----------------------------------------------------------------------
# Daily Power Outage 'Xt' Calculation
# ----------------------------------------------------------------------
# Calculate outage for each day 'i' where 'i < maxtf' using
# defined 'getxt' function


def getxt(x0, w, t):
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


# Find maximum tr value for each affected zip code
n = numpy.ceil(numpy.max(output['tr']))

# One column is created for each day, e.g. Day2, where the estimated
# power outage for each zip code on that day is stored

i = 0
while i <= n:
    fieldName = "Day" + str(i)
    x0 = output['X0']
    w = output['Omega']
    output[fieldName] = getxt(x0, w, i)
    i += 1

# Write csv table to file
result = pd.merge(output, df_bound, on='ID')
result.to_csv('result.csv')
