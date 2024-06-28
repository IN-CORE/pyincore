# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import math
import random
import sys

import networkx as nx
import numpy
from pyincore.utils.analysisutil import AnalysisUtil
from shapely.geometry import shape, LineString, MultiLineString

from pyincore import (
    BaseAnalysis,
    HazardService,
    FragilityService,
    DataService,
    FragilityCurveSet,
)
from pyincore import GeoUtil, NetworkUtil, NetworkDataset
from pyincore.models.dfr3curve import DFR3Curve


class TornadoEpnDamage(BaseAnalysis):
    """
    Computes electric power network (EPN) probability of damage based on a tornado hazard.
    The process for computing the structural damage is similar to other parts of the built environment.
    First, fragilities are obtained based on the hazard type and attributes of the network tower and network pole.
    Based on the fragility, the hazard intensity at the location of the infrastructure is computed. Using this
    information, the probability of exceeding each limit state is computed, along with the probability of damage.
    """

    def __init__(self, incore_client):
        self.hazardsvc = HazardService(incore_client)
        self.fragilitysvc = FragilityService(incore_client)
        self.datasetsvc = DataService(incore_client)
        self.fragility_tower_id = "5b201b41b1cf3e336de8fa67"
        self.fragility_pole_id = "5b201d91b1cf3e336de8fa68"

        # this is for deciding to use indpnode field. Not using this could be safer for general dataset
        self.use_indpnode = False
        self.nnode = 0
        self.highest_node_num = 0
        self.EF = 0
        self.nint = []
        self.indpnode = []
        self.mcost = 1435  # mean repair cost for single distribution pole
        self.vcost = (0.1 * self.mcost) ** 2
        self.sigmad = math.sqrt(
            math.log(self.vcost / (self.mcost**2) + 1)
        )  # convert to gaussian Std Deviation to be used in logncdf
        self.mud = math.log((self.mcost**2) / math.sqrt(self.vcost + self.mcost**2))

        self.mcost = 400000  # mean repair cost for single transmission pole
        self.vcost = (0.1 * self.mcost) ** 2
        self.sigmat = math.sqrt(
            math.log(self.vcost / (self.mcost**2) + 1)
        )  # convert to gaussian Std Deviation to be used in logncdf
        self.mut = math.log((self.mcost**2) / math.sqrt(self.vcost + self.mcost**2))

        self.tmut = 72  # mean repairtime for transmission tower in hrs
        self.tsigmat = 36  # std dev

        self.tmud = 5  # mean repairtime for poles in hrs
        self.tsigmad = 2.5

        self.totalcost2repairpath = []
        self.totalpoles2repair = []

        self.tornado_sim_field_name = "SIMULATION"
        self.tornado_ef_field_name = "EF_RATING"

        # tornado number of simulation and ef_rate
        self.nmcs = 0
        self.tornado_ef_rate = 0

        self.pole_distance = 38.1

        # node variables
        self.nodenwid_fld_name = "NODENWID"
        self.indpnode_fld_name = "INDPNODE"
        self.guid_fldname = "GUID"

        # link variables
        self.tonode_fld_name = "TONODE"
        self.fromnode_fld_name = "FROMNODE"
        self.linetype_fld_name = "LINETYPE"

        # line type variable
        self.line_transmission = "transmission"
        self.line_distribution = "distribution"

        super(TornadoEpnDamage, self).__init__(incore_client)

    def run(self):
        network_dataset = NetworkDataset.from_dataset(
            self.get_input_dataset("epn_network")
        )
        tornado = self.get_input_hazard("hazard")
        tornado_id = self.get_parameter("tornado_id")
        if tornado is None and tornado_id is None:
            raise ValueError(
                "Either tornado hazard object or tornado id must be provided"
            )
        elif tornado_id is None:
            tornado_id = tornado.id

        tornado_metadata = self.hazardsvc.get_tornado_hazard_metadata(tornado_id)
        self.load_remote_input_dataset(
            "tornado", tornado_metadata["hazardDatasets"][0].get("datasetId")
        )
        tornado_dataset = self.get_input_dataset("tornado").get_inventory_reader()
        ds_results, damage_results = self.get_damage(
            network_dataset, tornado_dataset, tornado_id
        )

        self.set_result_csv_data(
            "result", ds_results, name=self.get_parameter("result_name")
        )
        self.set_result_json_data(
            "metadata",
            damage_results,
            name=self.get_parameter("result_name") + "_additional_info",
        )

        return True

    def get_damage(self, network_dataset, tornado_dataset, tornado_id):
        """

        Args:
            network_dataset (obj): Network dataset.
            tornado_dataset (obj): Tornado dataset.
            tornado_id (str): Tornado id.

        """
        link_dataset = network_dataset.links.get_inventory_reader()
        node_dataset = network_dataset.nodes.get_inventory_reader()
        self.set_tornado_variables(tornado_dataset)
        self.set_node_variables(node_dataset)

        # get fragility curves set - tower for transmission, pole for distribution
        fragility_set_tower = FragilityCurveSet(
            self.fragilitysvc.get_dfr3_set(self.fragility_tower_id)
        )
        assert fragility_set_tower.id == self.fragility_tower_id
        fragility_set_pole = FragilityCurveSet(
            self.fragilitysvc.get_dfr3_set(self.fragility_pole_id)
        )
        assert fragility_set_pole.id == self.fragility_pole_id

        # network test
        node_id_validation = NetworkUtil.validate_network_node_ids(
            network_dataset,
            self.fromnode_fld_name,
            self.tonode_fld_name,
            self.nodenwid_fld_name,
        )
        if node_id_validation is False:
            sys.exit("ID in from or to node field doesn't exist in the node dataset")

        # getting network graph and node coordinates
        is_directed_graph = True
        link_filepath = link_dataset.path

        graph, node_coords = NetworkUtil.create_network_graph_from_link(
            link_filepath,
            self.fromnode_fld_name,
            self.tonode_fld_name,
            is_directed_graph,
        )

        # reverse the graph to acculate the damage to next to node
        graph = nx.DiGraph.reverse(graph, copy=True)

        # check the connection as a list
        connection_sets = []
        if is_directed_graph:
            connection_sets = list(nx.weakly_connected_components(graph))
        else:
            connection_sets = list(nx.connected_components(graph))

        # check the first node of the each network line, this first node should lead each separated network
        # also convert connection set to list
        first_node_list = []
        connection_list = []
        for c in connection_sets:
            connection_list.append(list(c))
            first_node_list.append(list(c)[0])

        intersection_list = []
        poly_list = []
        totalcost2repair = []
        totalpoles2repair = []
        totaltime2repair = []

        # construct guid field
        guid_list = []
        nodenwid_list = []
        for node_feature in node_dataset:
            # get guid colum
            guid_fld_val = ""
            if self.guid_fldname.lower() in node_feature["properties"]:
                guid_fld_val = node_feature["properties"][self.guid_fldname.lower()]
            elif self.guid_fldname in node_feature["properties"]:
                guid_fld_val = node_feature["properties"][self.guid_fldname]
            guid_list.append(guid_fld_val)

            # get nodenwid colum
            nodenwid_fld_val = ""
            if self.nodenwid_fld_name.lower() in node_feature["properties"]:
                nodenwid_fld_val = int(
                    node_feature["properties"][self.nodenwid_fld_name.lower()]
                )
            elif self.nodenwid_fld_name in node_feature["properties"]:
                nodenwid_fld_val = int(
                    node_feature["properties"][self.nodenwid_fld_name]
                )
            nodenwid_list.append(nodenwid_fld_val)

        for z in range(self.nmcs):
            nodedam = [
                0
            ] * self.nnode  # placeholder for recording number of damaged pole for each node
            noderepair = [
                0
            ] * self.nnode  # placeholder for recording repair cost for each node
            poles2repair = [
                0
            ] * self.nnode  # placeholder for recording total number of poles to repair
            cost2repairpath = [
                0
            ] * self.nnode  # placeholder for recording total repair cost for the network
            time2repairpath = [
                0
            ] * self.nnode  # placeholder for recording total repair time for the network
            nodetimerep = [0] * self.nnode
            hazardval = [[0]] * self.nnode  # placeholder for recording hazard values
            demandtypes = [[""]] * self.nnode  # placeholder for recording demand types
            demandunits = [[""]] * self.nnode  # placeholder for recording demand units

            # iterate link
            for line_feature in link_dataset:
                ndamage = 0  # number of damaged poles in each link
                repaircost = 0  # repair cost value
                repairtime = 0  # repair time value
                to_node_val = ""
                linetype_val = ""
                tor_hazard_values = [0]  # random wind speed in EF
                demand_types = [""]
                demand_units = [""]

                if self.tonode_fld_name.lower() in line_feature["properties"]:
                    to_node_val = line_feature["properties"][
                        self.tonode_fld_name.lower()
                    ]
                elif self.tonode_fld_name in line_feature["properties"]:
                    to_node_val = line_feature["properties"][self.tonode_fld_name]

                if self.linetype_fld_name in line_feature["properties"]:
                    linetype_val = line_feature["properties"][self.linetype_fld_name]
                elif self.linetype_fld_name.lower() in line_feature["properties"]:
                    linetype_val = line_feature["properties"][
                        self.linetype_fld_name.lower()
                    ]

                line = shape(line_feature["geometry"])

                # iterate tornado
                for tornado_feature in tornado_dataset:
                    resistivity_probability = (
                        0  # resistivity value at the point of windSpeed
                    )
                    random_resistivity = 0  # random resistivity value between 0 and one

                    sim_fld_val = ""
                    ef_fld_val = ""

                    # get EF rating and simulation number column
                    if (
                        self.tornado_sim_field_name.lower()
                        in tornado_feature["properties"]
                    ):
                        sim_fld_val = int(
                            tornado_feature["properties"][
                                self.tornado_sim_field_name.lower()
                            ]
                        )
                    elif self.tornado_sim_field_name in tornado_feature["properties"]:
                        sim_fld_val = int(
                            tornado_feature["properties"][self.tornado_sim_field_name]
                        )

                    if (
                        self.tornado_ef_field_name.lower()
                        in tornado_feature["properties"]
                    ):
                        ef_fld_val = tornado_feature["properties"][
                            self.tornado_ef_field_name.lower()
                        ]
                    elif self.tornado_ef_field_name in tornado_feature["properties"]:
                        ef_fld_val = tornado_feature["properties"][
                            self.tornado_ef_field_name
                        ]

                    if sim_fld_val == "" or ef_fld_val == "":
                        print(
                            "unable to convert tornado simulation field value to integer"
                        )
                        sys.exit(0)

                    # get Tornado EF polygon
                    # assumes that the polygon is not a multipolygon
                    poly = shape(tornado_feature["geometry"])
                    poly_list.append(poly)

                    # loop for ef ranges
                    for f in range(self.tornado_ef_rate):
                        npoles = 0  # number of poles in tornado ef box
                        poleresist = 0  # pole's resistance value
                        # setting EF rate value string to match in the tornado dataset's attribute table
                        ef_content = "EF" + str(f)

                        # compute the intersections between link line and ef polygon
                        # also figure out the length of the line that ovelapped with EF box
                        inter_length_meter = None
                        # compute the intersection between tornado polygon and line
                        if (
                            sim_fld_val == z
                            and ef_fld_val.lower() == ef_content.lower()
                        ):
                            if poly is not None and line is not None:
                                if poly.intersects(line):
                                    intersection = poly.intersection(line)
                                    any_point = None
                                    if intersection.length > 0:
                                        # print(intersection.__class__.__name__)
                                        # calculate the length of intersected line
                                        # since this is a geographic, it has to be projected to meters to be calcuated
                                        inter_length_meter = (
                                            GeoUtil.calc_geog_distance_from_linestring(
                                                intersection
                                            )
                                        )
                                        if isinstance(intersection, MultiLineString):
                                            intersection_list.append(intersection)
                                            for inter_line in intersection.geoms:
                                                any_point = inter_line.centroid
                                                break
                                        elif isinstance(intersection, LineString):
                                            intersection_list.append(intersection)
                                            any_point = intersection.centroid

                                            # also, random point can be possible
                                            # by changing the following lines value 0.5
                                            # any_point = intersection.interpolate(0.5, normalized=True)

                                    if any_point is not None:
                                        # check if any_point is in the polygon
                                        if poly.contains(any_point) is False:
                                            # this is very hardly happen but should be needed just in case
                                            any_point = poly.centroid

                                    # check if the line is tower or transmission
                                    if linetype_val.lower() == self.line_transmission:
                                        fragility_set_used = fragility_set_tower
                                    else:
                                        fragility_set_used = fragility_set_pole

                                    values_payload = [
                                        {
                                            "demands": [
                                                x.lower()
                                                for x in fragility_set_used.demand_types
                                            ],
                                            "units": [
                                                x.lower()
                                                for x in fragility_set_used.demand_units
                                            ],
                                            "loc": str(any_point.coords[0][1])
                                            + ","
                                            + str(any_point.coords[0][0]),
                                        }
                                    ]

                                    h_vals = self.hazardsvc.post_tornado_hazard_values(
                                        tornado_id,
                                        values_payload,
                                        self.get_parameter("seed"),
                                    )
                                    tor_hazard_values = (
                                        AnalysisUtil.update_precision_of_lists(
                                            h_vals[0]["hazardValues"]
                                        )
                                    )
                                    demand_types = h_vals[0]["demands"]
                                    demand_units = h_vals[0]["units"]
                                    hval_dict = dict()
                                    j = 0
                                    for d in h_vals[0]["demands"]:
                                        hval_dict[d] = tor_hazard_values[j]
                                        j += 1
                                    if isinstance(
                                        fragility_set_used.fragility_curves[0],
                                        DFR3Curve,
                                    ):
                                        inventory_args = fragility_set_used.construct_expression_args_from_inventory(
                                            tornado_feature
                                        )
                                        resistivity_probability = fragility_set_used.calculate_limit_state(
                                            hval_dict,
                                            inventory_type=fragility_set_used.inventory_type,
                                            **inventory_args
                                        )
                                    else:
                                        raise ValueError(
                                            "One of the fragilities is in deprecated format. This should not happen. "
                                            "If you are seeing this please report the issue."
                                        )

                                    # randomly generated capacity of each poles ; 1 m/s is 2.23694 mph
                                    poleresist = (
                                        resistivity_probability.get("LS_0") * 2.23694
                                    )
                                    npoles = int(
                                        round(inter_length_meter / self.pole_distance)
                                    )
                                    repairtime_list = []

                                    mu = None
                                    sigma = None
                                    for k in range(npoles):
                                        random_resistivity = random.uniform(0, 1)

                                        if random_resistivity <= poleresist:
                                            ndamage += 1
                                            # following codes can't be converted from matlab to python
                                            # however, the cross product <=3 or == 24 almost doesn't happen
                                            # since the time and cost differs when it is pole or tower,
                                            # this could be changed by see if it is tower or pole
                                            # if numpy.cross(k, z) <= 3 or numpy.cross(k, z) == 24:
                                            if (
                                                linetype_val.lower()
                                                == self.line_transmission
                                            ):
                                                mu = self.mut
                                                sigma = self.sigmat
                                                tmu = self.tmut
                                                tsigma = self.tsigmat
                                            else:
                                                mu = self.mud
                                                sigma = self.sigmad
                                                tmu = self.tmud
                                                tsigma = self.tsigmad

                                            repairtime_list.append(
                                                numpy.random.normal(tmu, tsigma)
                                            )

                                    for k in range(ndamage):
                                        repaircost += numpy.random.lognormal(mu, sigma)

                                    # max of the repair time among different poles is taken
                                    # as the repair time for that line
                                    if len(repairtime_list) > 0:
                                        repairtime = max(repairtime_list)
                noderepair[to_node_val - 1] = repaircost
                nodedam[to_node_val - 1] = ndamage
                nodetimerep[to_node_val - 1] = repairtime
                hazardval[to_node_val - 1] = tor_hazard_values
                demandtypes[to_node_val - 1] = demand_types
                demandunits[to_node_val - 1] = demand_units

            # Calculate damage and repair cost based on network
            for i in range(len(first_node_list)):
                for j in range(len(connection_list[i])):
                    # print(connection_list[i][j], first_node_list[i])
                    pathij = list(
                        nx.all_simple_paths(
                            graph, connection_list[i][j], first_node_list[i]
                        )
                    )
                    poler = 0
                    coster = 0
                    timer = []
                    # print(pathij)
                    if len(pathij) > 0:
                        for k in range(len(pathij)):
                            for var1 in range(len(pathij[k])):
                                poler = poler + nodedam[pathij[k][var1]]
                                coster = coster + noderepair[pathij[k][var1]]
                                # max of the time for different lines is taken as the repair time for that path.
                                # -- path is constituted of different lines.
                                timer.append(nodetimerep[pathij[k][var1]])
                    poles2repair[connection_list[i][j]] = poler
                    cost2repairpath[connection_list[i][j]] = coster
                    if len(timer) > 0:
                        time2repairpath[connection_list[i][j]] = max(timer)
                    else:
                        time2repairpath[connection_list[i][j]] = 0
            totalcost2repair.append(cost2repairpath)
            totalpoles2repair.append(poles2repair)
            totaltime2repair.append(time2repairpath)

        # create guid field from node dataset

        # calculate mean and standard deviation
        meanpoles = numpy.mean(numpy.asarray(totalpoles2repair), axis=0)
        stdpoles = numpy.std(numpy.asarray(totalpoles2repair), axis=0)
        meancost = numpy.mean(numpy.asarray(totalcost2repair), axis=0)
        stdcost = numpy.std(numpy.asarray(totalcost2repair), axis=0)
        meantime = numpy.mean(numpy.asarray(totaltime2repair), axis=0)
        stdtime = numpy.std(numpy.asarray(totaltime2repair), axis=0)

        # create result
        ds_results = []
        damage_results = []

        for i in range(len(meanpoles)):
            ds_result = dict()
            damage_result = dict()

            ds_result["guid"] = guid_list[i]
            ds_result["meanpoles"] = meanpoles[i]
            ds_result["stdpoles"] = stdpoles[i]
            ds_result["meancost"] = meancost[i]
            ds_result["stdcost"] = stdcost[i]
            ds_result["meantime"] = meantime[i]
            ds_result["stdtime"] = stdtime[i]
            ds_result["haz_expose"] = AnalysisUtil.get_exposure_from_hazard_values(
                hazardval[i], "tornado"
            )

            damage_result["guid"] = guid_list[i]
            damage_result["fragility_tower_id"] = self.fragility_tower_id
            damage_result["fragility_pole_id"] = self.fragility_pole_id
            damage_result["hazardtype"] = "Tornado"
            damage_result["hazardvals"] = hazardval[i]
            damage_result["demandtypes"] = demandtypes[i]
            damage_result["demandunits"] = demandunits[i]

            ds_results.append(ds_result)
            damage_results.append(damage_result)

        return ds_results, damage_results

    """
    align coordinate values in a list as a single pair in order
    """

    def set_tornado_variables(self, tornado_dataset):
        sim_num_list = []
        ef_rate_list = []

        for ef_poly in tornado_dataset:
            ef_string = ""
            if self.tornado_sim_field_name.lower() in ef_poly["properties"]:
                sim_num_list.append(
                    int(ef_poly["properties"][self.tornado_sim_field_name.lower()])
                )
            elif self.tornado_sim_field_name in ef_poly["properties"]:
                sim_num_list.append(
                    int(ef_poly["properties"][self.tornado_sim_field_name])
                )

            if self.tornado_ef_field_name.lower() in ef_poly["properties"]:
                ef_string = ef_poly["properties"][self.tornado_ef_field_name.lower()]
            elif self.tornado_ef_field_name in ef_poly["properties"]:
                ef_string = ef_poly["properties"][self.tornado_ef_field_name]
            # parse the number in EF and the format should be "EF0", "EF1", or something like it
            ef_rate_list.append(int(ef_string.lower().split("ef", 1)[1]))

        if len(sim_num_list) == 0 or len(ef_string) == 0:
            print("Could not convert tornado simulation value")
            sys.exit(0)

        self.nmcs = max(sim_num_list) + 1
        self.tornado_ef_rate = max(ef_rate_list) + 1

    def set_node_variables(self, node_dataset):
        i = 0

        for node_point in node_dataset:
            node_id = None
            indpnode_val = None
            if self.nodenwid_fld_name.lower() in node_point["properties"]:
                node_id = int(node_point["properties"][self.nodenwid_fld_name.lower()])
            elif self.nodenwid_fld_name in node_point["properties"]:
                node_id = int(node_point["properties"][self.nodenwid_fld_name])

            if self.use_indpnode is True:
                if self.indpnode_fld_name.lower() in node_point["properties"]:
                    indpnode_val = int(
                        node_point["properties"][self.indpnode_fld_name.lower()]
                    )
                elif self.indpnode_fld_name in node_point["properties"]:
                    indpnode_val = int(node_point["properties"][self.indpnode_fld_name])

            if node_id is None and indpnode_val is None:
                print("problem getting the value")
                sys.exit(1)

            if self.use_indpnode is True:
                if indpnode_val > 0:
                    self.indpnode.append(node_id)
                else:
                    self.nint.append(node_id)
            else:
                self.nint.append(node_id)

            if node_id > self.highest_node_num:
                self.highest_node_num = node_id
            i += 1

        self.nnode = i

    def get_spec(self):
        return {
            "name": "tornado-epn-damage",
            "description": "tornado epn damage analysis",
            "input_parameters": [
                {
                    "id": "result_name",
                    "required": True,
                    "description": "result dataset name",
                    "type": str,
                },
                {
                    "id": "tornado_id",
                    "required": False,
                    "description": "Tornado hazard id",
                    "type": str,
                },
                {
                    "id": "seed",
                    "required": False,
                    "description": "Initial seed for the tornado hazard value",
                    "type": int,
                },
            ],
            "input_hazards": [
                {
                    "id": "hazard",
                    "required": False,
                    "description": "Hazard object",
                    "type": ["tornado"],
                },
            ],
            "input_datasets": [
                {
                    "id": "epn_network",
                    "required": True,
                    "description": "EPN Network Dataset",
                    "type": ["incore:epnNetwork"],
                },
                {
                    "id": "tornado",
                    "required": False,
                    "description": "Tornado Dataset",
                    "type": ["incore:tornadoWindfield"],
                },
            ],
            "output_datasets": [
                {
                    "id": "result",
                    "parent_type": "epn_network",
                    "description": "CSV file of damages for electric power network by tornado",
                    "type": "incore:tornadoEPNDamageVer3",
                },
                {
                    "id": "metadata",
                    "parent_type": "epn_network",
                    "description": "Json file with information about applied hazard value and fragility",
                    "type": "incore:tornadoEPNDamageSupplement",
                },
            ],
        }
