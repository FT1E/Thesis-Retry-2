
# ? - VEHICLE OVERLOAD PENALTY - adjust it below expected services and spacing penalty
# ? - thought of this -  to get the solution wrt expected services count and the spacing between them, then fix routes later




VEHICLE_WEIGHT = 1_000_000                    # multiply by number of vehicles used for whole sp-carp, ie the minimum num of vehicles needed, ie maximum number of vehicles among days
VEHICLE_OVERLOAD_PENALTY = 2_000_000        # when a route has total demand or length greater than what vehicle can handle - multiply by number of routes which violate 
EXPECTED_SERVICES_PENALTY = 1_000_000       # multiply by number of edges who have too few or too many services
EXPECTED_SPACING_PENALTY = 200_000        # multiplied by number of spacings which are too tight or too wide
# last one is lower since i'm expecting there to be a lot of those violations - at least at the beginning
# todo - may set it higher
