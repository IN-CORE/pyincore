# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import json
from typing import Tuple

import pyincore.globals as pyglobals
from pyincore import IncoreClient
from pyincore.decorators import forbid_offline
from pyincore.utils import return_http_response
from urllib.parse import urljoin

logger = pyglobals.LOGGER


class SemanticService:
    """Semantics Service client.

    Use this class to interact with the semantics service.

    Args:
        client (IncoreClient): Service authentication.

    """

    def __init__(self, client: IncoreClient):
        self.client = client
        self.base_url = urljoin(client.service_url, "semantics/api/types")

    @forbid_offline
    def get_all_semantic_types(
        self,
        hyperlink: bool = False,
        order: str = "asc",
        skip: int = 0,
        limit: int = 50,
        detail: bool = False,
        save_json: bool = False,
        json_path: str = "",
        timeout: Tuple[int, int] = (30, 600),
        **kwargs,
    ) -> list:
        """Get all semantic types.

        Args:
            hyperlink (bool): If True, return a list of hyperlinks to the semantic types.
            order (str): Order of the semantic types. Can be 'asc' or 'desc'.
            skip (int): Number of semantic types to skip.
            limit (int): Number of semantic types to return.
            detail (bool): If True, return detailed information about the semantic types.
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
            "hyperlink": hyperlink,
            "order": order,
            "skip": skip,
            "limit": limit,
            "detail": detail,
        }
        response = self.client.get(url, params=payload, timeout=timeout, **kwargs)
        data = return_http_response(response).json()

        if save_json:
            with open(json_path, "w") as f:
                json.dump(data, f, indent=4)

        return data

    @forbid_offline
    def get_semantic_type_by_name(
        self,
        type_name: str,
        save_json: bool = False,
        json_path: str = "",
        timeout: Tuple[int, int] = (30, 600),
        **kwargs,
    ) -> dict:
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

        url = f"{self.base_url}/{type_name}"
        response = self.client.get(url, timeout=timeout, **kwargs)
        data = return_http_response(response).json()

        if save_json:
            with open(json_path, "w") as f:
                json.dump(data, f, indent=4)

        return data

    @forbid_offline
    def search_semantic_type(
        self, query: str, timeout: Tuple[int, int] = (30, 600), **kwargs
    ) -> list:
        """Search for a semantic type.

        Args:
            query (str): Query to search for.
            timeout (tuple): Timeout for the request in seconds.
                            First value is the connection timeout, second value is the read timeout.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            list or dict: List or dictionary of semantic type.

        """

        url = f"{self.base_url}/search"
        payload = {"text": query}
        response = self.client.get(url, params=payload, timeout=timeout, **kwargs)
        return return_http_response(response).json()
