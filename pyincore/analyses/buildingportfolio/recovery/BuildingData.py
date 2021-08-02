class BuildingData:
    def __init__(self, tract_id, lon, lat, structural, code_level, epsa_node_id, pwsa_node_id, tep_id, build_id_x,
                 epsa_id, pwsa_id, finance, ep_pw_id, occupation_code):
        self.tract_id = tract_id
        self.lon = lon
        self.lat = lat
        self.structural = structural
        self.code_level = code_level,
        self.epsa_node_id = epsa_node_id
        self.pwsa_node_id = pwsa_node_id
        self.tep_id = tep_id
        self.build_id_x = build_id_x
        self.epsa_id = epsa_id
        self.pwsa_id = pwsa_id
        self.finance = finance
        self.ep_pw_id = ep_pw_id
        self.occupation_code = occupation_code
