import urllib

import numpy
import requests
from typing import List

from pyincore import IncoreClient


class HazardService:
    """
    Hazard service client
    """
    def __init__(self, client: IncoreClient):
        self.client = client
        self.base_earthquake_url = urllib.parse.urljoin(client.service_url, 'hazard/api/earthquakes/')
        self.base_tornado_url = urllib.parse.urljoin(client.service_url, 'hazard/api/tornadoes/')
        self.base_tsunami_url = urllib.parse.urljoin(client.service_url, 'hazard/api/tsunamis/')
        self.base_hurricanewf_url = urllib.parse.urljoin(client.service_url, 'hazard/api/hurricaneWindfields/')

    def get_earthquake_hazard_metadata(self, hazard_id:str):
        url = urllib.parse.urljoin(self.base_earthquake_url, hazard_id)
        r = requests.get(url, headers=self.client.headers)
        response = r.json()

        return response

    def get_earthquake_hazard_value(self, hazard_id: str, demand_type: str, demand_units: str, site_lat, site_long):
        hazard_value_set = self.get_earthquake_hazard_values(hazard_id, demand_type, demand_units,
            points=str(site_lat) + ',' + str(site_long))
        return hazard_value_set[0]['hazardValue']

    def get_earthquake_hazard_values(self, hazard_id: str, demand_type: str, demand_units: str, points: List):
        url = urllib.parse.urljoin(self.base_earthquake_url, hazard_id + "/values")
        payload = {'demandType': demand_type, 'demandUnits': demand_units, 'point': points}
        r = requests.get(url, headers=self.client.headers, params = payload)
        response = r.json()

        return response

    def get_earthquake_hazard_value_set(self, hazard_id: str, demand_type: str, demand_units: str, bbox, grid_spacing: float):
        # bbox: [[minx, miny],[maxx, maxy]]
        # raster?demandType=0.2+SA&demandUnits=g&minX=-90.3099&minY=34.9942&maxX=-89.6231&maxY=35.4129&gridSpacing=0.01696
        # bbox
        url = urllib.parse.urljoin(self.base_earthquake_url, hazard_id + "/raster")
        payload = {'demandType': demand_type, 'demandUnits': demand_units, 'minX': bbox[0][0], 'minY': bbox[0][1],
                   'maxX': bbox[1][0], 'maxY': bbox[1][1], 'gridSpacing': grid_spacing}
        r = requests.get(url, headers=self.client.headers, params = payload)
        response = r.json()

        # TODO: need to handle error with the request
        xlist = []
        ylist = []
        zlist = []
        for entry in response['hazardResults']:
            xlist.append(float(entry['longitude']))
            ylist.append(float(entry['latitude']))
            zlist.append(float(entry['hazardValue']))
        x = numpy.array(xlist)
        y = numpy.array(ylist)
        hazard_val = numpy.array(zlist)

        return x, y, hazard_val

    def get_liquefaction_values(self, hazard_id: str, geology_dataset_id: str, demand_units: str, points: List):
        url = urllib.parse.urljoin(self.base_earthquake_url,  hazard_id+"/liquefaction/values")
        payload = {'demandUnits': demand_units, 'geologyDataset': geology_dataset_id, 'point': points}
        r = requests.get(url, headers=self.client.headers, params=payload)
        response = r.json()
        return response

    def create_earthquake(self, config):
        url = self.base_earthquake_url
        eq_data = {'earthquake': config}
        r = requests.post(url, files=eq_data, headers=self.client.headers)
        response = r.json()
        return response

    def get_tornado_hazard_metadata(self, hazard_id:str):
        url = urllib.parse.urljoin(self.base_tornado_url, hazard_id)
        r = requests.get(url, headers=self.client.headers)
        response = r.json()

        return response

    def get_tornado_hazard_value(self, hazard_id: str, demand_units: str, site_lat, site_long, simulation=0):
        points = str(site_lat) + ',' + str(site_long)

        hazard_value_set = self.get_tornado_hazard_values(hazard_id, demand_units, points, simulation)
        return hazard_value_set[0]['hazardValue']

    def get_tornado_hazard_values(self, hazard_id: str, demand_units: str, points: List, simulation=0):
        url = urllib.parse.urljoin(self.base_tornado_url, hazard_id + "/values")
        payload = {'demandUnits': demand_units, 'point': points, 'simulation': simulation}
        r = requests.get(url, headers=self.client.headers, params = payload)
        response = r.json()

        return response

    def create_tornado_scenario(self, scenario):
        url = self.base_tornado_url

        headers = {'Content-type': 'application/json'}
        # merge two headers
        new_headers = {**self.client.headers, **headers}
        r = requests.post(url, data=scenario, headers=new_headers)
        response = r.json()
        return response

    def get_tsunami_hazard_metadata(self, hazard_id:str):
        url = urllib.parse.urljoin(self.base_tsunami_url, hazard_id)
        r = requests.get(url, headers=self.client.headers)
        response = r.json()

        return response

    def get_tsunami_hazard_values(self, hazard_id: str, demand_type: str, demand_units: str, points: List):
        url = urllib.parse.urljoin(self.base_tsunami_url, hazard_id + "/values")
        payload = {'demandType': demand_type, 'demandUnits': demand_units, 'point': points}
        r = requests.get(url, headers=self.client.headers, params = payload)
        response = r.json()

        return response

    def create_hurricane_windfield(self, hurr_wf_inputs):
        url = self.base_hurricanewf_url
        headers = {'Content-type': 'application/json'}
        new_headers = {**self.client.headers, **headers}
        r = requests.post(url, data=hurr_wf_inputs, headers=new_headers)
        response = r.json()
        return response

    def get_hurricanewf_metadata(self, hazard_id):
        url = urllib.parse.urljoin(self.base_hurricanewf_url, hazard_id)
        r = requests.get(url, headers=self.client.headers)
        response = r.json()

        return response
    
    def get_hurricanewf_values(self, hazard_id: str, demand_type: str, demand_units: str, points: List):
        url = urllib.parse.urljoin(self.base_hurricanewf_url, hazard_id + "/values")
        payload = {'demandType': demand_type, 'demandUnits': demand_units, 'point': points}
        r = requests.get(url, headers=self.client.headers, params = payload)
        response = r.json()

        return response
