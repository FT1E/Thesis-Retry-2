
import sys
import time
import datetime
import random
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
def two_opt_routes_operator(solution, r1_cutpoint, r2_cutpoint, route_1, route_2):
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


    # TODO - maybe do some checking, cause I'm assuming both routes are non-empty
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


def undo_two_opt_routes_operator(solution, r1_cutpoint, r2_cutpoint, route_1, route_2, undo_info):

    route_cnt = undo_info

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

    day = solution.days[route_1.day]
    
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

def undo_route_move_service_operator(solution, edge_1_id, edge_2_id, route_1, route_2, undo_info = None):
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

    day = solution.days[route_a.day]
    
    # since edges are MOVED FROM route a, it's definetely not empty at this point
    cost_before = route_a.evaluate(day.vehicle) + route_b.evaluate(day.vehicle) + VEHICLE_WEIGHT
    # route b may be empty before move - for undo, but still just to be safe
    cost_before += (len(route_b.targets) > 0) * VEHICLE_WEIGHT

    
    # if some check fails, then op can't be done
    if route_move_service_operator(solution, edge_a12_id + 1, edge_b_id, route_a, route_b) is None:
        return None

    # otherwise all checks are done in above op call
    route_move_service_operator(solution, edge_a12_id, edge_b_id, route_a, route_b)


    # since edges were MOVED TO route b, it's definetely not empty
    cost_after = route_a.evaluate(day.vehicle) + route_b.evaluate(day.vehicle) + VEHICLE_WEIGHT
    # route a may be empty after move
    cost_after += (len(route_a.targets) > 0) * VEHICLE_WEIGHT

    estimate = cost_after - cost_before

    return None, estimate

def undo_route_move_pair_service_operator(solution, edge_a12_id, edge_b_id, route_a, route_b, undo_info = None):
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

# ? returns an index of where a number should be inserted
# ?  used in below method evaluate_operator_topN
# ? assuming list is sorted in ascending order

def binary_insertion(lst, num):
    if len(lst) == 0:
        return 0
    
    begin = 0
    end = len(lst)
    while begin < end:
        mid = (begin + end) // 2
        if num < lst[mid]:
            end = mid
        else:
            begin = mid + 1

    return mid


# save the top N best op tuples
def evaluate_operator_topN(best_estimates, best_ops, op, undo_op, *args, N=5, **kwargs):
    # evaluatethe newly provided op and see if it is part of top5 according to estimate
    
    # best_estimates and best_ops are arrays of length 0 to N
    # for first N candidates in iteration it grows from 0 to N, then it only keeps top N found until then

    res = op(*args, **kwargs)
    if res is None:
        return
    
    undo_info, new_estimate = res

    undo_op(*args, undo_info=undo_info, **kwargs)

    # ? use binary search to check if and where this op should be inserted
    # ? when N is a small number like 5, doing a linear search doesn't hurt time complexity
    # ? but left it as an argument to test stuff
    pos = binary_insertion(best_estimates, new_estimate)
    if pos < N:
        best_estimates.insert(pos, new_estimate)
        op_tuple = (op, undo_op, args, kwargs)
        best_ops.insert(pos, op_tuple)

        if len(best_estimates) > N:
            best_estimates.pop()
            best_ops.pop()

# similar as above but this one keeps all op_tuples
# but when doing full evaluation only pass the top N, corresponding to argument
def evaluate_operator_keepAll(best_estimates, best_ops, op, undo_op, *args, **kwargs):
    # evaluatethe newly provided op and see if it is part of top5 according to estimate
    
    # best_estimates and best_ops are arrays of length 0 to N
    # for first N candidates in iteration it grows from 0 to N, then it only keeps top N found until then

    res = op(*args, **kwargs)
    if res is None:
        return
    
    undo_info, new_estimate = res

    undo_op(*args, undo_info=undo_info, **kwargs)

    pos = binary_insertion(best_estimates, new_estimate)
    best_estimates.insert(pos, new_estimate)
    op_tuple = (op, undo_op, args, kwargs)
    best_ops.insert(pos, op_tuple)
    


def full_evaluate_topN_best_estimate(best_ops, solution):
    # evaluate the best_ops in order of best_estimates and apply the first one which actually improves
    # return False if no op_tuple actually improves solution score
    # else true and apply the first one which improves
    # op_tuples are sorted by best estimation
    # second part of return result is score of new (or old if not improving) solution
    
    before_score = solution.evaluate()

    for op_tuple in best_ops:
        op, undo_op, args, kwargs = op_tuple
        undo_info, _ = op(*args, **kwargs)
        score = solution.evaluate()
        
        if score < before_score:
            return True, score, op_tuple
        
        # else undo_op
        undo_op(*args, undo_info = undo_info, **kwargs)

    return False, before_score, None

