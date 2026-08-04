
import sys
import time
import datetime
import copy
from threading import Thread, Lock
from queue import Queue

printing_lock = Lock()

sys.path.append('..')

from solution_representation.Route import Route
from solution_representation.constants import VEHICLE_WEIGHT, EXPECTED_SERVICES_PENALTY, EXPECTED_SPACING_PENALTY, VEHICLE_OVERLOAD_PENALTY



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
    cost_before = edge.under_satisfaction_size(solution.vehicle) * EXPECTED_SERVICES_PENALTY

    
    assert solution.days[d1].add_edge(edge)
    

    # what this operator is trying to improve 
    #   - get closer to expected number of services - this one regardless of where it is put, it's getting closer since this operator is called on under-satisfied edges 
    #   - add the service so that the spacing is neither too wide nor too tight, or at least try to

    # so check the spacing, between this service and previous service and this service and next service

    # below for evaluating an estimate cost

    cost_after = edge.under_satisfaction_size(solution.vehicle) * EXPECTED_SERVICES_PENALTY
    if len(edge.service_days) > 2:
        # if there were at least 2 services before then check the spacing before and after
        service_id = edge.service_days.index(d1)    # get position of day in service days

        # add the spacing penalty for services before which had no service in-between
        cost_before += edge.evaluate_spacing(service_id-1, service_id + 1, solution.vehicle)

        # check the spacings which have one end at the newly added service
        # least acceptable case is one wide spacing turned into 1 valid spacing and 1 invalid (tight/wide)
        # more penalty if 1 invalid spacing turned into 2 invalid spacings 
        cost_after += edge.evaluate_service_spacing(service_id, solution.vehicle)

    estimate = cost_after - cost_before

    # below is so that it prioritizes days with fewer edges when penalty (or non-penalty) values are same for multiple positions
    estimate += len(solution.days[d1].edges)    

    # assert d1 in edge.service_days
    # assert edge.routes[d1] is not None
    # assert solution.days[d1].edge_in_day(edge)

    # ? nothing needed for undo - just remove the service
    return None, estimate

# undo_unfo is not needed for this operator, just making it a standard for every undo to have it
def undo_add_service_operator(solution, d1, edge, undo_info=None):
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

    # doing an estimate by checking the spacing between the two services which are done before and after this service
    service_id = edge.service_days.index(d1)    # get position of day in service days
    
    cost_before = edge.over_satisfaction_size(solution.vehicle) * EXPECTED_SERVICES_PENALTY
    cost_before += edge.evaluate_service_spacing(service_id, solution.vehicle)
    
    assert solution.days[d1].remove_edge(edge)


    cost_after = edge.over_satisfaction_size(solution.vehicle) * EXPECTED_SERVICES_PENALTY
    # service_id + 1 was shifted to position service_id, unless this was last edge but I think that's a fine metric too
    cost_after += edge.evaluate_spacing(service_id-1, service_id, solution.vehicle)
    
    # TODO - i don't think it will happen, but be mindful of scenario where len(edge.service_days) == 1

    estimate = cost_after - cost_before

    
    # doing this (minus) so that days with more edges are prioritized when penalty is same
    estimate -= len(solution.days[d1].edges)


    # assert d1 not in edge.service_days
    # assert edge.routes[d1] is None
    # assert not solution.days[d1].edge_in_day(edge)



    # ? for undo - return the route where the edge was in the day before and the position in that route
    return (route, pos), estimate

