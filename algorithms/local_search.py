
import sys
import time
import datetime
import copy

sys.path.append('..')

from solution_representation.Route import Route


# ! UNCOMMENT ASSERTIONS IF BUGS POP UP
# ? ADD ASSERTIONS FOR OTHER OPS

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

    # assert d1 not in edge.service_days
    # assert edge.routes[d1] is None
    # assert edge not in solution.days[d1].edges
    # assert solution.days[d1].get_edge_route(edge) is None
    # assert not solution.days[d1].edge_in_day(edge)
    
    
    assert solution.days[d1].add_edge(edge)


    # assert d1 in edge.service_days
    # assert edge.routes[d1] is not None
    # assert solution.days[d1].edge_in_day(edge)

    # ? nothing needed for undo - just remove the service
    return True

def undo_add_service_operator(solution, d1, edge):
    # just remove the added service

    # assert d1 in edge.service_days
    # assert edge.routes[d1] is not None
    # assert solution.days[d1].edge_in_day(edge)


    remove_service_operator(solution, d1, edge)

    # assert d1 not in edge.service_days
    # assert edge.routes[d1] is None
    # assert not solution.days[d1].edge_in_day(edge)



# ? remove a service for edge in day d1
def remove_service_operator(solution, d1, edge):
    #   - if edge is serviced on d1 - otherwise it does nothing
    
    # if edge has no route reference for day d1, then it's probably not serviced
    
    if d1 not in edge.service_days:
        return None

    route = solution.days[d1].get_edge_route(edge)
    if route is None:
        return None

    pos = route.targets.index(edge)
    
    assert solution.days[d1].remove_edge(edge)


    # assert d1 not in edge.service_days
    # assert edge.routes[d1] is None
    # assert not solution.days[d1].edge_in_day(edge)



    # ? for undo - return the route where the edge was in the day before and the position in that route
    return route, pos

def undo_remove_service_operator(solution, d1, edge, route, pos):

    solution.days[d1].insert_edge(edge, route, pos)

    # assert d1 in edge.service_days
    # assert edge.routes[d1] is route
    # assert pos == route.targets.index(edge)
    # assert solution.days[d1].edge_in_day(edge)



# ? move a service for an edge from day d1 to day d2
def move_service_operator(solution, d1, d2, edge):
    #   - if edge is serviced on day d1
    #   - if edge is not serviced on day d2 and d2 is a work day

    # 
    if d1 not in edge.service_days or d2 in edge.service_days or d2 % 7 >= 5:
        return None

    route, pos = remove_service_operator(solution, d1, edge)
    add_service_operator(solution, d2, edge)

    return route, pos

def undo_move_service_operator(solution, d1, d2, edge, route, pos):
    #   ? - intuitively this could be a call to same op with arguments reversed
    #   ? - but to not destroy the solution before, this inserts it back in the same route and same position of day where the edge was removed / moved from
    undo_add_service_operator(solution, d2, edge)
    undo_remove_service_operator(solution, d1, edge, route, pos)


# ? swap the service days of 2 edges
def swap_services_operator(solution, edge_1, edge_2):
    #   - only if the edges have the same frequency
    #   - else one gets too many services other gets too little services
    
    if edge_1.freq != edge_2.freq:
        return None

    # before_e1 = edge_1.service_days.copy()
    # before_e2 = edge_2.service_days.copy()

    # assert [solution.days[d].edge_in_day(edge_1) for d in edge_1.service_days] == [True for _ in edge_1.service_days]
    # assert [solution.days[d].edge_in_day(edge_2) for d in edge_2.service_days] == [True for _ in edge_2.service_days]


    all_days = set(edge_1.service_days + edge_2.service_days)

    only_edge_1_days = list(all_days.difference(edge_2.service_days))
    only_edge_2_days = list(all_days.difference(edge_1.service_days))

    edge_1_routes = []
    edge_2_routes = []

    for day in only_edge_1_days:
        route, pos = remove_service_operator(solution, day, edge_1)
        add_service_operator(solution, day, edge_2)

        edge_1_routes.append((route, pos))

    for day in only_edge_2_days:
        route, pos = remove_service_operator(solution, day, edge_2)
        add_service_operator(solution, day, edge_1)

        edge_2_routes.append((route, pos))

    
    # assert edge_2.service_days == before_e1
    # assert edge_1.service_days == before_e2

    return edge_1_routes, edge_2_routes