def full_evaluate_topN_best_full_eval(best_ops, solution):
    # evaluate all the best_ops and apply the best one
    # return result is False if no op_tuple actually improves solution score
    # else it's true and best op is applied
    # second part of return result is score of new (or old if not improving) solution
    # third part of return result is the min op tuple if any improved
    # in case some arguments are needed

    # baseline is the solution score before applying any op
    min_score = solution.evaluate()
    min_op = None


    for op_tuple in best_ops:
        op, undo_op, args, kwargs = op_tuple
        undo_info, _ = op(*args, **kwargs)
        score = solution.evaluate()
        
        if score < min_score:
            min_score = score
            min_op = op_tuple

        undo_op(*args, undo_info = undo_info, **kwargs)

    # apply best op if any actually improves the score
    improved = False
    if min_op is not None:
        op, _, args, kwargs = min_op
        op(*args, **kwargs)
        
        improved = True

    return improved, min_score, min_op

# below function for just applying the best operator
def apply_operator(operator, *args, **kwargs):
    # apply the operator with given args and kwargs
    # return the undo result of the operator

    res = operator(*args, **kwargs)
    return res
# END UTIL METHODS


# PHASE METHODS


# ? PHASE 1 - add_service_operator and remove_service_operator
def phase_1(working, N=5, best_full_eval=True):
    # ? N = how many best op tuples based on estimation to consider
    # ? best_full_eval = whether to find
    # ?    - False - the first improving op tuple among the top N sorted by best estimate
    # ?    - True  - or to apply best one based on best full eval
     
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
        # ? saving best N tuples based on estimation
        best_estimates = []
        best_op_tuples = []

        

        # adding a service to edges with too little services
        under_satisfied_edges = working.get_under_satisfied_edges()
        for edge in under_satisfied_edges:
            no_service_days = work_days.difference(edge.service_days)
            for day in no_service_days:
                evaluate_operator_topN(best_estimates, best_op_tuples, add_service_operator, undo_add_service_operator, working, day, edge, N = N)
            

        # removing a service of edges with too many services
        over_satisfied_edges = working.get_over_satisfied_edges()
        for edge in over_satisfied_edges:
            for day in edge.service_days:
                evaluate_operator_topN(best_estimates, best_op_tuples, remove_service_operator, undo_remove_service_operator, working, day, edge, N = N)
                

        # ? note solution is part of args
        if best_full_eval:
            improved, best_score, _ = full_evaluate_topN_best_full_eval(best_op_tuples, working)
        else:
            improved, best_score, _ = full_evaluate_topN_best_estimate(best_op_tuples, working)


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
def phase_2(working, N=5, best_full_eval=True):
    original_score = working.evaluate()
    best_score = original_score

    best_op_tuple = None
    best_score = original_score
    
    work_days = set(working.get_work_days())
    
    iteration_count = 0
    iteration_avg_time = 0

    last_report = time.time() - 600

    improved = True
    while improved:
        improved = False

        iteration_count += 1

        iter_start = time.time()

        # reset values
        # ? saving best N tuples based on estimation
        best_op_tuples = []
        best_estimates = []

        # move_service operator
        for edge in working.demanded_edges:
            no_service_days = list(work_days.difference(edge.service_days))

            for d1 in edge.service_days:
                for d2 in no_service_days:
                    evaluate_operator_topN(best_estimates, best_op_tuples, move_service_operator, undo_move_service_operator, working, d1, d2, edge, N=N)



        # swap_services operator
        for bucket in working.frequency_buckets.values():
            
            for i in range(len(bucket)):
                edge_1 = bucket[i]

                for j in range(i+1, len(bucket)):
                    edge_2 = bucket[j]
                    evaluate_operator_topN(best_estimates, best_op_tuples, swap_services_operator, undo_swap_services_operator, working, edge_1, edge_2, N=N)

                    

        # ? note solution is part of args
        if best_full_eval:
            improved, best_score, _ = full_evaluate_topN_best_full_eval(best_op_tuples, working)
        else:
            improved, best_score, _ = full_evaluate_topN_best_estimate(best_op_tuples, working)


            
        
        # else improved should be false and loop will exit


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


# ? PHASE 2 - move_service_operator and swap_services_operator
def phase_2_only_swap_services(working, N=5, best_full_eval=True):
    original_score = working.evaluate()
    best_score = original_score

    best_score = original_score
    
    
    iteration_count = 0
    iteration_avg_time = 0

    last_report = time.time() - 600

    improved = True
    while improved:
        improved = False

        iteration_count += 1

        iter_start = time.time()

        # reset values
        # ? saving best N tuples based on estimation
        best_op_tuples = []
        best_estimates = []


        # swap_services operator
        for bucket in working.frequency_buckets.values():
            
            for i in range(len(bucket)):
                edge_1 = bucket[i]

                for j in range(i+1, len(bucket)):
                    edge_2 = bucket[j]
                    evaluate_operator_topN(best_estimates, best_op_tuples, swap_services_operator, undo_swap_services_operator, working, edge_1, edge_2, N=N)

                    

        # ? note solution is part of args
        if best_full_eval:
            improved, best_score, _ = full_evaluate_topN_best_full_eval(best_op_tuples, working)
        else:
            improved, best_score, _ = full_evaluate_topN_best_estimate(best_op_tuples, working)


            
        
        # else improved should be false and loop will exit


        iter_end = time.time()

        last_iteration_time = iter_end - iter_start
        iteration_avg_time = iteration_avg_time * (iteration_count - 1) / iteration_count + last_iteration_time / iteration_count

        if iter_end - last_report > 600:
            last_report = iter_end
            print(f"Phase 2.5 only swap services mid-report:")
            print(f"Iteration count: {iteration_count}")
            print(f"Last iteration time: {last_iteration_time}")
            print(f"Average iteration time: {iteration_avg_time}")
            print(f"Current score: {best_score}")
            
    print("Phase 2.5 only swap services ended!")
    print("Phase 2.5 only swap services Report:")
    print(f"Iteration count: {iteration_count}")
    print(f"Last iteration time: {last_iteration_time}")
    print(f"Average iteration time: {iteration_avg_time}")
    print(f"Current score: {best_score}")



    return working, best_score, best_score < original_score


