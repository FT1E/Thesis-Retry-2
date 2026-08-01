
import sys
import random

sys.path.append('..')

from util.routing_heuristic import calculate_cost
from solution_representation.Route import Route

# used in the solution representation to represent a single day of the solution consisting of routes in the day
# also has a list of edges, which can be inferred from the routes


class Day:

    def __init__(self, number, serviced_edges, adjacency_lists, vehicle, graph_id):
        
        self.number = number                # which day is it - starting from 0

        # main elements
        self.edges = serviced_edges     # list of edges in the day
        self.routes = []                # list of routes using the edges assigned to this day

        # ? below 2 are just for reference for calculating initial routes using CW
        self.adjacency_lists = adjacency_lists
        self.vehicle = vehicle
        self.graph_id = graph_id        
        
        # calculate initial routes using CW
        self.recalculate_routes()


    # GENERAL METHODS
    # - for now only printing methods
    
    def __repr__(self):
        return f"Day {self.number}, number of edges {len(self.edges)}, number of routes {len(self.routes)}"

    def __str__(self):
        line_0 = [self.__repr__()]
        edge_lines = ["\n\tEdges:\n"] + [f"\t{edge}" for edge in self.edges]
        route_lines = ["\n\tRoutes:\n"] + [f"\tRoute: {i + 1}\n{str(route)}" for i, route in enumerate(self.routes)]
        lines = line_0 + edge_lines + route_lines
        return '\n'.join(lines)
    
    def print(self):
        print(str(self))


    # END GENERAL METHODS

    # INITIAL ROUTE GENERATION - using CW

    def recalculate_routes(self):

        info = calculate_cost(self.adjacency_lists, self.edges, self.vehicle, self.graph_id)

        self.routes = info['routes']

        for route in self.routes:
            route.set_day(self.number)



    # END INITIAL ROUTE GENERATION

    # LOCAL SEARCH METHODS

    # COST EVALUATION
    # ? note that number of vehicles used for the day is equal to the number of routes in the day

    # evaluate routing cost for the day
    def calculate_routing_cost(self):
        routing_cost = 0
        for route in self.routes.copy():

            if len(route.targets) == 0:
                self.remove_route(route)
                continue
            
            routing_cost += route.length
        
        return routing_cost
    
    # END COST EVALUATION

    def add_edge_in_list(self, edge):
        if edge not in self.edges:
            self.edges.append(edge)
            return True

        print(f"\nTrying to add {edge} to day {self.number}, but it's already added.")
        print(f"Service days: {edge.service_days}\n")
        return False

    def remove_edge_in_list(self, edge):
        try:
            self.edges.remove(edge)
            return True
        except:
            print(f"\nTrying to remove {edge} from edge list for day {self.number} but it's not in it.\n")
            
            return False

    def add_route(self, route):
        if len(route.targets) > 0 and route not in self.routes:
            self.routes.append(route)
            route.set_day(self.number)
            return True
        return False

    def remove_route(self, route = None, route_id=None):
        if route_id is not None:
            try:
                route = self.routes.pop(route_id)
            except:
                print(f"\nIndex out of bounds {route_id} for removing route in day {self.number} by giving route_id. Length of self.routes == {len(self.routes)}\n")
                return False
        elif route is not None:
            try:
                self.routes.remove(route)
            except:
                print(f"\nRoute not in day {self.number}, when trying to remove route by passing value. Length of self.routes == {len(self.routes)}\n")
                return False
        
        return True

    
    # ? add a new edge to the day, i.e. add a new service for the edge
    # ? use insert edge if adding to a specific route in a specific position
    def add_edge(self, edge):
        # - edge is added in a random route at the end

        # if edge is already in edge list, then it's already in some route
        if not self.add_edge_in_list(edge):
            return False

    
        # else either make a new route if day has no routes, or insert it in a random one
        if len(self.routes) == 0:
            # if day has no routes
            route = Route([edge])
            self.add_route(route)
        else:
            # add it to a random route
            # other operators will move it to a better route
            route = random.choice(self.routes)
            route.insert_edge(edge)

        edge.add_service_day(self.number)
        
        return True    
        
    # ? insert edge at a specific position in a specific route
    # ? add_edge just adds it to a random route at the end
    def insert_edge(self, edge, route, pos):
        # if edge is already in edge list, then it's already in some route
        if not self.add_edge_in_list(edge):
            return False

        # this is for undo
        route.insert_edge(edge, pos = pos)
        if len(route.targets) == 1:
            self.add_route(route)

        edge.add_service_day(self.number)
        


    # remove an edge from the day, i.e. remove the service of an edge in a day
    def remove_edge(self, edge):

        # implicitly connect the points which were connected by the removing edge
        # ex. say remove b in 0-a-b-c-0, result is 0-a-c-0, where 0 is depot node

        affected_route = self.get_edge_route(edge)
        if affected_route is None:
            print(f"\nTrying to remove {edge} from day {self.number} (day number) but its route not present\n")
            return False

        self.remove_edge_in_list(edge)
        affected_route.remove_edge(edge)
        edge.remove_service_day(self.number)


        if len(affected_route.targets) == 0:
            self.remove_route(affected_route)
        
        return edge
    

    def get_edge_route(self, edge):
        if edge.routes[self.number] is not None:
            return edge.routes[self.number]

        for route in self.routes:
            if edge in route.targets:
                return route

        if edge in self.edges:
            print(f"\n{edge} is in day {self.number} list, but not in any route in this day\n")
        
        return None

    # checker - if code works fine, it would be enough to return (edge not in self.edges), but extra checks just in case
    def edge_in_day(self, edge):
        if edge not in self.edges:
            return False
        if self.get_edge_route(edge) is None:
            return False

        return True
    
    # END LOCAL SEARCH METHODS
