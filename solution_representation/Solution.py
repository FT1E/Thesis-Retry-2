
# used mainly in local search
# represents a solution which can be manipulated to get a different (neighbouring) solution

import sys
import math
sys.path.append('..')
from solution_representation.Day import Day
from solution_representation.constants import VEHICLE_WEIGHT, VEHICLE_OVERLOAD_PENALTY, EXPECTED_SERVICES_PENALTY, EXPECTED_SPACING_PENALTY


# Hierarchy
#   - each solution contains days
#   - each day contains trips routes for it
#   - each route contains a sequence of required edges to traverse



class Solution:

    # self.day_assignments[i] = routes for day i
    # self.work_day[i] = true if i is a work day, else false - depends on vehicle

    
    # ? NOTE - adjacency lists should have edges with priority type distance
    def __init__(self, day_assignments, demanded_edges, adjacency_lists, vehicle, graph_id):
        
        self.demanded_edges = demanded_edges

        for i, edge in enumerate(self.demanded_edges):
            edge.sid = i
            
            # just create an empty list with size equal to the number of days
            # each day then sets its position in it to reference the route for the edge in that day
            edge.init_routes(vehicle)     


        self.graph_id = graph_id
        self.days = []
        day_id = 0
        for day_assignment in day_assignments:
            self.days.append(Day(day_id, day_assignment, adjacency_lists, vehicle, graph_id))
            day_id += 1

        # ? below just for reference for calculating routing cost
        self.vehicle = vehicle
        self.adjacency_lists = adjacency_lists
        
        # for op2 - self.frequency_bucket[i] = (list of all edges with frequency i)
        self.frequency_buckets = dict()
        self.init_freq_buckets()


    # GENERAL METHODS
    
    def __repr__(self):
        return f"Solution:\nNumber of days: {len(self.days)}\nSolution score: {self.evaluate()}"
    
    def __str__(self):
        return '\n\n'.join([str(day) for day in self.days])

    def print(self):
        print(str(self))

    # END GENERAL METHODS

    # LOCAL SEARCH METHODS

    
    def get_work_days(self):
        # all except weekends - 5,6 - considering monday 0, tue 1, etc.
        return [i for i in range(len(self.days)) if i % 7 < 5]

    # COST EVALUATION

    def evaluate(self):
        
        # vehicle count is the maximum number of vehicles used among all days, under the assumption that a vehicle has at most 1 route in a day
        vehicle_count = 0

        # routing cost is the total routing cost among all day
        routing_cost = 0
        
        # number of routes which can't be handled by a single vehicle, go over the limits
        overload_route_count = 0
        
        for day in self.days:
            routing_cost += day.calculate_routing_cost()

            vehicle_count = max(vehicle_count, len(day.routes))

            for route in day.routes:
                overload_route_count += route.overload_size(self.vehicle)


        # number of spacings which exceed the expected spacing for the edge
        irregular_spacing_count = 0

        # number of edges which have too many or too little services
        irregular_services_count = 0

        for edge in self.demanded_edges:
            if len(edge.service_days) == 0:
                # for edges which weren't serviced at all - skip them
                # that penalty is added separately - expected services count
                continue

            # number of services penalty
            if edge.is_under_satisfied(self.vehicle) or edge.is_over_satisfied(self.vehicle):
                irregular_services_count += 1

            irregular_spacing_count += edge.get_irregular_spacing_count()

        cost = routing_cost + VEHICLE_WEIGHT * vehicle_count + VEHICLE_OVERLOAD_PENALTY * overload_route_count + EXPECTED_SERVICES_PENALTY * irregular_services_count+ EXPECTED_SPACING_PENALTY * irregular_spacing_count
        return cost

    # END COST EVALUATION


    # for checking if all edges had their frequency satisfied
    def unsatisfied_edges(self, print_info = False):
        unsatisfied_edges = []
        ignored_edges = 0
        for edge in self.demanded_edges:
            if len(edge.service_days) == 0:
                ignored_edges += 1
                unsatisfied_edges.append(edge)
                continue
            
            if edge.get_irregular_spacing_count():
                unsatisfied_edges.append(edge)
    
        if print_info:
            print(f"Total number of edges: {len(self.demanded_edges)}")
            print(f"Number of unsatisfied edges: {len(unsatisfied_edges)}")
            print(f"{ignored_edges} edges were not serviced at all!")
        return unsatisfied_edges 

    def get_over_satisfied_edges(self):
        over_satisfied_edges = []

        for edge in self.demanded_edges:
            if edge.is_over_satisfied(self.vehicle):
                over_satisfied_edges.append(edge)

        return over_satisfied_edges

    def get_under_satisfied_edges(self):
        under_satisfied_edges = []
        
        for edge in self.demanded_edges:
            if edge.is_under_satisfied(self.vehicle):
                under_satisfied_edges.append(edge)

        return under_satisfied_edges


    def total_number_of_services(self):
        cnt = 0
        for day in self.days:
            cnt += len(day.edges)
        return cnt
    
    def expected_number_of_services(self):
        res = 0
        for edge in self.demanded_edges:
            res += (self.vehicle['planning_duration'] / math.ceil(edge.freq))
        return res
    

    # for op2 - instead of skipping to just directly get the needed edges
    def init_freq_buckets(self):
        for edge in self.demanded_edges:
            if edge.freq not in self.frequency_buckets:
                self.frequency_buckets[edge.freq] = [edge]
            else:
                self.frequency_buckets[edge.freq].append(edge)



    def checking_references(self):
        print("For checking specific reference trees. Method is empty right now.")
        pass

    # END LOCAL SEARCH METHODS