def undo_swap_services_operator(solution, edge_1, edge_2, edge_1_routes, edge_2_routes):
    # ? similar argument for move_service, insert the removed services into the same routes and same positions

    for route, pos in edge_1_routes:
        undo_add_service_operator(solution, route.day, edge_2)
        undo_remove_service_operator(solution, route.day, edge_1, route, pos)

    for route, pos in edge_2_routes:
        undo_add_service_operator(solution, route.day, edge_1)
        undo_remove_service_operator(solution, route.day, edge_2, route, pos)
    



# ? Take 2 routes, cut the routes in 2 (or don't), and merge a cut of a route with the cut of the other route
def two_opt_routes_operator(solution, route_1, route_2, r1_cutpoint, r2_cutpoint):
    #   - only if the two routes are in the same day
    #   - and they are different routes

    if route_1 is route_2:
        return None

    if route_1.day != route_2.day:
        return None

    day = solution.days[route_1.day]
    
    # working only with the routes
    # not removing and adding services to the day, since it's the same day

    # assert route_1 in day.routes
    # assert route_2 in day.routes


    cost_before = route_1.evaluate(solution.vehicle) + route_2.evaluate(solution.vehicle)


    r1_half1 = Route(route_1.targets[:r1_cutpoint], day = route_1.day)
    r1_half2 = Route(route_1.targets[r1_cutpoint:], day = route_1.day)

    r2_half1 = Route(route_2.targets[:r2_cutpoint], day = route_1.day)
    r2_half2 = Route(route_2.targets[r2_cutpoint:], day = route_1.day)


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
    assert day.remove_route(route_1)
    assert day.remove_route(route_2)

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


    # ? assertion checking
    # for edge in res_r1.targets:
    #     assert edge.routes[day.number] == res_r1
    # for edge in res_r2.targets:
    #     assert edge.routes[day.number] == res_r2

    return cnt


def undo_two_opt_routes_operator(solution, route_1, route_2, route_cnt):

    day = solution.days[route_1.day]
    for _ in range(route_cnt):
        day.remove_route(route_id = -1)

    day.add_route(route_1)
    day.add_route(route_2)

    for edge in route_1.targets:
        edge.routes[route_1.day] = route_1

    for edge in route_2.targets:
        edge.routes[route_2.day] = route_2


    # assert route_1 in day.routes
    # assert route_2 in day.routes


# ? Move a single service from one route to a different route in the same day
def route_move_service_operator(solution, edge_1_id, edge_2_id, route_1, route_2):
    #   - only if the routes are in the same day
    #   - and they are different routes

    
    if route_1 is route_2:
        return None

    if route_1.day != route_2.day:
        return None

    # todo - can remove below out of bound checks if that is done before calling the operator
    # todo - or wrap them in try except blocks when accessing
    if edge_1_id >= len(route_1.targets):
        return None


    edge_1 = route_1.targets[edge_1_id]
    route_1.remove_edge(pos = edge_1_id)
    route_2.insert_edge(edge_1, pos = edge_2_id)   

    edge_1.routes[route_2.day] = route_2


    if len(route_1.targets) == 0:
        solution.days[route_1.day].remove_route(route_1)

    # the below if only can happen in undo version of this operator
    # route had only 1 target and that was moved with the normal version of this operator
    # so it's left with 0 targets and removed above
    # then undo version calls this operator (for convenience to not copy paste code) 
    # and the route needs to be added back
    if len(route_2.targets) == 1:
        solution.days[route_2.day].add_route(route_2)


    # assert route_2 in edge_1.routes
    # assert route_2 is edge_1.routes[route_1.day]
    # assert route_2 == edge_1.routes[route_2.day]

    return True

