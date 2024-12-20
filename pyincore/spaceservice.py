# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
from urllib.parse import urljoin
from pyincore import IncoreClient
import pyincore.globals as pyglobals
from pyincore.decorators import forbid_offline
from pyincore.utils import return_http_response

logger = pyglobals.LOGGER


class SpaceService:
    """Space service client.

    Args:
        client (IncoreClient): Service authentication.

    """

    def __init__(self, client: IncoreClient):
        self.client = client
        self.base_space_url = urljoin(client.service_url, "space/api/spaces/")

    @forbid_offline
    def create_space(self, space_json, timeout=(30, 600), **kwargs):
        """Creates a Space.

        Args:
            space_json (json): A space representation. ID of the Space.
            timeout (tuple): Timeout for the request.
            **kwargs: Additional arguments.

        Returns:
            obj: HTTP response with the created space information.

        """
        url = self.base_space_url
        space_data = [("space", space_json)]
        kwargs["files"] = space_data
        r = self.client.post(url, timeout=timeout, **kwargs)
        return return_http_response(r).json()

    @forbid_offline
    def get_spaces(self, dataset_id: str = None, timeout=(30, 600), **kwargs):
        """Retrieve  a Space with the dataset.

        Args:
            dataset_id (str): ID of the Dataset.
            timeout (tuple): Timeout for the request.
            **kwargs: Additional arguments.

        Returns:
            obj: HTTP response with the created space information.

        """
        url = self.base_space_url
        payload = {}
        if dataset_id is not None:
            payload["dataset"] = dataset_id

        r = self.client.get(url, params=payload, timeout=timeout, **kwargs)

        return return_http_response(r).json()

    @forbid_offline
    def get_space_by_id(self, space_id: str, timeout=(30, 600), **kwargs):
        """Get space information.

        Args:
            space_id (str): A space representation. ID of the Space.

        Returns:
            obj: HTTP response with the created space information.

        """
        url = urljoin(self.base_space_url, space_id)
        r = self.client.get(url, timeout=timeout, **kwargs)

        return return_http_response(r).json()

    @forbid_offline
    def get_space_by_name(self, space_name: str, timeout=(30, 600), **kwargs):
        """Get space information by querying the name of space.

        Args:
            space_name (str): A space representation. Name of the Space.
            timeout (tuple): Timeout for the request.
            **kwargs: Additional arguments.

        Returns:
            obj: HTTP response with the returned space information.

        """
        r = self.client.get(
            self.base_space_url, params={"name": space_name}, timeout=timeout, **kwargs
        )
        return return_http_response(r).json()

    @forbid_offline
    def update_space(self, space_id: str, space_json, timeout=(30, 600), **kwargs):
        """Updates a Space.

        Args:
            space_id (str): ID of the space to update.
            space_json (json): JSON representing a space update.
            timeout (tuple): Timeout for the request.
            **kwargs: Additional arguments.

        Returns:
            obj: HTTP response with the updated space.

        """
        url = urljoin(self.base_space_url, space_id)
        space_data = {("space", space_json)}
        kwargs["files"] = space_data
        r = self.client.put(url, timeout=timeout, **kwargs)
        return return_http_response(r).json()

    @forbid_offline
    def add_to_space_by_name(self, space_name: str, dataset_id: str):
        """Add dataset to a space by using space name and dataset id.

        Args:
            space_name (str): Name of the space that dataset id will go to.
            dataset_id (json): ID of the dataset that will be copied in to the space.

        Returns:
            obj: HTTP response with the updated space.

        """
        space_id = self.get_space_by_name(space_name)[0]

        response = self.add_dataset_to_space(space_id["id"], dataset_id)

        return response

    @forbid_offline
    def remove_from_space_by_name(self, space_name: str, dataset_id: str):
        """Remove dataset from a space by using space name and dataset id.

        Args:
            space_name (str): Name of the space that dataset id will go to.
            dataset_id (json): ID of the dataset that will be copied in to the space.

        Returns:
            obj: HTTP response with the updated space.

        """
        space_id = self.get_space_by_name(space_name)[0]

        response = self.remove_dataset_from_space(space_id["id"], dataset_id)

        return response

    @forbid_offline
    def remove_dataset_from_space(
        self, space_id: str, dataset_id: str, timeout=(30, 600), **kwargs
    ):
        """Remove dataset from the space using dataset id and space id

        Args:
            space_id (str): ID of the space to update.
            dataset_id (str): ID of the dataset to be removed from the space.
            timeout (tuple): Timeout for the request.
            **kwargs: Additional arguments.

        Returns:
            obj: HTTP response with the updated space.

        """
        url = urljoin(self.base_space_url, space_id + "/members/" + dataset_id)

        r = self.client.delete(url, timeout=timeout, **kwargs)
        return return_http_response(r).json()

    @forbid_offline
    def add_dataset_to_space(
        self, space_id: str, dataset_id: str, timeout=(30, 600), **kwargs
    ):
        """Add member to a Space.

        Args:
            space_id (str): ID of the space to update.
            dataset_id (str): ID of the dataset to be added to the space.
            timeout (tuple): Timeout for the request.
            **kwargs: Additional arguments.

        Returns:
            obj: HTTP response with the updated space.

        """
        url = urljoin(self.base_space_url, space_id + "/members/" + dataset_id)

        r = self.client.post(url, timeout=timeout, **kwargs)
        return return_http_response(r).json()

    @forbid_offline
    def grant_privileges_to_space(
        self, space_id: str, privileges_json, timeout=(30, 600), **kwargs
    ):
        """Updates a Space.

        Args:
            space_id (str): ID of the space to update.
            privileges_json (json): JSON representing a space update.
            timeout (tuple): Timeout for the request.
            **kwargs: Additional arguments.

        Returns:
            obj: HTTP response with space privileges.

        """
        url = urljoin(self.base_space_url, space_id + "/grant")
        space_privileges = [("grant", privileges_json)]
        kwargs["files"] = space_privileges
        r = self.client.post(url, timeout=timeout, **kwargs)

        return return_http_response(r).json()
