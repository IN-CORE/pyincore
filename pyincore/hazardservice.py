import urllib

import requests
from typing import List

from pyincore import IncoreClient


class HazardService:
    """
    Hazard service client
    """
    def __init__(self, client: IncoreClient):
        self.client = client
        self.base_earthquake_url = str(urllib.parse.urljoin(client.service_url, 'hazard/api/earthquakes'))

    def get_hazard_value(self, hazard_id: str, demand_type: str, demand_units: str, site_lat, site_long):
        url = urllib.parse.urljoin(self.base_earthquake_url, hazard_id + "/value")
        payload = {'demandType': demand_type, 'demandUnits': demand_units, 'siteLat': site_lat, 'siteLong': site_long}
        r = requests.get(url, params = payload)
        response = r.json()

        return float(response['hazardValue'])

    def get_hazard_values(self, hazard_id: str, demand_type: str, demand_units: str, points: List):
        url = urllib.parse.urljoin(self.base_earthquake_url, hazard_id + "/values")
        payload = {'demandType': demand_type, 'demandUnits': demand_units, 'point': points}

        r = requests.get(url, params=payload)
        response = r.json()

        return response['hazardResults']

    def get_hazard_value_set(self, hazard_id: str, demand_type: str, demand_units: str, bbox, grid_spacing: float):
        # bbox: [[minx, miny],[maxx, maxy]]
        # raster?demandType=0.2+SA&demandUnits=g&minX=-90.3099&minY=34.9942&maxX=-89.6231&maxY=35.4129&gridSpacing=0.01696
        # bbox
        url = urllib.parse.urljoin(self.base_earthquake_url, hazard_id + "/raster")
        payload = {'demandType': demand_type, 'demandUnits': demand_units, 'minX': bbox[0][0], 'minY': bbox[0][1],
                   'maxX': bbox[1][0], 'maxY': bbox[1][1], 'gridSpacing': grid_spacing}
        r = requests.get(url, params = payload)
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
