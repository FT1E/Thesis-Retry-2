import heapq as hq


# ? NOTE - that priority for edges in demanded_edge_list should be set to PriorityType.Deadline
# ? NOTE - that this algorithm only takes into account total capacity used in the day
# ?         whether routing is actually possible with that many vehicles is not resolved here,
# ?         it's solved in local search procedure later
def run(demanded_edge_list, vehicle):

    hq.heapify(demanded_edge_list)

    day_assignment = [[] for _ in range(vehicle['planning_duration'])]
    capacity_used = [0] * vehicle['planning_duration']

    next_day_streets = [[] for _ in range(vehicle['planning_duration'] + 1)]


    max_day_capacity = vehicle['count'] * vehicle['capacity']

    for day in range(vehicle['planning_duration']):

        demanded_edge_list = demanded_edge_list + next_day_streets.pop(0)
        next_day_streets.append([])

        if day + 1 in vehicle['days_no_service']:
            # skip day if vehicle not available for today
            continue


        # in case there is a day where there are no edges to be serviced, then take extra from edges scheduled for future days
        # cnt is so that the loop isn't run infinitely at the end
        cnt = 0
        while len(demanded_edge_list) == 0 and cnt < vehicle['planning_duration'] - day:
            cnt += 1

            demanded_edge_list = demanded_edge_list + next_day_streets.pop(0)
            next_day_streets.append([])

        hq.heapify(demanded_edge_list)
            

        while capacity_used[day] < max_day_capacity and len(demanded_edge_list) > 0:
            
            # get edge with nearest deadline
            edge = hq.heappop(demanded_edge_list)

            if capacity_used[day] + edge.demand > max_day_capacity:
                # if edge has higher demand than the vehicle can handle for the day then skip it for today
                next_day_streets[0].append(edge)
                continue

            capacity_used[day] += edge.demand
            day_assignment[day].append(edge)
            edge.set_cleaning_day(day)


            if (edge.last_cleaning_day + edge.freq) < vehicle['planning_duration']:
                # push it to the future for at least freq/2 days
                # so some edgees that have higher frequency aren't clean
                next_day_streets[int(edge.freq // 2)].append(edge)

    return day_assignment, capacity_used