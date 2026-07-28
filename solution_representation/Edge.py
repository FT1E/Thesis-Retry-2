
import math
import sys
from enum import Enum

sys.path.append('..')

from solution_representation.constants import EXPECTED_SPACING_PENALTY

PriorityType = Enum('PriorityType', {'Frequency' : 0, 'Deadline' : 1, 'Distance' : 2})


class Edge:

    def __init__(self, number, start_node, end_node, demand, distance, freq, priority_type = PriorityType.Deadline, last_cleaning_day=-1, curr_day=0):
        
        
        # id - note some edges may have same id but different endpoints
        # so in equality check it's checked that edges have same id and same endpoints
        # to differentiate duplicate edges - for edges with more than 1 frequency type
        self.number = number


        self.sid = None # id in solution, set when it's added to a solution
        
        # end-nodes
        self.start_node = start_node
        self.end_node = end_node
        
        # demand, distance, frequency
        self.demand = demand
        self.distance = distance
        self.freq = freq

        # for static clustering algorithm
        self.static_cluster = None

        # run-time info
        self.curr_day = curr_day
        self.last_cleaning_day = last_cleaning_day      # irrelevant for streets which are cleaned only once in time duration
        self.priority_type = priority_type
        self.route = None       # used in CW

        self.service_days = []

        # ? storing references to routes for that day, None if not serviced in that day
        # ? updated whenever service_days is updated - maybe write methods to call to update both, more readable code
        # ? numbers in service_days are indexes where below list has an actual Route object, everywhere else it's None
        self.routes = [None for _ in range(56)]


    # GENERAL METHODS

    # for printing
    def __repr__(self):
        return f"Edge: {self.start_node} <--> {self.end_node} \t Freq: {self.freq} \t Demand: {self.demand}"

    # below to avoid assigning a duplicate edge in the same day
    # below to differentiate duplicate edges
    def __eq__(self, value):
        if not isinstance(value, Edge):
            return False
        return self.number == value.number and ((self.start_node == value.start_node and self.end_node == value.end_node) or (self.start_node == value.end_node and self.end_node == value.start_node))


    # END GENERAL METHODS



    # METHODS USED IN GREEDY ALGORITHM
    
    # ! this shouldn't be called on edges with different priority type
    # ? if their priority value is equal then return the shorter edge - with smaller distance/length
    def __lt__(self, other):
        if self.priority() != other.priority():
            return self.priority() < other.priority()
        else:
            return self.distance < other.distance
    
    def priority(self):
        match self.priority_type:
            case PriorityType.Deadline:
                if self.freq <= 0:
                    return 2000     # ? sufficiently large number so that it's always larger than vehicles with positive frequency
                if self.last_cleaning_day < 0:
                    return -self.freq                       # more priority for edges not serviced at all
                return self.freq + self.last_cleaning_day
            case PriorityType.Frequency:
                return self.freq
            case PriorityType.Distance:
                return self.distance
            case _:
                print("Undefined priority type for class Edge!")
                return None
    
    def set_curr_day(self, day):
        self.curr_day = day

    def set_cleaning_day(self, day):
        self.last_cleaning_day = day
        self.service_days.append(day)

    # used for static clustering - satisfied if since last cleaning day, less than half the frequency days have passed
    def is_satisfied(self, curr_day = None):
        if self.last_cleaning_day < 0:
            return False
        
        if curr_day is not None:
            self.curr_day = curr_day
        return self.last_cleaning_day + self.freq // 2 < self.curr_day
    
    # END - METHODS USED IN GREEDY ALGORITHM



    # METHODS USED IN LOCAL SEARCH / SOLUTION 


    # for just creating an empty list, so the solution can set the route for each day
    def init_routes(self, vehicle):
        self.routes = [None for _ in range(vehicle['planning_duration'])]

    # for having a direct reference to a route for a day
    def set_route(self, day : int, route):
        self.routes[day] = route
            
    # METHODS FOR MANAGING SERVICE_DAYS
    
    # todo remember to pass route argument
    def add_service_day(self, day, route):
        # insert it into the right place
        # loop is O(n), but n is pretty small in this case so it's fine
        for i in range(len(self.service_days)):
            if self.service_days[i] > day:
                self.service_days.insert(i, day)
                break
            elif self.service_days[i] == day:
                self.routes[day] = route
                return True

        # in case it's the last service
        self.service_days.append(day)
        self.routes[day] = route

        # ? below comments for previous implementation
        # todo - set route
        # todo - find all places where route of edge is accessed for day and change it
        # todo - not places where edge is changed when route is given, but when route is looked for
        # ? i guess all places which call day.get_edge_route()


    def remove_service_day(self, day):
        self.service_days.remove(day)
        self.routes[day] = None

    def swap_service_days(self, other_edge : Edge):
        self.service_days, other_edge.service_days = other_edge.service_days, self.service_days

    # END METHODS FOR MANAGING SERVICE_DAYS

    # COST EVALUATION

    # returns true if spacing is neither too wide or too tight for services of this edge
    # created a method so I don't rewrite the same code everywhere it's used
    def spacing_check(self, spacing):
        # check whether spacing is too wide or too tight for this edge with this frequency

        # ceiling of frequency + 1 day for how many weeks in frequency
        # ex. for freq = 7, upper_bound is 8, for freq = 3.5 upper bound is 4
        upper_bound = math.ceil(self.freq) + self.freq // 7 

        # similar to upper bound just subtract for weeks in duration
        # for freq = 7, lower bound is 6, for freq = 3.5 lower bound is 3
        lower_bound = math.floor(self.freq) - self.freq // 7

        return (lower_bound <= spacing and spacing <= upper_bound)
    
    
    def get_irregular_spacing_count(self):
        count = 0

        # not checking spacing between start of planning and first service and last service and end of planning
        # only between two services performed
        for i in range(len(self.service_days) - 1):
            spacing = self.service_days[i+1] - self.service_days[i]
            if not self.spacing_check(spacing):
                count += 1

        return count

    # for estimating cost of new solution after operators, instead of doing full solution evaluate
    def spacing_cost(self, vehicle):
        return self.get_irregular_spacing_count() * cost
        
    # END COST EVALUATION


    # LS PHASE 1 

    def is_under_satisfied(self, vehicle):
        service_count = len(self.service_days)
        expected_service_count = math.floor(vehicle['planning_duration'] / math.ceil(self.freq))
        if service_count < expected_service_count:
            return True
        return False


    def is_over_satisfied(self, vehicle):
        service_count = len(self.service_days)
        expected_service_count = math.ceil(vehicle['planning_duration'] / math.ceil(self.freq))
        if service_count > expected_service_count:
            return True
        return False

    # END LS PHASE 1

    # END METHODS USED IN LOCAL SEARCH / SOLUTION 


    