def undo_route_move_service_operator(solution, edge_1_id, edge_2_id, route_1, route_2):
    # call same operator with arguments reversed
    route_move_service_operator(solution, edge_2_id, edge_1_id, route_2, route_1)

    # assert route_1 in solution.days[route_1.day].routes
    # assert route_2 in solution.days[route_1.day].routes
    # assert route_1.targets[edge_1_id].routes[route_1.day] == route_1


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

# UTIL METHODS
def evaluate_neighbour(neighbour, current_best_solution, best_score):
    neighbour_score = neighbour.evaluate()
    improved = False
    if neighbour_score < best_score:
        current_best_solution = copy.deepcopy(neighbour)
        best_score = neighbour_score
        improved = True

    return current_best_solution, best_score, improved
# END UTIL METHODS


# PHASE METHODS


# ? PHASE 1 - add_service_operator and remove_service_operator
def phase_1(working):
    original_score = working.evaluate()

    current_best_solution = working
    best_score = original_score

    work_days = set(working.get_work_days())

    iteration_count = 0
    iteration_avg_time = 0

    improved = True

    while improved:
        improved = False
        
        iteration_count += 1

        iter_start = time.time()

        # reset values at start of iteration

        # adding a service to edges with too little services
        under_satisfied_edges = working.get_under_satisfied_edges()
        for edge in under_satisfied_edges:
            no_service_days = work_days.difference(edge.service_days)
            for day in no_service_days:
                if add_service_operator(working, day, edge):
                    current_best_solution, best_score, improved = evaluate_neighbour(working, current_best_solution, best_score)                    
                    undo_add_service_operator(working, day, edge)
            

        # removing a service of edges with too many services
        over_satisfied_edges = working.get_over_satisfied_edges()
        for edge in over_satisfied_edges:
            for day in edge.service_days:
                res = remove_service_operator(working, day, edge)
                if res is not None:
                    route, pos = res
                    current_best_solution, best_score, improved = evaluate_neighbour(working, current_best_solution, best_score)
                    undo_remove_service_operator(working, day, edge, route, pos)

        iter_end = time.time()

        last_iteration_time = iter_end - iter_start
        iteration_avg_time = iteration_avg_time * (iteration_count - 1) / iteration_count + last_iteration_time / iteration_count

        if iteration_count % 10 == 1:
            print(f"Phase 1 mid-report:")
            print(f"Iteration count: {iteration_count}")
            print(f"Last iteration time: {last_iteration_time}")
            print(f"Average iteration time: {iteration_avg_time}")
            print(f"Current score: {best_score}")
            
    print("Phase 1 ended!")
    print("Phase 1 Report:")
    print(f"Iteration count: {iteration_count}")
    print(f"Last iteration time: {last_iteration_time}")
    print(f"Average iteration time: {iteration_avg_time}")
    print(f"Current score: {best_score}")
    
    return current_best_solution, best_score, best_score < original_score


