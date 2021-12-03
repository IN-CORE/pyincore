# Define Python Libraries
import pandas as pd
import numpy as np
import pylab
import itertools
from numpy import array
import matplotlib.pyplot as plt

from pyincore import BaseAnalysis, HazardService, FragilityService, DataService, FragilityCurveSet


class HospitalFunctionality(BaseAnalysis):
    """
    Computes electric power network (EPN) probability of damage based on a tornado hazard.
    The process for computing the structural damage is similar to other parts of the built environment.
    First, fragilities are obtained based on the hazard type and attributes of the network tower and network pole.
    Based on the fragility, the hazard intensity at the location of the infrastructure is computed. Using this
    information, the probability of exceeding each limit state is computed, along with the probability of damage.
    """
    def __init__(self, incore_client):
        self.datasetsvc = DataService(incore_client)

        super(HospitalFunctionality, self).__init__(incore_client)

    ###############################################
    # Model Input Data
    ###############################################
    def run(self):
        hospital_dataset = self.get_input_dataset("hospital_functionality")
        hospital_input_dataset = self.get_input_dataset("hospital_functionality_input")

        bt = hospital_input_dataset.get_dataframe_from_csv(low_memory=False)
        Ht = hospital_dataset.get_dataframe_from_csv(low_memory=False)

        # Functionality and recovery trajectory of the water system in the investigated community
        Water = bt.iloc[:, 1].squeeze()
        # Functionality and recovery trajectory of the power system in the investigated community
        Power = bt.iloc[:, 2].squeeze()
        # Functionality and recovery trajectory of the transportation system in the investigated community
        Trans = bt.iloc[:, 3].squeeze()
        # Functionality and recovery trajectory of the telecommunication system in the investigated community
        Telecom = bt.iloc[:, 4].squeeze()
        # Functionality and recovery trajectory of the wastewater system in the investigated community
        Wastewater = bt.iloc[:, 5].squeeze()
        # Functionality and recovery trajectory of the fuel (natural gas) system in the investigated community
        Fuel = bt.iloc[:, 6].squeeze()
        # Functionality and recovery trajectory of the housing units in the investigated community
        Housing = bt.iloc[:, 7].squeeze()

        E_S = bt.iloc[:, 8].squeeze()  # Recovery trajectory of the hospital structural components
        E_S_n = bt.iloc[:, 9].squeeze()  # Recovery trajectory of the hospital non-structural components
        H_Travel_time = bt.iloc[:, 10].squeeze()  # Travel time to the investigated hospital
        N_t = bt.iloc[:, 11].squeeze()  # Daily number of patients at the investigated hospital

        F_s = Ht.iloc[0, 0].squeeze()  # Structural losses value at the investigated hospital
        F_ns = Ht.iloc[0, 1].squeeze()  # Non-structural losses value at the investigated hospital
        F_s_ns = Ht.iloc[0, 2].squeeze()  # Total losses value at the investigated hospital
        F_c = Ht.iloc[0, 3].squeeze()  # Conents losses value at the investigated hospital
        F_DS = Ht.iloc[0, 4].squeeze()  # Social losses value at the investigated hospital
        Housing_DS = Ht.iloc[0, 5].squeeze()  # Mean social losses for the whole community
        Wt = Ht.iloc[0, 6].squeeze()  # Delay time due to the structural repair
        Wt_ns = Ht.iloc[0, 7].squeeze()  # Delay time due to structural and non-structural repair
        T_structural = Ht.iloc[0, 8].squeeze()  # Time to finish the structural components repair
        T_nonstructural = Ht.iloc[0, 9].squeeze()  # Time to finish the non-structural components repair
        T_sev = Ht.iloc[0, 10].squeeze()  # Time of high severity patients

        a_0 = Ht.iloc[0, 11].squeeze()  # Basic waiting time
        a_t = Ht.iloc[0, 12].squeeze()  # Impact of staffed bed reduction on the waiting time
        a_e = Ht.iloc[0, 13].squeeze()  # Impact of patient increase on the waiting time
        N_0 = Ht.iloc[0, 14].squeeze()  # Number of patients at the investigated hospital before the disaster

        W_max = Ht.iloc[0, 15].squeeze()  # Maximum acceptable waiting time
        W_t_min = Ht.iloc[0, 16].squeeze()  # Minimal possible waiting time
        T_t_min = Ht.iloc[0, 17].squeeze()  # Maximum possible treatment time
        T_t_0 = Ht.iloc[0, 18].squeeze()  # Minimal possible treatment time

        n_hospitals = 1  # Total number of hospitals
        Recovery_T = 300  # The recovery time frame
        B_0 = 70  # Total number of staffed beds at the investigated hospital
        s = 1
        m = 1

        R1 = np.zeros((Recovery_T, n_hospitals))  # Physicians availability
        R2 = np.zeros((Recovery_T, n_hospitals))  # Nurses availability
        R3 = np.zeros((Recovery_T, n_hospitals))  # Supporting staff availability
        R4 = np.zeros((Recovery_T, n_hospitals))  # Alternative staffing availability
        R5 = np.zeros((Recovery_T, n_hospitals))  # Corridor functionality
        R6 = np.zeros((Recovery_T, n_hospitals))  # Elevator functionality
        R7 = np.zeros((Recovery_T, n_hospitals))  # Stairs functionality
        R8 = np.zeros((Recovery_T, n_hospitals))  # Municipal water functionality
        R9 = np.zeros((Recovery_T, n_hospitals))  # Backup water functionality
        R10 = np.zeros((Recovery_T, n_hospitals))  # Municipal power system functionality
        R11 = np.zeros((Recovery_T, n_hospitals))  # Backup power system functionality
        R12 = np.zeros((Recovery_T, n_hospitals))  # Transportation network functionality
        R13 = np.zeros((Recovery_T, n_hospitals))  # Transportation detors functionality
        R14 = np.zeros((Recovery_T, n_hospitals))  # Ambulance service functionality
        R15 = np.zeros((Recovery_T, n_hospitals))  # Telecommunication service functionality
        R16 = np.zeros((Recovery_T, n_hospitals))  # Backup Telecommunication service functionality
        R17 = np.zeros((Recovery_T, n_hospitals))  # Municipal wastewater functionality
        R18 = np.zeros((Recovery_T, n_hospitals))  # Backup wastewater functionality
        R19 = np.zeros((Recovery_T, n_hospitals))  # Drinking water system functionality
        R20 = np.zeros((Recovery_T, n_hospitals))  # Backup drinking water functionality
        R21 = np.zeros((Recovery_T, n_hospitals))  # Structural component functionality
        R22 = np.zeros((Recovery_T, n_hospitals))  # Non-structural component functionality
        R23 = np.zeros((Recovery_T, n_hospitals))  # Contents component functionality
        R24 = np.zeros((Recovery_T, n_hospitals))  # Backup space functionality
        R25 = np.zeros((Recovery_T, n_hospitals))  # Oxygen availability
        R26 = np.zeros((Recovery_T, n_hospitals))  # Surgical supply availability
        R27 = np.zeros((Recovery_T, n_hospitals))  # Rx availability
        R28 = np.zeros((Recovery_T, n_hospitals))  # Fuel supply availability
        R29 = np.zeros((Recovery_T, n_hospitals))  # Food supply availability
        R30 = np.zeros((Recovery_T, n_hospitals))  # Other supply availability

        # Average functionality of the utility without transportation for the investigated hospital
        E_s_average_no_trans = np.zeros((Recovery_T, n_hospitals))
        # Average functionality of the utility with transportation for the investigated hospital
        Utility_trans = np.zeros((Recovery_T, n_hospitals))
        # Average functionality of the utility with transportation and housing for the investigated hospital
        Utility_trans_Housing = np.zeros((Recovery_T, n_hospitals))

        # Plot the change in utility functionality over the recovery time
        T_p = list(range(0, 300))  # Plot X axis range
        plt.plot(T_p, Water, T_p, Power, T_p, Trans, T_p, Telecom, T_p, Wastewater, T_p, Fuel, T_p, Housing)
        plt.xlabel("Time (days)")
        plt.ylabel("Utility (Functionality)")
        font = {'family': 'DejaVu Sans', 'weight': 'bold', 'size': 15}
        plt.rc('font', **font)
        plt.xlim([0, 300])
        plt.ylim([0, 1])
        plt.show()

    ###############################################
    # Main Events Calculations
    ###############################################
        for s in range(Recovery_T):
            # Transportation network and detour
            R12[s] = Trans[s]  # Transportation system functionality
            R13[s] = 0.0  # Transportation debtors functionality

            # average functionality of the utility
            # average functionality of the utility without transportation
            E_s_average_no_trans[s] = np.mean([Water[s], Power[s], Telecom[s], Wastewater[s], Fuel[s], E_S_n[s]])
            # average utility and transportation
            Utility_trans[s] = (max(R12[s], R13[s]) + E_s_average_no_trans[s]) / 2
            # minimum of utility, transportation and housing
            Utility_trans_Housing[s] = (Utility_trans[s] + Housing[s]) / 2

        s = 1
        m = 1

        for s in range(Recovery_T):
            # Personnel Availability
            if s <= Wt:
                R1[s] = F_DS
            elif (Utility_trans_Housing[s]) > 0.5:
                R1[s] = 1.0
            else:
                R1[s] = Utility_trans_Housing[s]+1-Utility_trans_Housing[s]  # Physician availability

            R2[s] = R1[s]  # Nurses availability
            R3[s] = R1[s]  # Supportive staff availability

            if s <= Wt:  # Alternative staffing availability
                R4[s] = (1-Housing_DS)
            elif (Utility_trans_Housing[s]) > 0.5:
                R4[s] = 1.0
            else:
                R4[s] = Utility_trans_Housing[s]+1-Utility_trans_Housing[s]

            # Accessibility
            if s <= (Wt+T_structural):   # Corridor functionality
                R5[s] = F_ns
            else:
                R5[s] = E_S_n[s]

            R6[s] = R5[s]  # Elevator functionality
            R7[s] = R5[s]  # Stairs functionality

            # Supportive Infrastructure
            # Municipal systems
            R8[s] = Water[s]  # Municipal water functionality
            R10[s] = Power[s]   # Municipal power functionality

            # Ambulance service functionality
            R14[s] = min(E_S_n[s] - 0.25 * (1 - Telecom[s]) - N_t[s] * 0.0, E_S_n[s])
            R14[s] = max(R14[s], 0)

            R15[s] = Telecom[s]  # Telecom service functionality
            R17[s] = Wastewater[s]  # Municipal wastwater functionality
            R19[s] = Water[s]  # Drinking water functionality

            # Backup systems
            # Backup water system functionality
            if s == 1.0:
                R9[s] = min(F_s_ns+(R8[s]-0.33), E_S_n[s])
            else:
                R9[s] = min(R9[s-1] + (R8[s]-0.33), E_S_n[s])

            R9[s] = max(R9[s], 0)

            # Fuel availability
            if s == 1.0:
                R28[s] = min(F_s_ns + (Utility_trans[s] - N_t[s]*0.0005), E_S_n[s])
            else:
                R28[s] = min(R28[s-1] + (Utility_trans[s] - N_t[s]*0.0005), E_S_n[s])

            R28[s] = max(R28[s], 0)

            # Backup power system functionality
            if s == 1.0:
                R11[s] = min(F_s_ns+(R28[s]-0.25), E_S_n[s])
            else:
                R11[s] = min(R11[s-1] + (R28[s]-0.25), E_S_n[s])

            R11[s] = max(R11[s], 0)

            # Backup Telecom service functionality
            if s == 1.0:
                R16[s] = min(F_ns + (R10[s] + R11[s] - 0.1), F_ns)
            elif s <= ((Wt+T_structural) - 1):
                R16[s] = min(R16[s-1] + (R10[s] + R11[s] - 0.1), F_ns)
            else:
                R16[s] = min(R16[s-1] + (R10[s] + R11[s]-0.1), E_S_n[s])

            R16[s] = max(R16[s], 0)

            # Backup wastewater system functionality
            if s == 1.0:
                R18[s] = min((F_s + R12[s] + R13[s] - 0.1), (E_S_n[s] + (1 - F_ns)))
            elif s <= ((Wt+T_structural) - 1):
                R18[s] = min(R18[s - 1] + (R12[s] + R13[s] - 0.1), E_S_n[s] + (1 - F_ns))
            else:
                R18[s] = 1.0

            R18[s] = max(R18[s], 0)

            # Backup drinking water functionality
            if s == 1.0:
                R20[s] = min((F_s_ns + R8[s] - 0.33), E_S_n[s])
            else:
                R20[s] = min(R20[s-1] + (R8[s] - 0.33), E_S_n[s])

            R20[s] = max(R20[s], 0)

            # Working Space
            # Structural component functionality
            if s <= Wt:
                R21[s] = F_s
            elif s <= (Wt+T_structural - 1):
                R21[s] = E_S_n[s] + (1-F_ns)
            else:
                R21[s] = 1.0

            # Non-structural component functionality
            if s <= (Wt+T_structural - 1):
                R22[s] = F_ns
            else:
                R22[s] = E_S_n[s]

            # content functionality
            if s <= (Wt+T_structural):
                R23[s] = F_c
            else:
                R23[s] = min(F_c + (1 - F_c) * 0.25 * (s - Wt-T_structural), 1.0)

            # Backup space functionality
            R24[s] = 0.0

            # Supplies
            # Oxygen availability
            if s == 1.0:
                R25[s] = F_ns
            elif s <= ((Wt + T_structural) - 1):
                R25[s] = min(R25[s - 1] + (Utility_trans[s] - N_t[s] * 0.0002), F_ns)
            else:
                R25[s] = min(R25[s - 1] + (Utility_trans[s] - N_t[s] * 0.0002), E_S_n[s])

            R25[s] = max(R25[s], 0)

            R26[s] = R25[s]  # Surgical supply availability
            R27[s] = R25[s]  # Rx availability
            R29[s] = R25[s]  # Food supply availability
            R30[s] = R25[s]  # Other supply availability

        # Plot the change on the basic events over the recovery time
        T_p = list(range(0, 300))  # Plot X axis range
        plt.plot(T_p, R1, T_p, R2, T_p, R3, T_p, R4, T_p, R5, T_p, R6, T_p, R7, T_p, R8, T_p, R9, T_p, R10,
                 T_p, R11, T_p, R12, T_p, R13, T_p, R14, T_p, R15, T_p, R16, T_p, R17, T_p, R18, T_p, R19, T_p, R20,
                 T_p, R21, T_p, R22, T_p, R23, T_p, R24, T_p, R25, T_p, R26, T_p, R27, T_p, R28, T_p, R29, T_p, R30)
        plt.xlabel("Time (days)")
        plt.ylabel("Basic Event (Functionality)")
        font = {'family': 'DejaVu Sans', 'weight': 'bold', 'size': 15}
        plt.rc('font', **font)
        plt.xlim([0, 300])
        plt.ylim([0, 1])
        plt.show()

        ################################################
        # Success tree analysis
        ################################################
        r1_3 = np.zeros((Recovery_T, n_hospitals))       # functionality of physicians, nurses and supporting staff
        r1_4 = np.zeros((Recovery_T, n_hospitals))       # functionality of the staff
        r6_7 = np.zeros((Recovery_T, n_hospitals))       # vertical accessibility
        r5_7 = np.zeros((Recovery_T, n_hospitals))       # total accessibility
        r8_9 = np.zeros((Recovery_T, n_hospitals))       # water functionality
        r10_11 = np.zeros((Recovery_T, n_hospitals))     # power functionality
        r12_13 = np.zeros((Recovery_T, n_hospitals))     # trans functionality
        r12_14 = np.zeros((Recovery_T, n_hospitals))     # total trans functionality
        r15_16 = np.zeros((Recovery_T, n_hospitals))     # telecom. functionality
        r17_18 = np.zeros((Recovery_T, n_hospitals))     # wastewater functionality
        r19_20 = np.zeros((Recovery_T, n_hospitals))     # drinking water functionality
        r8_20 = np.zeros((Recovery_T, n_hospitals))      # total utility functionality
        r21_23 = np.zeros((Recovery_T, n_hospitals))     # hospital building functionality
        r21_24 = np.zeros((Recovery_T, n_hospitals))     # total hospital building functionality
        r5_24 = np.zeros((Recovery_T, n_hospitals))      # functionality of space
        r25_30 = np.zeros((Recovery_T, n_hospitals))     # functionality of supplies
        Func = np.zeros((Recovery_T, n_hospitals))       # total hospital quantity functionality
        Beds = np.zeros((Recovery_T, n_hospitals))       # number of staffed beds at any time t
        for s in range(Recovery_T):
            r1_3[s] = (R1[s] * R2[s] * R3[s])
            r1_4[s] = 1 - ((1 - r1_3[s]) * (1 - R4[s]))
            r6_7[s] = 1 - ((1 - R6[s]) * (1 - R7[s]))
            r5_7[s] = (R5[s] * r6_7[s])
            r8_9[s] = 1 - ((1 - R8[s]) * (1 - R9[s]))
            r10_11[s] = 1 - ((1 - R10[s]) * (1 - R11[s]))
            r12_13[s] = 1 - ((1 - R12[s]) * (1 - R13[s]))
            r12_14[s] = (r12_13[s] * R14[s])
            r15_16[s] = 1 - ((1 - R15[s]) * (1 - R16[s]))
            r17_18[s] = 1 - ((1 - R17[s]) * (1 - R18[s]))
            r19_20[s] = 1 - ((1 - R19[s]) * (1 - R20[s]))
            r8_20[s] = (r8_9[s] * r10_11[s] * r12_14[s] * r15_16[s] * r17_18[s] * r19_20[s])
            r21_23[s] = R21[s] * R22[s] * R23[s]
            r21_24[s] = 1 - ((1 - r21_23[s]) * (1 - R24[s]))
            r5_24[s] = (r5_7[s] * r8_20[s] * r21_24[s])
            r25_30[s] = (R25[s] * R26[s] * R27[s] * R28[s] * R29[s] * R30[s])
            Func[s] = (r1_4[s] * r5_24[s] * r25_30[s])
            Beds[s] = (Func[s] * B_0)

        # Plot the total functionality of the investigated hospital
        plt.plot(Beds)
        plt.xlabel("Time (days)")
        plt.ylabel("Quantity Functionality")
        font = {'family': 'DejaVu Sans', 'weight': 'bold', 'size': 15}
        plt.rc('font', **font)
        plt.xlim([0, 300])
        plt.ylim([0, 1])
        plt.show()

        ################################################
        # Hospital Quality
        ################################################
        W_t = np.zeros((Recovery_T, n_hospitals))   # Waiting time
        T_t = np.zeros((Recovery_T, n_hospitals))   # Treatment time
        S_A = np.zeros((Recovery_T, n_hospitals))   # Accessibility of the medical services at any time t
        S_E = np.zeros((Recovery_T, n_hospitals))   # Effectiveness of the medical services at any time t
        Q_s = np.zeros((Recovery_T, n_hospitals))
        F = np.zeros((Recovery_T, n_hospitals))

        for s in range(Recovery_T):
            # waiting time
            W_t[s] = max(a_0 + H_Travel_time[s] + a_t * (B_0 - Beds[s]) / B_0 + a_e * (N_t[s] - N_0) / N_0, a_0)
            T_t[s] = R1[s]/N_t[s]  # treatment time
            S_A[s] = min(max((W_max - W_t[s]) / (W_max - W_t_min), 0.0), 1.0)  # medical services accessibility
            S_E[s] = min(max((T_t[s] - T_t_min) / (T_t_0 - T_t_min), 0.0), 1.0)  # medical services effectiveness
            Q_s[s] = S_A[s] * S_E[s]  # qualitative functionality

        # Plot the total functionality of the investigated hospital
        plt.plot(Q_s)
        plt.xlabel("Time (days)")
        plt.ylabel("Quality Functionality")
        font = {'family': 'DejaVu Sans', 'weight': 'bold', 'size': 15}
        plt.rc('font', **font)
        plt.xlim([0, 300])
        plt.ylim([0, 1])
        plt.show()

        #################################################
        # Total Functionality
        #################################################
        T_recover = int(np.linalg.norm(Recovery_T) - 3 * T_sev)  # Total recovery stage time
        # Change in the weighting factor of the hospital quality
        I_quality = np.column_stack([np.array(0.25 * np.ones((1, T_sev))), np.array(0.5 * np.ones((1, T_sev))),
                                     0.5 * np.ones((1, T_sev)), 0.5 * np.ones((1, T_recover))])
        for s in range(Recovery_T):
            F[s] = Q_s[s]**(I_quality[0, s]) * Func[s]  # Total functionality of the investigated hospital
            # print(F)

        # Plot the total functionality of the investigated hospital
        plt.plot(F)
        plt.xlabel("Time (days)")
        plt.ylabel("Total Functionality")
        font = {'family': 'DejaVu Sans', 'weight': 'bold', 'size': 15}
        plt.rc('font', **font)
        plt.xlim([0, 300])
        plt.ylim([0, 1])
        plt.show()

        R_list = []
        R_list.append(R1)
        R_list.append(R2)
        R_list.append(R3)
        R_list.append(R4)
        R_list.append(R5)
        R_list.append(R6)
        R_list.append(R7)
        R_list.append(R8)
        R_list.append(R9)
        R_list.append(R10)
        R_list.append(R11)
        R_list.append(R12)
        R_list.append(R13)
        R_list.append(R14)
        R_list.append(R15)
        R_list.append(R16)
        R_list.append(R17)
        R_list.append(R18)
        R_list.append(R19)
        R_list.append(R20)
        R_list.append(R21)
        R_list.append(R22)
        R_list.append(R23)
        R_list.append(R24)
        R_list.append(R25)
        R_list.append(R26)
        R_list.append(R27)
        R_list.append(R28)
        R_list.append(R29)
        R_list.append(R30)

        return T_p, Water, Power, Trans, Telecom, Wastewater, Fuel, Housing, R_list, Beds, Q_s, F

    def get_spec(self):
        return {
            'name': 'hospital-functionality',
            'description': 'hospital functionality analysis',
            'input_parameters': [
                {
                    'id': 'result_name',
                    'required': True,
                    'description': 'result dataset name',
                    'type': str
                }
            ],
            'input_datasets': [
                {
                    'id': 'hospital_functionality',
                    'required': True,
                    'description': 'EPN Node',
                    'type': ['incore:hospitalFunctionality'],
                },
                {
                    'id': 'hospital_functionality_input',
                    'required': True,
                    'description': 'EPN Link',
                    'type': ['incore:hospitalFunctionalityInput'],
                }
            ],
            'output_datasets': [
                {
                    'id': 'result',
                    'parent_type': 'hospital_functionality',
                    'description': 'CSV file of hospital functionality analysis output',
                    'type': 'incore:hospitalFunctionalityOutput'
                }
            ]
        }
