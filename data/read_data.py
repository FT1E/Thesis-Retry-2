
import re
import os, sys
import pandas as pd


sys.path.append('..')

from solution_representation.Edge import Edge, PriorityType

# ! FIX BELOW SO IT CAN RUN ON ANY DEVICE
graph_data_directory = os.path.join('D:\\','Seminar-Restart', 'data', 'SP-CARP-graphs')
vehicle_data_directory = os.path.join('D:\\','Seminar-Restart', 'data', 'SP-CARP-vehicles')

# for file in os.listdir(graph_data_directory):
#     with open(os.path.join(graph_data_directory, file), 'r') as graph_file:
#         graph_data = graph_file.read()
#         lines = graph_data.splitlines()
        
        # num_fractions = int(re.sub(r'.*:\s*', '', lines[4]))


# to make sure that 0 is always the depot node
def swap_depot_node(node_number, depot_node):

    if node_number == depot_node:
        return 0
    elif node_number == 0:
        return depot_node
    
    return node_number

# get data for graph i
# list of all edges for graph i
def get_graph_edge_list(i, filter = None):
    try:
        file = os.listdir(graph_data_directory)[i]
    except IndexError:
        print('Index out of range for file!')
        return None
    except:
        print("Some other error while reading file")
        return None

    with open(os.path.join(graph_data_directory, file), 'r') as f:
        graph_data = f.read()

        lines = graph_data.splitlines()
    
        # * number of edges
        num_edges = int(re.sub(r'.*:\s*', '', lines[2]))

        # ? DEPOT NODE
        # ! TAKE NOTE OF BELOW
        # * in the first few files it's 0, but not in all of them
        depot_node = int(re.sub(r'.*:\s*', '', lines[3]))

        # * note fraction == trash type
        fraction_line = lines[5].split('\t')
        fraction_type = fraction_line[1]
        num_of_intervals = int(fraction_line[2])
        intervals = [float(x) for x in fraction_line[3:]]

        edge_header = lines[7].split('\t')
        edge_table = [x.split('\t') for x in lines[9:9+num_edges]]
        edge_data = pd.DataFrame(edge_table, columns = edge_header)

        
        edge_data = edge_data.drop([f"Bins_{i}" for i in range(num_of_intervals)], axis=1)


        # * converting data to numeric
        edge_data = edge_data.apply(pd.to_numeric)

        # * - assign frequency to each edge
        edge_frequencies = []
        res = []

        for e in edge_data.itertuples(False):
            edge_frequencies = [intervals[i] for i in range(num_of_intervals) if getattr(e, f'Demand_{i}') != 0]

            start_node = e.StartNodeNumber
            end_node = e.EndNodeNumber

            if depot_node != 0:
                start_node = swap_depot_node(e.StartNodeNumber, depot_node)
                end_node = swap_depot_node(e.EndNodeNumber, depot_node)

            # make 1 edge with invalid frequency - so it doesn't get skipped in routing calculations
            # in case it gets cut below
            res.append(Edge(e.EdgeNumber, start_node, end_node, -1, e.Cost, -1))

            # else make 1 edge for each frequency (1 or more)
            cnt = 0
            for freq in edge_frequencies:
                if filter is not None and freq > filter:
                    # skip edges with frequency higher than planning period
                    # example planning period is 14 days, but there is an edge with frequency 56
                    # no edge will be skipped when vehicle with longest planning period is used
                    continue
                res.append(Edge(int(e.EdgeNumber) + cnt, start_node, end_node, getattr(e, edge_header[5 + 2*intervals.index(freq)]), e.Cost, freq))
                cnt += 1
            
        return res


# list of edges with non-zero demand
def get_graph_demanded_edges(i, filter=None):
    
    edge_list = get_graph_edge_list(i, filter=filter)

    if edge_list is None:
        # log printed in the other function
        return None
    
    non_zero_edges = [edge for edge in edge_list if edge.freq > 0]

    return non_zero_edges

def get_graph_metadata(i):
    try:
        file = os.listdir(graph_data_directory)[i]
        # print(f"Graph file read: {file}")
    except IndexError:
        print('Index out of range for file!')
        return None
    except:
        print("Some other error while reading file")
        return None

    with open(os.path.join(graph_data_directory, file), 'r') as f:
        graph_data = f.read()

        lines = graph_data.splitlines()
    
        # * number of nodes/vertices
        num_nodes = int(re.sub(r'.*:\s*', '', lines[1]))
        
        # * number of edges
        num_edges = int(re.sub(r'.*:\s*', '', lines[2]))

        # * in the first few files it's 0, but not in all of them
        depot_node = int(re.sub(r'.*:\s*', '', lines[3]))

        return {'num_nodes' : num_nodes, 'num_edges' : num_edges, 'depot_node' : depot_node}

# get adjacency list for graph i
def get_graph_al(i, priority_type = PriorityType.Deadline, filter=None):
    raw_graph_data = get_graph_edge_list(i, filter=filter)
    if raw_graph_data is None:
        return None     # log messages in get_graph_data
    
    graph_metadata = get_graph_metadata(i)
    # not checking for None value on this - since if above works so should this
    # print(graph_metadata)

    adjacency_list = [[] for _ in range(graph_metadata['num_nodes'])]
    for edge in raw_graph_data:
        adjacency_list[edge.start_node].append(edge)
        edge.priority_type = priority_type

        # same edge just swap start_node and end_node
        reverse_edge = Edge(edge.number, edge.end_node, edge.start_node, edge.demand, edge.distance, edge.freq, priority_type)
        adjacency_list[edge.end_node].append(reverse_edge)

    # for i in range(len(adjacency_list)):
    #     print(f"Node {i} adjacency list:")
    #     for edge in adjacency_list[i]:
    #         print(edge, end='\t')
    #     print('\n')

    # print(f"Number of adjacency lists: {len(adjacency_list)}")
    # print('\n\n')

    
    return adjacency_list

# get data
def get_vehicle_data(i):

    try:
        file = os.listdir(vehicle_data_directory)[i]
    except IndexError:
        print('Index out of range for file!')
        return None
    except:
        print("Some other error while reading file")
        return None

    with open(os.path.join(vehicle_data_directory, file), 'r') as f:
        vehicle_data = f.read()
        lines = vehicle_data.splitlines()

        planning_duration = int(lines[0].split('\t')[1]) 
        

        days_no_service = [int(x) for x in lines[4].split('\t')[3:]]

        number_of_vehicles = int(lines[8].split('\t'* 4)[1])
 
        capacity = int(lines[10].split('\t\t\t')[1])
        
        speed = int(lines[14].split('\t\t\t')[1])
        time_limit = int(lines[17].split('\t\t\t')[1])

        distance_limit = speed * time_limit


        return {'planning_duration' : planning_duration, 'days_no_service': days_no_service, 'count' : number_of_vehicles ,'capacity' : capacity, 'distance_limit' : distance_limit}


