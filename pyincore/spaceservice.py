# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import urllib
from pyincore import IncoreClient


class SpaceService:
    """Space service client.

    Args:
        client (IncoreClient): Service authentication.

    """

    def __init__(self, client: IncoreClient):
        self.client = client
        self.base_space_url = urllib.parse.urljoin(client.service_url, "space/api/spaces/")

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
        response = r.json()
        return response

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
        response = r.json()

        return response

    def get_space_by_id(self, space_id: str):
        """Get space information.

        Args:
            space_id (str): A space representation. ID of the Space.

        Returns:
            obj: HTTP response with the created space information.

        """
        url = urllib.parse.urljoin(self.base_space_url, space_id)
        r = self.client.get(url)
        response = r.json()

        return response

    def update_space(self, space_id: str, space_json):
        """Updates a Space.

        Args:
            space_id (str): ID of the space to update.
            space_json (json): JSON representing a space update.

        Returns:
            obj: HTTP response with the updated space.

        """
        url = urllib.parse.urljoin(self.base_space_url, space_id)
        space_data = {('space', space_json)}
        kwargs = {"files": space_data}
        r = self.client.put(url, **kwargs)
        response = r.json()
        return response

    def add_dataset_to_space(self, space_id: str, dataset_id: str):
        """Add member to a Space.

        Args:
            space_id (str): ID of the space to update.
            dataset_id (str): ID of the dataset to be added to the space.

        Returns:
            obj: HTTP response with the updated space.

        """
        url = urllib.parse.urljoin(self.base_space_url, space_id + "/members/" + dataset_id)

        r = self.client.post(url)
        response = r.json()
        return response

    def grant_privileges_to_space(self, space_id: str, privileges_json):
        """Updates a Space.

        Args:
            space_id (str): ID of the space to update.
            privileges_json (json): JSON representing a space update.

        Returns:
            obj: HTTP response with space privileges.

        """
        url = urllib.parse.urljoin(self.base_space_url, space_id + "/grant")
        space_privileges = {('grant', privileges_json)}
        kwargs = {"files": space_privileges}
        r = self.client.post(url, **kwargs)

        response = r.json()
        return response
