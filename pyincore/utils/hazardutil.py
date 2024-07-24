# Copyright (c) 2024 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import logging
import sys
import math

logging.basicConfig(stream=sys.stderr, level=logging.INFO)


class HazardUtil:

    @staticmethod
    def compute_rupture_distance(magnitude, depth, mechanism, azimuth_angle, dip_angle, local_site, source_site):
        original_distances = HazardUtil.compute_original_distance(local_site, source_site, depth)

        rupture_length = HazardUtil.get_subsurface_rupture_length(magnitude, mechanism)
        rupture_width = HazardUtil.get_downdip_rupture_width(magnitude, mechanism)
        transformed_distances = HazardUtil.compute_transformed_distances(azimuth_angle, dip_angle, original_distances)

        if math.fabs(transformed_distances[0]) <= rupture_width / 2.0 and math.fabs(transformed_distances[1]) <= rupture_length / 2.0:
            r_rup = math.fabs(transformed_distances[2])
        elif (math.fabs(transformed_distances[0]) > rupture_width / 2.0 and math.fabs(
                transformed_distances[1]) <= rupture_length / 2.0):
            r_rup = math.sqrt(transformed_distances[2] * transformed_distances[2] + math.pow((math.fabs(
                transformed_distances[0]) - rupture_width / 2.0), 2))
        elif (math.fabs(transformed_distances[0]) <= rupture_width / 2.0 and math.fabs(
                transformed_distances[1]) > rupture_length / 2.0):
            r_rup = math.sqrt(transformed_distances[2] * transformed_distances[2] + math.pow((math.fabs(
                transformed_distances[1]) - rupture_length / 2.0), 2))
        else:
            r_rup = math.sqrt(transformed_distances[2] * transformed_distances[2] + math.pow((math.fabs(
                transformed_distances[0]) - rupture_width / 2.0), 2) + math.pow((math.fabs(transformed_distances[1]) -
                                                                                 rupture_length / 2.0), 2))

        if r_rup < 0.0:
            print("r_rup is less than 0?")

        return r_rup

    @staticmethod
    def compute_joyner_boore_distance(magnitude, mechanism, depth, azimuth_angle, dip_angle, local_site, source_site):
        original_distances = HazardUtil.compute_original_distance(local_site, source_site, depth)
        rupture_length = HazardUtil.get_subsurface_rupture_length(magnitude, mechanism)
        rupture_width = HazardUtil.get_downdip_rupture_width(magnitude, mechanism)

        transformed_distances = HazardUtil.compute_transformed_distances(azimuth_angle, dip_angle, original_distances)

        dip_angle_radians = math.radians(dip_angle)
        distance_x = transformed_distances[0]
        distance_y = transformed_distances[1]
        distance_z = transformed_distances[2]

        x_proj = distance_x * math.cos(dip_angle_radians) + distance_z * math.sin(dip_angle_radians)

        if (math.fabs(x_proj) <= rupture_width * math.cos(dip_angle_radians) / 2.0 and math.fabs(distance_y) <=
                rupture_length / 2.0):
            r_jb = 0.0
        elif (math.fabs(x_proj) > rupture_width * math.cos(dip_angle_radians) / 2.0 and math.fabs(distance_y) <=
              rupture_length / 2.0):
            r_jb = math.fabs(x_proj) - rupture_width * math.cos(dip_angle_radians) / 2.0
        elif (math.fabs(x_proj) <= rupture_width * math.cos(dip_angle_radians) / 2.0 and math.fabs(distance_y) >
              rupture_length / 2.0):
            r_jb = math.fabs(distance_y) - rupture_length / 2.0
        else:
            r_jb = math.sqrt(math.pow(math.fabs(x_proj) - rupture_width * math.cos(dip_angle_radians) / 2.0,
                                      2) + math.pow(math.fabs(distance_y) - rupture_length / 2.0, 2))

        return r_jb

    @staticmethod
    def compute_horizontal_distance(joyner_boore_distance, z_tor, down_dip_width, dip_angle, azimuth_angle, r_rup):
        dip_angle_radians = math.radians(dip_angle)
        azimuth_angle_radians = math.radians(azimuth_angle)

        if dip_angle != 90.0:
            if azimuth_angle >= 0 and azimuth_angle <= 180 and azimuth_angle != 90.0:
                if joyner_boore_distance * math.fabs(math.tan(azimuth_angle_radians)) <= down_dip_width * math.cos(
                        dip_angle_radians):
                    rx = joyner_boore_distance * math.tan(azimuth_angle_radians)
                else:
                    rx = joyner_boore_distance * math.tan(azimuth_angle_radians) * math.cos(azimuth_angle_radians -
                                                                                            math.asin((down_dip_width *
                                                                                                       math.cos(dip_angle_radians) *
                                                                 math.cos(azimuth_angle_radians) / joyner_boore_distance)))
            elif azimuth_angle == 90.0:
                if joyner_boore_distance > 0:
                    rx = joyner_boore_distance + down_dip_width * math.cos(dip_angle_radians)
                else:
                    if r_rup < z_tor * (1 / math.cos(dip_angle_radians)):
                        rx = math.sqrt(math.pow(r_rup, 2) - math.pow(z_tor, 2))
                    else:
                        rx = r_rup * (1 / math.sin(azimuth_angle_radians)) - z_tor * (1 / math.tan(dip_angle_radians))
            else:
                rx = joyner_boore_distance * math.sin(azimuth_angle_radians)
        else:
            rx = joyner_boore_distance * math.sin(azimuth_angle_radians)

        return rx

    @staticmethod
    def compute_original_distance(local_site, source_site, depth):
        site_latitude = local_site[0]
        site_longitude = local_site[1]
        source_latitude = source_site[0]
        source_longitude = source_site[1]

        original_distance = []
        # 6373 is approximate radius of earth
        original_distance.append((site_longitude - source_longitude) * math.pi * 6373.0 / 180.0)
        original_distance.append((site_latitude - source_latitude) * math.pi * 6373.0 / 180.0)
        original_distance.append(depth)

        return original_distance

    @staticmethod
    def compute_transformed_distances(azimuth_angle, dip_angle, original_distances):
        azimuth_angle_radians = math.radians(azimuth_angle)
        dip_angle_radians = math.radians(dip_angle)

        distance_x = (math.cos(dip_angle_radians) * math.cos(azimuth_angle_radians) * original_distances[0] -
                      math.cos(dip_angle_radians) * math.sin(azimuth_angle_radians) * original_distances[1] -
                      math.sin(dip_angle_radians) * original_distances[2])

        distance_y = math.sin(azimuth_angle_radians) * original_distances[0] + math.cos(
            azimuth_angle_radians) * original_distances[1]

        distance_z = (math.sin(dip_angle_radians) * math.cos(azimuth_angle_radians) * original_distances[0] -
                      math.sin(dip_angle_radians) * math.sin(azimuth_angle_radians) * original_distances[1] + math.cos(
                    dip_angle_radians) * original_distances[2])

        transformed_distances = [distance_x, distance_y, distance_z]

        return transformed_distances

    @staticmethod
    def get_subsurface_rupture_length(magnitude, mechanism):
        # TODO this should come from a dict of coefficients for different mechanisms
        a = -2.57
        b = 0.62

        return math.pow(10, a + b * magnitude)

    @staticmethod
    def get_downdip_rupture_width(magnitude, mechanism):
        # TODO this should come from a dict of coefficients for different mechanisms
        a = -0.76
        b = 0.27

        return math.pow(10, a + b * magnitude)