# ? PHASE 4 - route operators, two_opt, move (single) and move_pair, best move applied for each day
def phase_4(working, N=5, best_full_eval=True):
    original_score = working.evaluate()

    best_score = original_score

    # 1 iteration affects one day, otherwise iter_count == number of work days
    # counting like this bcs of better locality and bcs some days require extra iterations others require less iterations
    iteration_count = 0
    iteration_avg_time = 0

    
    work_days = working.get_work_days()

    # better locality if iterating on each day repeatedly as long as there is an improvement, then continue on to next day

    # ? iterate in the same day as long as there is an improvement, then move on to the next  one
    for day in work_days:

        improved = True
        while improved:
            improved = False

            iteration_count += 1

            iter_start = time.time()

            # reset values
            # ? saving best N tuples based on estimation
            best_op_tuples = []
            best_estimates = []


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
                                evaluate_operator_topN(best_estimates, best_op_tuples, two_opt_routes_operator, undo_two_opt_routes_operator, working, r1_pos, r2_pos, route1, route2, N=N)
                            
                            evaluate_operator_topN(best_estimates, best_op_tuples, route_move_service_operator, undo_route_move_service_operator, working, r1_pos, r2_pos, route1, route2, N=N)

                            if can_do_pair_move:
                                evaluate_operator_topN(best_estimates, best_op_tuples, route_move_pair_service_operator, undo_route_move_pair_service_operator, working, r1_pos, r2_pos, route1, route2, N=N)
            
            
            # ? note solution is part of args
            if best_full_eval:
                improved, best_score, _ = full_evaluate_topN_best_full_eval(best_op_tuples, working)
            else:
                improved, best_score, _ = full_evaluate_topN_best_estimate(best_op_tuples, working)
   

            iter_end = time.time()

            last_iteration_time = iter_end - iter_start
            iteration_avg_time = iteration_avg_time * (iteration_count - 1) / iteration_count + last_iteration_time / iteration_count

            if iteration_count % 10 == 1:
                print(f"Phase 4 (routing ops) mid-report:")
                print(f"Current day: {day}")
                print(f"Iteration count: {iteration_count}")
                print(f"Last iteration time: {last_iteration_time}")
                print(f"Average iteration time: {iteration_avg_time}")
                print(f"Current score: {best_score}\n")


        print(f"\nPhase 4 (routing ops) day {day} ended!")
        print("Phase 4 (routing ops) day report:")
        print(f"Current Iteration count: {iteration_count}")
        print(f"Last iteration time: {last_iteration_time}")
        print(f"Average iteration time: {iteration_avg_time}")
        print(f"Current score: {best_score}\n")

    print("\nPhase 4 (routing ops) ended!")
    print("Phase 4 (routing ops) Report:")
    print(f"Iteration count: {iteration_count}")
    print(f"Last iteration time: {last_iteration_time}")
    print(f"Average iteration time: {iteration_avg_time}")
    print(f"Current score: {best_score}")

    return working, best_score, best_score < original_score






# END PHASE METHODS



# PHASE METHODS - IMPROVED VERSIONS

# ? IMPROVED PHASE 1 - add_service_operator and remove_service_operator
# ? - apply best operation per edge, not for whole solution at each iteration
def improved_phase_1(working, N=5, best_full_eval=True):
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
        
            best_op_tuples = []
            best_estimates = []

            no_service_days = work_days.difference(edge.service_days)
            for day in no_service_days:
                evaluate_operator_topN(best_estimates, best_op_tuples, add_service_operator, undo_add_service_operator, working, day, edge, N=N)
                
        
            if best_full_eval:
                improved_edge, best_score, _ = full_evaluate_topN_best_full_eval(best_op_tuples, working)
            else:
                improved_edge, best_score, _ = full_evaluate_topN_best_estimate(best_op_tuples, working)

            if improved_edge:
                improved = True

        # removing a service of edges with too many services
        over_satisfied_edges = working.get_over_satisfied_edges()
        for edge in over_satisfied_edges:
            
            best_op_tuples = []
            best_estimates = []

            for day in edge.service_days:
                evaluate_operator_topN(best_estimates, best_op_tuples, remove_service_operator, undo_remove_service_operator, working, day, edge, N=N)

            if best_full_eval:
                improved_edge, best_score, _ = full_evaluate_topN_best_full_eval(best_op_tuples, working)
            else:
                improved_edge, best_score, _ = full_evaluate_topN_best_estimate(best_op_tuples, working)

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