def undo_remove_service_operator(solution, d1, edge, undo_info):

    route, pos = undo_info

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

    # estimate is only checking on the spacings, since number of services is the same before and after
    # since it's one remove_service and one add_service
    
    # check spacing at day d1
    # check spacing which includes d2 
    # - since d2 is not a service day there is 1 service before d2 and after d2, unless d2 is in last or first gap, but can deal with that by circling the service days
    removed_service_id = edge.service_days.index(d1)
    cost_before = edge.evaluate_service_spacing(removed_service_id, solution.vehicle)

    
    (route, pos), estimate_rs = remove_service_operator(solution, d1, edge)
    estimate_as = add_service_operator(solution, d2, edge)


    new_service_id = edge.service_days.index(d2)
    if new_service_id == removed_service_id:
        # if d2 is put in same position compare spacings
        cost_after = edge.evaluate_service_spacing(new_service_id, solution.vehicle)
    else:
        # else check the widened gap left by removing d1
        cost_after = edge.evaluate_spacing(removed_service_id - 1, removed_service_id, solution.vehicle)
        
        # also check the tightened gaps made by inserting d2
        cost_after += edge.evaluate_service_spacing(new_service_id, solution.vehicle)
        # also for before check the gap that was including d2
        cost_before += edge.evaluate_spacing(new_service_id - 1, new_service_id + 1, solution.vehicle)

    estimate = cost_after - cost_before

    # below is for prioritizing
    #   - moving FROM days with more edges
    #   - moving TO days with fewer edges
    # in case penalties are same for more candidates
    estimate = estimate - len(solution.days[d1].edges) + len(solution.days[d2].edges)

    # todo - make estimate a tuple, for above tie-breaker moving FROM days with more edges can be taken as more priority

    # not using estimates from remove_service and add_service since if this edge was on the border of lower_bound
    # one will include penalty for number of services, but that cancels out, so only checking the spacings affected

    return (route, pos), estimate

def undo_move_service_operator(solution, d1, d2, edge, undo_info):
    #   ? - intuitively this could be a call to same op with arguments reversed
    #   ? - but to not destroy the solution before, this inserts it back in the same route and same position of day where the edge was removed / moved from


    undo_add_service_operator(solution, d2, edge)
    undo_remove_service_operator(solution, d1, edge, undo_info)


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

    if len(only_edge_1_days) == 0 or len(only_edge_2_days) == 0:
        # above statemenst are equivalent
        # if one holds true the other one is true as well
        # since we're considering edges with same frequency
        # to not waste time on evaluating and doing undo
        return None

    edge_1_routes = []
    edge_2_routes = []

    cost_before = 0

    cost_after = 0

    # todo - evaluate routes before first
    # todo - add edges after
    # todo -evaluate routes after 

    for day in only_edge_1_days:
        cost_before += edge_1.routes[day].evaluate(solution.vehicle)

        (route, pos), _ = remove_service_operator(solution, day, edge_1)
        add_service_operator(solution, day, edge_2)

        cost_after += edge_2.routes[day].evaluate(solution.vehicle)

        edge_1_routes.append((route, pos))



    for day in only_edge_2_days:
        cost_before += edge_2.routes[day].evaluate(solution.vehicle)

        (route, pos), _ = remove_service_operator(solution, day, edge_2)
        add_service_operator(solution, day, edge_1)

        cost_after += edge_1.routes[day].evaluate(solution.vehicle)


        edge_2_routes.append((route, pos))

    
    # assert edge_2.service_days == before_e1
    # assert edge_1.service_days == before_e2

    # since spacing between services are symmetric after operation is done, those penalties will be the same
    # the only thing different is the routes - since they're inserted in random routes
    estimate = cost_after - cost_before

    return (edge_1_routes, edge_2_routes), estimate

def undo_swap_services_operator(solution, edge_1, edge_2, undo_info):
    # ? similar argument for move_service, insert the removed services into the same routes and same positions

    edge_1_routes, edge_2_routes = undo_info

    for route, pos in edge_1_routes:
        undo_add_service_operator(solution, route.day, edge_2)
        undo_remove_service_operator(solution, route.day, edge_1, (route, pos))

    for route, pos in edge_2_routes:
        undo_add_service_operator(solution, route.day, edge_1)
        undo_remove_service_operator(solution, route.day, edge_2, (route, pos))
    



