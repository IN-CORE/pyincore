import numpy as np
import pandas as pd
import math
import copy
from scipy.stats import norm
from shapely.geometry import Point, Polygon
import collections
import fiona
from fiona.crs import from_epsg
import json
import csv
import ast
from rtree import index

class WaterNetworkRecoveryUtil:

	@staticmethod
	def compute_recovery_probabilities(time, restoration_curve):
		median = restoration_curve['median']
		beta = restoration_curve['beta']
		point = time

		if point == 0:
			return 0

		else:
			x = (math.log(point)-math.log(median)) / beta
			probability = norm.cdf(x)

			return probability

	@staticmethod
	def sample_damage_state(Pr, state_name):
		"""
		Sample the damage state using a uniform random variable

		 Parameters
		-----------
		Pr : pd.Dataframe that contains probability of a damage state

		Returns
		-------
		damage_state : pd.Series
			The damage state of each element
		"""
		p = pd.Series(data=np.random.uniform(size=Pr.shape[0]), index=Pr.index)

		damage_state = pd.Series(data=[None] * Pr.shape[0], index=Pr.index)

		for DS_names in state_name:
			damage_state[p < Pr[DS_names]] = DS_names

		return damage_state

	@staticmethod
	def prodrate(crew, prodp, mincrew):
		"""
		 calculate productivity rate
		:param crew:
		:param prodp:
		:param mincrew:
		:return:
		"""
		from numpy.random import beta
		Prod = np.zeros(6)
		Prod[0] = 300.0 / 8 * WaterNetworkRecoveryUtil.cogestion_correction(crew[0], mincrew[0])
		Prod[1] = 330.0 / 8 * WaterNetworkRecoveryUtil.cogestion_correction(crew[1], mincrew[1])
		Prod[2] = 0.5 * WaterNetworkRecoveryUtil.cogestion_correction(crew[2], mincrew[2])
		Prod[3] = 2.0 * WaterNetworkRecoveryUtil.cogestion_correction(crew[3], mincrew[3])
		Prod[4] = 0.5 * WaterNetworkRecoveryUtil.cogestion_correction(crew[4], mincrew[4])
		Prod[5] = 1500.0 / 8 * WaterNetworkRecoveryUtil.cogestion_correction(crew[5], mincrew[5])
		Prod = Prod * beta(prodp[0], prodp[1], len(Prod))
		return Prod

	@staticmethod
	def cogestion_correction(x, xmin):
		y = min((x / xmin) ** 0.9, 10 ** 0.9)
		return y * xmin

	@staticmethod
	def zonescheduler(WN, zone, crew, tzero, Prod):
		dmgi = WN.index[np.logical_and(WN['RecZone'] == zone,
									   np.logical_or(WN['Breaks'] > 0,
													 WN['Leaks'] > 0))]
		# get activity quantities
		Qtt = WaterNetworkRecoveryUtil.Quant(WN['Breaks'][dmgi].values, WN['Leaks'][dmgi].values)
		# get durations in working hours
		Dura = Qtt / Prod
		# Get Inter unit times working hours
		Inter = np.zeros_like(Dura)
		Inter.fill(10. / 60.)
		# Start and finish time crew continuity and crew availability
		SCrew = np.zeros_like(Dura)
		FCrew = np.zeros_like(Dura)
		FCrew[0, :] = SCrew[0, :] + Dura[0, :]
		for i in range(1, len(Dura)):
			SCrew[i, :] = FCrew[i - 1, :] + Inter[i - 1, :]
			FCrew[i, :] = SCrew[i, :] + Dura[i, :]

		# Start and finish time acticity precedence
		SLogic = np.zeros_like(SCrew)
		for j in range(1, Dura.shape[1]):
			SLogic[:, j] = SLogic[:, j - 1] + Dura[:, j - 1]

		# Start and finish time all constraints
		Snew = np.zeros_like(SCrew)
		Snew[:, 0] = SCrew[:, 0]
		Snew[0, :] = SLogic[0, :]
		Fnew = np.zeros_like(SCrew)
		Fnew[:, 0] = Snew[:, 0] + Dura[:, 0]
		Fnew[0, :] = Snew[0, :] + Dura[0, :]
		for j in range(1, Dura.shape[1]):
			for i in range(1, Qtt.shape[0]):
				Snew[i, j] = max(Snew[i, j - 1] + SLogic[i, j],
								 Fnew[i - 1, j] + Inter[i - 1, j])
				Fnew[i, j] = Snew[i, j] + Dura[i, j]
		# Shift time origin to fit zone start times
		Snew = Snew + tzero
		Fnew = Fnew + tzero
		return dmgi, Snew, Fnew

	@staticmethod
	def Quant(breaks, leaks):
		# Q break[excavation,shoring,patching,caulk&seal,testing,backfill]
		# US units for RS means purposes
		Qtt = np.zeros((len(breaks), 6))
		# excaving dimensions, pavement breaking to be included later
		# 3ft by 4ft by 3ft deep
		Qtt[:, 0] = (breaks + leaks) * 3 * 4 * 3
		# shoring
		Qtt[:, 1] = (breaks + leaks) * 4 * 3 * 2
		# Patching
		Qtt[:, 2] = breaks
		# Caulk&seal
		Qtt[:, 3] = leaks
		# testing
		Qtt[:, 4] = 1
		# Backfill
		Qtt[:, 5] = Qtt[:, 0]
		return Qtt

	@staticmethod
	def pressure_plot(p):
		p[p < 10] = 0
		p[np.logical_and(p >= 10, p <= 15)] = 20
		p[p > 30] = 40
		return p

	@staticmethod
	def get_waternode_bldgs_relations(zoning, bldg):
		idx = index.Index()
		polygons = []
		waternode_bldg_relations = {}

		for i, zone in enumerate(zoning):
			polygon = Polygon(zone['geometry']['coordinates'][0])
			id = zone['properties']['id']
			waternode_bldg_relations[id] = {'type': zone['properties']['pattern'],
							 'buildings': [],
							 'area': zone['properties']['area']}

			idx.insert(i, polygon.bounds)
			polygons.append(polygon)

		for i, row in bldg.iterrows():

			point = Point(row['Longitude'], row['Latitude'])

			# interate through spatial index
			for j in idx.intersection(point.coords[0]):
				if point.within(polygons[j]):
					id = zoning[j]['properties']['id']
					waternode_bldg_relations[id]['buildings'].append(row['Address Point ID'])

		# sve that waternode_bldg_relations mapping file to json
		with open('waternode_bldg_relations.json', 'w+') as f:
			json.dump(waternode_bldg_relations, f)

		# save that waternode_bldg_relations mapping file to csv
		with open('waternode_bldg_relations.csv', 'w+') as f:
			headers = ['waternode_id', 'area', 'type', 'buildings']
			w = csv.writer(f, headers)
			w.writerow(headers)
			for key in waternode_bldg_relations.keys():
				w.writerow(
					[key] + [waternode_bldg_relations[key][column] for
							 column in headers[1:]])

		print('waternode_bldg_relations.json')
		print('waternode_bldg_relations.csv')

	@staticmethod
	def get_waternode_bldgs_relations_skeletonized(zoning,
													   water_demand_node,
													   buildings_waternode):
			"""
			:param zoning: zoning shapefile that has ORZoningID
			:param water_demand_node: water demand node that has id
			:param buildings_waternode: building_waternode input file
			:return: save relationships in either json or csv
			"""
			idx = index.Index()
			polygons = []
			waternode_bldg_relations = {}

			for i, zone in enumerate(zoning):
				polygon = Polygon(zone['geometry']['coordinates'][0])
				idx.insert(i, polygon.bounds)
				polygons.append(polygon)

			for node in water_demand_node:
				id = node['properties']['id']
				waternode_bldg_relations[id] = \
					{
						'type': '',
						'buildings': [],
						'area': 0.0
					}
				point = Point(node['geometry']['coordinates'])

				for j in idx.intersection(point.coords[0]):
					if point.within(polygons[j]):
						waternode_bldg_relations[id]['type'] = \
						zoning[j]['properties']['ORZoningID']
						waternode_bldg_relations[id]['area'] = \
						zoning[j]['properties']['Area']

			for i, row in buildings_waternode.iterrows():
				waternode_bldg_relations[str(int(row['wtrdnd1']))][
					'buildings'].append(row['strctid'])

			# sve that waternode_bldg_relations mapping file to json
			with open('waternode_bldg_relations.json', 'w+') as f:
				json.dump(waternode_bldg_relations, f)

			# save that waternode_bldg_relations mapping file to csv
			with open('waternode_bldg_relations.csv', 'w+') as f:
				headers = ['waternode_id', 'area', 'type', 'buildings']
				w = csv.writer(f, headers)
				w.writerow(headers)
				for key in waternode_bldg_relations.keys():
					w.writerow(
						[key] + [waternode_bldg_relations[key][column] for
								 column in headers[1:]])

			print('waternode_building_relations.json')
			print('waternode_building_relations.csv')

	@staticmethod
	def get_water_demand_node(water_facilities):
		water_demand_nodes = []
		for node in water_facilities:
			if node['properties']['demand'] != '' and float(
					node['properties']['demand']) > 0:
				water_demand_nodes.append(node)

		return water_demand_nodes

	@staticmethod
	def save_water_demand_node(water_demand_nodes,
							   shapefile_name='Facility_detailed_demand_node.shp'):
		properties = collections.OrderedDict()
		properties['id'] = 'str:10'
		properties['elev'] = 'float'
		properties['demand'] = 'float'
		properties['pattern'] = 'str:10'
		properties['head'] = 'int'
		properties['initlevel'] = 'int'
		properties['minlevel'] = 'int'
		properties['maxlevel'] = 'int'
		properties['diameter'] = 'float'
		properties['minvol'] = 'float'
		properties['volcurve'] = 'float'
		properties['data_type'] = 'str:10'

		schema = {
			'geometry': 'Point',
			'properties': properties
		}

		with fiona.open(shapefile_name,
						'w',
						crs=from_epsg(4326),
						driver='ESRI Shapefile',
						schema=schema) as output:
			for item in water_demand_nodes:
				output.write(item)

	@staticmethod
	def calc_waternode_population(waternode_bldg_relations_file,
								  stochastic_population_file):
		"""
		takes output of stochastic population model (pandas) and aggregate
		the population for each water node
		:param waternode_bldg_relations_file
		:param stochastic_population:
		:return: dictionary that contains { waternode: population }
		"""

		# read csv to dictionary
		waternode_bldg_relations = {}
		with open(waternode_bldg_relations_file, 'r') as f:
			file = csv.DictReader(f)
			for row in file:
				waternode_bldg_relations[row['waternode_id']] = \
					{'area': float(row['area']), 'type': row['type'],
					 'buildings': ast.literal_eval(row['buildings'])}

		# get the corrected number per building based on "dislocated" flag
		stochastic_population = pd.read_csv(stochastic_population_file)
		if 'dislocated' in stochastic_population.columns:
			stochastic_population.loc[
				stochastic_population.dislocated == True, ['numprec']] = 0.0
			stochastic_population[['numprec', 'dislocated']]

		# get population of each water node
		waternode_population = {}
		for waternode_id, content in waternode_bldg_relations.items():
			total_population = \
				stochastic_population[stochastic_population['strctid'].isin(
					content['buildings'])]['numprec'].sum()
			waternode_population[waternode_id] = total_population

		return waternode_population

	@staticmethod
	def calc_waternode_demand(waternode_bldg_relations_file, waternode_population):
		"""
		calculate the water demand based on type, population and area
		:param waternode_bldg_relations_file: waternode_bldg_relations csv
		:param waternode_population: dictionary that contains { waternode: population }
		:return: dictionary that contains { waternode: demand }
		"""

		# read csv to dictionary
		waternode_bldg_relations = {}
		with open(waternode_bldg_relations_file, 'r') as f:
			file = csv.DictReader(f)
			for row in file:
				waternode_bldg_relations[row['waternode_id']] = \
					{'area': float(row['area']), 'type': row['type'],
					 'buildings': ast.literal_eval(row['buildings'])}

		waternode_demand = {}
		for nodeid, population in waternode_population.items():
			# Residential demand = person * 111 gal/person/day
			if waternode_bldg_relations[nodeid]['type'][0:1].lower() == 'r':
				waternode_demand[nodeid] = population * 111 * 4.38126e-8

			# Commercial demand = acre * 2040 gal/acre/day
			elif waternode_bldg_relations[nodeid]['type'][0:1].lower() == 'c':
				waternode_demand[nodeid] = waternode_bldg_relations[nodeid][
											   'area'] * 2040 * 4.38126e-8

			# Industrial demand = acre * 1620 gal/acre/day
			elif waternode_bldg_relations[nodeid]['type'][0:1].lower() == 'm' or \
					waternode_bldg_relations[nodeid]['type'][0:1].lower() == 'i':
				waternode_demand[nodeid] = waternode_bldg_relations[nodeid][
											   'area'] * 1620 * 4.38126e-8

			# schools = person * 16 gal/person/day
			elif waternode_bldg_relations[nodeid]['type'][0:1].lower() == 's':
				waternode_demand[nodeid] = population * 16 * 4.38126e-8

			# hospital = person * 250 gal/person/day
			elif waternode_bldg_relations[nodeid]['type'][0:1].lower() == 'h':
				waternode_demand[nodeid] = population * 250 * 4.38126e-8

			else:
				waternode_demand[nodeid] = 0.0

		return waternode_demand

	@staticmethod
	def additional_waternode_population_dislocation(timestep, wntr_sim_resultsNday,
									 prev_waternode_population):
		"""
		based on water simulation results, if a node's pressure is < 10
		population on that water node dislocated again

		:param timestep: at which time to check node pressure
		:param wntr_sim_resultsNday: wntr simulation result
		:param prev_waternode_population: base population on that waternode to
		perform additional allocation

		:return: new waternode population relations {waternode: population}
		"""

		pressure_timestep = wntr_sim_resultsNday.node['pressure'].loc[timestep,
							:]
		unserved_nodes_timestep = pressure_timestep.index[
			pressure_timestep < 10]
		unserved_nodes_timestep.tolist()

		waternode_population = copy.deepcopy(prev_waternode_population)
		for unserved_node in unserved_nodes_timestep:
			if unserved_node in waternode_population.keys():
				waternode_population[unserved_node] = 0.0

		return waternode_population
