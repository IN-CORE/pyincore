# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from urllib.parse import urljoin
from pyincore import IncoreClient
import pyincore.globals as pyglobals
import requests

logger = pyglobals.LOGGER


class SpaceService:
    """Space service client.

    Args:
        client (IncoreClient): Service authentication.

    """

    def __init__(self, client: IncoreClient):
        self.client = client
        self.base_space_url = urljoin(client.service_url, "space/api/spaces/")

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

    def create_space(self, space_json):
        """Creates a Space.

        Args:
            space_json (json): A space representation. ID of the Space.

        Returns:
            obj: HTTP response with the created space information.

        """
        url = self.base_space_url
        space_data = {('space', space_json)}
        kwargs = {"files": space_data}
        r = self.client.post(url, **kwargs)
        return self.return_http_response(r).json()

    def get_spaces(self, dataset_id: str = None):
        """Retrieve  a Space with the dataset.

        Args:
            dataset_id (str): ID of the Dataset.

        Returns:
            obj: HTTP response with the created space information.

        """
        url = self.base_space_url
        payload = {}
        if dataset_id is not None:
            payload['dataset'] = dataset_id

        r = self.client.get(url, params=payload)

        return self.return_http_response(r).json()

    def get_space_by_id(self, space_id: str):
        """Get space information.

        Args:
            space_id (str): A space representation. ID of the Space.

        Returns:
            obj: HTTP response with the created space information.

        """
        url = urljoin(self.base_space_url, space_id)
        r = self.client.get(url)

        return self.return_http_response(r).json()

    def get_space_by_name(self, space_name: str):
        """Get space information by querying the name of space.

        Args:
            space_name (str): A space representation. Name of the Space.

        Returns:
            obj: HTTP response with the returned space information.

        """
        r = self.client.get(self.base_space_url, params={"name": space_name})
        if r.status_code == 200:
            return r.json()
        else:
            # throw an error instead of returning the empty result
            # return []
            raise r.exceptions.HTTPError("There is no matching name or you don't have a privilege to view the space.")

    def update_space(self, space_id: str, space_json):
        """Updates a Space.

        Args:
            space_id (str): ID of the space to update.
            space_json (json): JSON representing a space update.

        Returns:
            obj: HTTP response with the updated space.

        """
        url = urljoin(self.base_space_url, space_id)
        space_data = {('space', space_json)}
        kwargs = {"files": space_data}
        r = self.client.put(url, **kwargs)
        return self.return_http_response(r).json()

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

    def remove_dataset_from_space(self, space_id: str, dataset_id: str):
        """Remove dataset from the space using dataset id and space id

        Args:
            space_id (str): ID of the space to update.
            dataset_id (str): ID of the dataset to be removed from the space.

        Returns:
            obj: HTTP response with the updated space.

        """
        url = urljoin(self.base_space_url, space_id + "/members/" + dataset_id)

        r = self.client.delete(url)
        return self.return_http_response(r).json()

    def add_dataset_to_space(self, space_id: str, dataset_id: str):
        """Add member to a Space.

        Args:
            space_id (str): ID of the space to update.
            dataset_id (str): ID of the dataset to be added to the space.

        Returns:
            obj: HTTP response with the updated space.

        """
        url = urljoin(self.base_space_url, space_id + "/members/" + dataset_id)

        r = self.client.post(url)
        return self.return_http_response(r).json()

    def grant_privileges_to_space(self, space_id: str, privileges_json):
        """Updates a Space.

        Args:
            space_id (str): ID of the space to update.
            privileges_json (json): JSON representing a space update.

        Returns:
            obj: HTTP response with space privileges.

        """
        url = urljoin(self.base_space_url, space_id + "/grant")
        space_privileges = {('grant', privileges_json)}
        kwargs = {"files": space_privileges}
        r = self.client.post(url, **kwargs)

        return self.return_http_response(r).json()
