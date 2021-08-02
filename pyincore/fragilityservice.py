# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import urllib

from pyincore import IncoreClient
from pyincore.dfr3service import Dfr3Service


class FragilityService(Dfr3Service):
    """Fragility service client.

    Args:
        client (IncoreClient): Service authentication.

    """

    def __init__(self, client: IncoreClient):
        self.client = client
        self.base_dfr3_url = urllib.parse.urljoin(client.service_url, 'dfr3/api/fragilities/')

        super(FragilityService, self).__init__(client)

    def get_dfr3_sets(self, demand_type: str = None,
                      hazard_type: str = None, inventory_type: str = None,
                      author: str = None, legacy_id: str = None,
                      creator: str = None, space: str = None,
                      skip: int = None, limit: int = None):
        """Get the set of fragility data, curves.

        Args:
            demand_type (str): ID of the Mapping file, default None.
            hazard_type (str): Hazard type filter, default None.
            inventory_type (str): Inventory type, default None.
            author (str): Fragility set creator’s username, default None.
            legacy_id (str):  Legacy fragility Id from v1, default None.
            creator (str): Fragility creator’s username, default None.
            space (str): Name of space, default None.
            skip (int):  Skip the first n results, default None.
            limit (int): Limit number of results to return, default None.

        Returns:
            obj: HTTP response with search results.

        """
        url = self.base_dfr3_url
        payload = {}

        if demand_type is not None:
            payload['demand'] = demand_type
        if hazard_type is not None:
            payload['hazard'] = hazard_type
        if inventory_type is not None:
            payload['inventory'] = inventory_type
        if author is not None:
            payload['author'] = author
        if legacy_id is not None:
            payload['legacy_id'] = legacy_id
        if creator is not None:
            payload['creator'] = creator
        if skip is not None:
            payload['skip'] = skip
        if limit is not None:
            payload['limit'] = limit
        if space is not None:
            payload['space'] = space

        r = self.client.get(url, params=payload)
        return r.json()
