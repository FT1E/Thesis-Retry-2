
# Program start point in this script

import math
import time
from datetime import timedelta, datetime
import sys
import os

from data.read_data import get_graph_al, get_graph_demanded_edges, get_graph_metadata, get_vehicle_data, graph_data_directory, vehicle_data_directory
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

if len(sys.argv) == 3:
    GRAPH_ID = int(sys.argv[1])
    VEHICLE_ID = int(sys.argv[2])

print(f"Graph Data file used: {os.listdir(graph_data_directory)[GRAPH_ID]}")
print(f"Vehicle Data file used: {os.listdir(vehicle_data_directory)[VEHICLE_ID]}\n")
print(f"Program starting at: {datetime.now()}")

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
greedy_score = solution.evaluate()
print(f"Cost of initial solution: {greedy_score}")


max_routes = 0
min_routes = float('inf')
for d in solution.get_work_days():
    day = solution.days[d]
    max_routes = max(max_routes, len(day.routes))
    min_routes = min(min_routes, len(day.routes))

print(f"Maximum routes among all days: {max_routes}")
print(f"Minimum routes among all days: {min_routes}")


print("\nPenalties count:")

overloaded_route_count = solution.get_overload_route_count()
irregular_services_count, irreg_serv_count_edges = solution.get_irregular_services_count()
irregular_spacing_count, irreg_space_count_edges = solution.get_irregular_spacing_count()

print(f"Overloaded route count: {overloaded_route_count}")
print(f"Irregular services count: {irregular_services_count}")
print(f"Irregular spacing count: {irregular_spacing_count}")
print('\n')

N = 50      # how many top candidates to consider based on estimation

unsatisfied_edges = solution.unsatisfied_edges(print_info=True)

print(f"Running Local Search with top {N} operations according to estimation\n\n")

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
print(f"Greedy algorithm score: {greedy_score}")
print(f"LS return score: {ls_score}")
print(f"Final solution score: {ls_improved_solution.evaluate()}")



max_routes = 0
min_routes = float('inf')
for d in ls_improved_solution.get_work_days():
    day = ls_improved_solution.days[d]
    max_routes = max(max_routes, len(day.routes))
    min_routes = min(min_routes, len(day.routes))

print(f"Maximum routes among all days: {max_routes}")
print(f"Minimum routes among all days: {min_routes}")


print("\nPenalties count:")

overloaded_route_count = ls_improved_solution.get_overload_route_count()
irregular_services_count, irreg_serv_count_edges = ls_improved_solution.get_irregular_services_count()
irregular_spacing_count, irreg_space_count_edges = ls_improved_solution.get_irregular_spacing_count()

print(f"Overloaded route count: {overloaded_route_count}")
print(f"Irregular services count: {irregular_services_count}")
print(f"Irregular spacing count: {irregular_spacing_count}")
# print(f"Irregular spacing count edges:\n")
# for edge in irreg_space_count_edges:
#     print(f"\t{edge}")
#     print(f"\tService days:{edge.service_days}")
#     print(f"\tNumber of services:{len(edge.service_days)}")
#     print("\tIrregular spacings at:")
#     for i in range(len(edge.service_days)):
#         if edge.evaluate_spacing(i, i+1, ls_improved_solution.vehicle) > 0:
#             print(f"\tIrregular spacing between services {i} and {i+1} on days {edge.service_days[i]} and {edge.service_days[(i+1)%len(edge.service_days)]}")
#     print('\n')