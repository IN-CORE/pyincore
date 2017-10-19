import logging
import sys
import csv
import rasterio
import fiona
import math
import collections
import json
import urllib.request
import jsonpickle
import numpy as np

from shapely.geometry import shape
from scipy.stats import norm

from typing import Dict

logging.basicConfig(stream = sys.stderr, level = logging.INFO)


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


class FragilityResource:
    @staticmethod
    def map_fragility(service: str, inventory, key: str):
        mapping_request = MappingRequest()
        mapping_request.subject.schema = "building"
        mapping_request.subject.inventory = inventory
        mapping_request.params["key"] = key

        endpoint = service
        if not service.endswith('/'):
            endpoint = endpoint + '/'

        url = endpoint + "api/fragilities/map"

        json = jsonpickle.encode(mapping_request, unpicklable = False).encode("utf-8")
        request = urllib.request.Request(url, json, {'Content-Type': 'application/json'})
        response = urllib.request.urlopen(request)  # post
        content = response.read().decode('utf-8')

        mapping_response = jsonpickle.decode(content)

        fragility_set = next(iter(mapping_response["sets"].values()))

        return fragility_set


    @staticmethod
    def get_fragility_set(service, fragility_id: str, legacy: str):
        endpoint = service
        if not service.endswith('/'):
            endpoint = endpoint + '/'

        url = endpoint + "api/fragilities/query?legacyid=" + fragility_id + "&hazardType=Seismic&inventoryType=Building"

        request = urllib.request.Request(url)
        response = urllib.request.urlopen(request)
        content = response.read().decode('utf-8')
        fragility_set = json.loads(content)

        return fragility_set[0]


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
