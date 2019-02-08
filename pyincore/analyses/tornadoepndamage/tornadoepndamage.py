#!/usr/bin/env python3

import os
import math
import numpy
import sys
import random
import networkx as nx
import csv
import collections

from shapely.geometry import shape
from pyincore import InsecureIncoreClient, BaseAnalysis, HazardService, FragilityService, DataService
from pyincore import GeoUtil, AnalysisUtil


class TornadoEpnDamage(BaseAnalysis):
    def __init__(self, incore_client):
        self.hazardsvc = HazardService(incore_client)
        self.fragilitysvc = FragilityService(incore_client)
        self.hazardsvc = HazardService(incore_client)
        self.fragilitysvc = FragilityService(incore_client)
        self.datasetsvc = DataService(incore_client)
        self.fragility_tower_id = '5b201b41b1cf3e336de8fa67'
        self.fragility_pole_id = '5b201d91b1cf3e336de8fa68'
        self.fragility_mapping_id = '5b2bddcbd56d215b9b7471d8'
        self.client = incore_client

        self.use_indpnode = False  # this is for deciding to use indpnode field. Not using this could be safer for general dataset
        self.nnode = 0
        self.highest_node_num = 0
        self.EF = 0
        self.nint = []
        self.indpnode = []
        self.mcost = 1435  # mean repair cost for single distribution pole
        self.vcost = (0.1 * self.mcost) ** 2
        self.sigmad = math.sqrt(
            math.log(self.vcost / (self.mcost ** 2) + 1))  # convert to gaussian Std Deviation to be used in logncdf
        self.mud = math.log((self.mcost ** 2) / math.sqrt(self.vcost + self.mcost ** 2))

        self.mcost = 400000  # mean repair cost for single transmission pole
        self.vcost = (0.1 * self.mcost) ** 2
        self.sigmat = math.sqrt(
            math.log(self.vcost / (self.mcost ** 2) + 1))  # convert to gaussian Std Deviation to be used in logncdf
        self.mut = math.log((self.mcost ** 2) / math.sqrt(self.vcost + self.mcost ** 2))

        self.tmut = 72  # mean repairtime for transmission tower in hrs
        self.tsigmat = 36  # std dev

        self.tmud = 5  # mean repairtime for poles in hrs
        self.tsigmad = 2.5

        self.totalcost2repairpath = []
        self.totalpoles2repair = []

        self.tornado_sim_field_name = 'SIMULATION'
        self.tornado_ef_field_name = 'EF_RATING'

        # tornado number of simulation and ef_rate
        self.nmcs = 0
        self.tornado_ef_rate = 0

        self.pole_distance = 38.1

        # node variables
        self.nodenwid_fld_name = "NODENWID"
        self.indpnode_fld_name = "INDPNODE"
        self.guid_fldname = 'GUID'

        # link variables
        self.tonode_fld_name = "TONODE"
        self.fromnode_fld_name = "FROMNODE"
        self.linetype_fld_name = "LINETYPE"

        # line type variable
        self.line_transmission = "transmission"
        self.line_distribution = "distribution"

        super(TornadoEpnDamage, self).__init__(incore_client)

    def run(self):
        node_dataset = self.get_input_dataset("epn_node").get_inventory_reader()
        link_dataset = self.get_input_dataset("epn_link").get_inventory_reader()
        tornado_dataset = self.get_input_dataset("tornado").get_inventory_reader()

        # tornado_id = self.get_parameter('tornado_id')

        results = self.get_damage(node_dataset, link_dataset, tornado_dataset)

        self.set_result_csv_data("result", results, name=self.get_parameter("result_name"))

        return True

    def get_damage(self, node_dataset, link_dataset, tornado_dataset):
        """
        :param node_dataset:
        :param link_dataset:
        :param tornado_dataset:
        :return:
        """
        self.set_tornado_variables(tornado_dataset)
        self.set_node_variables(node_dataset)

        # get fragility curves set - tower for transmission, pole for distribution
        fragility_set_tower = self.fragilitysvc.get_fragility_set(self.fragility_tower_id)
        assert fragility_set_tower['id'] == self.fragility_tower_id
        fragility_set_pole = self.fragilitysvc.get_fragility_set(self.fragility_pole_id)
        assert fragility_set_pole['id'] == self.fragility_pole_id

        # network test
        node_id_validation = GeoUtil.validate_network_node_ids(node_dataset, link_dataset, self.fromnode_fld_name,
                                                               self.tonode_fld_name, self.nodenwid_fld_name)
        if node_id_validation == False:
            print("ID in from or to node field doesn't exist in the node dataset")
            os.exit(0)

        # getting network graph and node coordinates
        is_driected_graph = True
        # # another method of getting graph, this could be useful when there is no from and to node information
        # graph, node_coords = GeoUtil.get_network_graph(link_shp_name, is_driected_graph)
        graph, node_coords = GeoUtil.create_network_graph_from_field(link_dataset, self.fromnode_fld_name,
                                                                     self.tonode_fld_name, is_driected_graph)
        # reverse the graph to acculate the damage to next to node
        graph = nx.DiGraph.reverse(graph, copy=True)

        # check the connection as a list
        connection_sets = []
        if is_driected_graph:
            connection_sets = list(nx.weakly_connected_components(graph))
        else:
            connection_sets = list(nx.connected_components(graph))


        # # to plot graph
        # GeoUtil.plot_graph_network(graph, node_coords)

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
            guid_fld_val = ''
            try:
                guid_fld_val = node_feature['properties'][self.guid_fldname.lower()]
            except:
                pass
            try:
                guid_fld_val = node_feature['properties'][self.guid_fldname]
            except:
                pass
            guid_list.append(guid_fld_val)

            # get nodenwid colum
            nodenwid_fld_val = ''
            try:
                nodenwid_fld_val = int(node_feature['properties'][self.nodenwid_fld_name.lower()])
            except:
                pass
            try:
                nodenwid_fld_val = int(node_feature['properties'][self.nodenwid_fld_name])
            except:
                pass
            nodenwid_list.append(nodenwid_fld_val)

        for z in range(self.nmcs):
            nodedam = [0] * self.nnode    # placeholder for recording number of damaged pole for each node
            noderepair = [0] * self.nnode # placeholder for recording repair cost for each node
            poles2repair = [0] * self.nnode   # placeholder for recording total number of poles to repair
            cost2repairpath = [0] * self.nnode    # placeholder for recording total repair cost for the network
            time2repairpath = [0] * self.nnode  # placeholder for recording total repair time for the network
            nodetimerep = [0] * self.nnode

            # iterate link
            for line_feature in link_dataset:
                ndamage = 0  # number of damaged poles in each link
                repaircost = 0  # repair cost value
                repairtime = 0  # repair time value
                to_node_val = ""
                from_node_val = ""
                linetype_val = ""
                windspeed = 0  # random wind speed in EF

                try:
                    to_node_val = line_feature['properties'][self.tonode_fld_name.lower()]
                except:
                    pass
                try:
                    to_node_val = line_feature['properties'][self.tonode_fld_name]
                except:
                    pass
                try:
                    from_node_val = line_feature['properties'][self.fromnode_fld_name]
                except:
                    pass
                try:
                    from_node_val = line_feature['properties'][self.fromnode_fld_name.lower()]
                except:
                    pass
                try:
                    linetype_val = line_feature['properties'][self.linetype_fld_name]
                except:
                    pass
                try:
                    linetype_val = line_feature['properties'][self.linetype_fld_name.lower()]
                except:
                    pass

                line = shape(line_feature['geometry'])

                # # if the line consists of multiple segments
                # seg_coord_list = list(line.coords)
                # new_line_feature_list = []
                # if len(seg_coord_list) > 2:
                #     for seg_start, seg_end in self.align_list_cooridnate(seg_coord_list):
                #         tmp_line_feature = copy.deepcopy(line_feature)
                #         single_seg_coord_list = [seg_start, seg_end]
                #         line_geom = LineString(single_seg_coord_list)
                #         tmp_line_feature['geometry'] = mapping(line_geom)
                #         new_line_feature_list.append(tmp_line_feature)
                # # line only contains a single segment
                # else:
                #     new_line_feature_list.append(line_feature)

                # iterate tornado
                for tornado_feature in tornado_dataset:
                    resistivity_probability = 0  # resistivity value at the point of windSpeed
                    random_resistivity = 0  # random resistivity value between 0 and one

                    sim_fld_val = ""
                    ef_fld_val = ""

                    # get EF rating and simulation number column
                    try:
                        sim_fld_val = int(tornado_feature['properties'][self.tornado_sim_field_name.lower()])
                    except:
                        pass
                    try:
                        sim_fld_val = int(tornado_feature['properties'][self.tornado_sim_field_name])
                    except:
                        pass
                    try:
                        ef_fld_val = tornado_feature['properties'][self.tornado_ef_field_name.lower()]
                    except:
                        pass
                    try:
                        ef_fld_val = tornado_feature['properties'][self.tornado_ef_field_name]
                    except:
                        pass

                    if (sim_fld_val == "" or ef_fld_val == ""):
                        print("unable to convert tornado simulation field value to integer")
                        sys.exit(0)

                    # get Tornado EF polygon
                    # assumes that the polygon is not a multipolygon
                    poly = shape(tornado_feature['geometry'])
                    poly_list.append(poly)

                    # loop for ef ranges
                    for f in range(self.tornado_ef_rate):
                        npoles = 0  # number of poles in tornado ef box
                        poleresist = 0  # pole's resistance value
                        # setting EF rate value string to match in the tornado dataset's attribute table
                        ef_content = "EF" +  str(f)

                        # compute the intersections between link line and ef polygon
                        # also figure out the length of the line that ovelapped with EF box

                        # compute the intersection between tornado polygon and line
                        if (sim_fld_val == z) and ef_fld_val.lower() == ef_content.lower():
                            if (poly != None and line != None):
                                if poly.intersects(line):
                                    intersection = poly.intersection(line)
                                    any_point = None
                                    intersection_length = intersection.length
                                    if intersection.length > 0:
                                        #print(intersection.__class__.__name__)
                                        # calculate the length of intersected line
                                        # since this is a geographic, it has to be projected to meters to be calcuated
                                        inter_length_meter = GeoUtil.calc_geog_distance_from_linestring(intersection)
                                        if(intersection.__class__.__name__) == "MultiLineString":
                                            intersection_list.append(intersection)
                                            for inter_line in intersection:
                                                any_point = inter_line.centroid
                                                break
                                        elif (intersection.__class__.__name__) == "LineString":
                                            intersection_list.append(intersection)
                                            any_point = intersection.centroid
                                            # also, random point can be possible by changing the following lines value 0.5
                                            # any_point = intersection.interpolate(0.5, normalized=True)
                                    if (any_point != None):
                                        # check if any_point is in the polygon
                                        if (poly.contains(any_point) == False) :
                                            # this is very hardly happen but should be needed just in case
                                            any_point = poly.centroid

                                    windspeed = self.hazardsvc.get_tornado_hazard_value(tornado_id, "mph", any_point.coords[0][1], any_point.coords[0][0], z)

                                    # check if the line is tower or transmission
                                    if linetype_val.lower() == self.line_transmission:
                                        resistivity_probability = AnalysisUtil.calculate_damage_json(fragility_set_tower, windspeed)
                                    else:
                                        resistivity_probability = AnalysisUtil.calculate_damage_json(fragility_set_pole, windspeed)

                                    # randomly generated capacity of each poles ; 1 m/s is 2.23694 mph
                                    poleresist = resistivity_probability.get('immocc') * 2.23694
                                    npoles = int(round(inter_length_meter / self.pole_distance))
                                    repairtime_list = []

                                    for k in range(npoles):
                                        repair_time = 0
                                        random_resistivity = random.uniform(0, 1)

                                        if random_resistivity <= poleresist:
                                            ndamage += 1
                                            # following codes can't be converted from matlab to python
                                            # however, the cross product <=3 or == 24 almost doesn't happen
                                            # since the time and cost differs when it is pole or tower,
                                            # this could be changed by see if it is tower or pole
                                            # if numpy.cross(k, z) <= 3 or numpy.cross(k, z) == 24:
                                            if linetype_val.lower() == self.line_transmission:
                                                mu = self.mut
                                                sigma = self.sigmat
                                                tmu = self.tmut
                                                tsigma = self.tsigmat
                                            else:
                                                mu = self.mud
                                                sigma = self.sigmad
                                                tmu = self.tmud
                                                tsigma = self.tsigmad

                                            repairtime_list.append(numpy.random.normal(tmu, tsigma))

                                    for k in range(ndamage):
                                        repaircost =+ numpy.random.lognormal(mu, sigma)

                                    # max of the repair time among different poles is taken as the repair time for that line
                                    if len(repairtime_list) > 0:
                                        repairtime = max(repairtime_list)
                noderepair[to_node_val - 1] = repaircost
                nodedam[to_node_val - 1] = ndamage
                nodetimerep[to_node_val - 1] = repairtime

            # Calculate damage and repair cost based on network
            for i in range(len(first_node_list)):
                for j in range(len(connection_list[i])):
                    # print(connection_list[i][j], first_node_list[i])
                    pathij = list(nx.all_simple_paths(graph,connection_list[i][j], first_node_list[i]))
                    poler = 0
                    coster = 0
                    timer = []
                    # print(pathij)
                    if len(pathij) > 0:
                        for k in range(len(pathij)):
                            for l in range(len(pathij[k])):
                                poler = poler + nodedam[pathij[k][l]]
                                coster = coster + noderepair[pathij[k][l]]
                                # max of the time for different lines is taken as the repair time for that path.-- path is constituted of different lines.
                                timer.append(nodetimerep[pathij[k][l]])
                    poles2repair[connection_list[i][j]] = poler
                    cost2repairpath[connection_list[i][j]] = coster
                    if (len(timer)) > 0:
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
        results = []

        for i in range(len(meanpoles)):
            epn_results = collections.OrderedDict()
            guid_dict = collections.OrderedDict()
            meanpole_dict = collections.OrderedDict()
            stdpole_dict = collections.OrderedDict()
            meancost_dict = collections.OrderedDict()
            stdcost_dict = collections.OrderedDict()
            meantime_dict = collections.OrderedDict()
            stdtime_dict = collections.OrderedDict()

            guid_dict["guid"] = guid_list[i]
            meanpole_dict["meanpoles"] = meanpoles[i]
            stdpole_dict["stdpoles"] = stdpoles[i]
            meancost_dict["meancost"] = meancost[i]
            stdcost_dict["stdcost"] = stdcost[i]
            meantime_dict["meantime"] = meantime[i]
            stdtime_dict["stdtime"] = stdtime[i]

            epn_results.update(guid_dict)
            epn_results.update(meanpole_dict)
            epn_results.update(stdpole_dict)
            epn_results.update(meancost_dict)
            epn_results.update(stdcost_dict)
            epn_results.update(meantime_dict)
            epn_results.update(stdtime_dict)
            results.append(epn_results)

        return results

    """
    align coordinate values in a list as a single pair in order
    """
    def align_list_cooridnate(self, coord_list):
        coord_iterator = iter(coord_list)
        first = prev = next(coord_iterator)
        for coord in coord_iterator:
            yield prev, coord
            prev = coord

            # if it is polygon the following line is needed to close the polygon geometry
            # yield coord, first

    def set_tornado_variables(self, tornado_dataset):
        sim_num_list = []
        ef_rate_list = []

        for ef_poly in tornado_dataset:
            ef_string = ''
            try:
                sim_num_list.append(int(ef_poly['properties'][self.tornado_sim_field_name.lower()]))
            except:
                pass
            try:
                sim_num_list.append(int(ef_poly['properties'][self.tornado_sim_field_name]))
            except:
                pass
            try:
                ef_string = ef_poly['properties'][self.tornado_ef_field_name.lower()]
            except:
                pass
            try:
                ef_string = ef_poly['properties'][self.tornado_ef_field_name]
            except:
                pass
            # parse the number in EF and the format should be "EF0", "EF1", or something like it
            ef_rate_list.append(int(ef_string.lower().split("ef", 1)[1]))

        if (len(sim_num_list) == 0 or len(ef_string) == 0):
            print("Could not convert tornado simulation value")
            sys.exit(0)

        self.nmcs = max(sim_num_list) + 1
        self.tornado_ef_rate = max(ef_rate_list) + 1


    def set_node_variables(self, node_dataset):
        i = 0

        for node_point in node_dataset:
            node_id = None
            indpnode_val = None
            try:
                node_id = int(node_point['properties'][self.nodenwid_fld_name.lower()])
            except:
                pass
            try:
                node_id = int(node_point['properties'][self.nodenwid_fld_name])
            except:
                pass

            if self.use_indpnode == True:
                try:
                    indpnode_val = int(node_point['properties'][self.indpnode_fld_name.lower()])
                except:
                    pass
                try:
                    indpnode_val = int(node_point['properties'][self.indpnode_fld_name])
                except:
                    pass

            if (node_id == None and indpnode_val == None):
                print("problem getting the value")
                sys.exit(1)

            if self.use_indpnode == True:
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
            'name': 'tornado-epn-damage',
            'description': 'tornado epn damage analysis',
            'input_parameters': [
                {
                    'id': 'result_name',
                    'required': True,
                    'description': 'result dataset name',
                    'type': str
                },
                {
                    'id': 'tornado_id',
                    'required': True,
                    'description': 'Tornado hazard id',
                    'type': str
                }
            ],
            'input_datasets': [
                {
                    'id': 'epn_node',
                    'required': True,
                    'description': 'EPN Node',
                    'type': ['incore:epnNodeVer1'],
                },
                {
                    'id': 'epn_link',
                    'required': True,
                    'description': 'EPN Link',
                    'type': ['incore:epnLinkeVer1'],
                },
                {
                    'id': 'tornado',
                    'required': True,
                    'description': 'Bridge Damage Ratios',
                    'type': ['tornadowindfield'],
                }

            ],
            'output_datasets': [
                {
                    'id': 'result',
                    'parent_type': 'epn_node',
                    'type': 'incore:tornadoEPNDamageVer1'
                }
            ]
        }

if __name__ == "__main__":
    tornado_id = '5b2173a9b1cf3e336db2f1d8'
    tornado_dataset_id = '5b2173a0b1cf3e336d7d11b0'
    epn_node_id = '5b1fdb50b1cf3e336d7cecb1'
    epn_link_id = '5b1fdc2db1cf3e336d7cecc9'
    client = InsecureIncoreClient("http://incore2-services.ncsa.illinois.edu:8888", "ywkim")

    ted = TornadoEpnDamage(client)
    # tornado_file_id = self.datasetsvc.get_tornado_dataset_id_from_service(tornado_dataset_id, self.client)
    ted.load_remote_input_dataset("epn_node", epn_node_id)
    ted.load_remote_input_dataset("epn_link", epn_link_id)
    ted.load_remote_input_dataset("tornado", tornado_dataset_id)

    result_name = "eq_bldg_dmg_result"
    ted.set_parameter("result_name", result_name)
    ted.set_parameter('tornado_id', tornado_id)

    ted.run_analysis()