# ? Take 2 routes, cut the routes in 2 (or don't), and merge a cut of a route with the cut of the other route
def two_opt_routes_operator(route_1, route_2, r1_cutpoint, r2_cutpoint, solution=None, day = None):
    #   - only if the two routes are in the same day
    #   - and they are different routes

    if route_1 is route_2:
        return None

    if route_1.day != route_2.day:
        return None

    if solution is not None:
        day = solution.days[route_1.day]
    elif day is None:
        print("Calling two_opt op with solution and day both None")
        return None
    # else day is not None and work with it

    # working only with the routes
    # not removing and adding services to the day, since it's the same day

    # assert route_1 in day.routes
    # assert route_2 in day.routes


    # TODO - maybe do some checking, cause I'm assuming both routes are non-empty
    # todo - since number of vehicles is an important metric not allowing this operator to be used to split a single route into two
    cost_before = route_1.evaluate(day.vehicle) + route_2.evaluate(day.vehicle) + 2 * VEHICLE_WEIGHT


    r1_half1 = Route(route_1.targets[:r1_cutpoint], day = route_1.day)
    r1_half2 = Route(route_1.targets[r1_cutpoint:], day = route_1.day)

    r2_half1 = Route(route_2.targets[:r2_cutpoint], day = route_1.day)
    r2_half2 = Route(route_2.targets[r2_cutpoint:], day = route_1.day)


    a_route1 = r1_half1.merge(r2_half1)
    a_route2 = r1_half2.merge(r2_half2)

    b_route1 = r1_half1.merge(r2_half2)
    b_route2 = r1_half2.merge(r2_half1)

    cost_a = a_route1.evaluate(day.vehicle) + a_route2.evaluate(day.vehicle)
    cost_b = b_route1.evaluate(day.vehicle) + b_route2.evaluate(day.vehicle)

    cost_after = min(cost_a, cost_b)


    
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


    cost_after += cnt * VEHICLE_WEIGHT

    estimate = cost_after - cost_before

    # ? assertion checking
    # for edge in res_r1.targets:
    #     assert edge.routes[day.number] == res_r1
    # for edge in res_r2.targets:
    #     assert edge.routes[day.number] == res_r2

    return cnt, estimate


def undo_two_opt_routes_operator(route_1, route_2, r1_cutpoint, r2_cutpoint, undo_info, solution=None, day = None):

    route_cnt = undo_info

    if solution is not None:
        day = solution.days[route_1.day]
    elif day is None:
        print("Calling undo_two_opt_routes_operator with solution and day both None")
        return None

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
def route_move_service_operator(edge_1_id, edge_2_id, route_1, route_2, solution = None, day = None):
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

    if solution is not None:
        day = solution.days[route_1.day]
    elif day is None:
        print("Calling route_move_service_operator with solution and day both None")
        return None

    # since an edge is MOVED FROM route 1, it's definetely not empty at this point
    cost_before = route_1.evaluate(day.vehicle) + route_2.evaluate(day.vehicle) + VEHICLE_WEIGHT
    # route 2 may be empty before move - for undo, but still just to be safe
    cost_before += (len(route_2.targets) > 0) * VEHICLE_WEIGHT
    

    edge_1 = route_1.targets[edge_1_id]
    route_1.remove_edge(pos = edge_1_id)
    route_2.insert_edge(edge_1, pos = edge_2_id)   

    # ? below is done in route_2.insert_edge
    # edge_1.routes[route_2.day] = route_2


    # since an edge was MOVED TO route 2, it's definetely not empty
    cost_after = route_1.evaluate(day.vehicle) + route_2.evaluate(day.vehicle) + VEHICLE_WEIGHT
    # route 1 may be empty after move
    cost_after += (len(route_1.targets) > 0) * VEHICLE_WEIGHT

    estimate = cost_after - cost_before

    if len(route_1.targets) == 0:
        day.remove_route(route_1)

    # the below if only can happen in undo version of this operator
    # route had only 1 target and that was moved with the normal version of this operator
    # so it's left with 0 targets and removed above
    # then undo version calls this operator (for convenience to not copy paste code) 
    # and the route needs to be added back
    if len(route_2.targets) == 1:
        day.add_route(route_2)


    # assert route_2 in edge_1.routes
    # assert route_2 is edge_1.routes[route_2.day]
    # assert route_2 == edge_1.routes[route_2.day]

    return None, estimate

