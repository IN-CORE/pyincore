# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/


import pandas as pd
import numpy as np
import pickle
from collections import OrderedDict
import wntr
from pyincore import BaseAnalysis, Dataset
from pyincore.analyses.waternetworkrecovery.waternetworkrecoveryutil import WaterNetworkRecoveryUtil


class WaterNetworkRecovery(BaseAnalysis):

    def run(self):
        """
        Execute Water Network Recovery Process

        """

        # intial water network
        wn = self.get_input_dataset("wn_inp_file").get_EPAnet_inp_reader()

        # initial demand
        demand_initial = self.get_input_dataset("demand_initial").get_json_reader()

        # water network damage
        pipe_PEDS_csv = self.get_input_dataset("pipe_dmg").get_csv_reader()
        pipe_PEDS = pd.DataFrame(list(pipe_PEDS_csv))
        pipe_PEDS.set_index("id", inplace=True)
        pipe_PEDS.index = pipe_PEDS.index.map(str)
        pipe_PEDS = pipe_PEDS.astype({"pipe_length": float,
                                      "hazardval": float,
                                      "mean_repair_rate": float})

        pump_PEDS_csv = self.get_input_dataset("pump_dmg").get_csv_reader()
        pump_PEDS = pd.DataFrame(list(pump_PEDS_csv))
        pump_PEDS.set_index("id", inplace=True)
        pump_PEDS.index = pump_PEDS.index.map(str)
        pump_PEDS = pump_PEDS.astype({"hazardval": float,
                                      "Slight": float,
                                      "Moderate": float,
                                      "Extensive": float,
                                      "Complete": float})

        tank_PEDS_csv = self.get_input_dataset("tank_dmg").get_csv_reader()
        tank_PEDS = pd.DataFrame(list(tank_PEDS_csv))
        tank_PEDS.set_index("id", inplace=True)
        tank_PEDS.index = tank_PEDS.index.map(str)
        tank_PEDS = tank_PEDS.astype({"hazardval": float,
                                      "Slight": float,
                                      "Moderate": float,
                                      "Extensive": float,
                                      "Complete": float})

        # dislocation demand
        demand = self.get_input_dataset("demand").get_json_reader()
        pipe_zone = self.get_input_dataset("pipe_zone").get_csv_reader()

        # additional dislocation demand (optional)
        demand_additional_dataset = self.get_input_dataset("demand_additional")
        if demand_additional_dataset is not None:
            demand_additional = demand_additional_dataset.get_json_reader()
        else:
            demand_additional = None

        result_name = self.get_parameter("result_name")
        n_days = self.get_parameter("n_days")
        seed = self.get_parameter("seed")

        work_hour_day = self.get_parameter("work_hour_day")
        if work_hour_day is None:
            work_hour_day = 16

        tzero = self.get_parameter("tzero")
        if tzero is None:
            tzero = 4

        prod_param = self.get_parameter("prod_param")
        if prod_param is None:
            prod_param = (20, 4)

        crew = self.get_parameter("crew")
        if crew is None:
            crew = [[6, 5, 7, 7, 1, 6],
                    [4, 3, 4, 4, 1, 4],
                    [4, 3, 4, 4, 1, 4]]

        mincrew = self.get_parameter("mincrew")
        if mincrew is None:
            mincrew =[2, 2, 2, 2, 1, 2]

        intrp_day = self.get_parameter("intrp_day")

        ################################################
        # set up the water network
        if demand_initial is not None:
            for i in wn.junction_name_list:
                junction = wn.get_node(i)
                if str(i) in demand_initial.keys():
                    junction.demand = demand_initial[str(i)]
                else:
                    continue

        # save initial water network
        with open(result_name + '_wn.pickle', 'wb') as f:
            print('save water network as wn.pickle file')
            pickle.dump(wn, f)
        initial_wn = Dataset.from_file(result_name + '_wn.pickle', 'pickle')
        self.set_output_dataset("initial_water_network", initial_wn)

        wn.options.time.duration = n_days * 24 * 3600
        wn.options.time.hydraulic_timestep = 3600
        wn.options.time.report_timestep = 3600

        # get failing pumps
        pump_DS = WaterNetworkRecoveryUtil.sample_damage_state(pump_PEDS,
                                                               ['Complete',
                                                                'Extensive'])
        pumps_to_fail = list(
            pump_DS[(pump_DS == 'Complete') | (pump_DS == 'Extensive')].index)
        pump_durations = np.zeros_like(pumps_to_fail, dtype='float64')
        pump_durations = pd.DataFrame(pump_durations,
                                      index=pumps_to_fail,
                                      columns=['Duration'])
        np.random.seed(seed)
        for name in pumps_to_fail:
            if name[0:2] == '20':
                pump_durations.loc[name, 'Duration'] = np.round(
                    1 + 25 * np.random.beta(3, 9), 2) * 24
            else:
                pump_durations.loc[name, 'Duration'] = np.round(
                    0.5 + 3 * np.random.beta(3, 9), 2) * 24

        # get failing tanks
        tank_DS = WaterNetworkRecoveryUtil.sample_damage_state(tank_PEDS,
                                                               ['Complete',
                                                                'Extensive'])
        tanks_to_fail = list(
            tank_DS[(tank_DS == 'Complete') | (tank_DS == 'Extensive')].index)

        # get failing pipes
        nleak_pipe = pd.Series(np.random.poisson(
            0.85 * np.array(pipe_PEDS['mean_repair_rate']).astype('float64')),
                               index=pipe_PEDS.index)
        nbreak_pipe = pd.Series(
            np.random.poisson(
                0.15 * np.array(pipe_PEDS['mean_repair_rate']).astype(
                    'float64')),
            index=pipe_PEDS.index)

        WN_rec_atr, rec_params = self.set_recovery_attributes(pipe_PEDS,
                                                pipe_zone, work_hour_day, tzero,
                                                prod_param, crew)

        WN_rec_atr['Breaks'] = nbreak_pipe
        WN_rec_atr['Leaks'] = nleak_pipe

        # calculate recovery schedule
        crew, prod_param, work_hour_day, tzero = rec_params
        rectime_pipe = self.calculate_recoverytime(WN_rec_atr, crew,
                                                   prod_param,
                                                   work_hour_day, tzero,
                                                   mincrew)

        # Define outage for pipes
        pipes_original = list(pipe_PEDS.index)
        for name in pipes_original:
            if nbreak_pipe[name] > 0:
                pipe = wn.get_link(name)
                break_area = 3.14159 * (pipe.diameter / 2) ** 2
                wn.split_pipe(name, name + '_B', name + '_break_node')
                break_node = wn.get_node(name + '_break_node')

                # Select duration of damage
                duration_of_damage = np.round(rectime_pipe[name], 2) * 3600
                break_node.add_leak(wn, area=break_area, start_time=0,
                                    end_time=duration_of_damage)
            elif nleak_pipe[name] > 0:
                pipe = wn.get_link(name)
                leak_area = 0.03 * 3.14159 * (pipe.diameter / 2) ** 2
                wn.split_pipe(name, name + '_L', name + '_leak_node')
                leak_node = wn.get_node(name + '_leak_node')

                # Select duration of damage
                duration_of_damage = np.round(rectime_pipe[name], 2) * 3600
                leak_node.add_leak(wn, area=leak_area, start_time=0,
                                   end_time=duration_of_damage)
            else:
                continue

        # Define outage for pumps
        for name in pumps_to_fail:
            duration_of_outage = pump_durations.loc[name, 'Duration'] * 3600
            pump = wn.get_link(name)
            pump.add_outage(wn, 0, duration_of_outage)

        # Define outage for tanks
        for name in tanks_to_fail:
            if tank_DS[name] == 'Complete':
                duration_of_outage = np.round(1 + 25 * np.random.beta(3, 9), 2) \
                                     * 24 * 3600
                tank = wn.get_node(name)
                break_area = np.pi * tank.diameter ** 2 / 4
                tank.add_leak(wn, area=break_area, start_time=0.0,
                              end_time=duration_of_outage)
            else:
                duration_of_outage = np.round(0.5 + 3 * np.random.beta(3, 9),
                                              2) * 24 * 3600
                tank = wn.get_node(name)
                break_area = 0.75 * np.pi * tank.diameter ** 2 / 4
                tank.add_leak(wn, area=break_area, start_time=0.0,
                              end_time=duration_of_outage)

        # Change Demand
        if demand is not None:
            for i in wn.junction_name_list:
                junction = wn.get_node(i)
                if str(i) in demand.keys():
                    junction.demand = demand[str(i)]
                else:
                    continue

        with open(result_name + '_wnNday.pickle', 'wb') as f:
            pickle.dump(wn, f)
        recovery_wn = Dataset.from_file(result_name + '_wnNday.pickle', 'pickle')
        self.set_output_dataset("recovery_water_network", recovery_wn)

        # if there's additional allocation happens:
        if demand_additional is not None and intrp_day is not None:
            wn.options.time.duration = n_days * 24 * 3600
            wn.options.time.hydraulic_timestep = 3600
            wn.options.time.report_timestep = 3600

            time = intrp_day * 24 * 3600
            for i in wn.junction_name_list:
                if str(i) in demand_additional.keys():
                    junction = wn.get_node(i)
                    cond = wntr.network.controls.SimTimeCondition(wn, '>',
                                                                  time)
                    act = wntr.network.controls.ControlAction(junction,
                                                              'demand',
                                                              demand_additional[
                                                                  str(i)])
                    ctrl = wntr.network.controls.Control(cond, act,
                                                         name='intrp_demand_control')
                    wn.add_control('ctrl_' + str(i), ctrl)
                else:
                    continue

            with open(result_name + '_wnNday_add.pickle', 'wb') as f:
                pickle.dump(wn, f)
            recovery_wn_add = Dataset.from_file(result_name + '_wnNday_add.pickle', 'pickle')
            self.set_output_dataset("recovery_water_network_add", recovery_wn_add)

        sim = wntr.sim.WNTRSimulator(wn, mode='PDD')
        resultsNday = sim.run_sim()
        resultsNday.node['pressure'].to_csv(result_name + '_water_node_pressure.csv')
        pressure_dataset = Dataset.from_file(result_name + '_water_node_pressure.csv','csv')
        self.set_output_dataset("pressure", pressure_dataset)

        return True

    def set_recovery_attributes(self, pipe_PEDS, pipe_zone, work_hour_day,
                                tzero, prod_param, crew):
        """set the attributes and parameters of the WN recovery

        Args:
            pipe_PEDS: pipeline damage states
            pipe_zone: zones and the pipes belong to each zone
            work_hour_day: hours to work in a day
            tzero: time to start
            prod_param: productivity parameters
            crew: crew memebers and team

        Returns: wn attributes and recvoery parameters

        """

        WN_rec_atr = pipe_PEDS['pipe_length'].to_frame('Length')
        WN_rec_atr.index = WN_rec_atr.index.map(str)
        zone = pd.DataFrame(list(pipe_zone))
        zdict = {}

        for i, pipe in enumerate(zone['OBJECTID']):
            zdict[str(pipe).strip()] = zone['RecZone1'][i].strip()

        zones = []
        for i in WN_rec_atr.index:
            if i in zdict.keys():
                zones.append(zdict[i])

            # missing pipelines in the pipezone file
            # treat them as open space
            else:
                zones.append('OP')

        # zones = [zdict[i] for i in WN_rec_atr.index if i in zdict.keys()]
        zindex = list(np.unique(zones))
        order = ['M', 'R', 'I', 'O']
        zindex.sort(key=lambda x: order.index(x[0]))
        zonesnew = [zindex.index(i) for i in zones]
        WN_rec_atr['RecZone'] = zonesnew

        ##########################
        crew = np.array(crew)
        rec_params = (crew, prod_param, work_hour_day, tzero)

        return WN_rec_atr, rec_params

    def calculate_recoverytime(self, WN_rec_atr, crew, prod_param,
                               work_hour_day, tz, mincrew):
        """calculate the recovery time

        Args:
            WN_rec_atr: wn recovery attribues
            crew: crew members and team
            prod_param: productivity parameters
            work_hour_day: work hour each day
            tz: tzero time to start
            mincrew: minimum crew requirement

        Returns: recovery time

        """

        # Schedule intial common activities
        DATA = []
        meanmax = []
        index = 0
        cri = 1
        mean = 0
        while index < 10 or cri > 0.1:
            tzero = np.full(crew.shape, tz)
            dlinkind = OrderedDict()
            Startt = OrderedDict()
            Finisht = OrderedDict()

            # get hourly productivity rates of crews
            Prod = WaterNetworkRecoveryUtil.prodrate(crew[0], prod_param, mincrew)
            x = WN_rec_atr['RecZone']
            x = pd.unique(x.sort_values())
            for zone in x:
                if zone == 99999:
                    continue
                dmgi = WN_rec_atr.index[np.logical_and(WN_rec_atr['RecZone'] == zone,
                                               np.logical_or(WN_rec_atr['Breaks'] > 0,
                                                             WN_rec_atr['Leaks'] > 0))]
                if len(dmgi) == 0:
                    continue

                tindex = np.argmin(tzero[:, tzero.shape[1] - 1])
                Prod = WaterNetworkRecoveryUtil.prodrate(crew[tindex], prod_param, mincrew)
                dlinkind[zone], Startt[zone], Finisht[
                    zone] = WaterNetworkRecoveryUtil.zonescheduler(WN_rec_atr, zone, crew[tindex],
                                                                   tzero[tindex], Prod)
                tzero[tindex] = Finisht[zone][-1, :]

            for i, key in enumerate(dlinkind.keys()):
                if i == 0:
                    zn = np.zeros(len(dlinkind[key]))
                    zn.fill(key)
                    zn = pd.DataFrame(zn)
                    zn.columns = ['Zone']
                    x = pd.DataFrame(dlinkind[key])
                    x.columns = ['Index']
                    y = pd.DataFrame(Startt[key])
                    y.columns = ['SE', 'SS', 'SBr', 'SL', 'ST', 'SB']
                    z = pd.DataFrame(Finisht[key])
                    z.columns = ['FE', 'FS', 'FBr', 'FL', 'FT', 'FB']
                    df = pd.concat([zn, x, y, z], axis=1)
                else:
                    zn = np.zeros(len(dlinkind[key]))
                    zn.fill(key)
                    zn = zn.astype(int)
                    zn = pd.DataFrame(zn)
                    zn.columns = ['Zone']
                    x = pd.DataFrame(dlinkind[key])
                    x.columns = ['Index']
                    y = pd.DataFrame(Startt[key])
                    y.columns = ['SE', 'SS', 'SBr', 'SL', 'ST', 'SB']
                    z = pd.DataFrame(Finisht[key])
                    z.columns = ['FE', 'FS', 'FBr', 'FL', 'FT', 'FB']
                    temp = pd.concat([zn, x, y, z], axis=1)
                    df = pd.concat([df, temp], axis=0)

            DATA.append(df)
            mean = ((index) * mean + df['FT']) / (index + 1.0)
            meanmax.append(np.max(mean))
            cri = np.std(meanmax) / np.mean(meanmax)
            index += 1

        m = len(DATA)
        n = len(DATA[0])
        times = np.zeros((n, m))
        for i, df in enumerate(DATA):
            times[:, i] = df['FB']
        mean = np.mean(times, axis=1)
        # Output for script2
        pipeindex = DATA[0]['Index']
        pipeindex = pipeindex.astype(str)
        recdict = dict(zip(pipeindex, mean))
        rectime = []
        for i in WN_rec_atr.index.astype(str):
            try:
                rectime.append(recdict[str(i)])
            except:
                rectime.append(0)
        rectime = np.array(rectime)
        rectime = rectime // work_hour_day * 24 + rectime % work_hour_day
        WN_rec_atr['Rectime'] = rectime

        return WN_rec_atr['Rectime']

    def get_spec(self):
        return {
            'name': 'water-network-recovery',
            'description': 'water network recovery analysis',
            'input_parameters': [
                {
                    'id': 'n_days',
                    'required': True,
                    'description': 'n days of recovery simulation',
                    'type': int
                },
                {
                    'id': 'result_name',
                    'required': True,
                    'description': 'base result dataset name',
                    'type': str
                },
                {
                    'id': 'seed',
                    'required': True,
                    'description': 'random seed number',
                    'type': int
                },
                {
                    'id': 'work_hour_day',
                    'required': False,
                    'description': 'how many hours a day that crew works on the WN',
                    'type': int
                },
                {
                    'id': 'tzero',
                    'required': False,
                    'description': 'starting hour',
                    'type': int
                },
                {
                    'id': 'prod_param',
                    'required': False,
                    'description': '',
                    'type': tuple
                },
                {
                    'id': 'crew',
                    'required': False,
                    'description': 'crew setting',
                    'type': list
                },
                {
                    'id': 'mincrew',
                    'required': False,
                    'description': 'minimum crew requirement',
                    'type': list
                },
                {
                    'id': 'intrp_day',
                    'required': False,
                    'description': 'the day to start additional dislocation',
                    'type': int
                }
            ],
            'input_datasets': [
                {
                    'id': 'wn_inp_file',
                    'required': True,
                    'description': 'EPAnet input file',
                    'type': ['waterNetworkEpanetInp'],
                },
                {
                    'id': 'demand_initial',
                    'required': True,
                    'description': 'intial demand for water netowrk',
                    'type': ['json', 'waterNetworkDemand'],
                },
                {
                    'id': 'pipe_dmg',
                    'required': True,
                    'description': 'pipeline damage probability',
                    'type': ['csv', 'pipelineDamage'],
                },
                {
                    'id': 'pump_dmg',
                    'required': True,
                    'description': 'pump damage probability',
                    'type': ['csv', 'pumpDamage'],
                },
                {
                    'id': 'tank_dmg',
                    'required': True,
                    'description': 'tank damage probability',
                    'type': ['csv', 'tankDamage'],
                },
                {
                    'id': 'demand',
                    'required': True,
                    'description': 'demand after dislocation',
                    'type': ['json', 'waterNetworkDemand'],
                },
                {
                    'id': 'pipe_zone',
                    'required': True,
                    'description': 'pipezone to decide repair order',
                    'type': ['csv', 'pipeZoning'],
                },
                {
                    'id': 'demand_additional',
                    'required': False,
                    'description': 'water network demand after additional dislocation',
                    'type': ['json', 'waterNetworkDemand'],
                },
            ],
            'output_datasets': [
                {
                    'id': 'pressure',
                    'type': 'csv'
                },
                {
                    'id': 'initial_water_network',
                    'type': 'pickle'
                },
                {
                    'id': 'recovery_water_network',
                    'type': 'pickle'
                },
                {
                    'id': 'recovery_water_network_add',
                    'type': 'pickle'
                }
            ]
        }

    """
        def wn_impact1day(self, pipe_PEDS, pump_PEDS, tank_PEDS, demand=None, seed=67823):
            '''
            :param pipe_PEDS:
            :param pump_PEDS:
            :param tank_PEDS:
            :param ratio:
            :return:
            '''
            # load original water network
            with open('wn.pickle', 'rb') as f:
                wn = pickle.load(f)

            for name, node in wn.junctions():
                # water meter column: 0.704*psi
                node.nominal_pressure = 0.704 * 15
                node.minimum_pressure = 0.704 * 10

            wn.options.time.duration = 24 * 3600
            wn.options.time.hydraulic_timestep = 3600
            wn.options.time.report_timestep = 3600

            # get failing pumps
            pump_DS = WaterNetworkRecoveryUtil.sample_damage_state(pump_PEDS, ['Complete','Extensive'])
            pumps_to_fail = list(pump_DS[(pump_DS == 'Complete') | (pump_DS == 'Extensive')].index)

            # get failing tanks
            tank_DS = WaterNetworkRecoveryUtil.sample_damage_state(tank_PEDS, ['Complete','Extensive'])
            tanks_to_fail = list(tank_DS[(tank_DS == 'Complete') | (tank_DS == 'Extensive')].index)

            # get leaking pipes
            np.random.seed(seed)
            nleak_pipe = pd.Series(np.random.poisson(0.85 * np.array(pipe_PEDS['mean_repair_rate']).astype('float64')),
                                   index=pipe_PEDS.index)
            nbreak_pipe = pd.Series(np.random.poisson(0.15 * np.array(pipe_PEDS['mean_repair_rate']).astype('float64')),
                                     index=pipe_PEDS.index)

            # break the pipes in WNTR
            pipes_original = list(pipe_PEDS.index)
            for name in pipes_original:
                if nbreak_pipe[name] > 0:
                    pipe = wn.get_link(name)
                    break_area = 3.14159 * (pipe.diameter / 2) ** 2
                    wn.split_pipe(name, name + '_B', name + '_break_node')
                    break_node = wn.get_node(name + '_break_node')

                    # Select duration of damage
                    duration_of_damage = 48 * 3600
                    break_node.add_leak(wn, area=break_area, start_time=0,
                                        end_time=duration_of_damage)

                elif nleak_pipe[name] > 0:
                    pipe = wn.get_link(name)
                    leak_area = 0.03 * 3.14159 * (pipe.diameter / 2) ** 2
                    wn.split_pipe(name, name + '_L', name + '_leak_node')
                    leak_node = wn.get_node(name + '_leak_node')

                    # Select duration of damage
                    duration_of_damage = 48 * 3600
                    leak_node.add_leak(wn, area=leak_area, start_time=0,
                                       end_time=duration_of_damage)
                else:
                    continue

            # Define outage for pumps
            for name in pumps_to_fail:
                duration_of_outage = 48 * 3600
                pump = wn.get_link(name)
                pump.add_outage(wn, 0, duration_of_outage)

            # Define damage states for tanks
            for name in tanks_to_fail:
                if tank_DS[name] == 'Complete':
                    duration_of_outage = 48 * 3600
                    tank = wn.get_node(name)
                    break_area = np.pi * tank.diameter ** 2 / 4
                    tank.add_leak(wn, area=break_area, start_time=0.0,
                                  end_time=duration_of_outage)
                else:
                    duration_of_outage = 48 * 3600
                    tank = wn.get_node(name)
                    break_area = 0.75 * np.pi * tank.diameter ** 2 / 4
                    tank.add_leak(wn, area=break_area, start_time=0.0,
                                  end_time=duration_of_outage)

            # Change Demand
            if demand is not None:
                for i in wn.junction_name_list:
                    junction = wn.get_node(i)
                    if str(i) in demand.keys():
                        junction.demand = demand[str(i)]
                    else:
                        continue


            sim = wntr.sim.WNTRSimulator(wn, mode='PDD')

            return sim.run_sim(), wn
        """


