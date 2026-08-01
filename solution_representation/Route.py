import sys
import math
sys.path.append('..')

from util.min_distances import min_distance_ee, min_distance_ne

# for evaluating cost of route
from solution_representation.constants import VEHICLE_OVERLOAD_PENALTY

# used to represent the routes/trips in a day which is part of the solution to SP-CARP
# also used in the Clarke-Wright routing heuristic (modified to use edges instead of vertices as targets)

class Route:

    def __init__(self, targets, length = None, demand = None, day = None):
        
        self.targets = targets      # sequence of edges which will be visited then traversed
        if length is None:
            self.calculate_length()
        else:
            self.length = length

        if demand is None:
            self.calculate_demand()
        else:
            self.demand = demand

        self.day = day      # reference to the Day class object - the day in which the route belongs

        # set the route reference in the Edge object
        # for CW-Heuristic
        self.set_target_routes()

    # GENERAL METHODS

    def calculate_length(self):
        if len(self.targets) == 0:
            self.length = 0
            return self.length

        # distance beteen depot and first target + distance between depot and last target
        self.length = min_distance_ne(0, self.targets[0]) + min_distance_ne(0, self.targets[-1])
        for i in range(len(self.targets) - 1):
            self.length += min_distance_ee(self.targets[i], self.targets[i+1])
        
        # add length of the edges, not just distances between them
        for edge in self.targets:
            self.length += edge.distance

        return self.length
    
    def calculate_demand(self):
        self.demand = 0
        for target in self.targets:
            self.demand += target.demand
        return self.demand

    # todo - implement below if you sort routes somehow
    # def __lt__(self, other):
    #     return self.length < other.length
    
    def __repr__(self):
        return f"\tRoute length ({self.length}) and demand ({self.demand})"
    
    def __str__(self):
        lines = [self.__repr__()] + [f"\t{edge}" for edge in self.targets]
        return '\n'.join(lines)

    def print(self):
        print(str(self))

    # END GENERAL METHODS

    # METHODS FOR CLARKE-WRIGHT


    def merge_cw(self, other, saving):
        # the conditions for the merging are already checked before
        # if they are not satisfied this shouldn't be called

        # merge two routes and connect the points which are given in the saving
        #  and calculate the new length
        
        t1 = saving.target_1
        if t1 not in self.targets:
            t1 = saving.target_2
            t2 = saving.target_1
        else:
            t2 = saving.target_2

        if self.targets.index(t1) == 0:
            self.targets.reverse()

        if other.targets.index(t2) == 0:
            new_targets = self.targets + other.targets
        else:
            new_targets = self.targets + other.targets[::-1]
        
        length = self.length + other.length - saving.saving
        return Route(new_targets, length, self.demand + other.demand)

    # this is for setting references so above method gets the route immediately
    def set_target_routes(self):
        for target in self.targets:
            target.route = self

    # END METHODS FOR CLARKE-WRIGHT


    # LOCAL SEARCH METHODS - METHOD USED IN LOCAL SEARCH

    
    def set_day(self, day):
        self.day = day



    def overload_size(self, vehicle):
        overload_cnt = 0
        if self.length > vehicle['distance_limit']:            
            overload = self.length - vehicle['distance_limit']
            overload_cnt = math.ceil(overload / vehicle['distance_limit'])
            
        elif self.demand > vehicle['capacity']:
            overload = self.demand - vehicle['capacity']
            overload_cnt = math.ceil(overload / vehicle['capacity'])
            
        return overload_cnt

    # cost of the route in the solution
    #  == routing_cost + penalty * (how many times overload)
    # doing how many times overload, because one route may grow extra large while other routes are fine
    # this way "cheating" won't be tolerated in local search
    def evaluate(self, vehicle):
        cost = self.length
        cost += self.overload_size(vehicle) * VEHICLE_OVERLOAD_PENALTY

        return cost



    # inserts an edge at a position or before a given edge
    def insert_edge(self, new_edge, pos=None, edge_in_route=None):

        if new_edge in self.targets:
            # if edge is already in route
            print(f"The {new_edge} is already in route for day {self.day}")
            # todo - maybe allow this but to put it in different place in route
            return False
    
        # get the position argument if given
        # else put it at the end of the route
        if pos is not None:
            pass
        elif edge_in_route is not None and edge_in_route in self.targets:
            pos = self.targets.index(edge_in_route)
        else:
            # if no valid arguments are given add it at end of route
            pos = len(self.targets)
        
        self.targets.insert(pos, new_edge)
        self.demand += new_edge.demand
        self.calculate_length()
        
        new_edge.routes[self.day] = self

        return True


    def remove_edge(self, edge=None, pos = None):
        
        if edge is not None and edge in self.targets:
            self.targets.remove(edge)
        elif pos is not None:
            try:
                edge = self.targets.pop(pos)
            except:
                return False
        else:
            return False

        self.demand -= edge.demand
        self.calculate_length()
        
        edge.routes[self.day] = None

        return True
    
    def merge(self, other):
        # unlike the merge_cw which specifies with saving which 2 endpoints are to be linked in this case all the possible combinations of endpoint links are tried
        # route a and route b
        # a' means route a in reverse
        # possible links are ab, ab', a'b, a'b'
        # note that ba' is same as ab' since it's connecting last point of a with last point of b
        # deciding based on the cheapest link among endpoints

        if len(other.targets) == 0:
            return self
        elif len(self.targets) == 0:
            return other

        endpoint_a1 = self.targets[0]
        endpoint_a2 = self.targets[-1]
        endpoint_b1 = other.targets[0]
        endpoint_b2 = other.targets[-1]

        link1 = min_distance_ee(endpoint_a1, endpoint_b1)
        link2 = min_distance_ee(endpoint_a1, endpoint_b2)
        link3 = min_distance_ee(endpoint_a2, endpoint_b1)
        link4 = min_distance_ee(endpoint_a2, endpoint_b2)

        if min(link1, link2) < min(link3, link4):
            # link 1st point of a
            part1 = self.targets[::-1]
            if link1 < link2:
                # with 1st point of b
                part2 = other.targets[:]
            else:
                # with last point of b
                part2 = other.targets[::-1]
        else:
            # link last point of a
            part1 = self.targets[:]
            if link3 < link4:
                # with 1st point of b
                part2 = other.targets[:]
            else:
                # with last point of b
                part2 = other.targets[::-1]

        return Route(part1 + part2, demand=self.demand + other.demand)

    # END LOCAL SEARCH METHODS