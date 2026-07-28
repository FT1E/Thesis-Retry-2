

# * - make clusters
# * - cluster priority - sum of non-satisfied edges - for satisfaction see class Edge in solution_representation.Edge
#   * - edge is satisfied if since last cleaning day, less than half the frequency days have passed
# * - picking among clusters - when picking cluster only take as target the non-satisfied edges

import heapq as hq

from util.routing_heuristic import calculate_cost

class Cluster:
    def __init__(self, edges):
        self.edges = edges
        self.curr_day = -1

    def priority(self):
        # priority of cluster is equal to the sum of priority of non-satisfied edges
        return sum(edge.priority() for edge in self.edges if not edge.is_satisfied(self.curr_day))

    def demand(self):
        return sum(edge.demand for edge in self.edges if not edge.is_satisfied(self.curr_day))

    def size(self):
        return len(self.edges)
    
    def num_non_satisfied_edges(self):
        res = 0
        for edge in self.edges:
            if not edge.is_satisfied(self.curr_day):
                res += 1
        return res

    def assign_cluster(self):
        for edge in self.edges:
            edge.static_cluster = self

    def assign_egdges_to_cleaning_day(self, cleaning_day):
        # returns the edges which were assigned
        res = []
        for edge in self.edges:
            if not edge.is_satisfied(self.curr_day):
                edge.set_cleaning_day(cleaning_day)
                res.append(edge)

        return res

    def __lt__(self, other):
        return self.priority() < other.priority()



def generate_cw_clusters(demanded_edge_list, adjacency_list, vehicle, graph_id):
    # generate static clusters by giving all of the edges as targets to Clarke-Wright 
    # and turning each route into a static cluster
    routing_info = calculate_cost(adjacency_list, demanded_edge_list, vehicle, graph_id)

    cw_clusters = []
    for route in routing_info['routes']:
        cluster = Cluster(route.targets)
        cw_clusters.append(cluster)
        cluster.assign_cluster()

    return cw_clusters

def run(demanded_edge_list, adjacency_list, vehicle, graph_id):
    # returns day_assignment list
    
    day_assignment = [[] for _ in range(vehicle['planning_duration'])]
    capacity_used = [0] * vehicle['planning_duration']

    max_day_capacity = vehicle['count'] * vehicle['capacity']

    clusters = generate_cw_clusters(demanded_edge_list, adjacency_list, vehicle, graph_id)
    next_day_clusters = []

    for day in range(vehicle['planning_duration']):
        if day+1 in vehicle['days_no_service']:
            continue
        
        # update curr_day in every cluster
        for cluster in clusters:
            cluster.curr_day = day


        # re-sort it
        clusters = clusters + next_day_clusters
        hq.heapify(clusters)
        next_day_clusters = []


        while capacity_used[day] < max_day_capacity and len(clusters) > 0:
            cluster = hq.heappop(clusters)

            if cluster.num_non_satisfied_edges() == 0:
                # meaning that all clusters further will also have no demanding edges
                # print(f'Breaking for day {day+1}')
                next_day_clusters.append(cluster)
                break   # go to next day

            if capacity_used[day] + cluster.demand() > max_day_capacity:
                # if cluster has higher demand than the vehicle can handle for the day then skip it for today
                next_day_clusters.append(cluster)
                continue

            # ? note that this assigns only non-satisfied edges
            capacity_used[day] += cluster.demand()
            new_edges = cluster.assign_egdges_to_cleaning_day(day)
            day_assignment[day].extend(new_edges)

            next_day_clusters.append(cluster)


    return day_assignment, capacity_used