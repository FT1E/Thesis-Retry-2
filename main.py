
# Program start point in this script

import math
import time
from datetime import timedelta

from data.read_data import get_graph_al, get_graph_demanded_edges, get_graph_metadata, get_vehicle_data
from util.min_distances import calculate_distances
from solution_representation.Edge import PriorityType


# greedy algorithms
from algorithms.greedy_single import run as gs_run
from algorithms.greedy_dynamic_clusters import run as gdc_run
from algorithms.greedy_static_clusters import run as gsc_run


# solution representation
from solution_representation.Solution import Solution


# local search
from algorithms.local_search import run as run_ls
GRAPH_ID = 2
VEHICLE_ID = 6


DYNAMIC_CLUSTER_SIZE_LIMIT = 5


graph_meta_data = get_graph_metadata(GRAPH_ID)
vehicle = get_vehicle_data(VEHICLE_ID)


# adjacency lists for edge priority calculated by distance/length of edge
# used for calculating initial routes with Clarke-Wright Heuristic
adjacency_lists_distance = get_graph_al(GRAPH_ID, PriorityType.Distance, filter = 0)    # filter = 0 is to get no copies of edges in this one



# adjacency lists with edge priority calculated by deadline - for greedy dynamic clusters algorithm
adjacency_lists_deadline = get_graph_al(GRAPH_ID, filter = vehicle['planning_duration'])
demanded_edge_list = get_graph_demanded_edges(GRAPH_ID, filter = vehicle['planning_duration'])

# calculate the min distances before doing anything, then use the functions from there to do anything
calculate_distances(adjacency_lists_distance, GRAPH_ID)



total_demand = 0
for edge in demanded_edge_list:
    total_demand += (vehicle['planning_duration'] / edge.freq) * edge.demand

# print(f"Total demand of edges: {total_demand}")
# print(f"Expected vehicle count: {math.ceil(total_demand / (vehicle['capacity'] * len(vehicle['days_no_service'])))  }")

# ? this is used in greedy algorithms to limit the number of edges assigned in a single day
vehicle['count'] = math.ceil(total_demand / (vehicle['capacity'] * len(vehicle['days_no_service'])))

# todo - runs with different initial solution
# todo - greedy dynamic - run with different cluster sizes, at least one run with infinite size


start = time.perf_counter()

# day_assignments, capacity_used = gs_run(demanded_edge_list, vehicle)

day_assignments, capacity_used = gdc_run(demanded_edge_list, adjacency_lists_deadline, vehicle, DYNAMIC_CLUSTER_SIZE_LIMIT)

# day_assignments, capacity_used = gsc_run(demanded_edge_list, adjacency_lists_distance, vehicle, GRAPH_ID)

end = time.perf_counter()

greedy_time = end - start

print(f"Greedy algorithm time: {greedy_time:.6f} seconds")

solution = Solution(day_assignments, adjacency_lists_distance, vehicle, GRAPH_ID)

# print(solution)

print(f"Cost of initial solution: {solution.evaluate()}")


N = 50      # how many top candidates to consider based on estimation

unsatisfied_edges = solution.unsatisfied_edges(print_info=True)

print(f"Running Local Search with top {N} operations according to estimation")

start = time.time()

ls_score, ls_improved_solution = run_ls(solution, topN=N)

end = time.time()

ls_time = end - start


print("\n----- MARKER - SOLUTION PRINTED BELOW -------\n")

print(ls_improved_solution)

print("\n----- MARKER - SOLUTION PRINTED ABOVE -------\n")


print("Printing greedy algorithm time to avoid scrolling or ctrl+f")
print(f"Greedy algorithm time: {timedelta(seconds = greedy_time)} seconds")
print(f"LS time: {timedelta(seconds = ls_time)}")
print(f"LS return score: {ls_score}")
print(f"Final solution score: {ls_improved_solution.evaluate()}")