def undo_route_move_service_operator(edge_1_id, edge_2_id, route_1, route_2, undo_info = None, solution = None, day = None):
    # call same operator with arguments reversed
    route_move_service_operator(edge_2_id, edge_1_id, route_2, route_1, solution, day)

    # assert route_1 in solution.days[route_1.day].routes
    # assert route_2 in solution.days[route_1.day].routes
    # assert route_1.targets[edge_1_id].routes[route_1.day] == route_1


# ? Take a pair (2 edges served one after another in the same route) and move it to a different route in the same day
def route_move_pair_service_operator(edge_a12_id, edge_b_id, route_a, route_b, solution = None, day = None):
    #   - routes are in the same day
    #   - and they are different routes

    # take the pair of edges at positions (edge_a12_id, edge_a12_id + 1)

    
    # todo - can remove below out of bound checks if that is done before calling the operator
    if edge_a12_id + 1 >= len(route_a.targets):
        return None

    if solution is not None:
        day = solution.days[route_a.day]
    elif day is None:
        print("Calling route_move_pair_service_operator with solution and day both None")
        return None

    # since edges are MOVED FROM route a, it's definetely not empty at this point
    cost_before = route_a.evaluate(day.vehicle) + route_b.evaluate(day.vehicle) + VEHICLE_WEIGHT
    # route b may be empty before move - for undo, but still just to be safe
    cost_before += (len(route_b.targets) > 0) * VEHICLE_WEIGHT

    
    # if some check fails, then op can't be done
    if route_move_service_operator(edge_a12_id + 1, edge_b_id, route_a, route_b, solution, day) is None:
        return None

    # otherwise all checks are done in above op call
    route_move_service_operator(edge_a12_id, edge_b_id, route_a, route_b, solution, day)


    # since edges were MOVED TO route b, it's definetely not empty
    cost_after = route_a.evaluate(day.vehicle) + route_b.evaluate(day.vehicle) + VEHICLE_WEIGHT
    # route a may be empty after move
    cost_after += (len(route_a.targets) > 0) * VEHICLE_WEIGHT

    estimate = cost_after - cost_before

    return None, estimate

def undo_route_move_pair_service_operator(edge_a12_id, edge_b_id, route_a, route_b, undo_info = None, solution = None, day = None):
    # same op call with arguments in different order
    route_move_pair_service_operator(edge_b_id, edge_a12_id, route_b, route_a, solution, day)



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

# to avoid doing deepcopy
def evaluate_operator(best_estimate, best_op, op, undo_op, *args, **kwargs):
    # apply op, evaluate using estimate, do undo

    # best_op is a tuple of best op with args found so far
    # if this op is better than best_op, then return this op as best_op

    res = op(*args, **kwargs)
    if res is None:
        # if op wasn't performed don't evaluate
        return best_estimate, best_op

    undo_info, new_estimate = res

    if new_estimate < best_estimate:
        best_estimate = new_estimate
        best_op = (op, undo_op, args, kwargs)

    undo_op(*args, undo_info = undo_info, **kwargs)

    return best_estimate, best_op

def full_evaluate_operator(before_score, solution, best_op_tuple):

    operator, undo_operator, args, kwargs = best_op_tuple

    undo_info, _ = operator(*args, **kwargs)
    after_score = solution.evaluate()
    if after_score >= before_score:
        undo_operator(*args, undo_info = undo_info, **kwargs)
        return False, before_score
    
    return True, after_score


# below function for just applying the best operator
def apply_operator(operator, *args, **kwargs):
    # apply the operator with given args and kwargs
    # return the undo result of the operator

    res = operator(*args, **kwargs)
    return res
# END UTIL METHODS


# PHASE METHODS


