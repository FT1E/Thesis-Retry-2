
# Program start point in this script


from data.read_data import get_graph_al, get_graph_demanded_edges, get_graph_metadata, get_vehicle_data
from solution_representation.Edge import PriorityType

from util.logger import print_day_assignment

# greedy algorithms
from algorithms.greedy_single import run as gs_run
from algorithms.greedy_dynamic_clusters import run as gdc_run
from algorithms.greedy_static_clusters import run as gsc_run

GRAPH_ID = 0
VEHICLE_ID = 0


DYNAMIC_CLUSTER_SIZE_LIMIT = 5


graph_meta_data = get_graph_metadata(GRAPH_ID)
vehicle = get_vehicle_data(VEHICLE_ID)

vehicle['count'] = 35

# adjacency lists for edge priority calculated by distance/length of edge
# used for calculating initial routes with Clarke-Wright Heuristic
adjacency_lists_distance = get_graph_al(GRAPH_ID, PriorityType.Distance, filter = vehicle['planning_duration'])



# adjacency lists with edge priority calculated by deadline - for greedy dynamic clusters algorithm
adjacency_lists_deadline = get_graph_al(GRAPH_ID, filter = vehicle['planning_duration'])
demanded_edge_list = get_graph_demanded_edges(GRAPH_ID, filter = vehicle['planning_duration'])


# todo - runs with different initial solution

# day_assignments, capacity_used = gs_run(demanded_edge_list, vehicle)

day_assignments, capacity_used = gdc_run(demanded_edge_list.copy(), adjacency_lists_deadline, vehicle)

# day_assignments, capacity_used = gsc_run(demanded_edge_list, adjacency_lists_distance, vehicle, GRAPH_ID)


