
import sys

sys.path.append('..')

from solution_representation.Route import Route


# OPERATOR METHODS
# OPERATOR AND UNDO_OPERATOR FOR EACH


# ? add a new service for edge in day d1
def add_service_operator(solution, d1, edge):
    #   - if d1 is a work day - not weekend
    #   - if edge is not already serviced on day d1

    if d1 % 7 >= 5:
        # work days % 7 = 5 or 6
        # considering mon 0, tue 1, etc.
        return None

    if d1 in edge.service_days:
        return None

    solution.days[d1].add_edge(edge)

    # todo - assert that edge is not in day and that it's .routes array has route None at this position

    # ? nothing needed for undo - just remove the service
    return True

def undo_add_service_operator(solution, d1, edge):
    # just remove the added service
    remove_service_operator(solution, d1, edge)


# ? remove a service for edge in day d1
def remove_service_operator(solution, d1, edge):
    #   - if edge is serviced on d1 - otherwise it does nothing
    
    # if edge has no route reference for day d1, then it's probably not serviced
    
    route = edge.routes[d1]
    if route is None:
        return None

    pos = route.index(edge)
    
    # todo - assert that edge.routes[d1] is None, its service_days has no d1, and day has no edge



    # ? for undo - return the route where the edge was in the day before and the position in that route
    return route, pos

def undo_remove_service_operator(solution, d1, edge, route, pos):

    solution.days[d1].add_edge(edge, route, pos)

    # todo - assert that it's working fine


# ? move a service for an edge from day d1 to day d2
def move_service_operator(solution, d1, d2, edge):
    #   - if edge is serviced on day d1
    #   - if edge is not serviced on day d2 and d2 is a work day

    if edge.routes[d1] is None or edge.routes[d2] is not None or d2 % 7 >= 5:
        return None

    route, pos = remove_service_operator(solution, d1, edge)
    add_service_operator(solution, d2, edge)

    return route, pos

def undo_move_service_operator(solution, d1, d2, edge, route, pos):
    #   ? - intuitively this could be a call to same op with arguments reversed
    #   ? - but to not destroy the solution before, this inserts it back in the same route and same position of day where the edge was removed / moved from

    undo_remove_service_operator(solution, d1, edge, route, pos)
    undo_add_service_operator(solution, d2, edge)


# ? swap the service days of 2 edges
def swap_services_operator(solution, edge_1, edge_2):
    #   - only if the edges have the same frequency
    #   - else one gets too many services other gets too little services
    
    if edge_1.freq != edge_2.freq:
        return None

    all_days = set(edge_1.service_days + edge_2.service_days)

    only_edge_1_days = all_days.difference(edge_2.service_days)
    only_edge_2_days = all_days.difference(edge_1.service_days)

    edge_1_routes = []
    edge_2_routes = []

    for day in only_edge_1_days:
        route, pos = remove_service_operator(solution, day, edge_1)
        add_service_operator(solution, day, edge_2)

        edge_1_routes.routes.append((route, pos))

    for day in only_edge_2_days:
        route, pos = remove_service_operator(solution, day, edge_2)
        add_service_operator(solution, day, edge_1)

        edge_2_routes.routes.append((route, pos))

    
    return edge_1_routes, edge_2_routes

def undo_swap_services_operator(solution, edge_1, edge_2, edge_1_routes, edge_2_routes):
    # ? similar argument for move_service, insert the removed services into the same routes and same positions

    for route, pos in edge_1_routes:
        day = route.day.number

        undo_remove_service_operator(solution, day, edge_1, route, pos)
        undo_add_service_operator(solution, day, edge_2)

    for route, pos in edge_2_routes:
        day = route.day.number
        
        undo_remove_service_operator(solution, day, edge_2, route, pos)
        undo_add_service_operator(solution, day, edge_1)
    

    # todo - assert that edges have their service days swapped and are only in the original service_days, not in all of them


