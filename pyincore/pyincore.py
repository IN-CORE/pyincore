import logging
import sys
import csv
import rasterio
import fiona
import math
import collections
import json
import urllib.request
import requests   # http client module
import urllib.parse # joining path of url
import jsonpickle
import numpy as np
import re
import zipfile
import os, os.path

from shapely.geometry import shape
from scipy.stats import norm
from scipy.stats import lognorm
import scipy.stats as stats
import matplotlib.pyplot as plt

from typing import Dict

logging.basicConfig(stream = sys.stderr, level = logging.INFO)

class PlotUtil:
    @staticmethod
    def sample_lognormal_cdf_alt(mean: float, std: float, sample_size: int):
        dist = lognorm(s=std, loc=0, scale=np.exp(mean))
        start = dist.ppf(0.001) #cdf inverse
        end = dist.ppf(0.999) #cdf inverse
        x = np.linspace(start, end, sample_size)
        y = dist.cdf(x)
        return x, y

    @staticmethod
    def sample_lognormal_cdf(location: float, scale: float, sample_size: int):
        # convert location and scale parameters to the normal mean and std
        mean = np.log(np.square(location) / np.sqrt(scale + np.square(location)))
        std = np.sqrt(np.log((scale / np.square(location)) + 1))
        dist = lognorm(s=std, loc=0, scale=np.exp(mean))
        start = dist.ppf(0.001) #cdf inverse
        end = dist.ppf(0.999) #cdf inverse
        x = np.linspace(start, end, sample_size)
        y = dist.cdf(x)
        return x, y

    @staticmethod
    def sample_normal_cdf(mean: float, std: float, sample_size: int):
        dist = norm(mean, std)
        start = dist.ppf(0.001) #cdf inverse
        end = dist.ppf(0.999) #cdf inverse
        x = np.linspace(start, end, sample_size)
        y = dist.cdf(x)
        return x, y

    @staticmethod
    def get_x_y(disttype: str, alpha: float, beta: float):
        if disttype == 'LogNormal':
            return PlotUtil.sample_lognormal_cdf_alt(alpha, beta, 200)
        if disttype == 'Normal':
            return PlotUtil.sample_lognormal_cdf(alpha, beta, 200)
        if disttype == 'standardNormal':
            return PlotUtil.sample_normal_cdf(alpha, beta, 200)


class GeoUtil:
    @staticmethod
    def get_location(feature):
        geom = shape(feature['geometry'])
        return geom.centroid

    @staticmethod
    def create_output(filename, source, results, types):
        # the reults is the dictionary

        # create new schema
        new_schema = source.schema.copy()
        col_names = results[list(results.keys())[0]].keys()
        for col in col_names:
            new_schema['properties'][col] = types[col]
        empty_data = {}
        for col in col_names:
            empty_data[col] = None

        with fiona.open(
                filename, 'w',
                crs = source.crs,
                driver = source.driver,
                schema = new_schema,
        ) as sink:
            for f in source:
                try:
                    new_feature = f.copy()
                    if new_feature['id'] in results.keys():
                        new_feature['properties'].update(
                            results[new_feature['id']])
                    else:
                        new_feature['properties'].update(empty_data)
                    sink.write(new_feature)
                except Exception as e:
                    logging.exception("Error processing feature %s:", f['id'])


class InventoryDataset:
    inventory_set = None

    def __init__(self, filename):
        if os.path.isdir(filename):
            layers = fiona.listlayers(filename)
            if len(layers) > 0:
                # for now, open a first shapefile
                self.inventory_set = fiona.open(filename, layer = layers[0])
        else:
            self.inventory_set = fiona.open(filename)

    def close(self):
        self.inventory_set.close()

    def __del__(self):
        self.close()


class HazardDataset:
    hazard = None

    def __init__(self, filename):
        self.hazard = rasterio.open(filename)

    def get_hazard_value(self, location):
        row, col = self.hazard.index(location.x, location.y)
        # assume that there is only 1 band
        data = self.hazard.read(1)
        if row < 0 or col < 0 or row >= self.hazard.height or col >= self.hazard.width:
            return 0.0
        return np.asscalar(data[row, col])

    def close(self):
        self.hazard.close()

    def __del__(self):
        self.close()


class DamageRatioDataset:
    damage_ratio = None

    def __init__(self, filename):
        csvfile = open(filename, 'r')
        reader = csv.DictReader(csvfile)
        self.damage_ratio = []
        for row in reader:
            self.damage_ratio.append(row)


class MappingSubject(object):
    def __init__(self):
        self.schema = str()
        self.inventory = None  # Feature Collection


class MappingRequest(object):
    def __init__(self):
        self.params = dict()
        self.subject = MappingSubject()