# ? PHASE 1 - add_service_operator and remove_service_operator
def phase_1(working):
    original_score = working.evaluate()

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
        best_estimate = 0
        best_op_tuple = None


        # adding a service to edges with too little services
        under_satisfied_edges = working.get_under_satisfied_edges()
        for edge in under_satisfied_edges:
            no_service_days = work_days.difference(edge.service_days)
            for day in no_service_days:
                best_estimate, best_op_tuple = evaluate_operator(best_estimate, best_op_tuple, add_service_operator, undo_add_service_operator, working, day, edge)
                
            

        # removing a service of edges with too many services
        over_satisfied_edges = working.get_over_satisfied_edges()
        for edge in over_satisfied_edges:
            for day in edge.service_days:
                best_estimate, best_op_tuple = evaluate_operator(best_estimate, best_op_tuple, remove_service_operator, undo_remove_service_operator, working, day, edge)
                

        # ? note solution is part of args
        if best_op_tuple is not None:
            improved, best_score = full_evaluate_operator(best_score, working, best_op_tuple)


        iter_end = time.time()

        last_iteration_time = iter_end - iter_start
        iteration_avg_time = iteration_avg_time * (iteration_count - 1) / iteration_count + last_iteration_time / iteration_count

        if iteration_count % 10 == 1:
            print(f"Phase 1 mid-report:")
            print(f"Iteration count: {iteration_count}")
            print(f"Last iteration time: {last_iteration_time}")
            print(f"Average iteration time: {iteration_avg_time}")
            print(f"Current score: {best_score}")
            
    best_score = working.evaluate()

    print("Phase 1 ended!")
    print("Phase 1 Report:")
    print(f"Iteration count: {iteration_count}")
    print(f"Last iteration time: {last_iteration_time}")
    print(f"Average iteration time: {iteration_avg_time}")
    print(f"Current score: {best_score}")
    
    return working, best_score, best_score < original_score


# ? PHASE 2 - move_service_operator and swap_services_operator
def phase_2(working):
    original_score = working.evaluate()
    best_score = original_score

    best_op_tuple = None
    best_score = original_score
    
    work_days = set(working.get_work_days())
    
    iteration_count = 0
    iteration_avg_time = 0


    # todo - iterations, apply ops as long as there is some improvement
    improved = True
    while improved:
        improved = False

        iteration_count += 1

        iter_start = time.time()

        # reset values
        best_op_tuple = None
        best_estimate = 0

        # move_service operator
        for edge in working.demanded_edges:
            no_service_days = list(work_days.difference(edge.service_days))

            for d1 in edge.service_days:
                for d2 in no_service_days:
                    best_estimate, best_op_tuple = evaluate_operator(best_estimate, best_op_tuple, move_service_operator, undo_move_service_operator, working, d1, d2, edge)
                    
                    


        # swap_services operator
        for bucket in working.frequency_buckets.values():
            
            for i in range(len(bucket)):
                edge_1 = bucket[i]

                for j in range(i+1, len(bucket)):
                    edge_2 = bucket[j]
                    best_estimate, best_op_tuple = evaluate_operator(best_estimate, best_op_tuple, swap_services_operator, undo_swap_services_operator, working, edge_1, edge_2)

                    
            

        # apply the best operator after trying all
        if best_op_tuple is not None:
            improved, best_score = full_evaluate_operator(best_score, working, best_op_tuple)
            
            
        
        # else improved should be false and loop will exit


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



    return working, best_score, best_score < original_score


