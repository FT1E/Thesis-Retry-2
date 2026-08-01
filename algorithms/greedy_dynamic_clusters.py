import heapq as hq


# ? method returns assignment of edges into days, it does not make routes
# ? NOTE - adjacency_lists argument needs to have edges with PriorityType.Deadline
def run(demanded_edge_list, adjacency_lists, vehicle, CLUSTER_SIZE_LIMIT = 5):
    
    day_assignment = [[] for _ in range(vehicle['planning_duration'])]
    
    # ? below could be just a single variable instead of a list - just for caching
    capacity_used = [0] * vehicle['planning_duration']


    # ? below is if an edge needs to be served multiple times
    next_day_streets = [[] for _ in range(vehicle['planning_duration'] + 1)]


    max_day_capacity = vehicle['count'] * vehicle['capacity']
    
    # ? default values / info for dynamic cluster 
    cluster_heap = []
    current_cluster_size = 0
    cluster_vertices = []

    cluster_edges = []
    cluster_origin = None

    # going through every day
    for day in range(vehicle['planning_duration']):

        demanded_edge_list = demanded_edge_list + next_day_streets.pop(0)
        next_day_streets.append([])
            

        if day+1 in vehicle['days_no_service']:
            # skip day if vehicle not available for today
            continue
        
        # in case there is a day where there are no edges to be serviced, then take extra from edges scheduled for future days
        # cnt is so that the loop isn't run infinitely at the end
        if len(demanded_edge_list) == 0:
            demanded_edge_list = pull_next_day_edges(demanded_edge_list, next_day_streets)

        # without the above, it's possible the list is empty, so some work day can be left without edges which isn't optimal
        # LS can probably fix it, but with this it has less work to do

        while capacity_used[day] < max_day_capacity and len(demanded_edge_list) > 0:            

            hq.heapify(demanded_edge_list)
            
            
            # ? reseting to default values for dynamic cluster
            cluster_heap = []
            current_cluster_size = 0
            cluster_vertices = []
            cluster_edges = []


            # get edge with nearest deadline
            edge = hq.heappop(demanded_edge_list)
            cluster_origin = edge

            # add it to cluster_heap
            hq.heappush(cluster_heap, edge)

            # ? loop for expanding cluster until vehicle limit or cluster limit
            # ? CLUSTER_LIMIT = maximum number of edges allowed in the cluster (possibly infinite)
            while current_cluster_size < CLUSTER_SIZE_LIMIT and len(cluster_heap) > 0 and capacity_used[day] < max_day_capacity:

                # get top priority edge from cluster heap
                edge = hq.heappop(cluster_heap)

                # if edge is already assigned to this day
                if edge in day_assignment[day]:
                    # print(f"Edge {edge} is already assigned to day {day}")
                    continue

                # if it's not in demanded_edge_list (and it's not cluster origin) then it's somewhere in next_day_streets and it's too soon to service it
                if edge is not cluster_origin and edge not in demanded_edge_list:
                    continue

                # if edge doesn't require cleaning
                if edge.demand <= 0:
                    # ? if top edge has negative demand then every following edge has invalid frequency / demand 
                    # ? - set in Edge.__lt__ for PriorityType.deadline to return 2000 - always larger for this dataset than an edge with valid frequency
                    break

                if capacity_used[day] + edge.demand > max_day_capacity:
                    # if edge has higher demand than the vehicle can handle for the day then skip it for today
                    if edge is cluster_origin:
                        next_day_streets[0].append(edge)
                    continue
                
                # remove edge from demanding edge_list - it will be added back through next_day_streets if needed by below code
                if edge is not cluster_origin:
                    index = demanded_edge_list.index(edge)
                    edge = demanded_edge_list[index]


                # assign it to day
                capacity_used[day] += edge.demand
                day_assignment[day].append(edge)
                current_cluster_size += 1
                edge.set_cleaning_day(day)
                cluster_edges.append(edge)


                if (edge.last_cleaning_day + edge.freq) < vehicle['planning_duration']:
                    next_day_streets[int(edge.freq * 9/10)].append(edge)


                # - add new neighbouring edges to cluster heap
                # - keep track of which edges where added - which neighbourhoods of vertexes - basically just vertex number

                if edge.start_node not in cluster_vertices:
                    cluster_vertices.append(edge.start_node)
                    for adjacent_edge in adjacency_lists[edge.start_node]:
                        if adjacent_edge != edge and adjacent_edge not in cluster_heap and adjacent_edge not in cluster_edges:
                            hq.heappush(cluster_heap, adjacent_edge)            

                if edge.end_node not in cluster_vertices:
                    cluster_vertices.append(edge.end_node)
                    for adjacent_edge in adjacency_lists[edge.end_node]:
                        if adjacent_edge != edge and adjacent_edge not in cluster_heap and adjacent_edge not in cluster_edges:
                            hq.heappush(cluster_heap, adjacent_edge)
            
    return day_assignment, capacity_used


def pull_next_day_edges(demanded_edge_list, next_day_streets):
    cnt = 0
    while cnt == 0 or len(demanded_edge_list) == 0 and cnt < len(next_day_streets):
        cnt += 1
        demanded_edge_list = demanded_edge_list + next_day_streets.pop(0)
        next_day_streets.append([])

    return demanded_edge_list