# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import urllib
from typing import Dict

import jsonpickle

from pyincore import IncoreClient
from pyincore import Dfr3Service

class MappingSubject(object):
    def __init__(self):
        self.schema = str()
        self.inventory = None  # Feature Collection


class MappingRequest(object):
    def __init__(self):
        self.params = dict()
        self.subject = MappingSubject()


class MappingResponse(object):
    def __init__(self, sets: Dict[str, any], mapping: Dict[str, str]):
        self.sets = sets
        self.mapping = mapping

    def __init__(self):
        self.sets = dict()  # fragility id to fragility
        self.mapping = dict()  # inventory id to fragility id


class FragilityService(Dfr3Service):
    """Fragility service client.

    Args:
        client (IncoreClient): Service authentication.

    """
    def __init__(self, client: IncoreClient):
        self.client = client
        self.base_frag_url = urllib.parse.urljoin(client.service_url,
                                                  'dfr3/api/fragilities/')
        self.base_mapping_url = urllib.parse.urljoin(client.service_url,
                                                     'dfr3/api/fragility-mappings/')