# ? PHASE 3 - route operators, two_opt, move (single) and move_pair, best move applied for each day
def phase_3(working):
    original_score = working.evaluate()

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

            # reset values
            best_op_tuple = None
            best_estimate = 0


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
                                best_estimate, best_op_tuple = evaluate_operator(best_estimate, best_op_tuple, two_opt_routes_operator, undo_two_opt_routes_operator, route1, route2, r1_pos, r2_pos, solution = working)
                                
                            best_estimate, best_op_tuple = evaluate_operator(best_estimate, best_op_tuple, route_move_service_operator, undo_route_move_service_operator, r1_pos, r2_pos, route1, route2, solution = working)


                            if can_do_pair_move:
                                best_estimate, best_op_tuple = evaluate_operator(best_estimate, best_op_tuple, route_move_pair_service_operator, undo_route_move_pair_service_operator, r1_pos, r2_pos, route1, route2, solution = working)
            
            # ? apply best found for the day
            if best_op_tuple is not None:
                improved, best_score = full_evaluate_operator(best_score, working, best_op_tuple)
                

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

    return working, best_score, best_score < original_score



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
                                res = two_opt_routes_operator(route1, route2, r1_pos, r2_pos, solution = working)
                                if res is not None:
                                    cnt = res
                                    current_best_solution, best_score, improved = evaluate_neighbour(working, current_best_solution, best_score)
                                    undo_two_opt_routes_operator(route1, route2, cnt, solution = working)

                            if route_move_service_operator(r1_pos, r2_pos, route1, route2, solution = working):
                                current_best_solution, best_score, improved = evaluate_neighbour(working, current_best_solution, best_score)
                                undo_route_move_service_operator(r1_pos, r2_pos, route1, route2, solution = working)

                            if can_do_pair_move:
                                if route_move_pair_service_operator(r1_pos, r2_pos, route1, route2, solution = working):
                                    current_best_solution, best_score, improved = evaluate_neighbour(working, current_best_solution, best_score)
                                    undo_route_move_pair_service_operator(r1_pos, r2_pos, route1, route2, solution = working)

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
# ? - apply best operation per edge, not for whole solution at each iteration
def improved_phase_1(working):
    original_score = working.evaluate()

    best_score = original_score

    work_days = set(working.get_work_days())

    iteration_count = 0
    iteration_avg_time = 0

    improved = True

    improved_edge = False
    while improved:
        improved = False
        
        iteration_count += 1
        iter_start = time.time()


        # adding a service to edges with too little services
        under_satisfied_edges = working.get_under_satisfied_edges()
        for edge in under_satisfied_edges:
        
            best_op_tuple = None
            best_estimate = 0

            no_service_days = work_days.difference(edge.service_days)
            for day in no_service_days:
                best_estimate, best_op_tuple = evaluate_operator(best_estimate, best_op_tuple, add_service_operator, undo_add_service_operator, working, day, edge)
                
            
            # full - evaluate the best one for each edge
            if best_op_tuple is not None:
                improved_edge, best_score = full_evaluate_operator(best_score, working, best_op_tuple)

                if improved_edge:
                    improved = True

        # removing a service of edges with too many services
        over_satisfied_edges = working.get_over_satisfied_edges()
        for edge in over_satisfied_edges:
            
            best_op_tuple = None
            best_estimate = 0

            for day in edge.service_days:
                best_estimate, best_op_tuple = evaluate_operator(best_estimate, best_op_tuple, remove_service_operator, undo_remove_service_operator, working, day, edge)

            # full - evaluate the best one for each edge
            if best_op_tuple is not None:
                improved_edge, best_score = full_evaluate_operator(best_score, working, best_op_tuple)

                if improved_edge:
                    improved = True


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
    
    return working, best_score, best_score < original_score