# ? PHASE 2 - move_service_operator and swap_services_operator
def phase_2(working):
    original_score = working.evaluate()

    current_best_solution = working
    best_score = original_score
    
    work_days = set(working.get_work_days())
    
    iteration_count = 0
    iteration_avg_time = 0

    # todo - iterations, apply ops as long as there is some improvement
    improved = True
    improved_op = False
    while improved:
        improved = False

        iteration_count += 1

        iter_start = time.time()

        # move_service operator
        for edge in working.demanded_edges:
            no_service_days = work_days.difference(edge.service_days)

            for d1 in edge.service_days:
                for d2 in no_service_days:

                    res = move_service_operator(working, d1, d2, edge)
                    if res is not None:
                        route, pos = res
                        current_best_solution, best_score, improved_op = evaluate_neighbour(working, current_best_solution, best_score)
                        undo_move_service_operator(working, d1, d2, edge, route, pos)
                        if improved_op:
                            improved = True


        # swap_services operator
        for bucket in working.frequency_buckets.values():
            
            for i in range(len(bucket)):
                edge_1 = bucket[i]

                for j in range(i+1, len(bucket)):
                    edge_2 = bucket[j]

                    res = swap_services_operator(working, edge_1, edge_2)
                    if res is not None:
                        e1_routes, e2_routes = res
                        current_best_solution, best_score, improved_op = evaluate_neighbour(working, current_best_solution, best_score)
                        undo_swap_services_operator(working, edge_1, edge_2, e1_routes, e2_routes)
                        if improved_op:
                            improved = True
            

        working = current_best_solution


        iter_end = time.time()

        last_iteration_time = iter_end - iter_start
        iteration_avg_time = iteration_avg_time * (iteration_count - 1) / iteration_count + last_iteration_time / iteration_count

        if iteration_count % 10 == 1:
            print(f"Phase 2 mid-report:")
            print(f"Iteration count: {iteration_count}")
            print(f"Last iteration time: {last_iteration_time}")
            print(f"Average iteration time: {iteration_avg_time}")
            print(f"Current score: {best_score}")
            
    print("Phase 2 ended!")
    print("Phase 2 Report:")
    print(f"Iteration count: {iteration_count}")
    print(f"Last iteration time: {last_iteration_time}")
    print(f"Average iteration time: {iteration_avg_time}")
    print(f"Current score: {best_score}")



    return current_best_solution, best_score, best_score < original_score


# ? PHASE 3 - route operators, two_opt, move (single) and move_pair, best move applied for each day
def phase_3(working):
    original_score = working.evaluate()

    current_best_solution = working
    best_score = original_score

    # 1 iteration affects one day, otherwise iter_count == number of work days
    # counting like this bcs of better locality and bcs some days require extra iterations others require less iterations
    iteration_count = 0
    iteration_avg_time = 0

    
    work_days = working.get_work_days()

    # better locality if iterating on each day repeatedly as long as there is an improvement, then continue on to next day
    # todo - parallelism - 1 thread per day, i.e. give a Day object and let its routes be modified

    # ? iterate in the same day as long as there is an improvement, then move on to the next  one
    for day in work_days:

        improved = True
        while improved:
            improved = False

            iteration_count += 1

            iter_start = time.time()

            routes = working.days[day].routes.copy()

            for i_count, route1 in enumerate(routes):
                for r1_pos in range(len(route1.targets)):

                    can_do_pair_move = r1_pos + 1 < len(route1.targets)

                    for j_count, route2 in enumerate(routes):
                        if i_count == j_count:
                            continue
                        
                        can_do_two_opt = i_count < j_count  # to perform this op on every unordered pair of routes
                        # other ops perform work on every ordered pair of routes

                        for r2_pos in range(len(route2.targets)):

                            if can_do_two_opt:
                                res = two_opt_routes_operator(working, route1, route2, r1_pos, r2_pos)
                                if res is not None:
                                    cnt = res
                                    current_best_solution, best_score, improved = evaluate_neighbour(working, current_best_solution, best_score)
                                    undo_two_opt_routes_operator(working, route1, route2, cnt)

                            if route_move_service_operator(working, r1_pos, r2_pos, route1, route2):
                                current_best_solution, best_score, improved = evaluate_neighbour(working, current_best_solution, best_score)
                                undo_route_move_service_operator(working, r1_pos, r2_pos, route1, route2)

                            if can_do_pair_move:
                                if route_move_pair_service_operator(working, r1_pos, r2_pos, route1, route2):
                                    current_best_solution, best_score, improved = evaluate_neighbour(working, current_best_solution, best_score)
                                    undo_route_move_pair_service_operator(working, r1_pos, r2_pos, route1, route2)
            
            working = current_best_solution
            # apply best found for the day

            iter_end = time.time()

            last_iteration_time = iter_end - iter_start
            iteration_avg_time = iteration_avg_time * (iteration_count - 1) / iteration_count + last_iteration_time / iteration_count

            if iteration_count % 10 == 1:
                print(f"Phase 3 mid-report:")
                print(f"Current day: {day}")
                print(f"Iteration count: {iteration_count}")
                print(f"Last iteration time: {last_iteration_time}")
                print(f"Average iteration time: {iteration_avg_time}")
                print(f"Current score: {best_score}\n")
            
                
        print(f"\nPhase 3 day {day} ended!")
        print("Phase 3 day report:")
        print(f"Current Iteration count: {iteration_count}")
        print(f"Last iteration time: {last_iteration_time}")
        print(f"Average iteration time: {iteration_avg_time}")
        print(f"Current score: {best_score}\n")

    print("\nPhase 3 ended!")
    print("Phase 3 Report:")
    print(f"Iteration count: {iteration_count}")
    print(f"Last iteration time: {last_iteration_time}")
    print(f"Average iteration time: {iteration_avg_time}")
    print(f"Current score: {best_score}")

    return current_best_solution, best_score, best_score < original_score



