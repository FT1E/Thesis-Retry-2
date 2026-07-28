
import os
import json
import heapq as hq
import sys

sys.path.append('..')
from solution_representation.Edge import PriorityType

memo_distances = None
loaded_graph_id = None

min_dist_directory = os.path.join('D:\\','Seminar-Restart', 'data', 'SP-CARP-graphs-min-distances')



def calculate_distances(adjacency_list, graph_id):
    global memo_distances
    global loaded_graph_id

    if loaded_graph_id == graph_id:
        return

    loaded_graph_id = graph_id

    file = f'md_g_{graph_id}.json'
    try:
        with open(os.path.join(min_dist_directory, file), 'r') as f:
            memo_distances = json.load(f)
            memo_distances = {int(k) : {int(k1) : v1 for k1,v1 in v.items()} for k,v in memo_distances.items() if k != 'max_distance'}
            return
    except Exception as e:
        print(e)
        print(f'No cached distance matrix found for graph with id {graph_id}, calculating min_distances...')

    # ? for debugging purposes - seeing the graph's max distance
    max_distance = 0

    # make sure edges are sorted by their length / distance
    for al in adjacency_list:
        if len(al) > 0 and al[0].priority_type == PriorityType.Distance:
            # if one edge has this priority_type then all have as well
            break

        for edge in al:
            edge.priority_type = PriorityType.Distance

    memo_distances = dict()
    for i in range(len(adjacency_list)):
        memo_distances[i] = dict()
        memo_distances[i][i] = 0
        current = adjacency_list[i].copy()
        

        # do dijkstra - take edge with smallest distance - then add that new point
        hq.heapify(current)
        while len(current) > 0:
            min_edge = hq.heappop(current)
            if min_edge.end_node not in memo_distances[i] or memo_distances[i][min_edge.start_node] + min_edge.distance < memo_distances[i][min_edge.end_node]:
                memo_distances[i][min_edge.end_node] = memo_distances[i][min_edge.start_node] + min_edge.distance
                
                if memo_distances[i][min_edge.end_node] > max_distance:
                    max_distance = memo_distances[i][min_edge.end_node]

                for edge in adjacency_list[min_edge.end_node]:
                    hq.heappush(current, edge)

    memo_distances['max_distance'] = max_distance   # not needed but idk for me
    json_str = json.dumps(memo_distances, indent=4)
    with open(os.path.join(min_dist_directory, file), 'w') as f:
        f.write(json_str)

    print(f"Max distance in the graph: {max_distance}")

def min_distance_nn(node_1, node_2):
    return memo_distances[node_1][node_2]

# get the minimum distance from a node to an edge
def min_distance_ne(node, edge):
    return min(memo_distances[node][edge.start_node], memo_distances[node][edge.end_node])


# get the minimum distance from an edge to another edge
def min_distance_ee(edge1, edge2):
    d1 = memo_distances[edge1.start_node][edge2.start_node]
    d2 = memo_distances[edge1.start_node][edge2.end_node]
    d3 = memo_distances[edge1.end_node][edge2.start_node]
    d4 = memo_distances[edge1.end_node][edge2.end_node]
    return min([d1, d2, d3, d4])
