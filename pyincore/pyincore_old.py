import logging
import sys
import csv
import rasterio
import fiona
import math
import collections
import numpy as np
import os
import os.path

from scipy.stats import norm
from wikidata.client import Client as wikidata_client


logging.basicConfig(stream = sys.stderr, level = logging.INFO)




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
                period = fragility_curve['periodParam1'] * math.pow(fragility_curve['periodParam0'] * num_stories,
                                                                    fragility_curve['periodParam2'])

        return period



class GlossaryService:
    @staticmethod
    def get_term(service: str, term: str):
        client = wikidata_client(service)
        # definition_prop = client.get('P13')  # definition
        # image_prop = client.get('P4')  # image
        entity = client.get(term, load = True)
        return entity


class ComputeDamage:
    @staticmethod
    def calculate_damage(bridge_fragility, hazard_value):
        output = collections.OrderedDict()
        limit_states = map(str.strip, bridge_fragility.getProperties()[
            'LimitStates'].split(":"))
        for i in range(len(limit_states)):
            limit_state = limit_states[i]
            fragility_curve = bridge_fragility.getFragilities()[i]
            if fragility_curve.getType() == 'Normal':
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

    pp = pprint.PrettyPrinter(indent = 4)
    # test code here
