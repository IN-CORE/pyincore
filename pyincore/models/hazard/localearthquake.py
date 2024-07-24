
import pygmm
import numpy as np
import math

from pyincore.models.hazard.earthquake import Earthquake
from pyincore.utils.hazardutil import HazardUtil
from pyincore.models.units import Units


class LocalEarthquake(Earthquake):

    def __init__(self, metadata):
        super().__init__(metadata)

        attenuations = metadata["attenuations"]

        # Currently, we only support one attenuation
        self.attenuation = list(attenuations.keys())[0]

        self.eq_parameters = self.get_pygmm_parameters(metadata)
        self.default_units = {"pga": "g", "pgv": "cm/s", "pgd": "cm", "sa": "g"}

    def read_hazard_values(self, payload: list, hazard_service=None, **kwargs):
        """Retrieve bulk earthquake hazard values either from the Hazard service or read it from local Dataset

        Args:
            payload (list):
            hazard_service (obj): Hazard service.
            kwargs (dict): Keyword arguments.
        Returns:
            obj: Hazard values.

        """

        print("read value from model: "+self.attenuation)
        model_class = getattr(pygmm, self.attenuation)
        # magnitude = self.magnitude
        eq_parameters = self.eq_parameters

        response = []

        # TODO shouldn't need this
        magnitude = eq_parameters["mag"]
        for req in payload:
            hazard_values = []
            for index, req_demand_type in enumerate(req["demands"]):
                req_demand = req_demand_type.lower()
                req_demand_period = 0.0

                if "sa" in req_demand:
                    req_demand_parts = req_demand.split(" ")
                    req_demand_period = req_demand_parts[0]
                    req_demand = req_demand_parts[1]

                latitude = float(req["loc"].split(",")[0])
                longitude = float(req["loc"].split(",")[1])
                # longitude, latitude

                local_site = [latitude, longitude]

                rupture_distance_ergo = HazardUtil.compute_rupture_distance(magnitude, self.depth, self.mechanism,
                                                                            self.azimuth_angle, self.dip_angle,
                                                                            local_site, self.source_site,)
                joyner_boore_distance = HazardUtil.compute_joyner_boore_distance(magnitude, self.mechanism, self.depth,
                                                                                 self.azimuth_angle, self.dip_angle,
                                                                                 local_site, self.source_site)

                z_tor = self.coseismic_rupture_depth
                down_dip_width = self.get_downdip_rupture_width(magnitude, self.mechanism)

                horizontal_distance = HazardUtil.compute_horizontal_distance(joyner_boore_distance, z_tor,
                                                                             down_dip_width, self.dip_angle,
                                                                             self.azimuth_angle, rupture_distance_ergo)

                # TODO - this should come from a shapefile of site conditions maybe?
                site_condition = self.default_site_condition
                site_vs30 = 760

                eq_parameters["dist_rup"] = rupture_distance_ergo
                eq_parameters["dist_jb"] = joyner_boore_distance
                eq_parameters["dist_x"] = horizontal_distance

                scenario = pygmm.Scenario(**eq_parameters)
                model = model_class(scenario)
                if req_demand == "pga":
                    raw_hazard_value = model.pga
                elif req_demand == "pgv":
                    raw_hazard_value = model.pgv
                elif req_demand == "pgd":
                    raw_hazard_value = model.pgd
                elif req_demand == "sa":
                    sa_values = model.spec_accels
                    sa_index_array = np.where(model.periods == float(req_demand_period))
                    if len(sa_index_array[0]) != 0:
                        sa_index = sa_index_array[0][0]
                    else:
                        sa_index = self.find_nearest(model.periods, float(req_demand_period))

                    sa_values = model.spec_accels
                    raw_hazard_value = sa_values[sa_index]

                if raw_hazard_value is None:
                    converted_hazard_value = raw_hazard_value
                else:
                    converted_hazard_value = Units.convert_hazard(raw_hazard_value, 
                                                                  original_demand_units=self.default_units[req_demand],
                                                                  requested_demand_units=req["units"][index])

                hazard_values.append(converted_hazard_value)

            req.update({"hazardValues": hazard_values})
            response.append(req)

        return response

    def find_nearest(self, period_array, period):
        array = np.asarray(period_array)
        idx = (np.abs(period_array - period)).argmin()
        return idx

    def get_pygmm_parameters(self, metadata):

        eq_parameters = metadata["eqParameters"]
        magnitude = float(eq_parameters["magnitude"])
        event_type = eq_parameters["eventType"]

        # TODO - need to handle the multiple attenuation models case
        fault_type_map = eq_parameters["faultTypeMap"]
        mechanism = fault_type_map[self.attenuation]

        if mechanism == "Strike-Slip":
            mechanism_pygmm = "SS"
        else:
            # TODO handle other cases
            mechanism_pygmm = mechanism

        dip_angle = float(eq_parameters["dipAngle"])
        # self.azimuth_angle = eq_parameters["azimuthAngle"]

        # TODO remove these later
        self.mechanism = mechanism_pygmm
        self.dip_angle = dip_angle

        self.azimuth_angle = 130.0
        self.default_site_condition = "soil"
        self.default_site_vs30 = 760
        self.source_site = [float(eq_parameters["srcLatitude"]), float(eq_parameters["srcLongitude"])]
        self.depth = float(eq_parameters["depth"])
        self.coseismic_rupture_depth = float(eq_parameters["coseismicRuptureDepth"])

        # TODO all the eq parameters should be mapped into a dictionary that can be passed to the pygmm Scenario so
        # we can map IN-CORE parameters to pygmm parameters (e.g. Ztor is depth_tor in pygmm)

        eq_parameters = {"mag": magnitude, "site_cond": self.default_site_condition, "v_s30": self.default_site_vs30,
                         "dip": dip_angle, "mechanism": mechanism_pygmm, "event_type": event_type,
                         "depth_tor": 3.0, "depth_1_0": 0.0}

        return eq_parameters

    def get_downdip_rupture_width(self, magnitude, mechanism):
        # TODO this should come from a dict of coefficients for different mechanisms
        a = -0.76
        b = 0.27

        return math.pow(10, a + b * magnitude)
