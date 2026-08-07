
import os
import numpy as np
from pathlib import Path


memo_distances = None


min_distances = None
loaded_graph_id = None



min_dist_directory = os.path.join('D:\\','Seminar-Restart', 'data', 'SP-CARP-graphs-min-distances')



# calculate minimum distances among all pairs using Floyd-Warshall
def calculate_distances(adjacency_lists, graph_id):
    
    global min_distances
    global loaded_graph_id

    file_path = Path(min_dist_directory) / f"fw_min_dist_{graph_id}.npy"

    if file_path.exists():
        min_distances = np.load(file_path)
        loaded_graph_id = graph_id
        return
    else:
        print(f"Calculating min distances for graph with id {graph_id}")


    loaded_graph_id = graph_id

    # create NxN matrix with each cell set to infinity
    n = len(adjacency_lists)

    min_distances = np.full((n, n), np.inf)

    # initialize shortest distance to be the direct edge
    for al in adjacency_lists:
        for edge in al:
            min_distances[edge.start_node, edge.end_node] = edge.distance
            min_distances[edge.end_node, edge.start_node] = edge.distance

    for i in range(n):
        min_distances[i, i] = 0

    for k in range(n):
        
        # shortest path (i, j) does it involve k
        for i in range(n):
            for j in range(n):
                if min_distances[i, k] != np.inf and min_distances[k, j] != np.inf:
                    path_with_k_length = min_distances[i, k] + min_distances[k, j]
                    if path_with_k_length < min_distances[i, j]:
                        min_distances[i, j] = path_with_k_length

    np.save(file_path, min_distances)

def min_distance_nn(node_1, node_2):
    return min_distances[node_1, node_2]

# get the minimum distance from a node to an edge
def min_distance_ne(node, edge):
    return min(min_distances[node, edge.start_node], min_distances[node, edge.end_node])


# get the minimum distance from an edge to another edge
def min_distance_ee(edge1, edge2):
    d1 = min_distances[edge1.start_node, edge2.start_node]
    d2 = min_distances[edge1.start_node, edge2.end_node]
    d3 = min_distances[edge1.end_node, edge2.start_node]
    d4 = min_distances[edge1.end_node, edge2.end_node]
    return min([d1, d2, d3, d4])