class MappingResponse(object):
    def __init__(self, sets: Dict[str, any], mapping: Dict[str, str]):
        self.sets = sets
        self.mapping = mapping

    def __init__(self):
        self.sets = dict()  # fragility id to fragility
        self.mapping = dict() # inventory id to fragility id

        
class DataService:
    @staticmethod
    def unzip_dataset(local_filename: str):
        foldername, file_extension = os.path.splitext(local_filename)
        # if it is not a zip file, no unzip 
        if not file_extension.lower() == '.zip': 
            print('It is not a zip file; no unzip')
            return None
        # check the folder existance, no unzip
        if os.path.isdir(foldername): 
            print('It already exsists; no unzip')
            return foldername
        os.makedirs(foldername)
        
        zip_ref = zipfile.ZipFile(local_filename, 'r')
        zip_ref.extractall(foldername)
        zip_ref.close()
        return foldername
        
        
    @staticmethod
    def get_dataset_metadata(service: str, dataset_id: str):
        # construct url with service, dataset api, and id
        url = urllib.parse.urljoin(service, 'data/api/datasets/'+dataset_id)
        r = requests.get(url)
        return r.json()

    @staticmethod
    def get_dataset(service: str, dataset_id: str):
        # construct url for file download
        url = urllib.parse.urljoin(service, 'data/api/datasets/'+dataset_id+'/files')
        r = requests.get(url, stream=True)
        d = r.headers['content-disposition']
        fname = re.findall("filename=(.+)", d)
        local_filename = 'data/'+fname[0].strip('\"')
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024): 
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)

        folder = DataService.unzip_dataset(local_filename)
        if folder != None: 
            return folder
        else:
            return local_filename

        
class FragilityService:
    @staticmethod
    def map_fragility(service: str, inventory, key: str):
        mapping_request = MappingRequest()
        mapping_request.subject.schema = "building"
        mapping_request.subject.inventory = inventory
        mapping_request.params["key"] = key

        endpoint = service
        if not service.endswith('/'):
            endpoint = endpoint + '/'

        url = endpoint + "fragility/api/fragilities/map"

        json = jsonpickle.encode(mapping_request, unpicklable = False).encode("utf-8")
        request = urllib.request.Request(url, json, {'Content-Type': 'application/json'})
        response = urllib.request.urlopen(request)  # post
        content = response.read().decode('utf-8')

        mapping_response = jsonpickle.decode(content)

        fragility_set = next(iter(mapping_response["sets"].values()))

        return fragility_set


    @staticmethod
    def get_fragility_set(service, fragility_id: str, legacy: bool):
        endpoint = service
        if not service.endswith('/'):
            endpoint = endpoint + '/'

        url = ""
        if legacy:
            url = endpoint + "fragility/api/fragilities/query?legacyid=" + fragility_id + "&hazardType=Seismic&inventoryType=Building"
        else:
            url = endpoint + "fragility/api/fragilities/"+ fragility_id
        print(url)
        request = urllib.request.Request(url)
        response = urllib.request.urlopen(request)
        content = response.read().decode('utf-8')
        fragility_set = json.loads(content)

        return fragility_set

class BuildingUtil:

    @staticmethod
    def get_building_period(num_stories, fragility_set):
        period = 0.0

        fragility_curve = fragility_set['fragilityCurves'][0]
        if fragility_curve['className'] == 'edu.illinois.ncsa.incore.services.fragility.model.PeriodStandardFragilityCurve':
            period_equation_type = fragility_curve['periodEqnType']
            if period_equation_type == 1:
                period = fragility_curve['periodParam0']
            elif period_equation_type == 2:
                period = fragility_curve['periodParam0'] * num_stories
            elif period_equation_type == 3:
                period = fragility_curve['periodParam1'] * math.pow(fragility_curve['periodParam0'] * num_stories, fragility_curve['periodParam2'] )

        return period

class HazardService:

    @staticmethod
    def get_hazard_value(service: str, hazard_id: str, demand_type: str, demand_units: str, site_lat, site_long):
        endpoint = service
        if not service.endswith('/'):
            endpoint = endpoint + '/'

        hazard_service = endpoint + "hazard/api/earthquakes/" + hazard_id + "/"
        hazard_demand_type = urllib.parse.quote_plus(demand_type)

        request_url = hazard_service + "value?" + "siteLat="+str(site_lat) +  "&siteLong="+str(site_long)

        # Add Demand Type and Units
        request_url = request_url + "&demandType="+hazard_demand_type + "&demandUnits="+demand_units

        request = urllib.request.Request(request_url)
        response = urllib.request.urlopen(request)
        content = response.read().decode('utf-8')

        response = json.loads(content)

        return float(response['hazardValue'])