# ? Take 2 routes, cut the routes in 2 (or don't), and merge a cut of a route with the cut of the other route
def two_opt_routes_operator(solution, route_1, route_2, r1_cutpoint, r2_cutpoint):
    #   - only if the two routes are in the same day
    #   - and they are different routes

    if route_1 is route_2:
        return None

    if route_1.day.number != route_2.day.number:
        return None

    day = route_1.day
    
    # working only with the routes
    # not removing and adding services to the day, since it's the same day


    cost_before = route_1.evaluate(solution.vehicle) + route_2.evaluate(solution.vehicle)


    r1_half1 = Route(route_1.targets[:r1_cutpoint])
    r1_half2 = Route(route_1.targets[r1_cutpoint:])

    r2_half1 = Route(route_2.targets[:r2_cutpoint])
    r2_half2 = Route(route_2.targets[r2_cutpoint:])


    a_route1 = r1_half1.merge(r2_half1)
    a_route2 = r1_half2.merge(r2_half2)

    b_route1 = r1_half1.merge(r2_half2)
    b_route2 = r1_half2.merge(r2_half1)

    cost_a = a_route1.evaluate(solution.vehicle) + a_route2.evaluate(solution.vehicle)
    cost_b = b_route1.evaluate(solution.vehicle) + b_route2.evaluate(solution.vehicle)

    cost_after = min(cost_a, cost_b)


    # if performing the operation leads to a more expensive solution don't do it
    # ? NOTE - that this is just an estimation, a full re-evaluation still needs to be done if the number of vehicles for the whole horizon is decreased
    if cost_before < cost_after:
        return None
    
    # else remove the original routes
    day.remove_route(route_1)
    day.remove_route(route_2)

    # and insert the merging with cheaper cost
    if cost_a < cost_b:
        res_r1 = a_route1
        res_r2 = a_route2
    else:
        res_r1 = b_route1
        res_r2 = b_route2

    day.add_route(res_r1)    
    day.add_route(res_r2)

    cnt = 0         # how many new routes were added
    if len(res_r1.targets) > 0:
        cnt += 1
    if len(res_r2.targets) > 0:
        cnt += 1
        
    for edge in res_r1.targets:
        edge.routes[day.number] = res_r1

    for edge in res_r2.targets:
        edge.routes[day.number] = res_r2


    return route_1, route_2, cnt


def undo_two_opt_routes_operator(solution, route_1, route_2, route_cnt):

    for _ in range(route_cnt):
        day.remove_route(route_id = -1)

    day.add_route(route_1)
    day.add_route(route_2)

    for edge in route_1.targets:
        edge.routes[route_1.day.number] = route_1

    for edge in route_2.targets:
        edge.routes[route_2.day.number] = route_2


# ? Move a single service from one route to a different route in the same day
def route_move_service_operator(solution, edge_1_id, edge_2_id, route_1, route_2):
    #   - only if the routes are in the same day
    #   - and they are different routes

    
    if route_a is route_b:
        return None

    if route_a.day.number != route_b.day.number:
        return None

    # todo - can remove below out of bound checks if that is done before calling the operator
    # todo - or wrap them in try except blocks when accessing
    if edge_1_id >= len(route_a.targets):
        return None


    edge_1 = route_1.targets[edge_1_id]
    route_1.remove_edge(pos = edge_1_id)
    route_2.insert_edge(edge_1, pos = edge_2_id)   

    edge_1.routes[route_2.day.number] = route_2


    return True

def undo_route_move_service_operator(solution, edge_1_id, edge_2_id, route_1, route_2):
    # call same operator with arguments reversed
    route_move_service_operator(solution, edge_2_id, edge_1_id, route_2, route_1)


# ? Take a pair (2 edges served one after another in the same route) and move it to a different route in the same day
def route_move_pair_service_operator(solution, edge_a12_id, edge_b_id, route_a, route_b):
    #   - routes are in the same day
    #   - and they are different routes

    # take the pair of edges at positions (edge_a12_id, edge_a12_id + 1)

    
    # todo - can remove below out of bound checks if that is done before calling the operator
    if edge_a12_id + 1 >= len(route_a.targets):
        return None

    
    # if some check fails, then op can't be done
    if route_move_service_operator(solution, edge_a12_id + 1, edge_b_id, route_a, route_b) is None:
        return None

    # otherwise all checks are done in above op call
    route_move_service_operator(solution, edge_a12_id, edge_b_id, route_a, route_b)
    
    return True

def undo_route_move_pair_service_operator(solution, edge_a12_id, edge_b_id, route_a, route_b):
    # same op call with arguments in different order
    route_move_pair_service_operator(solution, edge_b_id, edge_a12_id, route_b, route_a)



# END OPERATOR METHODS


# PHASE METHODS


# ? PHASE 1 - add_service_operator and remove_service_operator
def phase_1(working):
    original_score = working.evaluate()

    current_best_solution = working
    best_score = original_score

    # todo - iterations, apply ops as long as there is some improvement

    return current_best_solution, best_score


# ? PHASE 2 - move_service_operator and swap_services_operator
def phase_2(working):
    original_score = working.evaluate()

    current_best_solution = working
    best_score = original_score

    # todo - iterations, apply ops as long as there is some improvement

    return current_best_solution, best_score


# ? PHASE 3 - route operators, two_opt, move (single) and move_pair, best move applied for each day
def phase_3(working):
    original_score = working.evaluate()

    current_best_solution = working
    best_score = original_score

    # todo - iterations, apply ops as long as there is some improvement
    
    work_days = working.get_work_days()

    # better locality if iterating on each day repeatedly as long as there is an improvement, then continue on to next day
    for day in work_days:

        improved = True
        while improved:
            improved = False

    return current_best_solution, best_score


# END PHASE METHODS