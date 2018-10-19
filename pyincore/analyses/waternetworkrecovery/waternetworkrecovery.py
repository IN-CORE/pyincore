import pandas as pd
import numpy as np
import pickle
from collections import OrderedDict
from matplotlib import colors
import wntr
from pyincore.analyses.waternetworkrecovery.waternetworkrecoveryutil import WaterNetworkRecoveryUtil


class WaterNetworkRecovery:

    def __init__(self, WN_input_file, demand):
        '''
        initailize the water network
        :param WN_input_file:
        '''

        self.WN_input_file = WN_input_file

        # save original water network
        wn = wntr.network.WaterNetworkModel(WN_input_file)

        if demand is not None:
            for i in wn.junction_name_list:
                junction = wn.get_node(i)
                if str(i) in demand.keys():
                    junction.demand = demand[str(i)]
                else:
                    continue

        with open('wn.pickle', 'wb') as f:
            print('save water network as wn.pickle file')
            pickle.dump(wn, f)

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


    def wn_recoveryNday(self, pipe_PEDS, pump_PEDS, tank_PEDS, WN_rec_atr, rec_params,
                        n_days=3, demand=None, save_model=True, seed=67823):

        # load original water network
        with open('wn.pickle', 'rb') as f:
            wn = pickle.load(f)

        wn.options.time.duration = n_days * 24 * 3600
        wn.options.time.hydraulic_timestep = 3600
        wn.options.time.report_timestep = 3600

        # get failing pumps
        pump_DS = WaterNetworkRecoveryUtil.sample_damage_state(pump_PEDS,['Complete','Extensive'])
        pumps_to_fail = list(pump_DS[(pump_DS == 'Complete') | (pump_DS == 'Extensive')].index)
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
        tank_DS = WaterNetworkRecoveryUtil.sample_damage_state(tank_PEDS, ['Complete', 'Extensive'])
        tanks_to_fail = list(tank_DS[(tank_DS == 'Complete') | (tank_DS == 'Extensive')].index)

        # get failing pipes
        nleak_pipe = pd.Series(np.random.poisson(0.85 * np.array(pipe_PEDS['mean_repair_rate']).astype('float64')),
            index=pipe_PEDS.index)
        nbreak_pipe = pd.Series(
            np.random.poisson(0.15 * np.array(pipe_PEDS['mean_repair_rate']).astype('float64')),
            index=pipe_PEDS.index)
        WN_rec_atr['Breaks'] = nbreak_pipe
        WN_rec_atr['Leaks'] = nleak_pipe

        # calculate recovery schedule
        crew, prod_param, work_hour_day, tzero = rec_params
        rectime_pipe = self.calculate_recoverytime(WN_rec_atr, crew, prod_param,
                                       work_hour_day, tz=tzero,
                                       mincrew=[2, 2, 2, 2, 1, 2])

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
                                              2) * 24  * 3600
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

        # save water network model
        if save_model == True:
            with open('wnNday.pickle', 'wb') as f:
                pickle.dump(wn, f)

        # run simulation
        sim = wntr.sim.WNTRSimulator(wn, mode='PDD')

        return sim.run_sim(), wn


    def wn_rec_intrp_Nday(self, n_days=5, intrp_day=3, demand=None):

        with open('wnNday.pickle', 'rb') as f:
            wn = pickle.load(f)
        wn.options.time.duration = n_days * 24 * 3600
        wn.options.time.hydraulic_timestep = 3600
        wn.options.time.report_timestep = 3600

        ########
        if demand is not None:
            time = intrp_day * 24 * 3600
            timeflag = 'SIM_TIME'
            dailyflag = False
            for i in wn.junction_name_list:
                if str(i) in demand.keys():
                    junction = wn.get_node(i)
                    cond = wntr.network.controls.SimTimeCondition(wn, '>', time)
                    act = wntr.network.controls.ControlAction(junction,
                                                              'demand',
                                                              demand[str(i)])
                    ctrl = wntr.network.controls.Control(cond, act, name='intrp_demand_control')
                    wn.add_control('ctrl_' + str(i), ctrl)
                else:
                    continue

        sim = wntr.sim.WNTRSimulator(wn, mode='PDD')

        return sim.run_sim(), wn


    def set_recovery_attributes(self,
                                pipe_PEDS,
                                pipe_zone_file,
                                work_hour_day=16,
                                tzero=4,
                                prod_param = (20, 4),
                                crew= [[6, 5, 7, 7, 1, 6],[4, 3, 4, 4, 1, 4],[4, 3, 4, 4, 1, 4]]):
        WN_rec_atr = pipe_PEDS['pipe_length'].to_frame('Length')
        WN_rec_atr.index = WN_rec_atr.index.map(str)
        zone = pd.read_csv(pipe_zone_file)
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


    def calculate_recoverytime(self, WN_rec_atr, crew, prod_param, work_hour_day, tz=0,
                         mincrew=[1, 1, 1, 1, 1, 1]):

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


    def output_water_network(self,resultsNday, wnNday, timestamp):
        pressure = resultsNday.node['pressure'].loc[timestamp, :]
        pressure0 = WaterNetworkRecoveryUtil.pressure_plot(np.array(pressure))
        pressure0 = pd.Series(pressure0, index=pressure.index)
        mycmap = colors.ListedColormap(['red', 'yellow', 'green'])

        wntr.graphics.plot_network(wnNday, node_attribute=pressure0,
                                   node_cmap=mycmap)
