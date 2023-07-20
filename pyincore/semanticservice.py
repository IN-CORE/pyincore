# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import json
import os
from typing import Tuple, Union

import pyincore.globals as pyglobals
from pyincore import IncoreClient
from urllib.parse import urljoin
import requests

logger = pyglobals.LOGGER

class SemanticService:
    """Semantics Service client.

    Use this class to interact with the semantics service.

    Args:
        client (IncoreClient): Service authentication.

    """

    def __init__(self, client: IncoreClient):
        self.client = client
        self.base_url = urljoin(client.service_url, 'semantics/api/types')

    
    @staticmethod
    def return_http_response(http_response):
        try:
            http_response.raise_for_status()
            return http_response
        except requests.exceptions.HTTPError:
            logger.error('A HTTPError has occurred \n' +
                         'HTTP Status code: ' + str(http_response.status_code) + '\n' +
                         'Error Message: ' + http_response.content.decode()
                         )
            raise
        except requests.exceptions.ConnectionError:
            logger.error("ConnectionError: Failed to establish a connection with the server. "
                         "This might be due to a refused connection. "
                         "Please check that you are using the right URLs.")
            raise
        except requests.exceptions.RequestException:
            logger.error("RequestException: There was an exception while trying to handle your request. "
                         "Please go to the end of this message for more specific information about the exception.")
            raise

    
    def get_all_semantic_types(
            self, 
            hyperlink: bool = False, 
            order: str = 'asc', 
            skip: int = 0, 
            limit: int = 50,
            save_json: bool = False,
            json_path: str = None,
            timeout: Tuple[int, int] = (30, 600), 
            **kwargs
        ) -> Union[list, dict]:
        """Get all semantic types.

        Args:
            hyperlink (bool): If True, return a list of hyperlinks to the semantic types.
            order (str): Order of the semantic types. Can be 'asc' or 'desc'.
            skip (int): Number of semantic types to skip.
            limit (int): Number of semantic types to return.
            save_json (bool): If True, save the json response to a file.
            json_path (str): Path to save the json response.
            timeout (tuple): Timeout for the request in seconds. 
                            First value is the connection timeout, second value is the read timeout.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            list: List of semantic types.

        """

        url = self.base_url
        payload = {
            'hyperlink': hyperlink,
            'order': order,
            'skip': skip,
            'limit': limit
        }
        response = self.client.get(url, params=payload, timeout=timeout, **kwargs)
        data = self.return_http_response(response).json()

        if save_json:
            # if json_path is None: then save to the default location (incore cache folder)
            if json_path is None:
                json_path = os.path.join(
                    pyglobals.PYINCORE_USER_CACHE, 
                    f'semantic_types_ord_{order}_sk_{skip}_lim_{limit}.json'
                )
            with open(json_path, 'w') as f:
                json.dump(data, f, indent=4)

        return data
    

    def get_semantic_type_by_name(
            self,
            type_name: str,
            save_json: bool = False,
            json_path: str = None,
            timeout: Tuple[int, int] = (30, 600), 
            **kwargs
    ) -> Union[list, dict]:
        """Get semantic type by name.

        Args:
            type_name (str): Name of the semantic type.
            save_json (bool): If True, save the json response to a file.
            json_path (str): Path to save the json response.
            timeout (tuple): Timeout for the request in seconds. 
                            First value is the connection timeout, second value is the read timeout.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            list or dict: List or dictionary of semantic type.

        """

        url = f'{self.base_url}/{type_name}'
        print(url)
        response = self.client.get(url, timeout=timeout, **kwargs)
        data = self.return_http_response(response).json()

        if save_json:
            # if json_path is None: then save to the default location (incore cache folder)
            if json_path is None:
                json_path = os.path.join(pyglobals.PYINCORE_USER_CACHE, f'{type_name}.json')
            with open(json_path, 'w') as f:
                json.dump(data, f, indent=4)

        return data
    

    def search_semantic_type(
            self,
            query: str,
            timeout: Tuple[int, int] = (30, 600),
            **kwargs
    ) -> Union[list, dict]:
        """Search for a semantic type.

        Args:
            query (str): Query to search for.
            timeout (tuple): Timeout for the request in seconds. 
                            First value is the connection timeout, second value is the read timeout.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            list or dict: List or dictionary of semantic type.

        """

        url = self.base_url + '/search'
        payload = {
            'text': query
        }
        response = self.client.get(url, params=payload, timeout=timeout, **kwargs)
        return self.return_http_response(response).json()
