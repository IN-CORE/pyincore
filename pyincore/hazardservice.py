# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import json
from typing import List
from urllib.parse import urljoin
import numpy

import pyincore.globals as pyglobals
from pyincore.decorators import forbid_offline
from pyincore.utils import return_http_response
from pyincore import IncoreClient

logger = pyglobals.LOGGER


class HazardService:
    """Hazard service client

    Args:
        client (IncoreClient): Service authentication.

    """

    def __init__(self, client: IncoreClient):
        self.client = client

        self.base_earthquake_url = urljoin(
            client.service_url, "hazard/api/earthquakes/"
        )
        self.base_tornado_url = urljoin(client.service_url, "hazard/api/tornadoes/")
        self.base_tsunami_url = urljoin(client.service_url, "hazard/api/tsunamis/")
        self.base_hurricane_url = urljoin(client.service_url, "hazard/api/hurricanes/")
        self.base_hurricanewf_url = urljoin(
            client.service_url, "hazard/api/hurricaneWindfields/"
        )
        self.base_flood_url = urljoin(client.service_url, "hazard/api/floods/")

    @forbid_offline
    def get_earthquake_hazard_metadata_list(
        self,
        skip: int = None,
        limit: int = None,
        space: str = None,
        timeout: tuple = (30, 600),
        **kwargs
    ):
        """Retrieve earthquake metadata list from hazard service. Hazard API endpoint is called.

        Args:
            skip (int):  Skip the first n results, passed to the parameter "skip". Dafault None.
            limit (int):  Limit number of results to return. Passed to the parameter "limit". Dafault None.
            space (str): User's namespace on the server, passed to the parameter "space". Dafault None.
            timeout (tuple): Timeout for the request in seconds. Default (30, 600).
            **kwargs: Arbitrary keyword arguments.

        Returns:
            json: Response containing the metadata.

        """
        url = self.base_earthquake_url
        payload = {}
        if skip is not None:
            payload["skip"] = skip
        if limit is not None:
            payload["limit"] = limit
        if space is not None:
            payload["space"] = space

        r = self.client.get(url, params=payload, timeout=timeout, **kwargs)

        return return_http_response(r).json()

    @forbid_offline
    def get_earthquake_hazard_metadata(
        self, hazard_id: str, timeout=(30, 600), **kwargs
    ):
        """Retrieve earthquake metadata from hazard service. Hazard API endpoint is called.

        Args:
            hazard_id (str): ID of the Earthquake.
            timeout (tuple): Timeout for the request in seconds. Default (30, 600).
            **kwargs: Arbitrary keyword arguments.

        Returns:
            json: Response containing the metadata.

        """
        url = urljoin(self.base_earthquake_url, hazard_id)
        r = self.client.get(url, timeout=timeout, **kwargs)

        return return_http_response(r).json()

    @forbid_offline
    def get_earthquake_hazard_value_set(
        self,
        hazard_id: str,
        demand_type: str,
        demand_unit: str,
        bbox,
        grid_spacing: float,
        timeout=(30, 600),
        **kwargs
    ):
        """Retrieve earthquake hazard value set from the Hazard service.

        Args:
            hazard_id (str): ID of the Earthquake.
            demand_type (str):  Ground motion demand type. Examples: PGA, PGV, 0.2 SA
            demand_unit (str): Ground motion demand unit. Examples: g, %g, cm/s, etc.
            bbox (list): Bounding box, list of points.
            grid_spacing (float): Grid spacing.
            timeout (tuple): Timeout for the request in seconds. Default (30, 600).
            **kwargs: Arbitrary keyword arguments.

        Returns:
            np.array: X values..
            np.array: Y values.
            np.array: Hazard value.

        """
        # bbox: [[minx, miny],[maxx, maxy]]
        # raster?demandType=0.2+SA&demandUnits=g&minX=-90.3099&minY=34.9942&maxX=-89.6231&maxY=35.4129&gridSpacing=0.01696
        # bbox
        url = urljoin(self.base_earthquake_url, hazard_id + "/raster")
        payload = {
            "demandType": demand_type,
            "demandUnits": demand_unit,
            "minX": bbox[0][0],
            "minY": bbox[0][1],
            "maxX": bbox[1][0],
            "maxY": bbox[1][1],
            "gridSpacing": grid_spacing,
        }
        r = self.client.get(url, params=payload, timeout=timeout, **kwargs)
        response = return_http_response(r).json()

        # TODO: need to handle error with the request
        xlist = []
        ylist = []
        zlist = []
        for entry in response["hazardResults"]:
            xlist.append(float(entry["longitude"]))
            ylist.append(float(entry["latitude"]))
            zlist.append(float(entry["hazardValue"]))
        x = numpy.array(xlist)
        y = numpy.array(ylist)
        hazard_val = numpy.array(zlist)

        return x, y, hazard_val

    @forbid_offline
    def post_earthquake_hazard_values(
        self,
        hazard_id: str,
        payload: list,
        amplify_hazard=True,
        timeout=(30, 600),
        **kwargs
    ):
        """Retrieve bulk hurricane hazard values from the Hazard service.

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
        url = urljoin(self.base_earthquake_url, hazard_id + "/values")
        kwargs = {
            "files": {
                ("points", json.dumps(payload)),
                ("amplifyHazard", json.dumps(amplify_hazard)),
            }
        }
        r = self.client.post(url, timeout=timeout, **kwargs)

        return return_http_response(r).json()

    @forbid_offline
    def get_liquefaction_values(
        self,
        hazard_id: str,
        geology_dataset_id: str,
        demand_unit: str,
        points: List,
        timeout=(30, 600),
        **kwargs
    ):
        """Retrieve earthquake liquefaction values.

        Args:
            hazard_id (str): ID of the Earthquake.
            geology_dataset_id (str):  ID of the geology dataset.
            demand_unit (str): Ground motion demand unit. Examples: g, %g, cm/s, etc.
            points (list): List of points provided as lat,long.
            timeout (tuple): Timeout for the request in seconds. Default (30, 600).
            **kwargs: Arbitrary keyword arguments.

        Returns:
            obj: HTTP response.

        """
        url = urljoin(self.base_earthquake_url, hazard_id + "/liquefaction/values")
        payload = {
            "demandUnits": demand_unit,
            "geologyDataset": geology_dataset_id,
            "point": points,
        }
        r = self.client.get(url, params=payload, timeout=timeout, **kwargs)
        response = r.json()
        return response

    @forbid_offline
    def post_liquefaction_values(
        self,
        hazard_id: str,
        geology_dataset_id: str,
        payload: list,
        timeout=(30, 600),
        **kwargs
    ):
        """Retrieve bulk earthquake liquefaction hazard values from the Hazard service.

        Args:
            hazard_id (str): ID of the Tornado.
            payload (list):
            timeout (tuple): Timeout for the request in seconds. Default (30, 600).
            **kwargs: Arbitrary keyword arguments.
        Returns:
            obj: Hazard values.

        """
        url = urljoin(self.base_earthquake_url, hazard_id + "/liquefaction/values")
        kwargs = {
            "files": {
                ("points", json.dumps(payload)),
                ("geologyDataset", geology_dataset_id),
            }
        }
        r = self.client.post(url, timeout=timeout, **kwargs)

        return return_http_response(r).json()

    @forbid_offline
    def get_soil_amplification_value(
        self,
        method: str,
        dataset_id: str,
        site_lat: float,
        site_long: float,
        demand_type: str,
        hazard: float,
        default_site_class: str,
        timeout=(30, 600),
        **kwargs
    ):
        """Retrieve earthquake liquefaction values.

        Args:
            method (str): ID of the Earthquake.
            dataset_id (str): ID of the Dataset.
            site_lat (float): Latitude of a point.
            site_long (float): Longitude of a point.
            demand_type (str):  Ground motion demand type. Examples: PGA, PGV, 0.2 SA
            hazard (float): Hazard value.
            default_site_class (str): Default site classification. Expected A, B, C, D, E or F.
            timeout (tuple): Timeout for the request in seconds. Default (30, 600).
            **kwargs: Arbitrary keyword arguments.

        Returns:
            obj: HTTP response.

        """
        url = urljoin(self.base_earthquake_url, "soil/amplification")
        payload = {
            "method": method,
            "datasetId": dataset_id,
            "siteLat": site_lat,
            "siteLong": site_long,
            "demandType": demand_type,
            "hazard": hazard,
            "defaultSiteClass": default_site_class,
        }
        r = self.client.get(url, params=payload, timeout=timeout, **kwargs)
        return return_http_response(r).json()

    # TODO get_slope_amplification_value needed to be implemented on the server side
    # def get_slope_amplification_value(self)

    @forbid_offline
    def get_supported_earthquake_models(self, timeout=(30, 600), **kwargs):
        """Retrieve suported earthquake models.

        Args:
            timeout (tuple): Timeout for the request in seconds. Default (30, 600).
            **kwargs: Arbitrary keyword arguments.

        Returns:
            obj: HTTP response.

        """
        url = urljoin(self.base_earthquake_url, "models")
        r = self.client.get(url, timeout=timeout, **kwargs)

        return return_http_response(r).json()

    @forbid_offline
    def create_earthquake(
        self, eq_json, file_paths: List = [], timeout=(30, 600), **kwargs
    ):
        """Create earthquake on the server. POST API endpoint is called.

        Args:
            eq_json (json): Json representing the Earthquake.
            file_paths (list): List of strings pointing to the paths of the datasets. Not needed for
                model based earthquakes. Default empty list.
            timeout (tuple): Timeout for the request in seconds. Default (30, 600).
            **kwargs: Arbitrary keyword arguments.

        Returns:
            obj: HTTP POST Response. Json of the earthquake posted to the server.

        """
        url = self.base_earthquake_url
        eq_data = [("earthquake", eq_json)]

        for file_path in file_paths:
            eq_data.append(("file", open(file_path, "rb")))
        kwargs = {"files": eq_data}
        r = self.client.post(url, timeout=timeout, **kwargs)
        return return_http_response(r).json()

    @forbid_offline
    def delete_earthquake(self, hazard_id: str, timeout=(30, 600), **kwargs):
        """Delete an earthquake by it's id, and it's associated datasets

        Args:
            hazard_id (str): ID of the Earthquake.
            timeout (tuple): Timeout for the request in seconds. Default (30, 600).
            **kwargs: Arbitrary keyword arguments.

        Returns:
            obj: Json of deleted hazard

        """
        url = urljoin(self.base_earthquake_url, hazard_id)
        r = self.client.delete(url, timeout=timeout, **kwargs)
        return return_http_response(r).json()

    @forbid_offline
    def search_earthquakes(
        self,
        text: str,
        skip: int = None,
        limit: int = None,
        timeout=(30, 600),
        **kwargs
    ):
        """Search earthquakes.

        Args:
            text (str): Text to search by, passed to the parameter "text".
            skip (int):  Skip the first n results, passed to the parameter "skip". Dafault None.
            limit (int):  Limit number of results to return. Passed to the parameter "limit". Dafault None.
            timeout (tuple):  Timeout for the request. Passed to the parameter "timeout". Dafault (30, 600).
            **kwargs:  Additional keyword arguments.

        Returns:
            obj: HTTP response with search results.

        """
        url = urljoin(self.base_earthquake_url, "search")
        payload = {"text": text}
        if skip is not None:
            payload["skip"] = skip
        if limit is not None:
            payload["limit"] = limit

        r = self.client.get(url, params=payload, timeout=timeout, **kwargs)

        return return_http_response(r).json()

    @forbid_offline
    def get_earthquake_aleatory_uncertainty(
        self, hazard_id: str, demand_type: str, timeout=(30, 600), **kwargs
    ):
        """Gets aleatory uncertainty for an earthquake

        Args:
            hazard_id (str): ID of the Earthquake
            demand_type (str):  Ground motion demand type. Examples: PGA, PGV, 0.2 SA
            timeout (tuple):  Timeout for the request. Passed to the parameter "timeout". Dafault (30, 600).
            **kwargs:  Additional keyword arguments.

        Returns:
             obj: HTTP POST Response with aleatory uncertainty value.

        """
        url = urljoin(self.base_earthquake_url, hazard_id + "/aleatoryuncertainty")
        payload = {"demandType": demand_type}

        r = self.client.get(url, params=payload, timeout=timeout, **kwargs)
        return return_http_response(r).json()

    @forbid_offline
    def get_earthquake_variance(
        self,
        hazard_id: str,
        variance_type: str,
        demand_type: str,
        demand_unit: str,
        points: List,
        timeout=(30, 600),
        **kwargs
    ):
        """Gets total and epistemic variance for a model based earthquake

        Args:
            hazard_id (str): ID of the Earthquake
            variance_type (str): Type of Variance. epistemic or total
            demand_type (str):  Ground motion demand type. Examples: PGA, PGV, 0.2 SA
            demand_unit (str): Demand unit. Examples: g, in
            points (list): List of points provided as lat,long.
            timeout (tuple):  Timeout for the request. Passed to the parameter "timeout". Dafault (30, 600).
            **kwargs:  Additional keyword arguments.

        Returns:
            obj: HTTP POST Response with variance value.

        """
        url = urljoin(
            self.base_earthquake_url, hazard_id + "/variance/" + variance_type
        )
        payload = {
            "demandType": demand_type,
            "demandUnits": demand_unit,
            "point": points,
        }

        r = self.client.get(url, params=payload, timeout=timeout, **kwargs)
        return return_http_response(r).json()

    @forbid_offline
    def get_tornado_hazard_metadata_list(
        self,
        skip: int = None,
        limit: int = None,
        space: str = None,
        timeout=(30, 600),
        **kwargs
    ):
        """Retrieve tornado metadata list from hazard service. Hazard API endpoint is called.

        Args:
            skip (int):  Skip the first n results, passed to the parameter "skip". Dafault None.
            limit (int):  Limit number of results to return. Passed to the parameter "limit". Dafault None.
            space (str): User's namespace on the server, passed to the parameter "space". Dafault None.
            timeout (tuple):  Timeout for the request. Passed to the parameter "timeout". Dafault (30, 600).
            **kwargs:  Additional keyword arguments.

        Returns:
            obj: HTTP response containing the metadata.

        """
        url = self.base_tornado_url
        payload = {}
        if skip is not None:
            payload["skip"] = skip
        if limit is not None:
            payload["limit"] = limit
        if space is not None:
            payload["space"] = space

        r = self.client.get(url, params=payload, timeout=timeout, **kwargs)

        return return_http_response(r).json()

    @forbid_offline
    def get_tornado_hazard_metadata(self, hazard_id: str, timeout=(30, 600), **kwargs):
        """Retrieve tornado metadata list from hazard service. Hazard API endpoint is called.

        Args:
            hazard_id (str): ID of the Tornado.
            timeout (tuple):  Timeout for the request. Passed to the parameter "timeout". Dafault (30, 600).
            **kwargs:  Additional keyword arguments.

        Returns:
            obj: HTTP response containing the metadata.

        """
        url = urljoin(self.base_tornado_url, hazard_id)
        r = self.client.get(url, timeout=timeout, **kwargs)

        return return_http_response(r).json()

    @forbid_offline
    def post_tornado_hazard_values(
        self, hazard_id: str, payload: list, seed=None, timeout=(30, 600), **kwargs
    ):
        """Retrieve bulk tornado hazard values from the Hazard service.

        Args:
            hazard_id (str): ID of the Tornado.
            payload (list):
            seed: (None or int): Seed value for random values.
        Returns:
            obj: Hazard values.

        """
        url = urljoin(self.base_tornado_url, hazard_id + "/values")

        if seed is not None:
            kwargs["files"] = {
                ("points", json.dumps(payload)),
                ("seed", json.dumps(seed)),
            }
        else:
            kwargs["files"] = {("points", json.dumps(payload))}

        r = self.client.post(url, timeout=timeout, **kwargs)

        return return_http_response(r).json()

    @forbid_offline
    def create_tornado_scenario(
        self, tornado_json, file_paths: List = [], timeout=(30, 600), **kwargs
    ):
        """Create tornado on the server. POST API endpoint is called.

        Args:
            tornado_json (json): JSON representing the tornado.
            file_paths (list): List of strings pointing to the paths of the shape files. Not needed for
                model based tornadoes.
            timeout (tuple):  Timeout for the request. Passed to the parameter "timeout". Dafault (30, 600).
            **kwargs:  Additional keyword arguments.

        Returns:
            obj: HTTP POST Response. Json of the created tornado.

        """
        url = self.base_tornado_url
        tornado_data = [("tornado", tornado_json)]

        for file_path in file_paths:
            tornado_data.append(("file", open(file_path, "rb")))
        kwargs = {"files": tornado_data}
        r = self.client.post(url, timeout=timeout, **kwargs)
        return return_http_response(r).json()

    @forbid_offline
    def delete_tornado(self, hazard_id: str, timeout=(30, 600), **kwargs):
        """Delete a tornado by it's id, and it's associated datasets

        Args:
            hazard_id (str): ID of the Tornado.
            timeout (tuple):  Timeout for the request. Passed to the parameter "timeout". Dafault (30, 600).
            **kwargs:  Additional keyword arguments.

        Returns:
            obj: Json of deleted hazard

        """
        url = urljoin(self.base_tornado_url, hazard_id)
        r = self.client.delete(url, timeout=timeout, **kwargs)
        return return_http_response(r).json()

    @forbid_offline
    def search_tornadoes(
        self,
        text: str,
        skip: int = None,
        limit: int = None,
        timeout=(30, 600),
        **kwargs
    ):
        """Search tornadoes.

        Args:
            text (str): Text to search by, passed to the parameter "text".
            skip (int):  Skip the first n results, passed to the parameter "skip". Dafault None.
            limit (int):  Limit number of results to return. Passed to the parameter "limit". Dafault None.
            timeout (tuple):  Timeout for the request. Passed to the parameter "timeout". Dafault (30, 600).
            **kwargs:  Additional keyword arguments.

        Returns:
            obj: HTTP response with search results.

        """
        url = urljoin(self.base_tornado_url, "search")
        payload = {"text": text}
        if skip is not None:
            payload["skip"] = skip
        if limit is not None:
            payload["limit"] = limit

        r = self.client.get(url, params=payload, timeout=timeout, **kwargs)

        return return_http_response(r).json()

    @forbid_offline
    def get_tsunami_hazard_metadata_list(
        self,
        skip: int = None,
        limit: int = None,
        space: str = None,
        timeout=(30, 600),
        **kwargs
    ):
        """Retrieve tsunami metadata list from hazard service. Hazard API endpoint is called.

        Args:
            skip (int): Skip the first n results, passed to the parameter "skip". Dafault None.
            limit (int): Limit number of results to return. Passed to the parameter "limit". Dafault None.
            space (str): User's namespace on the server, passed to the parameter "space". Dafault None.
            timeout (tuple):  Timeout for the request. Passed to the parameter "timeout". Dafault (30, 600).
            **kwargs:  Additional keyword arguments.

        Returns:
            obj: HTTP response containing the metadata.

        """
        url = self.base_tsunami_url
        payload = {}
        if skip is not None:
            payload["skip"] = skip
        if limit is not None:
            payload["limit"] = limit
        if space is not None:
            payload["space"] = space

        r = self.client.get(url, params=payload, timeout=timeout, **kwargs)

        return return_http_response(r).json()

    @forbid_offline
    def get_tsunami_hazard_metadata(self, hazard_id: str, timeout=(30, 600), **kwargs):
        """Retrieve tsunami metadata list from hazard service. Hazard API endpoint is called.

        Args:
            hazard_id (str): ID of the Tsunami.
            timeout (tuple):  Timeout for the request. Passed to the parameter "timeout". Dafault (30, 600).
            **kwargs:  Additional keyword arguments.

        Returns:
            obj: HTTP response containing the metadata.

        """
        url = urljoin(self.base_tsunami_url, hazard_id)
        r = self.client.get(url, timeout=timeout, **kwargs)

        return return_http_response(r).json()

    @forbid_offline
    def post_tsunami_hazard_values(
        self, hazard_id: str, payload: list, timeout=(30, 600), **kwargs
    ):
        """Retrieve bulk tsunami hazard values from the Hazard service.

        Args:
            hazard_id (str): ID of the Tsunami.
            payload (list):
            timeout (tuple):  Timeout for the request. Passed to the parameter "timeout". Dafault (30, 600).
            **kwargs:  Additional keyword arguments.
        Returns:
            obj: Hazard values.

        """
        url = urljoin(self.base_tsunami_url, hazard_id + "/values")
        kwargs = {"files": {("points", json.dumps(payload))}}
        r = self.client.post(url, timeout=timeout, **kwargs)

        return return_http_response(r).json()

    @forbid_offline
    def create_tsunami_hazard(
        self, tsunami_json, file_paths: List, timeout=(30, 600), **kwargs
    ):
        """Create tsunami on the server. POST API endpoint is called.

        Args:
            tsunami_json: JSON representing the tsunami.
            file_paths: List of strings pointing to the paths of the datasets.
            timeout (tuple):  Timeout for the request. Passed to the parameter "timeout". Dafault (30, 600).
            **kwargs:  Additional keyword arguments.

        Returns:
            obj: HTTP POST Response. Json of the created tsunami.

        """

        url = self.base_tsunami_url
        tsunami_data = [("tsunami", tsunami_json)]

        for file_path in file_paths:
            tsunami_data.append(("file", open(file_path, "rb")))
        kwargs = {"files": tsunami_data}
        r = self.client.post(url, timeout=timeout, **kwargs)
        return return_http_response(r).json()

    @forbid_offline
    def delete_tsunami(self, hazard_id: str, timeout=(30, 600), **kwargs):
        """Delete a tsunami by it's id, and it's associated datasets

        Args:
            hazard_id (str): ID of the Tsunami.
            timeout (tuple):  Timeout for the request. Passed to the parameter "timeout". Dafault (30, 600).
            **kwargs:  Additional keyword arguments.

        Returns:
            obj: Json of deleted hazard

        """
        url = urljoin(self.base_tsunami_url, hazard_id)
        r = self.client.delete(url, timeout=timeout, **kwargs)
        return return_http_response(r).json()

    @forbid_offline
    def search_tsunamis(
        self,
        text: str,
        skip: int = None,
        limit: int = None,
        timeout=(30, 600),
        **kwargs
    ):
        """Search tsunamis.

        Args:
            text (str): Text to search by, passed to the parameter "text".
            skip (int):  Skip the first n results, passed to the parameter "skip". Default None.
            limit (int):  Limit number of results to return. Passed to the parameter "limit". Dafault None.
            timeout (tuple):  Timeout for the request. Passed to the parameter "timeout". Dafault (30, 600).
            **kwargs:  Additional keyword arguments.

        Returns:
            obj: HTTP response with search results.

        """
        url = urljoin(self.base_tsunami_url, "search")
        payload = {"text": text}
        if skip is not None:
            payload["skip"] = skip
        if limit is not None:
            payload["limit"] = limit

        r = self.client.get(url, params=payload, timeout=timeout, **kwargs)

        return return_http_response(r).json()

    @forbid_offline
    def create_hurricane(
        self, hurricane_json, file_paths: List, timeout=(30, 600), **kwargs
    ):
        """Create hurricanes on the server. POST API endpoint is called.

        Args:
            hurricane_json (obj): JSON representing the hurricane.
            file_paths (list): List of strings pointing to the paths of the datasets.
            timeout (tuple):  Timeout for the request. Passed to the parameter "timeout". Dafault (30, 600).
            **kwargs:  Additional keyword arguments.

        Returns:
            obj: HTTP POST Response. Json of the created hurricane.

        """
        url = self.base_hurricane_url
        hurricane_data = [("hurricane", hurricane_json)]

        for file_path in file_paths:
            hurricane_data.append(("file", open(file_path, "rb")))
        kwargs = {"files": hurricane_data}
        r = self.client.post(url, timeout=timeout, **kwargs)

        return return_http_response(r).json()

    @forbid_offline
    def get_hurricane_metadata_list(
        self,
        skip: int = None,
        limit: int = None,
        space: str = None,
        timeout=(30, 600),
        **kwargs
    ):
        """Retrieve hurricane metadata list from hazard service. Hazard API endpoint is called.

        Args:
            skip (int):  Skip the first n results, passed to the parameter "skip". Default None.
            limit (int):  Limit number of results to return. Passed to the parameter "limit". Default None.
            space (str): User's namespace on the server, passed to the parameter "space". Default None.
            timeout (tuple):  Timeout for the request. Passed to the parameter "timeout". Dafault (30, 600).
            **kwargs:  Additional keyword arguments.

        Returns:
            obj: HTTP response containing the metadata.

        """
        url = self.base_hurricane_url
        payload = {}

        if skip is not None:
            payload["skip"] = skip
        if limit is not None:
            payload["limit"] = limit
        if space is not None:
            payload["space"] = space

        r = self.client.get(url, params=payload, timeout=timeout, **kwargs)

        return return_http_response(r).json()

    @forbid_offline
    def get_hurricane_metadata(self, hazard_id, timeout=(30, 600), **kwargs):
        """Retrieve hurricane metadata list from hazard service. Hazard API endpoint is called.

        Args:
            hazard_id (str): ID of the Hurricane.
            timeout (tuple):  Timeout for the request. Passed to the parameter "timeout". Dafault (30, 600).
            **kwargs:  Additional keyword arguments.

        Returns:
            obj: HTTP response containing the metadata.

        """
        url = urljoin(self.base_hurricane_url, hazard_id)
        r = self.client.get(url, timeout=timeout, **kwargs)

        return return_http_response(r).json()

    @forbid_offline
    def post_hurricane_hazard_values(
        self, hazard_id: str, payload: list, timeout=(30, 600), **kwargs
    ):
        """Retrieve bulk hurricane hazard values from the Hazard service.

        Args:
            hazard_id (str): ID of the Hurricane.
            payload (list):
        Returns:
            obj: Hazard values.

        """
        url = urljoin(self.base_hurricane_url, hazard_id + "/values")
        kwargs = {"files": {("points", json.dumps(payload))}}
        r = self.client.post(url, timeout=timeout, **kwargs)

        return return_http_response(r).json()

    @forbid_offline
    def delete_hurricane(self, hazard_id: str, timeout=(30, 600), **kwargs):
        """Delete a hurricane by it's id, and it's associated datasets

        Args:
            hazard_id (str): ID of the Hurricane.
            timeout (tuple):  Timeout for the request. Passed to the parameter "timeout". Dafault (30, 600).
            **kwargs:  Additional keyword arguments.

        Returns:
            obj: Json of deleted hazard

        """
        url = urljoin(self.base_hurricane_url, hazard_id)
        r = self.client.delete(url, timeout=timeout, **kwargs)
        return return_http_response(r).json()

    @forbid_offline
    def search_hurricanes(
        self,
        text: str,
        skip: int = None,
        limit: int = None,
        timeout=(30, 600),
        **kwargs
    ):
        """Search hurricanes.

        Args:
            text (str): Text to search by, passed to the parameter "text".
            skip (int):  Skip the first n results, passed to the parameter "skip", default None.
            limit (int):  Limit number of results to return. Passed to the parameter "limit", default None.
            timeout (tuple):  Timeout for the request. Passed to the parameter "timeout". Dafault (30, 600).
            **kwargs:  Additional keyword arguments.
        Returns:
            obj: HTTP response with search results.

        """
        url = urljoin(self.base_hurricane_url, "search")
        payload = {"text": text}
        if skip is not None:
            payload["skip"] = skip
        if limit is not None:
            payload["limit"] = limit

        r = self.client.get(url, params=payload, timeout=timeout, **kwargs)

        return return_http_response(r).json()

    @forbid_offline
    def create_flood(self, flood_json, file_paths: List, timeout=(30, 600), **kwargs):
        """Create floods on the server. POST API endpoint is called.

        Args:
            flood_json (obj): JSON representing the flood.

        Returns:
            response (obj): HTTP POST Response. Json of the created flood.

        """
        url = self.base_flood_url
        flood_data = [("flood", flood_json)]

        for file_path in file_paths:
            flood_data.append(("file", open(file_path, "rb")))
        kwargs = {"files": flood_data}
        r = self.client.post(url, timeout=timeout, **kwargs)

        return return_http_response(r).json()

    @forbid_offline
    def get_flood_metadata_list(
        self,
        skip: int = None,
        limit: int = None,
        space: str = None,
        timeout=(30, 600),
        **kwargs
    ):
        """Retrieve flood metadata list from hazard service. Hazard API endpoint is called.

        Args:
            skip (int):  Skip the first n results, passed to the parameter "skip". Default None.
            limit (int):  Limit number of results to return. Passed to the parameter "limit". Default None.
            space (str): User's namespace on the server, passed to the parameter "space". Default None.
            timeout (tuple):  Timeout for the request. Passed to the parameter "timeout". Dafault (30, 600).
            **kwargs:  Additional keyword arguments.

        Returns:
            obj: HTTP response containing the metadata.

        """
        url = self.base_flood_url
        payload = {}

        if skip is not None:
            payload["skip"] = skip
        if limit is not None:
            payload["limit"] = limit
        if space is not None:
            payload["space"] = space

        r = self.client.get(url, params=payload, timeout=timeout, **kwargs)

        return return_http_response(r).json()

    @forbid_offline
    def get_flood_metadata(self, hazard_id, timeout=(30, 600), **kwargs):
        """Retrieve flood metadata list from hazard service. Hazard API endpoint is called.

        Args:
            hazard_id (str): ID of the flood.
            timeout (tuple):  Timeout for the request. Passed to the parameter "timeout". Dafault (30, 600).
            **kwargs:  Additional keyword arguments.
        Returns:
            obj: HTTP response containing the metadata.

        """
        url = urljoin(self.base_flood_url, hazard_id)
        r = self.client.get(url, timeout=timeout, **kwargs)

        return return_http_response(r).json()

    @forbid_offline
    def post_flood_hazard_values(
        self, hazard_id: str, payload: list, timeout=(30, 600), **kwargs
    ):
        """Retrieve bulk flood hazard values from the Hazard service.

        Args:
            hazard_id (str): ID of the Flood.
            payload (list):
            timeout (tuple):  Timeout for the request. Passed to the parameter "timeout". Dafault (30, 600).
            **kwargs:  Additional keyword arguments.
        Returns:
            obj: Hazard values.

        """
        url = urljoin(self.base_flood_url, hazard_id + "/values")
        kwargs = {"files": {("points", json.dumps(payload))}}
        r = self.client.post(url, timeout=timeout, **kwargs)

        return return_http_response(r).json()

    @forbid_offline
    def delete_flood(self, hazard_id: str, timeout=(30, 600), **kwargs):
        """Delete a flood by it's id, and it's associated datasets

        Args:
            hazard_id (str): ID of the Flood.
            timeout (tuple):  Timeout for the request. Passed to the parameter "timeout". Dafault (30, 600).
            **kwargs:  Additional keyword arguments.

        Returns:
            obj: Json of deleted hazard

        """
        url = urljoin(self.base_flood_url, hazard_id)
        r = self.client.delete(url, timeout=timeout, **kwargs)
        return return_http_response(r).json()

    @forbid_offline
    def search_floods(
        self,
        text: str,
        skip: int = None,
        limit: int = None,
        timeout=(30, 600),
        **kwargs
    ):
        """Search floods.

        Args:
            text (str): Text to search by, passed to the parameter "text".
            skip (int):  Skip the first n results, passed to the parameter "skip", default None.
            limit (int):  Limit number of results to return. Passed to the parameter "limit", default None.
            timeout (tuple):  Timeout for the request. Passed to the parameter "timeout". Dafault (30, 600).
            **kwargs:  Additional keyword arguments.

        Returns:
            obj: HTTP response with search results.

        """
        url = urljoin(self.base_flood_url, "search")
        payload = {"text": text}
        if skip is not None:
            payload["skip"] = skip
        if limit is not None:
            payload["limit"] = limit

        r = self.client.get(url, params=payload, timeout=timeout, **kwargs)

        return return_http_response(r).json()

    @forbid_offline
    def create_hurricane_windfield(self, hurr_wf_inputs, timeout=(30, 10800), **kwargs):
        """Create wind fields on the server. POST API endpoint is called.

        Args:
            hurr_wf_inputs (obj): JSON representing the hurricane.
            timeout (tuple):  Timeout for the request. Passed to the parameter "timeout". Dafault (30, 10800).
            **kwargs:  Additional keyword arguments.

        Returns:
            obj: HTTP POST Response. Json of the created hurricane.

        """
        url = self.base_hurricanewf_url
        headers = {"Content-type": "application/json"}
        new_headers = {**self.client.session.headers, **headers}
        kwargs = {"headers": new_headers}
        r = self.client.post(url, data=hurr_wf_inputs, timeout=timeout, **kwargs)

        return return_http_response(r).json()

    @forbid_offline
    def get_hurricanewf_metadata_list(
        self,
        coast: str = None,
        category: int = None,
        skip: int = None,
        limit: int = None,
        space: str = None,
        timeout=(30, 600),
        **kwargs
    ):
        """Retrieve hurricane metadata list from hazard service. Hazard API endpoint is called.

        Args:
            coast (str): Coast, passed to the parameter "coast".  Examples: gulf, florida or east.
            category (int): Hurricane category, passed to the parameter "coast".  Examples: between 1 and 5.
            skip (int):  Skip the first n results, passed to the parameter "skip". Default None.
            limit (int):  Limit number of results to return. Passed to the parameter "limit". Dafault None.
            space (str): User's namespace on the server, passed to the parameter "space". Dafault None.
            timeout (tuple):  Timeout for the request. Passed to the parameter "timeout". Dafault (30, 600).
            **kwargs:  Additional keyword arguments.

        Returns:
            obj: HTTP response containing the metadata.

        """
        url = self.base_hurricanewf_url
        payload = {}

        if coast is not None:
            payload["coast"] = coast
        if category is not None:
            payload["category"] = category
        if skip is not None:
            payload["skip"] = skip
        if limit is not None:
            payload["limit"] = limit
        if space is not None:
            payload["space"] = space

        r = self.client.get(url, params=payload, timeout=timeout, **kwargs)

        return return_http_response(r).json()

    @forbid_offline
    def get_hurricanewf_metadata(self, hazard_id, timeout=(30, 600), **kwargs):
        """Retrieve hurricane metadata list from hazard service. Hazard API endpoint is called.

        Args:
            hazard_id (str): ID of the Hurricane.
            timeout (tuple):  Timeout for the request. Passed to the parameter "timeout". Dafault (30, 600).
            **kwargs:  Additional keyword arguments.

        Returns:
            obj: HTTP response containing the metadata.

        """
        url = urljoin(self.base_hurricanewf_url, hazard_id)
        r = self.client.get(url, timeout=timeout, **kwargs)

        return return_http_response(r).json()

    @forbid_offline
    def post_hurricanewf_hazard_values(
        self,
        hazard_id: str,
        payload: list,
        elevation: int,
        roughness: float,
        timeout=(30, 600),
        **kwargs
    ):
        """Retrieve bulk hurricane windfield hazard values from the Hazard service.

        Args:
            hazard_id (str): ID of the hurricanewf.
            payload (list):
            elevation (int):
            roughness (float):
            timeout (tuple):  Timeout for the request. Passed to the parameter "timeout". Dafault (30, 600).
            **kwargs:  Additional keyword arguments.
        Returns:
            obj: Hazard values.

        """
        url = urljoin(self.base_hurricanewf_url, hazard_id + "/values")
        kwargs["files"] = {
            ("points", json.dumps(payload)),
            ("elevation", json.dumps(elevation)),
            ("roughness", json.dumps(roughness)),
        }
        r = self.client.post(url, timeout=timeout, **kwargs)

        return return_http_response(r).json()

    @forbid_offline
    def get_hurricanewf_json(
        self,
        coast: str,
        category: int,
        trans_d: float,
        land_fall_loc: int,
        demand_type: str,
        demand_unit: str,
        resolution: int = 6,
        grid_points: int = 80,
        rf_method: str = "circular",
        timeout=(30, 600),
        **kwargs
    ):
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
            timeout (tuple):  Timeout for the request. Passed to the parameter "timeout". Dafault (30, 600).
            **kwargs:  Additional keyword arguments.

        Returns:
            obj: HTTP response.

        """
        # land_fall_loc: IncorePoint e.g.'28.01, -83.85'
        url = urljoin(self.base_hurricanewf_url, "json/" + coast)
        payload = {
            "category": category,
            "TransD": trans_d,
            "LandfallLoc": land_fall_loc,
            "demandType": demand_type,
            "demandUnits": demand_unit,
            "resolution": resolution,
            "gridPoints": grid_points,
            "reductionType": rf_method,
        }
        r = self.client.get(url, params=payload, timeout=timeout, **kwargs)

        return return_http_response(r).json()

    @forbid_offline
    def delete_hurricanewf(self, hazard_id: str, timeout=(30, 600), **kwargs):
        """Delete a hurricane windfield by it's id, and it's associated datasets

        Args:
            hazard_id (str): ID of the Hurricane Windfield.
            timeout (tuple):  Timeout for the request. Passed to the parameter "timeout". Dafault (30, 600).
            **kwargs:  Additional keyword arguments.

        Returns:
            obj: Json of deleted hazard

        """
        url = urljoin(self.base_hurricanewf_url, hazard_id)
        r = self.client.delete(url, timeout=timeout, **kwargs)
        return return_http_response(r).json()

    @forbid_offline
    def search_hurricanewf(
        self,
        text: str,
        skip: int = None,
        limit: int = None,
        timeout=(30, 600),
        **kwargs
    ):
        """Search hurricanes.

        Args:
            text (str): Text to search by, passed to the parameter "text".
            skip (int):  Skip the first n results, passed to the parameter "skip", default None.
            limit (int):  Limit number of results to return. Passed to the parameter "limit", default None.
            timeout (tuple):  Timeout for the request. Passed to the parameter "timeout". Dafault (30, 600).
            **kwargs:  Additional keyword arguments.

        Returns:
            obj: HTTP response with search results.

        """
        url = urljoin(self.base_hurricanewf_url, "search")
        payload = {"text": text}
        if skip is not None:
            payload["skip"] = skip
        if limit is not None:
            payload["limit"] = limit

        r = self.client.get(url, params=payload, timeout=timeout, **kwargs)

        return return_http_response(r).json()

    def get_allowed_demands(self, hazard_type, timeout=(30, 600), **kwargs):
        if self.client.offline:
            if hazard_type in HazardConstant.DEFAULT_ALLOWED_DEMANDS.keys():
                return HazardConstant.DEFAULT_ALLOWED_DEMANDS.get(hazard_type)
            else:
                raise ValueError("Unknown hazard type!")
        else:
            if hazard_type == "earthquake":
                url = urljoin(self.base_earthquake_url, "demands")
            elif hazard_type == "tornado":
                url = urljoin(self.base_tornado_url, "demands")
            elif hazard_type == "tsunami":
                url = urljoin(self.base_tsunami_url, "demands")
            elif hazard_type == "hurricane":
                url = urljoin(self.base_hurricane_url, "demands")
            elif hazard_type == "hurricaneWindfield":
                url = urljoin(self.base_hurricanewf_url, "demands")
            elif hazard_type == "flood":
                url = urljoin(self.base_flood_url, "demands")
            else:
                raise ValueError("Unknown hazard type!")

            r = self.client.get(url, timeout=timeout, **kwargs)
            return return_http_response(r).json()