# ? PHASE 3 - route operators, two_opt, move (single) and move_pair, best move applied for each day
def phase_3_reverse_loops(working):
    original_score = working.evaluate()
    working_score = original_score

    current_best_solution = working
    best_score = original_score

    
    iteration_count = 0
    iteration_avg_time = 0

    # todo - iterations, apply ops as long as there is some improvement
    
    work_days = working.get_work_days()

    # todo - one test run with the other way around for bug testing
    improved = True
    while improved:
        improved = False
    
        iteration_count += 1
        iter_start = time.time()


        for day in work_days:

            routes = working.days[day].routes.copy()

            for i_count, route1 in enumerate(routes):
                for r1_pos in range(len(route1.targets)):

                    can_do_pair_move = r1_pos + 1 < len(route1.targets)

                    for j_count, route2 in enumerate(routes):
                        if i_count == j_count:
                            continue
                        
                        can_do_two_opt = i_count < j_count  # to perform this op on every unordered pair of routes
                        # other ops perform work on every ordered pair of routes

                        for r2_pos in range(len(route2.targets)):

                            if can_do_two_opt:
                                res = two_opt_routes_operator(working, route1, route2, r1_pos, r2_pos)
                                if res is not None:
                                    cnt = res
                                    current_best_solution, best_score, improved = evaluate_neighbour(working, current_best_solution, best_score)
                                    undo_two_opt_routes_operator(working, route1, route2, cnt)

                            if route_move_service_operator(working, r1_pos, r2_pos, route1, route2):
                                current_best_solution, best_score, improved = evaluate_neighbour(working, current_best_solution, best_score)
                                undo_route_move_service_operator(working, r1_pos, r2_pos, route1, route2)

                            if can_do_pair_move:
                                if route_move_pair_service_operator(working, r1_pos, r2_pos, route1, route2):
                                    current_best_solution, best_score, improved = evaluate_neighbour(working, current_best_solution, best_score)
                                    undo_route_move_pair_service_operator(working, r1_pos, r2_pos, route1, route2)

            print(f"Ended iteration for day {day}, current time: {datetime.datetime.now()}")

            working = current_best_solution
            working_score = best_score


        iter_end = time.time()

        last_iteration_time = iter_end - iter_start
        iteration_avg_time = iteration_avg_time * (iteration_count - 1) / iteration_count + last_iteration_time / iteration_count

        if iteration_count % 10 == 1:
            print(f"Phase 3 mid-report:")
            print(f"Iteration count: {iteration_count}")
            print(f"Last iteration time: {last_iteration_time}")
            print(f"Average iteration time: {iteration_avg_time}")
            print(f"Current score: {best_score}")
            
    print("Phase 3 ended!")
    print("Phase 3 Report:")
    print(f"Iteration count: {iteration_count}")
    print(f"Last iteration time: {last_iteration_time}")
    print(f"Average iteration time: {iteration_avg_time}")
    print(f"Current score: {best_score}")


    return current_best_solution, best_score, best_score < original_score



