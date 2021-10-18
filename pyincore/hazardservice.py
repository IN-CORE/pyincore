# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import json
import urllib
from typing import List

import numpy

from pyincore import IncoreClient


class HazardService:
    """Hazard service client

    Args:
        client (IncoreClient): Service authentication.

    """

    def __init__(self, client: IncoreClient):
        self.client = client

        self.base_earthquake_url = urllib.parse.urljoin(client.service_url,
                                                        'hazard/api/earthquakes/')
        self.base_tornado_url = urllib.parse.urljoin(client.service_url,
                                                     'hazard/api/tornadoes/')
        self.base_tsunami_url = urllib.parse.urljoin(client.service_url,
                                                     'hazard/api/tsunamis/')
        self.base_hurricane_url = urllib.parse.urljoin(client.service_url, 'hazard/api/hurricanes/')
        self.base_hurricanewf_url = urllib.parse.urljoin(client.service_url,
                                                         'hazard/api/hurricaneWindfields/')
        self.base_flood_url = urllib.parse.urljoin(client.service_url, 'hazard/api/floods/')

    def get_earthquake_hazard_metadata_list(self, skip: int = None, limit: int = None, space: str = None):
        """Retrieve earthquake metadata list from hazard service. Hazard API endpoint is called.

        Args:
            skip (int):  Skip the first n results, passed to the parameter "skip". Dafault None.
            limit (int):  Limit number of results to return. Passed to the parameter "limit". Dafault None.
            space (str): User's namespace on the server, passed to the parameter "space". Dafault None.

        Returns:
            json: Response containing the metadata.

        """
        url = self.base_earthquake_url
        payload = {}
        if skip is not None:
            payload['skip'] = skip
        if limit is not None:
            payload['limit'] = limit
        if space is not None:
            payload['space'] = space

        r = self.client.get(url, params=payload)
        response = r.json()

        return response

    def get_earthquake_hazard_metadata(self, hazard_id: str):
        """Retrieve earthquake metadata from hazard service. Hazard API endpoint is called.

        Args:
            hazard_id (str): ID of the Earthquake.

        Returns:
            json: Response containing the metadata.

        """
        url = urllib.parse.urljoin(self.base_earthquake_url, hazard_id)
        r = self.client.get(url)
        response = r.json()

        return response

    def get_earthquake_hazard_value_set(self, hazard_id: str, demand_type: str,
                                        demand_unit: str, bbox,
                                        grid_spacing: float):
        """Retrieve earthquake hazard value set from the Hazard service.

        Args:
            hazard_id (str): ID of the Earthquake.
            demand_type (str):  Ground motion demand type. Examples: PGA, PGV, 0.2 SA
            demand_unit (str): Ground motion demand unit. Examples: g, %g, cm/s, etc.
            bbox (list): Bounding box, list of points.
            grid_spacing (float): Grid spacing.

        Returns:
            np.array: X values..
            np.array: Y values.
            np.array: Hazard value.

        """
        # bbox: [[minx, miny],[maxx, maxy]]
        # raster?demandType=0.2+SA&demandUnits=g&minX=-90.3099&minY=34.9942&maxX=-89.6231&maxY=35.4129&gridSpacing=0.01696
        # bbox
        url = urllib.parse.urljoin(self.base_earthquake_url,
                                   hazard_id + "/raster")
        payload = {'demandType': demand_type, 'demandUnits': demand_unit,
                   'minX': bbox[0][0], 'minY': bbox[0][1],
                   'maxX': bbox[1][0], 'maxY': bbox[1][1],
                   'gridSpacing': grid_spacing}
        r = self.client.get(url, params=payload)
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

    def post_earthquake_hazard_values(self, hazard_id: str, payload: list, amplify_hazard=True):
        """ Retrieve bulk hurricane hazard values from the Hazard service.

        Args:
            hazard_id (str): ID of the Earthquake.
            payload (list):
            [
                {
                    "demands": ["PGA", "1.0 SD", "0.9 SA", "1.0 SA", "PGV"],
                    "units": ["g", "cm", "g", "g", "in/s"],
                    "loc": "35.84,-89.90"
                },
                {
                    "demands": ["1.0 SD", "1.0 SA"],
                    "units": ["cm", "g"],
                    "amplifyHazards": [false, false],
                    "loc": "35.84,-89.90"
                }
            ]
        Returns:
            obj: Hazard values.

        """
        url = urllib.parse.urljoin(self.base_earthquake_url, hazard_id + "/values")
        kwargs = {"files": {('points', json.dumps(payload)), ('amplifyHazard', json.dumps(amplify_hazard))}}
        r = self.client.post(url, **kwargs)
        response = r.json()

        return response

    def get_liquefaction_values(self, hazard_id: str, geology_dataset_id: str,
                                demand_unit: str, points: List):
        """Retrieve earthquake liquefaction values.

        Args:
            hazard_id (str): ID of the Earthquake.
            geology_dataset_id (str):  ID of the geology dataset.
            demand_unit (str): Ground motion demand unit. Examples: g, %g, cm/s, etc.
            points (list): List of points provided as lat,long.

        Returns:
            obj: HTTP response.

        """
        url = urllib.parse.urljoin(self.base_earthquake_url,
                                   hazard_id + "/liquefaction/values")
        payload = {'demandUnits': demand_unit,
                   'geologyDataset': geology_dataset_id, 'point': points}
        r = self.client.get(url, params=payload)
        response = r.json()
        return response

    def post_liquefaction_values(self, hazard_id: str, geology_dataset_id: str, payload: list):
        """ Retrieve bulk earthquake liquefaction hazard values from the Hazard service.

        Args:
            hazard_id (str): ID of the Tornado.
            payload (list):
        Returns:
            obj: Hazard values.

        """
        url = urllib.parse.urljoin(self.base_earthquake_url, hazard_id + "/liquefaction/values")
        kwargs = {"files": {('points', json.dumps(payload)), ('geologyDataset', geology_dataset_id)}}
        r = self.client.post(url, **kwargs)
        response = r.json()

        return response

    def get_soil_amplification_value(self, method: str, dataset_id: str,
                                     site_lat: float, site_long: float,
                                     demand_type: str, hazard: float,
                                     default_site_class: str):
        """Retrieve earthquake liquefaction values.

        Args:
            method (str): ID of the Earthquake.
            dataset_id (str): ID of the Dataset.
            site_lat (float): Latitude of a point.
            site_long (float): Longitude of a point.
            demand_type (str):  Ground motion demand type. Examples: PGA, PGV, 0.2 SA
            hazard (float): Hazard value.
            default_site_class (str): Default site classification. Expected A, B, C, D, E or F.

        Returns:
            obj: HTTP response.

        """
        url = urllib.parse.urljoin(self.base_earthquake_url,
                                   'soil/amplification')
        payload = {"method": method, "datasetId": dataset_id,
                   "siteLat": site_lat, "siteLong": site_long,
                   "demandType": demand_type, "hazard": hazard,
                   "defaultSiteClass": default_site_class}
        r = self.client.get(url, params=payload)
        response = r.json()
        return response

    # TODO get_slope_amplification_value needed to be implemented on the server side
    # def get_slope_amplification_value(self)

    def get_supported_earthquake_models(self):
        """Retrieve suported earthquake models.

        Returns:
            obj: HTTP response.

        """
        url = urllib.parse.urljoin(self.base_earthquake_url, 'models')
        r = self.client.get(url)
        response = r.json()

        return response

    def create_earthquake(self, eq_json, file_paths: List = []):
        """Create earthquake on the server. POST API endpoint is called.

        Args:
            eq_json (json): Json representing the Earthquake.
            file_paths (list): List of strings pointing to the paths of the datasets. Not needed for
                model based earthquakes. Default empty list.

        Returns:
            obj: HTTP POST Response. Json of the earthquake posted to the server.

        """
        url = self.base_earthquake_url
        eq_data = {('earthquake', eq_json)}

        for file_path in file_paths:
            eq_data.add(('file', open(file_path, 'rb')))
        kwargs = {"files": eq_data}
        r = self.client.post(url, **kwargs)
        response = r.json()
        return response

    def delete_earthquake(self, hazard_id: str):
        """Delete an earthquake by it's id, and it's associated datasets

        Args:
            hazard_id (str): ID of the Earthquake.

        Returns:
            obj: Json of deleted hazard

        """
        url = urllib.parse.urljoin(self.base_earthquake_url, hazard_id)
        r = self.client.delete(url)
        return r.json()

    def search_earthquakes(self, text: str, skip: int = None, limit: int = None):
        """Search earthquakes.

        Args:
            text (str): Text to search by, passed to the parameter "text".
            skip (int):  Skip the first n results, passed to the parameter "skip". Dafault None.
            limit (int):  Limit number of results to return. Passed to the parameter "limit". Dafault None.

        Returns:
            obj: HTTP response with search results.

        """
        url = urllib.parse.urljoin(self.base_earthquake_url, "search")
        payload = {"text": text}
        if skip is not None:
            payload['skip'] = skip
        if limit is not None:
            payload['limit'] = limit

        r = self.client.get(url, params=payload)

        return r.json()

    def get_earthquake_aleatory_uncertainty(self, hazard_id: str, demand_type: str):
        """ Gets aleatory uncertainty for an earthquake

        Args:
            hazard_id (str): ID of the Earthquake
            demand_type (str):  Ground motion demand type. Examples: PGA, PGV, 0.2 SA

        Returns:
             obj: HTTP POST Response with aleatory uncertainty value.

        """
        url = urllib.parse.urljoin(self.base_earthquake_url, hazard_id + "/aleatoryuncertainty")
        payload = {"demandType": demand_type}

        r = self.client.get(url, params=payload)
        return r.json()

    def get_earthquake_variance(self, hazard_id: str, variance_type: str, demand_type: str,
                                demand_unit: str, points: List):
        """Gets total and epistemic variance for a model based earthquake

        Args:
            hazard_id (str): ID of the Earthquake
            variance_type (str): Type of Variance. epistemic or total
            demand_type (str):  Ground motion demand type. Examples: PGA, PGV, 0.2 SA
            demand_unit (str): Demand unit. Examples: g, in
            points (list): List of points provided as lat,long.

        Returns:
            obj: HTTP POST Response with variance value.

        """
        url = urllib.parse.urljoin(self.base_earthquake_url, hazard_id + "/variance/" + variance_type)
        payload = {"demandType": demand_type, "demandUnits": demand_unit, 'point': points}

        r = self.client.get(url, params=payload)
        return r.json()

    def get_tornado_hazard_metadata_list(self, skip: int = None, limit: int = None, space: str = None):
        """Retrieve tornado metadata list from hazard service. Hazard API endpoint is called.

        Args:
            skip (int):  Skip the first n results, passed to the parameter "skip". Dafault None.
            limit (int):  Limit number of results to return. Passed to the parameter "limit". Dafault None.
            space (str): User's namespace on the server, passed to the parameter "space". Dafault None.

        Returns:
            obj: HTTP response containing the metadata.

        """
        url = self.base_tornado_url
        payload = {}
        if skip is not None:
            payload['skip'] = skip
        if limit is not None:
            payload['limit'] = limit
        if space is not None:
            payload['space'] = space

        r = self.client.get(url, params=payload)
        response = r.json()

        return response

    def get_tornado_hazard_metadata(self, hazard_id: str):
        """Retrieve tornado metadata list from hazard service. Hazard API endpoint is called.

        Args:
            hazard_id (str): ID of the Tornado.

        Returns:
            obj: HTTP response containing the metadata.

        """
        url = urllib.parse.urljoin(self.base_tornado_url, hazard_id)
        r = self.client.get(url)
        response = r.json()

        return response

    def post_tornado_hazard_values(self, hazard_id: str, payload: list, seed=None):
        """ Retrieve bulk tornado hazard values from the Hazard service.

        Args:
            hazard_id (str): ID of the Tornado.
            payload (list):
            seed: (None or int): Seed value for random values.
        Returns:
            obj: Hazard values.

        """
        url = urllib.parse.urljoin(self.base_tornado_url, hazard_id + "/values")

        if seed is not None:
            kwargs = {"files": {('points', json.dumps(payload)), ('seed', json.dumps(seed))}}
        else:
            kwargs = {"files": {('points', json.dumps(payload))}}

        r = self.client.post(url, **kwargs)
        response = r.json()

        return response

    def create_tornado_scenario(self, tornado_json, file_paths: List = []):
        """Create tornado on the server. POST API endpoint is called.

        Args:
            tornado_json (json): JSON representing the tornado.
            file_paths (list): List of strings pointing to the paths of the shape files. Not needed for
                model based tornadoes.

        Returns:
            obj: HTTP POST Response. Json of the created tornado.

        """
        url = self.base_tornado_url
        tornado_data = {('tornado', tornado_json)}

        for file_path in file_paths:
            tornado_data.add(('file', open(file_path, 'rb')))
        kwargs = {"files": tornado_data}
        r = self.client.post(url, **kwargs)
        response = r.json()
        return response

    def delete_tornado(self, hazard_id: str):
        """Delete a tornado by it's id, and it's associated datasets

        Args:
            hazard_id (str): ID of the Tornado.

        Returns:
            obj: Json of deleted hazard

        """
        url = urllib.parse.urljoin(self.base_tornado_url, hazard_id)
        r = self.client.delete(url)
        return r.json()

    def search_tornadoes(self, text: str, skip: int = None, limit: int = None):
        """Search tornadoes.

        Args:
            text (str): Text to search by, passed to the parameter "text".
            skip (int):  Skip the first n results, passed to the parameter "skip". Dafault None.
            limit (int):  Limit number of results to return. Passed to the parameter "limit". Dafault None.

        Returns:
            obj: HTTP response with search results.

        """
        url = urllib.parse.urljoin(self.base_tornado_url, "search")
        payload = {"text": text}
        if skip is not None:
            payload['skip'] = skip
        if limit is not None:
            payload['limit'] = limit

        r = self.client.get(url, params=payload)

        return r.json()

    def get_tsunami_hazard_metadata_list(self, skip: int = None, limit: int = None, space: str = None):
        """Retrieve tsunami metadata list from hazard service. Hazard API endpoint is called.

        Args:
            skip (int): Skip the first n results, passed to the parameter "skip". Dafault None.
            limit (int): Limit number of results to return. Passed to the parameter "limit". Dafault None.
            space (str): User's namespace on the server, passed to the parameter "space". Dafault None.

        Returns:
            obj: HTTP response containing the metadata.

        """
        url = self.base_tsunami_url
        payload = {}
        if skip is not None:
            payload['skip'] = skip
        if limit is not None:
            payload['limit'] = limit
        if space is not None:
            payload['space'] = space

        r = self.client.get(url, params=payload)
        response = r.json()

        return response

    def get_tsunami_hazard_metadata(self, hazard_id: str):
        """Retrieve tsunami metadata list from hazard service. Hazard API endpoint is called.

        Args:
            hazard_id (str): ID of the Tsunami.

        Returns:
            obj: HTTP response containing the metadata.

        """
        url = urllib.parse.urljoin(self.base_tsunami_url, hazard_id)
        r = self.client.get(url)
        response = r.json()

        return response

    def post_tsunami_hazard_values(self, hazard_id: str, payload: list):
        """ Retrieve bulk tsunami hazard values from the Hazard service.

        Args:
            hazard_id (str): ID of the Tsunami.
            payload (list):
        Returns:
            obj: Hazard values.

        """
        url = urllib.parse.urljoin(self.base_tsunami_url, hazard_id + "/values")
        kwargs = {"files": {('points', json.dumps(payload))}}
        r = self.client.post(url, **kwargs)
        response = r.json()

        return response

    def create_tsunami_hazard(self, tsunami_json, file_paths: List):
        """Create tsunami on the server. POST API endpoint is called.

        Args:
            tsunami_json: JSON representing the tsunami.
            file_paths: List of strings pointing to the paths of the datasets.

        Returns:
            obj: HTTP POST Response. Json of the created tsunami.

        """

        url = self.base_tsunami_url
        tsunami_data = {('tsunami', tsunami_json)}

        for file_path in file_paths:
            tsunami_data.add(('file', open(file_path, 'rb')))
        kwargs = {"files": tsunami_data}
        r = self.client.post(url, **kwargs)
        response = r.json()
        return response

    def delete_tsunami(self, hazard_id: str):
        """Delete a tsunami by it's id, and it's associated datasets

        Args:
            hazard_id (str): ID of the Tsunami.

        Returns:
            obj: Json of deleted hazard

        """
        url = urllib.parse.urljoin(self.base_tsunami_url, hazard_id)
        r = self.client.delete(url)
        return r.json()

    def search_tsunamis(self, text: str, skip: int = None, limit: int = None):
        """Search tsunamis.

        Args:
            text (str): Text to search by, passed to the parameter "text".
            skip (int):  Skip the first n results, passed to the parameter "skip". Default None.
            limit (int):  Limit number of results to return. Passed to the parameter "limit". Dafault None.

        Returns:
            obj: HTTP response with search results.

        """
        url = urllib.parse.urljoin(self.base_tsunami_url, "search")
        payload = {"text": text}
        if skip is not None:
            payload['skip'] = skip
        if limit is not None:
            payload['limit'] = limit

        r = self.client.get(url, params=payload)

        return r.json()

    def create_hurricane(self, hurricane_json, file_paths: List):
        """Create hurricanes on the server. POST API endpoint is called.

        Args:
            hurricane_json (obj): JSON representing the hurricane.

        Returns:
            obj: HTTP POST Response. Json of the created hurricane.

        """
        url = self.base_hurricane_url
        hurricane_data = {('hurricane', hurricane_json)}

        for file_path in file_paths:
            hurricane_data.add(('file', open(file_path, 'rb')))
        kwargs = {"files": hurricane_data}
        r = self.client.post(url, **kwargs)
        response = r.json()

        return response

    def get_hurricane_metadata_list(self, skip: int = None, limit: int = None, space: str = None):
        """Retrieve hurricane metadata list from hazard service. Hazard API endpoint is called.

        Args:
            skip (int):  Skip the first n results, passed to the parameter "skip". Default None.
            limit (int):  Limit number of results to return. Passed to the parameter "limit". Default None.
            space (str): User's namespace on the server, passed to the parameter "space". Default None.

        Returns:
            obj: HTTP response containing the metadata.

        """
        url = self.base_hurricane_url
        payload = {}

        if skip is not None:
            payload['skip'] = skip
        if limit is not None:
            payload['limit'] = limit
        if space is not None:
            payload['space'] = space

        r = self.client.get(url, params=payload)
        response = r.json()

        return response

    def get_hurricane_metadata(self, hazard_id):
        """Retrieve hurricane metadata list from hazard service. Hazard API endpoint is called.

        Args:
            hazard_id (str): ID of the Hurricane.

        Returns:
            obj: HTTP response containing the metadata.

        """
        url = urllib.parse.urljoin(self.base_hurricane_url, hazard_id)
        r = self.client.get(url)
        response = r.json()

        return response

    def post_hurricane_hazard_values(self, hazard_id: str, payload: list):
        """ Retrieve bulk hurricane hazard values from the Hazard service.

        Args:
            hazard_id (str): ID of the Hurricane.
            payload (list):
        Returns:
            obj: Hazard values.

        """
        url = urllib.parse.urljoin(self.base_hurricane_url, hazard_id + "/values")
        kwargs = {"files": {('points', json.dumps(payload))}}
        r = self.client.post(url, **kwargs)
        response = r.json()

        return response

    def delete_hurricane(self, hazard_id: str):
        """Delete a hurricane by it's id, and it's associated datasets

        Args:
            hazard_id (str): ID of the Hurricane.

        Returns:
            obj: Json of deleted hazard

        """
        url = urllib.parse.urljoin(self.base_hurricane_url, hazard_id)
        r = self.client.delete(url)
        return r.json()

    def search_hurricanes(self, text: str, skip: int = None, limit: int = None):
        """Search hurricanes.

        Args:
            text (str): Text to search by, passed to the parameter "text".
            skip (int):  Skip the first n results, passed to the parameter "skip", default None.
            limit (int):  Limit number of results to return. Passed to the parameter "limit", default None.

        Returns:
            obj: HTTP response with search results.

        """
        url = urllib.parse.urljoin(self.base_hurricane_url, "search")
        payload = {"text": text}
        if skip is not None:
            payload['skip'] = skip
        if limit is not None:
            payload['limit'] = limit

        r = self.client.get(url, params=payload)

        return r.json()

    def create_flood(self, flood_json, file_paths: List):
        """Create floods on the server. POST API endpoint is called.

        Args:
            flood_json (obj): JSON representing the flood.

        Returns:
            response (obj): HTTP POST Response. Json of the created flood.

        """
        url = self.base_flood_url
        flood_data = {('flood', flood_json)}

        for file_path in file_paths:
            flood_data.add(('file', open(file_path, 'rb')))
        kwargs = {"files": flood_data}
        r = self.client.post(url, **kwargs)
        response = r.json()

        return response

    def get_flood_metadata_list(self, skip: int = None, limit: int = None, space: str = None):
        """Retrieve flood metadata list from hazard service. Hazard API endpoint is called.

        Args:
            skip (int):  Skip the first n results, passed to the parameter "skip". Default None.
            limit (int):  Limit number of results to return. Passed to the parameter "limit". Default None.
            space (str): User's namespace on the server, passed to the parameter "space". Default None.

        Returns:
            obj: HTTP response containing the metadata.

        """
        url = self.base_flood_url
        payload = {}

        if skip is not None:
            payload['skip'] = skip
        if limit is not None:
            payload['limit'] = limit
        if space is not None:
            payload['space'] = space

        r = self.client.get(url, params=payload)
        response = r.json()

        return response

    def get_flood_metadata(self, hazard_id):
        """Retrieve flood metadata list from hazard service. Hazard API endpoint is called.

        Args:
            hazard_id (str): ID of the flood.

        Returns:
            obj: HTTP response containing the metadata.

        """
        url = urllib.parse.urljoin(self.base_flood_url, hazard_id)
        r = self.client.get(url)
        response = r.json()

        return response

    def post_flood_hazard_values(self, hazard_id: str, payload: list):
        """ Retrieve bulk flood hazard values from the Hazard service.

        Args:
            hazard_id (str): ID of the Flood.
            payload (list):
        Returns:
            obj: Hazard values.

        """
        url = urllib.parse.urljoin(self.base_flood_url, hazard_id + "/values")
        kwargs = {"files": {('points', json.dumps(payload))}}
        r = self.client.post(url, **kwargs)
        response = r.json()

        return response

    def delete_flood(self, hazard_id: str):
        """Delete a flood by it's id, and it's associated datasets

        Args:
            hazard_id (str): ID of the Flood.

        Returns:
            obj: Json of deleted hazard

        """
        url = urllib.parse.urljoin(self.base_flood_url, hazard_id)
        r = self.client.delete(url)
        return r.json()

    def search_floods(self, text: str, skip: int = None, limit: int = None):
        """Search floods.

        Args:
            text (str): Text to search by, passed to the parameter "text".
            skip (int):  Skip the first n results, passed to the parameter "skip", default None.
            limit (int):  Limit number of results to return. Passed to the parameter "limit", default None.

        Returns:
            obj: HTTP response with search results.

        """
        url = urllib.parse.urljoin(self.base_flood_url, "search")
        payload = {"text": text}
        if skip is not None:
            payload['skip'] = skip
        if limit is not None:
            payload['limit'] = limit

        r = self.client.get(url, params=payload)

        return r.json()

    def create_hurricane_windfield(self, hurr_wf_inputs):
        """Create wind fields on the server. POST API endpoint is called.

        Args:
            hurr_wf_inputs (obj): JSON representing the hurricane.

        Returns:
            obj: HTTP POST Response. Json of the created hurricane.

        """
        url = self.base_hurricanewf_url
        headers = {'Content-type': 'application/json'}
        new_headers = {**self.client.session.headers, **headers}
        kwargs = {"headers": new_headers}
        r = self.client.post(url, data=hurr_wf_inputs, timeout=(30, 10800), **kwargs)
        response = r.json()

        return response

    def get_hurricanewf_metadata_list(self, coast: str = None, category: int = None, skip: int = None,
                                      limit: int = None, space: str = None):
        """Retrieve hurricane metadata list from hazard service. Hazard API endpoint is called.

        Args:
            coast (str): Coast, passed to the parameter "coast".  Examples: gulf, florida or east.
            category (int): Hurricane category, passed to the parameter "coast".  Examples: between 1 and 5.
            skip (int):  Skip the first n results, passed to the parameter "skip". Default None.
            limit (int):  Limit number of results to return. Passed to the parameter "limit". Dafault None.
            space (str): User's namespace on the server, passed to the parameter "space". Dafault None.

        Returns:
            obj: HTTP response containing the metadata.

        """
        url = self.base_hurricanewf_url
        payload = {}

        if coast is not None:
            payload['coast'] = coast
        if category is not None:
            payload['category'] = category
        if skip is not None:
            payload['skip'] = skip
        if limit is not None:
            payload['limit'] = limit
        if space is not None:
            payload['space'] = space

        r = self.client.get(url, params=payload)
        response = r.json()

        return response

    def get_hurricanewf_metadata(self, hazard_id):
        """Retrieve hurricane metadata list from hazard service. Hazard API endpoint is called.

        Args:
            hazard_id (str): ID of the Hurricane.

        Returns:
            obj: HTTP response containing the metadata.

        """
        url = urllib.parse.urljoin(self.base_hurricanewf_url, hazard_id)
        r = self.client.get(url)
        response = r.json()

        return response

    def post_hurricanewf_hazard_values(self, hazard_id: str, payload: list, elevation: int, roughness: float):
        """ Retrieve bulk hurricane windfield hazard values from the Hazard service.

        Args:
            hazard_id (str): ID of the hurricanewf.
            payload (list):
        Returns:
            obj: Hazard values.

        """
        url = urllib.parse.urljoin(self.base_hurricanewf_url, hazard_id + "/values")
        kwargs = {"files": {('points', json.dumps(payload)),
                            ('elevation', json.dumps(elevation)),
                            ('roughness', json.dumps(roughness))}}
        r = self.client.post(url, **kwargs)
        response = r.json()

        return response

    def get_hurricanewf_json(self, coast: str, category: int, trans_d: float, land_fall_loc: int, demand_type: str,
                             demand_unit: str, resolution: int = 6, grid_points: int = 80,
                             rf_method: str = "circular"):
        """Retrieve hurricane wind field values from the Hazard service.

        Args:
            coast (str): Coast, passed to the parameter "coast".  Examples: gulf, florida or east.
            category (int): Hurricane category, passed to the parameter "coast".  Examples: between 1 and 5.
            trans_d (float): Trans_d.
            land_fall_loc (float):
            demand_type (str):
            demand_unit (str):
            resolution (int): Resolution, default 6.
            grid_points (int): Grid points, default 80.
            rf_method (str): Rf method, Default "circular"

        Returns:
            obj: HTTP response.

        """
        # land_fall_loc: IncorePoint e.g.'28.01, -83.85'
        url = urllib.parse.urljoin(self.base_hurricanewf_url, "json/" + coast)
        payload = {"category": category, "TransD": trans_d,
                   "LandfallLoc": land_fall_loc,
                   "demandType": demand_type, "demandUnits": demand_unit,
                   "resolution": resolution, "gridPoints": grid_points,
                   "reductionType": rf_method}
        r = self.client.get(url, params=payload)
        response = r.json()

        return response

    def delete_hurricanewf(self, hazard_id: str):
        """Delete a hurricane windfield by it's id, and it's associated datasets

        Args:
            hazard_id (str): ID of the Hurricane Windfield.

        Returns:
            obj: Json of deleted hazard

        """
        url = urllib.parse.urljoin(self.base_hurricanewf_url, hazard_id)
        r = self.client.delete(url)
        return r.json()

    def search_hurricanewf(self, text: str, skip: int = None, limit: int = None):
        """Search hurricanes.

        Args:
            text (str): Text to search by, passed to the parameter "text".
            skip (int):  Skip the first n results, passed to the parameter "skip", default None.
            limit (int):  Limit number of results to return. Passed to the parameter "limit", default None.

        Returns:
            obj: HTTP response with search results.

        """
        url = urllib.parse.urljoin(self.base_hurricanewf_url, "search")
        payload = {"text": text}
        if skip is not None:
            payload['skip'] = skip
        if limit is not None:
            payload['limit'] = limit

        r = self.client.get(url, params=payload)

        return r.json()
