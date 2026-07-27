

import sys

sys.path.append('..')

from util.routing_heuristic import calculate_cost
# TODO - MIGHT NEED TO CHANGE STUFF - RE-READ THE CODE BELOW AFTER ALL SOLUTION CLASSES ARE FINISHED
# 


def print_day_assignment(day_assignment, adjacency_lists, vehicle, graph_id, capacity_used=None, v_distance_limit = None):

    if v_distance_limit is not None:
        vehicle['distance_limit'] = 500     # ! for debugging purposes

    if capacity_used is None:
        capacity_used = [0 for _ in day_assignment]
        for i in range(len(day_assignment)):
            for street in day_assignment[i]:
                capacity_used[i] += street.demand

    print(f"Max vehicle capacity: {vehicle['capacity']}")
    total_distance = 0
    for i in range(vehicle['planning_duration']):
        day = i+1
        if len(day_assignment[i]) > 0:
            print(f"Edges Assigned for day {day}:")
            for e in day_assignment[i]:
                # print(e, end=', ')
                print(f'\t{e}')
            print(f"\nCapacity used for day {day}:{str(capacity_used[i])}")
            
            
            routing_cost = calculate_cost(adjacency_lists, day_assignment[i], vehicle, graph_id)

            print(f"Total routing distance for day {day}:{routing_cost['total_distance']}\nNumber of routes: {routing_cost['num_routes']}\n\nRoutes")
            for route in routing_cost['routes']:
                print(f'Route demand: {route.demand}')
                print(f'Route length: {route.length}')
                # print(route.targets)
                for target in route.targets:
                    print(f'\t{target}')
            print('\n-----------------------------\n')

            total_distance += routing_cost['total_distance']

    print(f"\nTotal distance for all days: {total_distance}")