
# used mainly in local search
# represents a solution which can be manipulated to get a different (neighbouring) solution

import sys
import math
import copy

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
    def __init__(self, day_assignments, adjacency_lists, vehicle, graph_id):
        
        self.demanded_edges = []    


        self.graph_id = graph_id
        self.days = []
        day_id = 0
        for day_assignment in day_assignments:
            self.days.append(Day(day_id, day_assignment, adjacency_lists, vehicle, graph_id))
            day_id += 1
            
            for edge in day_assignment:
                if edge not in self.demanded_edges:
                    self.demanded_edges.append(edge)
                
        
        for i, edge in enumerate(self.demanded_edges):
            edge.sid = i
            
            # just create an empty list with size equal to the number of days
            # each day then sets its position in it to reference the route for the edge in that day
            edge.init_routes(vehicle)

        for day in self.days:
            for route in day.routes:
                for edge in route.targets:
                    edge.routes[day.number] = route


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
            # number of services penalty
            irregular_services_count += edge.under_satisfaction_size(self.vehicle)
            irregular_services_count += edge.over_satisfaction_size(self.vehicle)


            irregular_spacing_count += edge.get_irregular_spacing_count(self.vehicle)

        cost = routing_cost + VEHICLE_WEIGHT * vehicle_count + VEHICLE_OVERLOAD_PENALTY * overload_route_count + int(EXPECTED_SERVICES_PENALTY * irregular_services_count) + EXPECTED_SPACING_PENALTY * irregular_spacing_count
        return cost


    def get_overload_route_count(self):
        # number of routes which can't be handled by a single vehicle, go over the limits
        overload_route_count = 0
        
        for day in self.days:
            for route in day.routes:
                overload_route_count += route.overload_size(self.vehicle)

        return overload_route_count

    def get_irregular_services_count(self):
        # number of edges which have too many or too little services
        irregular_services_count = 0

        res_edges = []
        for edge in self.demanded_edges:
            # number of services penalty
            if edge.is_under_satisfied(self.vehicle):
                irregular_services_count += edge.under_satisfaction_size(self.vehicle)
                res_edges.append(edge)
            elif edge.is_over_satisfied(self.vehicle):
                irregular_services_count += edge.over_satisfaction_size(self.vehicle)
                res_edges.append(edge)

        return irregular_services_count, res_edges

    def get_irregular_spacing_count(self):
        # number of spacings which exceed the expected spacing for the edge
        irregular_spacing_count = 0
        res_edges = []
        for edge in self.demanded_edges:
            t = edge.get_irregular_spacing_count(self.vehicle)
            
            irregular_spacing_count += t
            if t > 0:
                res_edges.append(edge)

        return irregular_spacing_count, res_edges

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
            
            if edge.is_under_satisfied(self.vehicle) or edge.is_over_satisfied(self.vehicle):
                unsatisfied_edges.append(edge)
            elif edge.get_irregular_spacing_count(self.vehicle):
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



    def checking_references_1(self):
        print("Checking that every edge is in its service days and not in its no service days")
        
        work_days = set(self.get_work_days())
        for edge in self.demanded_edges:

            for d in edge.service_days:
                try:
                    assert self.days[d].edge_in_day(edge)
                except Exception as e:
                    print(e)
                    print(f"{edge}")
                    print(f"not found in day {d}")
                    print(f"edge service days {edge.service_days}")


            no_service_days = list(work_days.difference(edge.service_days))
            for d in no_service_days:
                try:
                    assert not self.days[d].edge_in_day(edge)
                except Exception as e:
                    print(e)
                    print(f"{edge}")
                    print(f"found in day {d}")
                    print(f"edge service days {edge.service_days}")
                
        print("References are fine!")

    def checking_references_2(self):
        print("Checking that edges in day.edges are the same edges as in solution.demanded edges")
        
        for day in self.days:
            for edge in day.edges:
                di = self.demanded_edges.index(edge)
                if edge is not self.demanded_edges[di]:
                    print(f"{edge} has mismatching references")
                    print(f"Day edge: {edge}")
                    print(f"Solution edge: {self.demanded_edges[di]}")
                    print(f"day.edges edge service days: {edge.service_days}")
                    print(f"solution.demanded_edges edge service days: {self.demanded_edges[di].service_days}")
                
        print("References are fine!")

    def checking_references_3(self):
        print("Checking that all routes in day.routes have targets length > 0")
        for day in self.days:
            for route in day.routes:
                assert len(route.targets) > 0

        print("Routes are fine!")

    # END LOCAL SEARCH METHODS


    # CUSTOM DEEPCOPY
    # because of circular references due to edge.routes
    # Route has edges in Route.targets
    # those edges have the same route in edge.routes[route.day]
    def __deepcopy__(self, memo):
        
        # get edge.routes array for each edge
        # and set it to none

        original_edge_routes = [None] * len(self.demanded_edges)
        for edge in self.demanded_edges:
            original_edge_routes[edge.sid] = edge.routes
            edge.routes = [None] * len(edge.routes)


        # normal deep copy, copied edge.routes will be None-s
        class_copy = self.__class__
        new_solution = class_copy.__new__(class_copy)
        memo[id(self)] = new_solution

        for k, v in self.__dict__.items():
            setattr(new_solution, k, copy.deepcopy(v, memo))

        # set edge.routes in this solution
        for sid, routes in enumerate(original_edge_routes):
            self.demanded_edges[sid].routes = routes

        # set routes in new copy
        for day in new_solution.days:
            for route in day.routes:
                for edge in route.targets:
                    edge.routes[day.number] = route
                    
        return new_solution

    # END CUSTOM DEEPCOPY