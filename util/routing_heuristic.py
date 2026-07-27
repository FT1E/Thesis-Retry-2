import heapq as hq
import sys

sys.path.append('..')

from solution_representation.Route import Route
from util.min_distances import calculate_distances, min_distance_ne, min_distance_ee


class Saving:
    def __init__(self, target_1, target_2, saving):
        self.target_1 = target_1
        self.target_2 = target_2
        self.saving = saving

    # defining less than as more than so I can use min-heap - already implemented heapq
    def __lt__(self, other):
        return self.saving > other.saving
    
    # whether the targets in the savings are in the same route
    def same_route(self):
        return self.target_1.route == self.target_2.route
    
    # whether the targets are not endpoints in their routes
    def internal_targets(self):
        # check if both targets are either beginning or ending points of the route
        route = self.target_1.route
        pos_in_route = route.targets.index(self.target_1)
        if pos_in_route > 0 and pos_in_route < len(route.targets) - 1:
            return True
        
        # same for target 2
        route = self.target_2.route
        pos_in_route = route.targets.index(self.target_2)
        if pos_in_route > 0 and pos_in_route < len(route.targets) - 1:
            return True
        
   
     


# * using memoization so distances in a graph are calculated once and then re-using
def calculate_cost(adjacency_list, targets, vehicle, graph_id):

    calculate_distances(adjacency_list, graph_id)

    savings = []
    routes = []

    # ! ASSUMING NODE 0 IS THE DEPOT
    # ? above is handled in read_data.py - if depot node is different than 0, node ids are swapped so that 0 is the depot node


    # initial routing depot-target-depot
    for i in range(len(targets)):
        routes.append(Route([targets[i]]))
        targets[i].route = routes[i]
        

    for i in range(len(targets)):
        d0_e1 = min_distance_ne(0, targets[i])      # distance between depot and edge 1
        for j in range(i+1, len(targets)):
            d0_e2 = min_distance_ne(0, targets[j])              # distance between depot and edge 2
            d_e1_e2 = min_distance_ee(targets[i], targets[j])   # distance between edge 1 and edge 2

            saving = d0_e1 + d0_e2 - d_e1_e2             # savings by connecting edge 1 and edge 2

            savings.append(Saving(targets[i], targets[j], saving))

    hq.heapify(savings)
    while len(routes) > 1 and len(savings) >= 1:
        
        top_saving = hq.heappop(savings)
        
        if top_saving.saving <= 0:
            break      # if the top saving has a negative value stop and return the routes made so far
        
        if top_saving.same_route():
            continue    # if this link is in the same route

        if top_saving.internal_targets():
            continue    # if one of the targets is a mid-point in a route (not beginning or ending point)


        # check if vehicle can handle the distance and capacity of the merged route
        route_1 = top_saving.target_1.route
        route_2 = top_saving.target_2.route


        if route_1.length + route_2.length - top_saving.saving > vehicle['distance_limit']:
            continue
        if route_1.demand + route_2.demand > vehicle['capacity']:
            continue

        # else it's fine and merge the routes
        new_route = route_1.merge_cw(route_2, top_saving)

        routes.remove(route_1)
        routes.remove(route_2)

        routes.append(new_route)


    # organize the output
    res = {'total_distance' : 0, 'num_routes' : len(routes), 'routes' : routes}

    # calculate distance covered
    for route in routes:
        route.set_target_routes()
        res['total_distance'] += route.length

    return res