# END PHASE METHODS



# PHASE METHODS - IMPROVED VERSIONS

# ? IMPROVED PHASE 1 - add_service_operator and remove_service_operator
# todo - apply best operation per edge, not for whole solution at each iteration
def improved_phase_1(working):
    original_score = working.evaluate()
    working_score = original_score

    current_best_solution = working
    best_score = original_score

    work_days = set(working.get_work_days())

    iteration_count = 0
    iteration_avg_time = 0

    improved = True

    # best add service op day for each edge (which is under-satisfied)
    # [0] - best day
    # [1] - score if op applied with best day
    best_as_op = None

    # best remove service op day for each edge (which is over-satisfied)
    best_rs_op = None


    while improved:
        improved = False
        
        iteration_count += 1
        iter_start = time.time()

        # reset values at start of iteration
        best_as_op = dict()
        best_rs_op = dict()

        # adding a service to edges with too little services
        under_satisfied_edges = working.get_under_satisfied_edges()
        for edge in under_satisfied_edges:
            no_service_days = work_days.difference(edge.service_days)
            for day in no_service_days:
                if add_service_operator(working, day, edge):
                    neighbour_score = working.evaluate()
                    if edge.sid not in best_as_op:
                        best_as_op[edge.sid] = [day, neighbour_score]
                    elif neighbour_score < best_as_op[edge.sid][1]:
                        best_as_op[edge.sid][0] = day
                        best_as_op[edge.sid][1] = neighbour_score
                    
                    undo_add_service_operator(working, day, edge)
            

        # removing a service of edges with too many services
        over_satisfied_edges = working.get_over_satisfied_edges()
        for edge in over_satisfied_edges:
            for day in edge.service_days:
                res = remove_service_operator(working, day, edge)
                if res is not None:
                    route, pos = res
                    neighbour_score = working.evaluate()
                    if edge.sid not in best_rs_op:
                        best_rs_op[edge.sid] = [day, neighbour_score]
                    elif neighbour_score < best_rs_op[edge.sid][1]:
                        best_rs_op[edge.sid][0] = day
                        best_rs_op[edge.sid][1] = neighbour_score


                    undo_remove_service_operator(working, day, edge, route, pos)

        # apply best ops for each edge

        for sid, res in best_as_op.items():
            edge = working.demanded_edges[sid]
            day = res[0]
            add_service_operator(working, day, edge)

        
        for sid, res in best_rs_op.items():
            edge = working.demanded_edges[sid]
            day = res[0]
            remove_service_operator(working, day, edge)

        # ? should be fine to do it without deepcopy, but doing it just in case
        current_best_solution = copy.deepcopy(working)
        best_score = working.evaluate()

        iter_end = time.time()

        last_iteration_time = iter_end - iter_start
        iteration_avg_time = iteration_avg_time * (iteration_count - 1) / iteration_count + last_iteration_time / iteration_count

        if iteration_count % 10 == 1:
            print(f"Phase 1 mid-report:")
            print(f"Iteration count: {iteration_count}")
            print(f"Last iteration time: {last_iteration_time}")
            print(f"Average iteration time: {iteration_avg_time}")
            print(f"Current score: {best_score}")
            
    print("Phase 1 ended!")
    print("Phase 1 Report:")
    print(f"Iteration count: {iteration_count}")
    print(f"Last iteration time: {last_iteration_time}")
    print(f"Average iteration time: {iteration_avg_time}")
    print(f"Current score: {best_score}")
    
    return current_best_solution, best_score, best_score < original_score