# ? PHASE 2 - move_service_operator and swap_services_operator
# todo - maybe try saving estimates of move_service - will require A LOT MORE SPACE
# todo - save estimate costs of op2, and re-calculate when something changes
def improved_phase_2(working):
    original_score = working.evaluate()

    best_score = original_score
    
    work_days = set(working.get_work_days())
    
    iteration_count = 0
    iteration_avg_time = 0
    last_report = time.time() - 600

    ss_min_estimate_pair = None
    ss_min_estimate_val = 0

    # estimations for swap_service_operator
    ss_estimations = dict()

    # todo - calculate initial estimates for swap_services
    for bucket in working.frequency_buckets.values():
        
        for i, edge_1 in enumerate(bucket):

            for j in range(i+1, len(bucket)):
                edge_2 = bucket[j]


                estimate, _ = evaluate_operator(0, None, swap_services_operator, undo_swap_services_operator, working, edge_1, edge_2)
                if estimate != 0:
                    # only consider candidates with estimate < 0
                    # below is because calling swap(e1, e2) is same as swap(e2, e1)
                    id1 = min(edge_1.sid, edge_2.sid)
                    id2 = max(edge_1.sid, edge_2.sid)
                    ss_estimations[(id1, id2)] = estimate
                    



    affected_edges = tuple()    # initially empty tuple

    improved = True
    while improved:
        improved = False

        prev_best_estimate = 0

        best_estimate = 0
        best_op_tuple = None

        iteration_count += 1
        iter_start = time.time()

        # ? re-calculate swap_services for affected_edges from last iteration
        for edge_1 in affected_edges:
            for edge_2 in working.frequency_buckets[edge_1.freq]:
                if edge_1 == edge_2 or edge_2 in affected_edges:
                    # if both edges are affected then they are part of best op from previous iteration
                    continue
                
                estimate, _ = evaluate_operator(0, None, swap_services_operator, undo_swap_services_operator, working, edge_1, edge_2)
                # below is because calling swap(e1, e2) is same as swap(e2, e1)
                id1 = min(edge_1.sid, edge_2.sid)
                id2 = max(edge_1.sid, edge_2.sid)
                ss_estimations[(id1, id2)] = estimate
                        

        # ? - check best estimate for move_service, same as in original phase_2
        for edge in working.demanded_edges:
            no_service_days = list(work_days.difference(edge.service_days))

            for d1 in edge.service_days:
                for d2 in no_service_days:
                    best_estimate, best_op_tuple = evaluate_operator(best_estimate, best_op_tuple, move_service_operator, undo_move_service_operator, working, d1, d2, edge)
                    if best_estimate < prev_best_estimate:
                        affected_edges = (edge,)

        # todo - compare with min ss estimates
        
        ss_min_estimate_val = best_estimate
        for pair, estimate in ss_estimations.items():
            if estimate < ss_min_estimate_val:
                ss_min_estimate_val = estimate
                ss_min_estimate_pair = pair

        # if swap_services has better lowest estimate than move_service estimate
        if ss_min_estimate_val < best_estimate:
            e1_sid, e2_sid = ss_min_estimate_pair
            edge_1 = working.demanded_edges[e1_sid]
            edge_2 = working.demanded_edges[e2_sid]
            op_tuple = (swap_services_operator, undo_swap_services_operator, (working, edge_1, edge_2), {})
            improved_op, best_score = full_evaluate_operator(best_score, working, op_tuple)
            if improved_op:
                improved = True

        if best_op_tuple is not None:
            # regardless of whether above was improving, it's worth a try if this is improving as well after it
            improved_op, best_score = full_evaluate_operator(best_score, working, best_op_tuple)
            if improved_op:
                improved = True


        best_estimate = 0
        best_op_tuple = None


        iter_end = time.time()

        last_iteration_time = iter_end - iter_start
        iteration_avg_time = iteration_avg_time * (iteration_count - 1) / iteration_count + last_iteration_time / iteration_count


        if iter_end - last_report > 600:
            last_report = iter_end
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



    return working, best_score, best_score < original_score

  


def improved_phase_3(working):
    # todo
    pass

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
        current_best_solution, best_score, phase_improving = phase_1(current_best_solution)
        # current_best_solution, best_score, phase_improving = improved_phase_1(current_best_solution)

        # print("Skipped phase 1!")

        p1_end_time = time.time()

        if phase_improving:
            improving = True


        # print("\nSolution after phase 1:\n\n")
        # print(current_best_solution)


        # phase 2 - move services from 1 day to another day and swap service days of edges with same frequency 
        current_best_solution, best_score, phase_improving = phase_2(current_best_solution)
        # current_best_solution, best_score, phase_improving = improved_phase_2(current_best_solution)

        p2_end_time = time.time()

        if phase_improving:
            improving = True

        # phase 3 - improve the routes
        current_best_solution, best_score, phase_improving = phase_3(current_best_solution)
        # current_best_solution, best_score, phase_improving = improved_phase_3(current_best_solution)

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