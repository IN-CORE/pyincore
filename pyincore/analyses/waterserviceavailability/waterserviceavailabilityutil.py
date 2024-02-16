import pandas as pd
import networkx as nx
import wntr


class WaterServiceAvailabilityUtil:

    @staticmethod
    def generate_results_normal(wdn, stage_end_time, demand_model="PDD"):
        """
        Perform hydraulic simulation for normal conditions as the baseline

        Args:
            wdn:
            stage_end_time:
            demand_model:

        Returns:

        """
        # Specify time duration of interest
        wdn.options.time.duration = stage_end_time * 3600
        # Specify the demand model to be pressure driven demand
        wdn.options.hydraulic.demand_model = demand_model
        # Specify the simulatior
        sim_normal = wntr.sim.WNTRSimulator(wdn)
        # Results is the object stores necessary flow, pressure, and demand data (all in SI units)
        results = sim_normal.run_sim()

        return results

    @staticmethod
    def hourly_dgraph(wdn, flow, t):
        """
        Build hourly hydraulic-informed directed graph

        Args:
            flow:
            t:

        Returns:

        """

        # Initiated the directed graph
        dgraph = nx.DiGraph()
        # Iterate over all the links
        for name, link in wdn.links():
            # Determine the direction of edge through the flow rate, positive: as stored, negative: change direction
            linkflow = flow.loc[3600 * t, name]
            if linkflow >= 0:
                start_node = link.start_node_name
                end_node = link.end_node_name
            else:
                start_node = link.end_node_name
                end_node = link.start_node_name
            dgraph.add_node(start_node, pos=wdn.get_node(start_node).coordinates)
            dgraph.add_node(end_node, pos=wdn.get_node(end_node).coordinates)
            dgraph.add_edge(start_node, end_node, linkid=name)
        return dgraph

    @staticmethod
    def map_to_household_service_availability(house_junction, service_availability):
        household_service_availability = pd.DataFrame(columns=house_junction.keys(), index=service_availability.index)
        for index, row in household_service_availability.iterrows():
            for c in household_service_availability.columns:
                # The water service availability for this household is equal to its corresponding junction node
                row[c] = service_availability.loc[index, house_junction[c]]

        return household_service_availability

    @staticmethod
    def map_to_building_service_availability(building_junction, service_availability):
        building_service_availability = pd.DataFrame(columns=building_junction.keys(), index=service_availability.index)
        for index, row in building_service_availability.iterrows():
            for c in building_service_availability.columns:
                # The water service availability for this household is equal to its corresponding junction node
                row[c] = service_availability.loc[index, building_junction[c]]

        return building_service_availability