# ? PHASE 2 - move_service_operator
def improved_phase_2(working, N=5, best_full_eval=True):
    original_score = working.evaluate()

    best_score = original_score
    
    work_days = set(working.get_work_days())
    
    iteration_count = 0
    iteration_avg_time = 0
    last_report = time.time() - 600


    # this can be a list here since all edge.sid maps to position in solution.demanded_edges
    best_ops = [None] * len(working.demanded_edges)
    # best_op[edge.sid] = best op_tuple for this edge with estimation at [0]

    

    # ? initial calculations - consider a almost all candidate space

    # ? - check best estimate for move_service, same as in original phase_2
    # ? - only ignore moving to obvious tight spacings - within less than (freq // 2) days from another service
    for edge in working.demanded_edges:
        
        edge_best_op_tuples = []
        best_estimations = []

        tight_range = int(edge.freq // 2)

        for d1 in edge.service_days:

            # 1. estimate possible candidates for moving FROM d1
            move_to_ignore_candidates = set()
            for day in edge.service_days:
                if day == d1:
                    continue
                for i in range(-tight_range, tight_range):
                    move_to_ignore_candidates.add(day + i)

            move_to_actual_candidates = work_days.difference(move_to_ignore_candidates)
            
            # 2. perform attempts on the candidate list
            for d2 in move_to_actual_candidates:        
                evaluate_operator_topN(best_estimations, edge_best_op_tuples, move_service_operator, undo_move_service_operator, working, d1, d2, edge, N=5)

        # now we have the top 5 move_service op for this edge edge
        best_ops[edge.sid] = (best_estimations, edge_best_op_tuples)

    improved = True
    while improved:
        improved = False

        # ? resetting values
        # ? for finding best estimates of move_service operator
        best_estimates = []
        best_op_tuples = []

        iteration_count += 1
        iter_start = time.time()

        # ? - sort best_ops for each edge
        for edge_best_estimations, edge_best_op_tuples in best_ops:
            for i in range(len(edge_best_estimations)):
                estimation = edge_best_estimations[i]
                op_tuple = edge_best_op_tuples[i]
                pos = binary_insertion(best_estimates, estimation)
                if pos < N:
                    best_estimates.insert(pos, estimation)
                    best_op_tuples.insert(pos, op_tuple)

        
        if best_full_eval:
            improved, best_score, min_op_tuple = full_evaluate_topN_best_full_eval(best_op_tuples, working)
        else:
            improved, best_score, min_op_tuple = full_evaluate_topN_best_estimate(best_op_tuples, working)

        # ? keep a list of best 5 ops for each edge - memory space is O(n) = 5*n with n being the number of edges in solution
        # ? recalculate ops for edges which have as d1 or d2 argument a day which was part of previous best op
        # ? basically if top5 ops for an edge don't contain the days of prev best op, then only compare them with re-calculation for the affected days
        # ? else gotta re-calculate all candidates to fill the top 5 ops list
        
        if min_op_tuple is not None:
            # (op, undo_op, args, kwargs)
            args = min_op_tuple[2]
            # (working, d1, d2, edge)
            affected_days = args[1:3]

            recalculate = [False] * len(working.demanded_edges)

            # find edges which have one of these days in their best op args
            for edge in working.demanded_edges:
                _, edge_best_op_tuples = best_ops[edge.sid]
                for op_tuple in edge_best_op_tuples:
                    args = op_tuple[2]
                    d1 = args[1]
                    d2 = args[2]
                    if d1 in affected_days or d2 in affected_days:
                        recalculate[edge.sid] = True
                        break
            
            for i in range(len(recalculate)):
                edge = working.demanded_edges[i]
                if not recalculate[i]:
                    # ? - only compare with re-calculations of affected days using evaluate_operator_topN on previous list
                    # take the top 5 found from previous iterations
                    best_estimations, edge_best_op_tuples = best_ops[edge.sid]
                else:
                    # else start the list from scratch
                    edge_best_op_tuples = []
                    best_estimations = []
                    # compare them with re-calculations of affected days

                
                # re-calculation - same as initial calculations
                # using tight_range to skip moves which are HIGHLY LIKELY not optimal    

                tight_range = int(edge.freq // 2)

                for d1 in edge.service_days:

                    # 1. estimate possible candidates for moving FROM d1
                    move_to_ignore_candidates = set()
                    for day in edge.service_days:
                        if day == d1:
                            continue
                        for i in range(-tight_range, tight_range):
                            move_to_ignore_candidates.add(day + i)

                    move_to_actual_candidates = work_days.difference(move_to_ignore_candidates)
                    
                    # 2. perform attempts on the candidate list
                    for d2 in move_to_actual_candidates:
                        if not recalculate[i] and d1 not in affected_days and d2 not in affected_days:
                            # ? for one which didn't have the affected days in tops
                            # ? only try the op if at least one of the days was affected by previous best op
                            continue
                        evaluate_operator_topN(best_estimations, edge_best_op_tuples, move_service_operator, undo_move_service_operator, working, d1, d2, edge, N=5)

                    # now we have the top 5 move_service op for this edge edge
                    best_ops[edge.sid] = (best_estimations, edge_best_op_tuples)


        iter_end = time.time()

        last_iteration_time = iter_end - iter_start
        iteration_avg_time = iteration_avg_time * (iteration_count - 1) / iteration_count + last_iteration_time / iteration_count


        if iter_end - last_report > 300:
            last_report = iter_end
            print(f"Phase 2 (only move_services) mid-report:")
            print(f"Iteration count: {iteration_count}")
            print(f"Last iteration time: {last_iteration_time}")
            print(f"Average iteration time: {iteration_avg_time}")
            print(f"Current score: {best_score}")
            
    print("Phase 2 (only move_services) ended!")
    print("Phase 2 (only move_services) Report:")
    print(f"Iteration count: {iteration_count}")
    print(f"Last iteration time: {last_iteration_time}")
    print(f"Average iteration time: {iteration_avg_time}")
    print(f"Current score: {best_score}")



    return working, best_score, best_score < original_score

  
# ? different from above in that it keeps iterating over one edge as long as it can find improvement
# ? when it can't it goes on to the next edge
# ? basically the goal is to focus on one edge at a time
# ? similar to improved_phase_1, apply best op per edge, not per solution
# ? or rather more like phase 4, best op per day, and keep iterating over the same day
# ? since some edges may converge to optimality sooner than later
def improved_phase_2_per_edge(working, N=5, best_full_eval=True):
    original_score = working.evaluate()

    best_score = original_score
    
    work_days = set(working.get_work_days())
    
    iteration_count = 0
    iteration_avg_time = 0
    last_report = time.time() - 600


    # best_op[edge.sid] = best op_tuple for this edge with estimation at [0]


    # ? keep finding best op for this edge
    # ? as long as an improvement can be found
    # ? then move on to the next edge

    # ? option 2 - find best op for edge, apply it

    improved = True
    while improved:
        improved = False
        iteration_count += 1
        iter_start = time.time()
    
        for edge in working.demanded_edges:


            # ? resetting values
            # ? for finding best estimates of move_service operator
            best_estimates = []
            best_op_tuples = []


            tight_range = int(edge.freq // 2)

            for d1 in edge.service_days:

                # 1. estimate possible candidates for moving FROM d1
                move_to_ignore_candidates = set()
                for day in edge.service_days:
                    if day == d1:
                        continue
                    for i in range(-tight_range, tight_range):
                        move_to_ignore_candidates.add(day + i)

                move_to_actual_candidates = work_days.difference(move_to_ignore_candidates)
                
                # 2. perform attempts on the candidate list
                for d2 in move_to_actual_candidates:        
                    evaluate_operator_topN(best_estimates, best_op_tuples, move_service_operator, undo_move_service_operator, working, d1, d2, edge, N=N)

            # todo - maybe apply similar estimation tricks
            # todo - maybe save all candidates for a single edge
            # todo - according to my calcs that is at most 3600, without using the tight_range limitation of candidates, which makes it less

            
            if best_full_eval:
                improved_edge, best_score, _ = full_evaluate_topN_best_full_eval(best_op_tuples, working)
            else:
                improved_edge, best_score, _ = full_evaluate_topN_best_estimate(best_op_tuples, working)

            if improved_edge:
                improved = True



        iter_end = time.time()

        last_iteration_time = iter_end - iter_start
        iteration_avg_time = iteration_avg_time * (iteration_count - 1) / iteration_count + last_iteration_time / iteration_count


        if iter_end - last_report > 300:
            last_report = iter_end
            print(f"Phase 2 (only move_services) mid-report:")
            print(f"Iteration count: {iteration_count}")
            print(f"Last iteration time: {last_iteration_time}")
            print(f"Average iteration time: {iteration_avg_time}")
            print(f"Current score: {best_score}")
            
    print("Phase 2 (only move_services) ended!")
    print("Phase 2 (only move_services) Report:")
    print(f"Iteration count: {iteration_count}")
    print(f"Last iteration time: {last_iteration_time}")
    print(f"Average iteration time: {iteration_avg_time}")
    print(f"Current score: {best_score}")



    return working, best_score, best_score < original_score



# ? previously phase_2 was using move_service and swap_service
# ? now improved_phase_2 uses move_service (more efficiently) and improved_phase_3 uses swap_service (also more efficiently)

# ? apply swap_services operator with fewer candidates
# ? attempt only 1 swap with an edge with some given service days pattern
# ? some edges may have the same service day pattern
# ? every edge attempts a swap with each unique pattern once,
# ? it's useless to try to attempt swap with 2 edges who have the same service day pattern
def improved_phase_3(working, N=5, best_full_eval=True):
    
    original_score = working.evaluate()

    best_score = original_score
    
    
    iteration_count = 0
    iteration_avg_time = 0
    last_report = time.time() - 600

    affected_edges = tuple()    # edges which were picked to be the best from last iteration
    # estimations are re-calculated only for pairs involving one of these edges
    # both edges which form the pair formed the best improvement in last iteration and for them it isn't re-calculated

    # calculate initial estimations involving all pairs
    best_estimates = []
    best_op_tuples = []


    patterns = dict()
    # ? patterns[freq] = list of all unique service_day paterns used for edges with this frequence
    
    edge_patterns = [-1] * len(working.demanded_edges)
    # ? edge_patterns[sid] == i only if edge with this sid has service_days == patterns[freq][i]
    
    # take 1 edge to be representative of all other edges with the same service pattern
    # probably useless if few edges have same pattern, but still saves some time
    for freq, bucket in working.frequency_buckets.items():
        patterns[freq] = []

        for edge in bucket:
            if edge.service_days not in patterns[freq]:
                patterns[freq].append(edge.service_days)
                edge_patterns[edge.sid] = len(patterns[freq]) - 1       # since it's the last one
            else:
                pos = patterns[freq].index(edge.service_days)
                edge_patterns[edge.sid] = pos

    improved = True
    while improved:
        improved = False

        # ? resetting values
        # ? for finding best estimates of move_service operator
        best_estimates = []
        best_op_tuples = []

        iteration_count += 1
        iter_start = time.time()


        for freq, bucket in working.frequency_buckets.items():

            candidates = []
            patterns_used = []
            for edge_2 in bucket:
                if edge_patterns[edge_2.sid] not in patterns_used:
                    candidates.append(edge_2)
                    patterns_used.append(edge_patterns[edge_2.sid])
                    if len(patterns_used) == len(patterns[freq]):
                        break
            for edge_1 in bucket:                

                for edge_2 in candidates:
                    # try to perform a swap only with 1 candidate who has service_days == patterns[freq][i]
                    evaluate_operator_topN(best_estimates, best_op_tuples, swap_services_operator, undo_swap_services_operator, working, N=N, edge_1 = edge_1, edge_2 = edge_2)

        


        if best_full_eval:
            improved, best_score, min_op_tuple = full_evaluate_topN_best_full_eval(best_op_tuples, working)
        else:
            improved, best_score, min_op_tuple = full_evaluate_topN_best_estimate(best_op_tuples, working)

        if min_op_tuple is not None:
            # (op, undo_op, args, kwargs)
            kwargs = min_op_tuple[3]

            edge_1, edge_2 = kwargs.values()

            # - swap their edge patterns value
            edge_patterns[edge_1.sid], edge_patterns[edge_2.sid] = edge_patterns[edge_2.sid], edge_patterns[edge_1.sid]

        iter_end = time.time()

        last_iteration_time = iter_end - iter_start
        iteration_avg_time = iteration_avg_time * (iteration_count - 1) / iteration_count + last_iteration_time / iteration_count


        if iter_end - last_report > 600:
            last_report = iter_end
            print(f"Phase 3 (using only swap_services) mid-report:")
            print(f"Iteration count: {iteration_count}")
            print(f"Last iteration time: {last_iteration_time}")
            print(f"Average iteration time: {iteration_avg_time}")
            print(f"Current score: {best_score}")
            
    print("Phase 3 (using only swap_services) ended!")
    print("Phase 3 (using only swap_services) Report:")
    print(f"Iteration count: {iteration_count}")
    print(f"Last iteration time: {last_iteration_time}")
    print(f"Average iteration time: {iteration_avg_time}")
    print(f"Current score: {best_score}")



    return working, best_score, best_score < original_score


# ? PHASE 4 - route operators, two_opt, move (single) and move_pair, best move applied for each day
# ? - initial calculation and then re-calculate only using the affected routes in while loop
# ? - remove from best ops the ones which use arguments which need to be re-calculated or have route which doesn't exist
# ? - recalculate
# ? - don't keep all op_tuples, only keep the best op_tuple for each pair of routes
# ? - once a route changes re-calculate the best op_tuple for every pair involving at least one of those two routes
def improved_phase_4(working, N=5, best_full_eval=True):
    original_score = working.evaluate()

    best_score = original_score

    # 1 iteration affects one day, otherwise iter_count == number of work days
    # counting like this bcs of better locality and bcs some days require extra iterations others require less iterations
    iteration_count = 0
    iteration_avg_time = 0

    
    work_days = working.get_work_days()

    # better locality if iterating on each day repeatedly as long as there is an improvement, then continue on to next day
    
    # ? iterate in the same day as long as there is an improvement, then move on to the next  one
    for day in work_days:


        # ? calculate initial estimates
        # ? save top1 for each route pair in a day

        routes = working.days[day].routes.copy()

        best_ops  = dict()      # stores the best ops per pair
        # uses route ids as keys, 
        # (id1, id2) - ids of route1 and route2, 
        # applying best op which uses those routes as arguments 
        # re-calculate only if one of those routes was modified in previous iteration

        for i, route_1 in enumerate(routes):


            for j in range(i+1, len(routes)):
                # reset values when moving to next pair of routes
                # ? saving top 1 tuple based on estimation
                # ? it's a list so I don't have to create another method
                best_op_tuple = None
                best_estimate = float('inf')

                route_2 = routes[j]
                for r1_pos in range(len(route_1.targets)):

                    for r2_pos in range(len(route_2.targets)):

                        best_estimate, best_op_tuple = evaluate_operator(best_estimate, best_op_tuple, two_opt_routes_operator, undo_two_opt_routes_operator, working, r1_pos, r2_pos, route_1 = route_1, route_2 = route_2)
                        
                        # perform route_move_single and route_move_pair from both directions
                        # ? note that this loop loops through every unordered pair of routes unlike the one in phase_4 at the point of writing this comment
                        best_estimate, best_op_tuple = evaluate_operator(best_estimate, best_op_tuple, route_move_service_operator, undo_route_move_service_operator, working, r1_pos, r2_pos, route_1 = route_1, route_2 = route_2)
                        best_estimate, best_op_tuple = evaluate_operator(best_estimate, best_op_tuple, route_move_service_operator, undo_route_move_service_operator, working, r2_pos, r1_pos, route_1 = route_2, route_2 = route_1)

                        if r1_pos + 1 < len(route_1.targets):
                            best_estimate, best_op_tuple = evaluate_operator(best_estimate, best_op_tuple, route_move_pair_service_operator, undo_route_move_pair_service_operator, working, r1_pos, r2_pos, route_a = route_1, route_b = route_2)
                        
                        if r2_pos + 1 < len(route_2.targets):
                            best_estimate, best_op_tuple = evaluate_operator(best_estimate, best_op_tuple, route_move_pair_service_operator, undo_route_move_pair_service_operator, working, r2_pos, r1_pos, route_a = route_2, route_b = route_1)

                # best_op_tuples holds the single best op_tuple based on estimation
                # and estimation is worth more here since it's more accurate
                
                # ? if might be redundant, but better be safe than sorry
                if best_op_tuple is not None:
                    id1 = min(route_1.rid, route_2.rid)
                    id2 = max(route_1.rid, route_2.rid)
                    # create a new tuple using the estimate
                    # now of the form (estimate, op, undo_op, args, kwargs)
                    # ? doing this because estimate is more accurate here, meaning it's more useful
                    best_ops[(id1, id2)] = (best_estimate, best_op_tuple)


        improved = True
        while improved:
            improved = False

            iteration_count += 1

            iter_start = time.time()


            best_estimates = []
            best_op_tuples = []

            # ? extract the top N values from the dictionary
            for op_est_tuple in best_ops.values():
                estimation, op_tuple = op_est_tuple
                pos = binary_insertion(best_estimates, estimation)
                if pos < N:
                    best_estimates.insert(pos, estimation)
                    best_op_tuples.insert(pos, op_tuple)
                    if len(best_estimates) > N:
                        best_estimates.pop()
                        best_op_tuples.pop()

            # ? note solution is part of args
            # only pass the top N evaluations
            if best_full_eval:
                improved, best_score, min_op_tuple = full_evaluate_topN_best_full_eval(best_op_tuples, working)
            else:
                improved, best_score, min_op_tuple = full_evaluate_topN_best_estimate(best_op_tuples, working)
   
            # ? - re-calculate only for routes involving the routes from previous best op
            if min_op_tuple is not None:
                # op_tuple == (op, undo_op, args, kwargs)
                kwargs = min_op_tuple[3]
                affected_route_1, affected_route_2 = kwargs.values()

                r1_id = affected_route_1.rid
                r2_id = affected_route_2.rid
                # re-calculate best estimate for pairs having at least 1 route with this rid
                routes = working.days[day].routes.copy()

                # remove from dictionary these values
                for pair_ids in list(best_ops.keys()):
                    if pair_ids[0] == r1_id or pair_ids[0] == r2_id or pair_ids[1] == r1_id or pair_ids[1] == r2_id:
                        del best_ops[pair_ids]

                op = min_op_tuple[0]
                if op is two_opt_routes_operator:
                    # if improving op was two-opt
                    # then the routes for which re-calculation needs to be done are the new routes
                    # not actually a re-calculation, but first time calculation
                    recalc_1_id = routes[-1].rid
                    if len(routes) > 1:
                        recalc_2_id = routes[-2].rid
                else:
                    # else the routes are the arguments in route_move single/double
                    # if one of them was left empty as a result, it won't be in Day.routes
                    recalc_1_id = r1_id
                    recalc_2_id = r2_id

                # ? the pair (route_1, route_2) which was part of previous best_op is evaluated twice but it's not that big of an issue
                # ? i mean this gets from O(n^2) to O(n) with n being the number of routes in the day
                for route_1 in routes:
                    if route_1.rid != recalc_1_id and route_1.rid != recalc_2_id:
                        continue

                    for route_2 in routes:
                        if route_1.rid == route_2.rid:
                            # since operators will return None and not do any work might as well skip them
                            continue

                        # reset values when moving to next pair of routes
                        # ? saving top 1 tuple based on estimation
                        best_op_tuple = None
                        best_estimate = float('inf')
                        
                        for r1_pos in range(len(route_1.targets)):

                            for r2_pos in range(len(route_2.targets)):

                                best_estimate, best_op_tuple = evaluate_operator(best_estimate, best_op_tuple, two_opt_routes_operator, undo_two_opt_routes_operator, working, r1_pos, r2_pos, route_1 = route_1, route_2 = route_2)
                                
                                # perform route_move_single and route_move_pair from both directions
                                # ? note that this loop loops through every unordered pair of routes unlike the one in phase_4 at the point of writing this comment
                                best_estimate, best_op_tuple = evaluate_operator(best_estimate, best_op_tuple, route_move_service_operator, undo_route_move_service_operator, working, r1_pos, r2_pos, route_1 = route_1, route_2 = route_2)
                                best_estimate, best_op_tuple = evaluate_operator(best_estimate, best_op_tuple, route_move_service_operator, undo_route_move_service_operator, working, r2_pos, r1_pos, route_1 = route_2, route_2 = route_1)

                                if r1_pos + 1 < len(route_1.targets):
                                    best_estimate, best_op_tuple = evaluate_operator(best_estimate, best_op_tuple, route_move_pair_service_operator, undo_route_move_pair_service_operator, working, r1_pos, r2_pos, route_a = route_1, route_b = route_2)
                                
                                if r2_pos + 1 < len(route_2.targets):
                                    best_estimate, best_op_tuple = evaluate_operator(best_estimate, best_op_tuple, route_move_pair_service_operator, undo_route_move_pair_service_operator, working, r2_pos, r1_pos, route_a = route_2, route_b = route_1)

                        # best_op_tuples holds the single best op_tuple based on estimation
                        # and estimation is worth more here since it's more accurate

                        # ? if might be redundant, but better be safe than sorry
                        if best_op_tuple is not None:
                            id1 = min(route_1.rid, route_2.rid)
                            id2 = max(route_1.rid, route_2.rid)
                            best_ops[(id1, id2)] = (best_estimate, best_op_tuple)



            
            # if min_op_tuple is None then improved is False and will exit

            iter_end = time.time()

            last_iteration_time = iter_end - iter_start
            iteration_avg_time = iteration_avg_time * (iteration_count - 1) / iteration_count + last_iteration_time / iteration_count

            if iteration_count % 10 == 1:
                print(f"Phase 4 (routing operators) mid-report:")
                print(f"Current day: {day}")
                print(f"Iteration count: {iteration_count}")
                print(f"Last iteration time: {last_iteration_time}")
                print(f"Average iteration time: {iteration_avg_time}")
                print(f"Current score: {best_score}\n")


        print(f"\nPhase 4 (routing operators) day {day} ended!")
        print("Phase 4 (routing operators) day report:")
        print(f"Current Iteration count: {iteration_count}")
        print(f"Last iteration time: {last_iteration_time}")
        print(f"Average iteration time: {iteration_avg_time}")
        print(f"Current score: {best_score}\n")

    print("\nPhase 4 (routing operators) ended!")
    print("Phase 4 (routing operators) Report:")
    print(f"Iteration count: {iteration_count}")
    print(f"Last iteration time: {last_iteration_time}")
    print(f"Average iteration time: {iteration_avg_time}")
    print(f"Current score: {best_score}")

    return working, best_score, best_score < original_score


# END PHASE METHODS - IMPROVED VERSIONS


# RUN METHOD
# ? topN = how many top operation candidates to consider, best ordered by estimation
# ? best_full_eval - whether to pick the best among top N based on full evaluation or best estimation
def run(solution, topN = 5, best_full_eval = True):

     
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
        # current_best_solution, best_score, phase_improving = phase_1(current_best_solution, N=N, best_full_eval = best_full_eval)
        current_best_solution, best_score, phase_improving = improved_phase_1(current_best_solution, N=topN, best_full_eval = best_full_eval)



        if phase_improving:
            improving = True


        # print("\nSolution after phase 1:\n\n")
        # print(current_best_solution)


        # phase 2 - move services from 1 day to another day 
        # current_best_solution, best_score, phase_improving = phase_2(current_best_solution, N=topN, best_full_eval = best_full_eval)
        current_best_solution, best_score, phase_improving = improved_phase_2(current_best_solution, N=topN, best_full_eval = best_full_eval)
        # current_best_solution, best_score, phase_improving = improved_phase_2_per_edge(current_best_solution, N=topN, best_full_eval = best_full_eval)

        if phase_improving:
            improving = True

        # todo - again move_service phase but only trying moves from days with too many routes to days with too little routes
        
        # phase 3 - swap service days of edges with same frequency 
        current_best_solution, best_score, phase_improving = improved_phase_3(current_best_solution, N=topN, best_full_eval = best_full_eval)

        if phase_improving:
            improving = True


        # phase 4 - improve the routes
        # current_best_solution, best_score, phase_improving = phase_4(current_best_solution, N=topN, best_full_eval = best_full_eval)
        current_best_solution, best_score, phase_improving = improved_phase_4(current_best_solution, N=topN, best_full_eval = best_full_eval)

        if phase_improving:
            improving = True

        iteration_end_time = time.time()
        

        iteration_time_taken = iteration_end_time - iteration_start_time
        average_iteration_time = average_iteration_time * (iteration_count - 1) / iteration_count + iteration_time_taken / iteration_count

        print(f"Local search report:")
        print(f"Iteration count: {iteration_count} iterations")
        print(f"Last iteration time: {iteration_time_taken} seconds")
        print(f"Iteration average time: {average_iteration_time} seconds")
        print(f"Current score: {best_score}")

        if iteration_count == 1:
            print("\nSolution after going through each phase once:\n\n")
            print(current_best_solution)
            print('\n\n')
        
    print(f"Local search ended after {iteration_count} iterations.")
    print(f"Last iteration time: {iteration_time_taken} seconds")
    print(f"Iteration average time: {average_iteration_time} seconds")
    print(f"Original score: {original_score}")
    print(f"Current score: {best_score}")

    return best_score, current_best_solution


# END RUN METHOD