# ? PHASE 2 - move_service_operator and swap_services_operator
# todo - maybe try saving estimates of move_service - will require A LOT MORE SPACE
# todo - save estimate costs of op2, and re-calculate when something changes
def improved_phase_2(working):
    original_score = working.evaluate()
    working_score = original_score

    current_best_solution = working
    best_score = original_score
    
    work_days = set(working.get_work_days())
    
    iteration_count = 0
    iteration_avg_time = 0


    # estimates of applying swap services (ss) operator
    ss_estimates = dict()

    # calculate once initially
    for bucket in working.frequency_buckets:
        for i in range(len(bucket)):
            edge_1 = bucket[i]
            for j in range(i+1, len(bucket)):
                edge_2 = bucket[j]

                res = swap_services_operator(working, edge_1, edge_2)
                if res is not None:
                    e1_routes, e2_routes = res
                    id1 = min(edge_1.sid, edge_2.sid)
                    id2 = max(edge_1.sid, edge_2.sid)
                    ss_estimates[(id1, id2)] = working_score -  working.evaluate()
                    undo_swap_services_operator(working, edge_1, edge_2, e1_routes, e2_routes)
            

    current_affected_days = None
    # list of days which are affected by application of last iteration's best op
    # an estimation is recalculated only for edges with services in these days
    # well the pairs including those edges, no need to recalculate for pairs of non-affected days 

    improved = True
    improved_op = False
    while improved:
        improved = False
        iteration_count += 1
        iter_start = time.time()

        current_affected_days = None

        # move_service operator
        for edge in working.demanded_edges:
            no_service_days = work_days.difference(edge.service_days)

            for d1 in edge.service_days:
                for d2 in no_service_days:

                    res = move_service_operator(working, d1, d2, edge)
                    if res is not None:
                        route, pos = res
                        current_best_solution, best_score, improved_op = evaluate_neighbour(working, current_best_solution, best_score)
                        undo_move_service_operator(working, d1, d2, edge, route, pos)
                        current_affected_days = frozenset((d1, d2))
                        if improved_op:
                            improved = True


        # swap_services operator - recalculate estimates


        # see if best swap_service estimate has better than best move_service
        min_pair = None
        min_estimate = 0
        for pair, estimate in ss_estimates.items():
            if estimate < min_estimate:
                min_pair = pair
                min_estimate = estimate

        # evaluate the application of swap_services
        # since this is just an estimate
        if min_pair is not None:
            edge_1 = pair[0]
            edge_2 = pair[1]
            res = swap_services_operator(working, edge_1, edge_2)
            current_best_solution, best_score, improved = evaluate_neighbour(working, current_best_solution, best_score)
            if not improved:
                e1_routes, e2_routes = res
                undo_swap_services_operator(working, edge_1, edge_2, e1_routes, e2_routes)
            else:
                current_affected_days = frozenset(edge_1.service_days + edge_2.service_days)

        working = current_best_solution
        working_score = best_score

        if current_affected_days is not None:
            # recalculate ss estimates for edges in these days
            affected_edges = set()
            for day in current_affected_days:
                affected_edges.update(day.edges)

                
            for edge_1 in affected_edges:
                
                for edge_2 in working.frequency_buckets[edge_1.freq]:
                    if edge_1 == edge_2:
                        continue
                    
                    res = swap_services_operator(working, edge_1, edge_2)
                    if res is not None:
                        e1_routes, e2_routes = res
                        id1 = min(edge_1.sid, edge_2.sid)
                        id2 = max(edge_1.sid, edge_2.sid)
                        ss_estimates[(id1, id2)] = working_score -  working.evaluate()
                        undo_swap_services_operator(working, edge_1, edge_2, e1_routes, e2_routes)
                    
        current_affected_days = None



        iter_end = time.time()

        last_iteration_time = iter_end - iter_start
        iteration_avg_time = iteration_avg_time * (iteration_count - 1) / iteration_count + last_iteration_time / iteration_count

        if iteration_count % 10 == 1:
            print(f"Phase 2 mid-report:")
            print(f"Iteration count: {iteration_count}")
            print(f"Last iteration time: {last_iteration_time}")
            print(f"Average iteration time: {iteration_avg_time}")
            print(f"Current score: {best_score}")
            
    print("Phase 2 ended!")
    print("Phase 2 Report:")
    print(f"Iteration count: {iteration_count}")
    print(f"Last iteration time: {last_iteration_time}")
    print(f"Average iteration time: {iteration_avg_time}")
    print(f"Current score: {best_score}")



    return current_best_solution, best_score, best_score < original_score



