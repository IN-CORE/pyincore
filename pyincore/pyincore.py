import base64
import collections
import csv
import logging
import math
import os
import os.path
import re
import sys
import urllib.parse  # joining path of url
import urllib.request
import zipfile
from typing import Dict

import fiona
import jsonpickle
import numpy as np
import rasterio
import requests  # http client module
from scipy.stats import lognorm
from scipy.stats import norm
from shapely.geometry import shape
from wikidata.client import Client as wikidata_client

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
    @staticmethod
    def get_datasets(service: str, datatype=None, title=None):
        url = urllib.parse.urljoin(service, 'data/api/datasets')
        if datatype == None and title == None:
            r = requests.get(url)
            return r.json()
        else:
            payload = {}
            if datatype != None:
                payload['type'] = datatype
            if title != None:
                payload['title'] = title
            r = requests.get(url, params=payload)
            # need to handle there is no datasets
            return r.json()
        
class FragilityService:
    @staticmethod
    def map_fragility(service: str, inventory, key: str):
        mapping_request = MappingRequest()
        mapping_request.subject.schema = "building"
        mapping_request.subject.inventory = inventory
        mapping_request.params["key"] = key

        url = urllib.parse.urljoin(service, "fragility/api/fragilities/map")
        
        json = jsonpickle.encode(mapping_request, unpicklable = False).encode("utf-8")

        r = requests.post(url, data=json, headers={'Content-type':'application/json'})
        
        response = r.json()
        
        fragility_set = next(iter(response["sets"].values()))

        return fragility_set

    @staticmethod
    def get_fragility_set(service: str, fragility_id: str, legacy: bool):
        url = None
        if legacy: 
            url = urllib.parse.urljoin(service, "fragility/api/fragilities/query?legacyid=" + fragility_id + "&hazardType=Seismic&inventoryType=Building")
        else:
            url = urllib.parse.urljoin(service, "fragility/api/fragilities/"+ fragility_id)
        r = requests.get(url)

        return r.json()

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
        url = urllib.parse.urljoin(service, "hazard/api/earthquakes/"+ hazard_id+"/value")
        payload = {'demandType':demand_type, 'demandUnits':demand_units, 'siteLat':site_lat, 'siteLong':site_long}
        r = requests.get(url, params=payload)
        response = r.json()
        
        return float(response['hazardValue'])
    def get_hazard_value_set(service: str, hazard_id: str, demand_type: str, demand_units: str, bbox, grid_spacing: float):
        # bbox: [[minx, miny],[maxx, maxy]]
        # raster?demandType=0.2+SA&demandUnits=g&minX=-90.3099&minY=34.9942&maxX=-89.6231&maxY=35.4129&gridSpacing=0.01696
        bbox
        url = urllib.parse.urljoin(service, "hazard/api/earthquakes/"+ hazard_id+"/raster")
        payload = {'demandType':demand_type, 'demandUnits':demand_units, 'minX':bbox[0][0], 'minY':bbox[0][1], 'maxX': bbox[1][0], 'maxY': bbox[1][1], 'gridSpacing': grid_spacing}
        r = requests.get(url, params=payload)
        response = r.json()
        
        # TODO: need to handle error with the request
        xlist = []
        ylist = []
        zlist = []
        for entry in response['hazardResults']:
            xlist.append(float(entry['longitude']))
            ylist.append(float(entry['latitude']))
            zlist.append(float(entry['hazardValue']))
        x = np.array(xlist)
        y = np.array(ylist)
        hazard_val = np.array(zlist)
        return x, y, hazard_val


class GlossaryService:
    @staticmethod
    def get_term(service: str, term: str):
        client = wikidata_client(service)
        # definition_prop = client.get('P13')  # definition
        # image_prop = client.get('P4')  # image
        entity = client.get(term, load = True)
        return entity


class AuthService:
    """
    Authentication service
    """
    def __init__(self, service_url):
        self.service_url = service_url

    def get_token(self, username: str, password: str):
        url = urllib.parse.urljoin(self.service_url, "auth/api/login")
        b64_value = base64.b64encode(bytes('%s:%s' % (username, password), "utf-8"))
        r = requests.get(url, headers={"Authorization": "LDAP %s" % b64_value.decode('ascii')})
        print(r.request.headers['Authorization'])
        return r.json()


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
