# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


from wikidata.client import Client as WikidataClient


class GlossaryService:
    """
    Glossary service client to wikidata.
    TODO need to find out authentication mechanism
    """
    @staticmethod
    def get_term(service: str, term: str):
        client = WikidataClient(service)
        # definition_prop = client.get('P13')  # definition
        # image_prop = client.get('P4')  # image
        entity = client.get(term, load = True)
        return entity