# END PHASE METHODS - IMPROVED VERSIONS


# RUN METHOD
def run(solution):

     
    no_improvement_count = 0
    patience = 10       # how many iterations to go without improvement

    current_best_solution = solution

    original_score = current_best_solution.evaluate()
    best_before_score = original_score
    best_score = best_before_score
    
    iteration_count = 0
    iteration_start_time = 0
    iteration_end_time = 0
    iteration_time_taken = 0
    average_iteration_time = 0

 
    improving = True
    phase_improving = False
    while improving:
        improving = False

        iteration_count += 1
        iteration_start_time = time.time()

        # phase 1 - add or remove services of edges with too litle or too many services
        # best_score, current_best_solution, phase_improving = phase_1(current_best_solution, best_score)
        best_score, current_best_solution, phase_improving = improved_phase_1(current_best_solution, best_score)

        # print("Skipped phase 1!")

        p1_end_time = time.time()
        if iteration_count == 1:
            print(f"Phase 1 ended after {p1_end_time - iteration_start_time} seconds")
            print(f"Current score: {best_score}")

        if phase_improving:
            improving = True


        # print("\nSolution after phase 1:\n\n")
        # print(current_best_solution)


        # phase 2 - move services from 1 day to another day and swap service days of edges with same frequency 
        best_score, current_best_solution, phase_improving = phase_2(current_best_solution, best_score)
        # best_score, current_best_solution, phase_improving = improved_phase_2(current_best_solution, best_score)

        p2_end_time = time.time()
        if iteration_count == 1:
            print(f"Phase 2 ended after {p2_end_time - p1_end_time} seconds")
            print(f"Current score: {best_score}")

        if phase_improving:
            improving = True

        # phase 3 - improve the routes
        best_score, current_best_solution, phase_improving = phase_3(current_best_solution, best_score)

        if phase_improving:
            improving = True

        iteration_end_time = time.time()
        if iteration_count == 1:
            print(f"Phase 3 ended after {iteration_end_time - p2_end_time} seconds")
            print(f"Current score: {best_score}")
        

        iteration_time_taken = iteration_end_time - iteration_start_time
        average_iteration_time = average_iteration_time * (iteration_count - 1) / iteration_count + iteration_time_taken / iteration_count

        print(f"Local search report:")
        print(f"Iteration count: {iteration_count} iterations")
        print(f"Last iteration time: {iteration_time_taken} seconds")
        print(f"Iteration average time: {iteration_time_taken} seconds")
        print(f"Current score: {best_score}")

        if iteration_count == 1:
            print("\nSolution after going through each phase once:\n\n")
            print(current_best_solution)
        
    print(f"Local search ended after {iteration_count} iterations.")
    print(f"Last iteration time: {iteration_time_taken} seconds")
    print(f"Iteration average time: {iteration_time_taken} seconds")
    print(f"Original score: {original_score}")
    print(f"Current score: {best_score}")

    return best_score, current_best_solution


# END RUN METHOD