class ComputeDamage:
    @staticmethod
    def calculate_damage(bridge_fragility, hazard_value):
        output = collections.OrderedDict()
        limit_states = map(str.strip, bridge_fragility.getProperties()[
            'LimitStates'].split(":"))
        for i in range(len(limit_states)):
            limit_state = limit_states[i]
            fragility_curve = bridge_fragility.getFragilities()[i]
            if (fragility_curve.getType() == 'Normal'):
                median = float(fragility_curve.getProperties()
                               ['fragility-curve-median'])
                beta = float(fragility_curve.getProperties()
                             ['fragility-curve-beta'])
                sp = (math.log(hazard_value) - math.log(median)) / beta
                p = norm.cdf(sp)
                output['DS_' + limit_state] = p

        return output

    @staticmethod
    def calculate_damage_json(fragility_set, hazard):
        fragility_curves = fragility_set['fragilityCurves']
        output = collections.OrderedDict()

        index = 0
        limit_state = ['immocc', 'lifesfty', 'collprev']
        for fragility_curve in fragility_curves:
            median = float(fragility_curve['median'])
            beta = float(fragility_curve['beta'])
            # limit_state = fragility_curve['description']
            probability = float(0.0)

            if hazard > 0.0:
                if (fragility_curve['curveType'] == 'Normal'):
                    sp = (math.log(hazard_value) - math.log(median)) / beta
                    probability = norm.cdf(sp)
                elif (fragility_curve['curveType'] == "LogNormal"):
                    x = (math.log(hazard) - median) / beta
                    probability = norm.cdf(x)

            output[limit_state[index]] = probability
            index += 1

        return output
    
    @staticmethod
    def calculate_damage_json2(fragility_set, hazard):
        # using the "description" for limit_state
        fragility_curves = fragility_set['fragilityCurves']
        output = collections.OrderedDict()

        for fragility_curve in fragility_curves:
            median = float(fragility_curve['median'])
            beta = float(fragility_curve['beta'])
            # limit_state = fragility_curve['description']
            probability = float(0.0)

            if hazard > 0.0:
                if (fragility_curve['curveType'] == 'Normal'):
                    sp = (math.log(hazard_value) - math.log(median)) / beta
                    probability = norm.cdf(sp)
                elif (fragility_curve['curveType'] == "LogNormal"):
                    x = (math.log(hazard) - median) / beta
                    probability = norm.cdf(x)

            output[fragility_curve['description']] = probability

        return output
    
    @staticmethod
    def calculate_damage_interval(damage):
        output = collections.OrderedDict()
        if len(damage) == 4:
            output['I_None'] = 1.0 - damage['DS_Slight']
            output['I_Slight'] = damage['DS_Slight'] - damage['DS_Moderate']
            output['I_Moderate'] = damage['DS_Moderate'] - damage['DS_Extensive']
            output['I_Extensive'] = damage['DS_Extensive'] - damage['DS_Complete']
            output['I_Complete'] = damage['DS_Complete']
        elif len(damage) == 3:
            output['insignific'] = 1.0 - damage['immocc']
            output['moderate'] = damage['immocc'] - damage['lifesfty']
            output['heavy'] = damage['lifesfty'] - damage['collprev']
            output['complete'] = damage['collprev']
        return output

    @staticmethod
    def calculate_mean_damage(weights, dmg_intervals):
        output = collections.OrderedDict()
        if len(weights) == 5:
            output['MeanDamage'] = weights[0] * float(dmg_intervals['I_None']) \
                                   + weights[1] * float(dmg_intervals['I_Slight']) \
                                   + weights[2] * float(dmg_intervals['I_Moderate']) \
                                   + weights[3] * float(dmg_intervals['I_Extensive']) \
                                   + weights[4] * float(dmg_intervals['I_Complete'])
        elif len(weights) == 4:
            output['meandamage'] = float(weights[0]) * float(dmg_intervals['insignific']) + float(weights[1]) * float(
                dmg_intervals['moderate']) + float(weights[2]) * float(dmg_intervals['heavy']) + float(weights[3]) * float(
                dmg_intervals['complete'])
        return output

    @staticmethod
    def calculate_mean_damage_std_deviation(weights, weights_std_dev, dmg_intervals, mean_damage):
        output = collections.OrderedDict()
        result = 0.0

        idx = 0
        for dmg_interval in dmg_intervals:
            result += dmg_intervals[dmg_interval] * (math.pow(weights[idx], 2) + math.pow(weights_std_dev[idx], 2))
            idx += 1

        output['mdamagedev'] = math.sqrt(result - math.pow(mean_damage, 2))
        return output


if __name__ == "__main__":
    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    # test code here
    
