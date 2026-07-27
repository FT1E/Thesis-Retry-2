
VEHICLE_WEIGHT = 100_000                    # multiply by number of vehicles used for whole sp-carp, ie the minimum num of vehicles needed, ie maximum number of vehicles among days
VEHICLE_OVERLOAD_PENALTY = 400_000        # when a route has total demand or length greater than what vehicle can handle - multiply by number of routes which violate 
EXPECTED_SERVICES_PENALTY = 1_000_000       # multiply by number of edges who have too few or too many services
EXPECTED_SPACING_PENALTY = 500_000        # multiplied by number of spacings which are too tight or too wide