class HazardConstant:

    """HazardConstant class to hold all the constants related to hazard."""

    DEFAULT_ALLOWED_DEMANDS = {
        "earthquake": [
            {
                "demand_type": "pga",
                "demand_unit": ["g", "in/sec^2", "m/sec^2"],
                "description": "Peak ground acceleration",
            },
            {
                "demand_type": "pgv",
                "demand_unit": ["in/s", "cm/s"],
                "description": "Peak ground velocity",
            },
            {
                "demand_type": "pgd",
                "demand_unit": ["in", "ft", "m"],
                "description": "Peak ground displacement",
            },
            {
                "demand_type": "sa",
                "demand_unit": ["g", "in/sec^2", "m/sec^2"],
                "description": "Spectral acceleration",
            },
            {
                "demand_type": "sd",
                "demand_unit": ["in", "ft", "m", "cm"],
                "description": "Spectral displacement",
            },
            {
                "demand_type": "sv",
                "demand_unit": ["cm/s", "in/s"],
                "description": "Spectral Velocity",
            },
        ],
        "tsunami": [
            {
                "demand_type": "Hmax",
                "demand_unit": ["ft", "m"],
                "description": "Onshore: maximum tsunami height above local ground level overland. Offshore: "
                "maximum tsunami height taken crest to trough",
            },
            {
                "demand_type": "Vmax",
                "demand_unit": ["mph", "kph", "ft/sec", "m/sec"],
                "description": "Maximum near-coast or overland water velocity due to tsunami",
            },
            {
                "demand_type": "Mmax",
                "demand_unit": ["m^3/s^2", "ft^3/s^2"],
                "description": "",
            },
        ],
        "flood": [
            {
                "demand_type": "inundationDepth",
                "demand_unit": ["ft", "m"],
                "description": "Depth of the water surface relative to local ground level",
            },
            {
                "demand_type": "waterSurfaceElevation",
                "demand_unit": ["ft", "m"],
                "description": "Elevation of the water surface above reference datum (e.g. NAVD88, mean sea level)",
            },
        ],
        "tornado": [
            {
                "demand_type": "wind",
                "demand_unit": ["mps", "mph"],
                "description": "Defined as a wind velocity below",
            }
        ],
        "hurricaneWindfield": [
            {
                "demand_type": "3s",
                "demand_unit": ["kph", "mph", "kt"],
                "description": "Typically, reported at 10 m above local ground or sea level",
            },
            {
                "demand_type": "60s",
                "demand_unit": ["kph", "mph", "kt"],
                "description": "Typically, reported at 10 m above local ground or sea level",
            },
        ],
        "hurricane": [
            {
                "demand_type": "waveHeight",
                "demand_unit": ["ft", "m", "in", "cm"],
                "description": " Height of wave measured crest to trough.  Characteristic wave height is typically the  "
                "average of one third highest waves for a random sea.",
            },
            {
                "demand_type": "surgeLevel",
                "demand_unit": ["ft", "m", "in", "cm"],
                "description": "Elevation of the water surface above reference datum (e.g. NAVD88, mean sea level)",
            },
            {
                "demand_type": "inundationDuration",
                "demand_unit": ["hr", "min", "s"],
                "description": "Time that inundation depth exceeds a critical threshold for a given storm",
            },
            {
                "demand_type": "inundationDepth",
                "demand_unit": ["ft", "m", "in", "cm"],
                "description": "Depth of the water surface relative to local ground level",
            },
            {
                "demand_type": "wavePeriod",
                "demand_unit": ["s", "hr", "min"],
                "description": "Time between wave crests.  Characteristic wave period is typically the inverse of the "
                "spectral peak frequency for a random sea",
            },
            {
                "demand_type": "waveDirection",
                "demand_unit": ["deg", "rad"],
                "description": "Principle wave direction associated with the characteristic wave height and period",
            },
            {
                "demand_type": "waterVelocity",
                "demand_unit": ["ft/s", "m/s", "in/s"],
                "description": "",
            },
            {
                "demand_type": "windVelocity",
                "demand_unit": ["ft/s", "m/s", "m/sec", "in/s"],
                "description": "",
            },
        ],
        "earthquake+tsunami": [
            {
                "demand_type": "pga",
                "demand_unit": ["g", "in/sec^2", "m/sec^2"],
                "description": "Peak ground acceleration",
            },
            {
                "demand_type": "pgv",
                "demand_unit": ["in/s", "cm/s"],
                "description": "Peak ground velocity",
            },
            {
                "demand_type": "pgd",
                "demand_unit": ["in", "ft", "m"],
                "description": "Peak ground displacement",
            },
            {
                "demand_type": "sa",
                "demand_unit": ["g", "in/sec^2", "m/sec^2"],
                "description": "Spectral acceleration",
            },
            {
                "demand_type": "sd",
                "demand_unit": ["in", "ft", "m", "cm"],
                "description": "Spectral displacement",
            },
            {
                "demand_type": "sv",
                "demand_unit": ["cm/s", "in/s"],
                "description": "Spectral Velocity",
            },
            {
                "demand_type": "Hmax",
                "demand_unit": ["ft", "m"],
                "description": "Onshore: maximum tsunami height above local ground level overland. Offshore: maximum tsunami height taken crest to trough",
            },
            {
                "demand_type": "Vmax",
                "demand_unit": ["mph", "kph", "ft/sec", "m/sec"],
                "description": "Maximum near-coast or overland water velocity due to tsunami",
            },
            {
                "demand_type": "Mmax",
                "demand_unit": ["m^3/s^2", "ft^3/s^2"],
                "description": "",
            },
        ],
    }
