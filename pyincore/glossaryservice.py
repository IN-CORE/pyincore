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

