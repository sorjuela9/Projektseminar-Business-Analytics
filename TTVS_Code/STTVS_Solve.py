import pulp
import pandas as pd
from SeniorTTVS import SeniorTTVS

class STTVS_Solve:

    def __init__(self, sttvs):
        self.__sttvs = sttvs
        self.__model = pulp.LpProblem("STTVS", pulp.LpMinimize)
        

    def generateVariables(self):
        fleet = self.__sttvs.getFleet()  # Lade die Fahrzeugflotte
        directions = self.__sttvs.getDirections()  # Lade die Fahrtrichtungen
    
        # Binary variable x_t: 1 if trip t is covered, 0 otherwise
        self.__x = {
            trip.getID(): pulp.LpVariable(f"x_{trip.getID()}", cat="Binary") 
            for d in directions for trip in d.getTrips()
        }
    
        # Binary variable y_v: 1 if vehicle v is used, 0 otherwise
        self.__y = {
            vehicle.getID(): pulp.LpVariable(f"y_{vehicle.getID()}", cat="Binary") 
            for vehicle in fleet
        }
    
        # Binary variable z_t_v: 1 if trip t is assigned to vehicle v, 0 otherwise
        self.__z = {
            (trip.getID(), vehicle.getID()): pulp.LpVariable(f"z_{trip.getID()}_{vehicle.getID()}", cat="Binary")
            for d in directions for trip in d.getTrips()
            for vehicle in fleet
        }
    
        # Binary variable s_i_j_v: 1 if vehicle v goes directly from trip i to trip j, 0 otherwise
        self.__s = {
            (trip_i.getID(), trip_j.getID(), vehicle.getID()): pulp.LpVariable(f"s_{trip_i.getID()}_{trip_j.getID()}_{vehicle.getID()}", cat="Binary")
            for d in directions for trip_i in d.getTrips() for trip_j in d.getTrips()
            if trip_i != trip_j for vehicle in fleet
        }
    
        # Binary variable f_t_v: 1 if vehicle v starts with trip t, 0 otherwise
        self.__f = {
            (trip.getID(), vehicle.getID()): pulp.LpVariable(f"f_{trip.getID()}_{vehicle.getID()}", cat="Binary")
            for d in directions for trip in d.getTrips()
            for vehicle in fleet
        }
    
        # Binary variable l_t_v: 1 if vehicle v ends with trip t, 0 otherwise
        self.__l = {
            (trip.getID(), vehicle.getID()): pulp.LpVariable(f"l_{trip.getID()}_{vehicle.getID()}", cat="Binary")
            for d in directions for trip in d.getTrips()
            for vehicle in fleet
        }

   

    def generateObjectiveFunction(self):
        fleet = self.__sttvs.getFleet()
        directions = self.__sttvs.getDirections() 
        nodes = self.__sttvs.getNodes()
        

        # Vehicle usage costs
        vehicle_costs = pulp.lpSum(
            vehicle.getUsageCost() * self.__y[vehicle.getID()]
            for vehicle in fleet
        )

        # Break costs
        break_costs = pulp.lpSum(
            self.__s[trip_i.getID(), trip_j.getID(), vehicle.getID()] *
            self.__sttvs.getBreakCostCoefficient() *
            (trip_j.getStartTime() - trip_i.getEndTime() - nodes[trip_i.getEndNode()].getMinMaxStoppingTimes(0)[0])
            for direction in directions
            for trip_i, trip_j in self.calculate_in_line_compatibility(direction.getTrips(), directions, nodes)
            for vehicle in fleet
        )

       

        # Deadhead costs
        # deadhead_costs = pulp.lpSum(
        #     self.__s[i, j, vehicle.getID()] * vehicle.getPullInOutCost()
        #     for vehicle in fleet for (i, j) in self.__s.keys() if vehicle.getID() == self.__s[i, j]
        # )

        # CO2 costs (only for Combustion Vehicles)
        #co2_costs = pulp.lpSum(
        #    (vehicle.getEmissionCoefficient() * (trip.getEndTime() - trip.getStartTime()) * self.__z[trip.getID(), vehicle.getID()]
        #    if isinstance(vehicle, CombustionVehicle) else 0)
        #    for vehicle in fleet
        #    for trip in trips
        #)
        #es fehlen noch die co2 Kosten  mit f unf l

        # Define the objective function
        self.__model += (
            vehicle_costs 
             + break_costs 
            # + deadhead_costs 
            # + co2_costs
        ), "Minimize total operating costs"

    # This function calculates the inline compatible pairs of trips based on the start and end nodes of each trip,
    # and ensures that the time difference between the end of one trip and the start of another is within
    # the allowed minimum and maximum stopping times at the respective nodes.
    # It returns a list of trip pairs that can be assigned to the same vehicle based on these compatibility conditions.
    
    def calculate_in_line_compatibility(self, trips, directions, nodes):
        compatible_pairs = []

        for trip_i in trips:
            # Find the Direction that the trip belongs to
            direction_i = None
            for direction in directions:
                if trip_i in direction.getTrips():  
                    direction_i = direction
                    break

            if direction_i is None:
                continue  # Skip trip_i if no associated direction is found

            end_node_i = direction_i.getEndNode()  # End node of trip_i

            if end_node_i is None:
                continue  # Skip trip_i if no end node found (raise ValueError?!)

            for trip_j in trips:
                if trip_i.getID() == trip_j.getID():
                    continue  # Skip the same trip

                # Find the Direction that trip_j belongs to
                direction_j = None
                for direction in directions:
                    if trip_j in direction.getTrips():  
                        direction_j = direction
                        break

                if direction_j is None:
                    continue  # Skip trip_j if no associated direction is found

                start_node_j = direction_j.getStartNode()  # Start node of trip_j

                if start_node_j is None:
                    continue  # Skip trip_j if no start node found

                # Check in-line compatibility
                if end_node_i == start_node_j:
                    # Get stopping time limits at the end node of trip_i
                    min_stopping_time = nodes[end_node_i].getMinMaxStoppingTimes(0)[0]
                    max_stopping_time = nodes[end_node_i].getMinMaxStoppingTimes(0)[1]
                    time_diff = trip_j.getStartTime() - trip_i.getEndTime()

                    # Ensure time difference is within allowed bounds
                    if min_stopping_time <= time_diff <= max_stopping_time:
                        compatible_pairs.append((trip_i.getID(), trip_j.getID()))

        return compatible_pairs
   #def calculate_out_line_compatibility(self, trips, directions, nodes):
   

    def generateConstraints(self):
        directions = self.__sttvs.getDirections() 
        vehicles = self.__sttvs.getFleet()
        fleet = self.__sttvs.getFleet()
        tH = self.__sttvs.getTimeHorizon()
        nodes = self.__sttvs.getNodes()
        deadheadArcs = self.__sttvs.getDeadheadArcs()

        # 1. Ensure the first trip of each timetable is an initial trip
        for direction in directions:
            initial_trips = [trip for trip in direction.getTrips() if trip.getInitialFinal() == "initial"]
            self.__model += pulp.lpSum(
                self.__x[trip.getID()] for trip in initial_trips
            ) == 1, f"FirstTrip_timetable_{direction.getLine()}_{direction.getType()}"

        #2.  Ensure the last trip of each timetable is a final trip
        for direction in directions:
            final_trips = [trip for trip in direction.getTrips() if trip.getInitialFinal() == "final"]
            self.__model += pulp.lpSum(
                self.__x[trip.getID()] for trip in final_trips
            ) == 1, f"LastTrip_timetable_{direction.getLine()}_{direction.getType()}"

        # 3. Constraint: -x[i] + Sum(x[j] for j in T_d \ T_ini if a(j) - a(i) <= Iij_max) >= 0
        
        for direction in directions:
                trips = direction.getTrips()  # Get all trips for the current direction
                line_name = direction.getLine()
                direction_type = direction.getType()

                not_final_trips = [trip for trip in direction.getTrips() if trip.getInitialFinal() != "final"]
                not_initial_trips = [trip for trip in direction.getTrips() if trip.getInitialFinal() != "initial"]

                for trip_i in not_final_trips:
                    #a_i = trip_i.getStartTime()  # Start time of trip i, hier arrivaltime....
                    a_i = trip_i.getMainStopArrivalTime()
                    

                    # Identify the time window for trip_i
                    tw_trip_i = next(
                        (idx for idx in range(len(tH) - 1) if tH[idx] < a_i <= tH[idx + 1]),
                        None
                    )
                    if tw_trip_i is None:
                        raise ValueError(f"Trip {trip_i.getID()} has a start time outside defined time horizons.")

                    hw_trip_i = direction.getMaxHeadway(tw_trip_i)

                    # Find all potential successor trips j
                    related_trips = []
                    for trip_j in not_initial_trips:
                        if trip_j.getID() == trip_i.getID():
                            continue

                        a_j = trip_j.getMainStopArrivalTime()
                        tw_trip_j = next(
                            (idx for idx in range(len(tH) - 1) if tH[idx] < a_j <= tH[idx + 1]),
                            None
                        )

                        if tw_trip_j is None:
                            continue  # Skip trips outside defined time windows

                        # Calculate the maximum headway between trip_i and trip_j
                        if tw_trip_j == tw_trip_i:
                            hw_trip_j = hw_trip_i
                        elif tw_trip_j == tw_trip_i + 1:
                            hw_next = direction.getMaxHeadway(tw_trip_j)
                            hw_trip_j = max(hw_trip_i, hw_next)
                        else:
                            continue  # Ignore trips not in the current or next time window

                        # Check if the time difference between trip_i and trip_j satisfies the constraint
                        if 0 < (a_j - a_i) <= hw_trip_j:
                            related_trips.append(trip_j)

                    # Add constraint: -x[i] + Sum(x[j] for j in related_trips) >= 0
                    self.__model += (
                        -self.__x[trip_i.getID()] + pulp.lpSum(self.__x[trip_j.getID()] for trip_j in related_trips) >= 0,
                        f"MaxHeadwayConstraint_Line{line_name}_Dir{direction_type}_Trip{trip_i.getID()}"
                    )
                    
        # 4. Link trip coverage (x) with vehicle assignment (z)
        for direction in directions:
            for trip in direction.getTrips():
                trip_id = trip.getID()

                # If a trip is assigned to a vehicle, it is considered covered
                self.__model += self.__x[trip_id] == pulp.lpSum(self.__z[trip_id, vehicle.getID()] for vehicle in fleet), \
                            f"Link_x_z_{trip_id}"


        
        
        # 5,6 Ensure no vehicle covers two incompatible trips
        for direction in directions:
            trips = direction.getTrips()
            compatible_pairs = self.calculate_in_line_compatibility(trips, directions, nodes)

            for trip_i_id, trip_j_id in compatible_pairs:
                for vehicle in fleet:
                    vehicle_id = vehicle.getID()
                    self.__model += (
                        self.__z[trip_i_id, vehicle_id] + self.__z[trip_j_id, vehicle_id] <= 1,
                        f"Constraint_5_{trip_i_id}_{trip_j_id}_Vehicle_{vehicle_id}"
                    )
        
        
        # 8.

        # 9. Ensure a vehicle is marked as used if it is assigned to at least one trip
        num_trips = sum(len(direction.getTrips()) for direction in directions)
        for vehicle in fleet:
            vehicle_id = vehicle.getID()

            self.__model += pulp.lpSum(self.__z[trip.getID(), vehicle_id] for direction in directions for trip in direction.getTrips()) <= \
                            num_trips * self.__y[vehicle_id], \
                            f"VehicleUsage_{vehicle_id}"


        # sijv ∈ {0, 1} which is supposed to be equal to one if Trip j is the immediate successor of trip i run by vehicle v and supposed to be equal to zero otherwise.              
        '''  
        ---die def für outline compatibility fehlt noch----          
        # For each trip `j` and each vehicle `v`, we define the constraint for f_{j,v}
        for trip_j in trips:
            for vehicle in fleet:
        
                # Determine the compatible trips for trip_j from the in-line and out-line compatibility
                compatible_trips_in = self.calculate_in_line_compatibility(trip_j, trips, directions, nodes)
                compatible_trips_out = self.calculate_out_line_compatibility(trip_j, trips, directions, nodes)
        
                # Union of the compatible trips (in-line and out-line compatible)
                compatible_trips = set(compatible_trips_in).union(set(compatible_trips_out))

                # The constraint for f_{j,v}: It indicates if vehicle `v` starts with trip `j`
                # f_{j,v} = z_{j,v} - sum of s_{i,j,v} for all compatible trip `i` with `j` as the successor
                prob += self.__f[(trip_j.getID(), vehicle.getID())] == (
                    self.__z[(trip_j.getID(), vehicle.getID())] - 
                    pulp.lpSum(self.__s[(trip_i.getID(), trip_j.getID(), vehicle.getID())] 
                            for trip_i in compatible_trips if trip_i != trip_j)
                )

        # Similarly, for each trip `i` and each vehicle `v`, we define the constraint for l_{i,v}
        for trip_i in trips:
            for vehicle in fleet:

                # Determine the compatible trips for trip_i from the in-line and out-line compatibility
                compatible_trips_in = self.calculate_in_line_compatibility(trip_i, trips, directions, nodes)
                compatible_trips_out = self.calculate_out_line_compatibility(trip_i, trips, directions, nodes)

                # Union of the compatible trips (in-line and out-line compatible)
                compatible_trips = set(compatible_trips_in).union(set(compatible_trps_out))

                # The constraint for l_{i,v}: It indicates if vehicle `v` ends with trip `i`
                # l_{i,v} = z_{i,v} - sum of s_{i,j,v} for all compatible trip `j` with `i` as the predecessor
                prob += self.__l[(trip_i.getID(), vehicle.getID())] == (
                    self.__z[(trip_i.getID(), vehicle.getID())] - 
                    pulp.lpSum(self.__s[(trip_i.getID(), trip_j.getID(), vehicle.getID())] 
                               for trip_j in compatible_trips if trip_j != trip_i)
                )
        '''  
        # Ensure every trip is covered by exactly one vehicle
        #for direction in directions:
        #    for trip in direction.getTrips():
        #        trip_id = trip.getID()

                # Each trip must be assigned to one and only one vehicle
        #        self.__model += pulp.lpSum(self.__z[trip_id, vehicle.getID()] for vehicle in fleet) == 1, \
        #                    f"TripCoverage_{trip_id}"
        # Ensure at least one vehicle is used
        #self.__model += pulp.lpSum(self.__y[vehicle.getID()] for vehicle in fleet) >= 1, \
        #                "AtLeastOneVehicleUsed"

        #print("TODO")

    def solve(self):
        self.__model.solve()
        directions = self.__sttvs.getDirections() 

        # Function to convert seconds into HH:MM format
        def seconds_to_time(seconds):
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours:02}:{minutes:02}"
        
        # Check if an optimal solution has been found
        if pulp.LpStatus[self.__model.status] == 'Optimal':
            print("Optimal solution found!")
            print("Objective value:", self.__model.objective.value())

            # Output the covered trips
            covered_trips = []
            for direction in directions:
                for trip in direction.getTrips():
                    trip_id = trip.getID()
                    if self.__x[trip_id].value() == 1:  # If the trip is covered
                        covered_trips.append(trip)

            print(f"Number of covered trips: {len(covered_trips)}")

            uncovered_trips = [trip.getID() for direction in directions for trip in direction.getTrips() if self.__x[trip.getID()].value() == 0]

            timetable_by_line_direction = {}
            # Get time horizon and define start time (5:00 AM = 18000 seconds)
            time_horizon = self.__sttvs.getTimeHorizon() 
            start_of_day = 18000  # 5:00 AM in seconds
            time_windows = [start_of_day] + time_horizon  # Start time + time horizon
        
            # Create a dictionary to store trips by time window
            grouped_trips = {}
        
            # Loop through covered trips and assign them to time windows
            for trip in covered_trips:
                trip_id = trip.getID()
                start_time = trip.getStartTime()  # Get start time in seconds
                end_time = trip.getEndTime()  # Get end time in seconds
            
                # Find the appropriate time window for this trip
                for i in range(len(time_windows) - 1):
                    if time_windows[i] <= start_time < time_windows[i+1]:
                        time_window_key = f"{seconds_to_time(time_windows[i])} - {seconds_to_time(time_windows[i+1])}"
                        if time_window_key not in grouped_trips:
                            grouped_trips[time_window_key] = {"trip_ids": [], "start_times": [], "end_times": []}
                        grouped_trips[time_window_key]["trip_ids"].append(trip.getID())
                        grouped_trips[time_window_key]["start_times"].append(seconds_to_time(start_time))
                        grouped_trips[time_window_key]["end_times"].append(seconds_to_time(end_time))
                        break
        
            # Output timetable and vehicles used for each line and direction
            for direction in self.__sttvs.getDirections():
                line_name = direction.getLine()
                direction_type = direction.getType()

                # Create a key for the timetable based on line and direction
                timetable_key = f"Line {line_name}, Direction {direction_type}"

                # Create a list to store the trips for this line and direction
                if timetable_key not in timetable_by_line_direction:
                    timetable_by_line_direction[timetable_key] = {"trips": [], "vehicles": set()}

                # Loop through trips in this direction
                for trip in direction.getTrips():
                    trip_id = trip.getID()

                    # If the trip is covered (x=1), add it to the timetable for this line and direction
                    if self.__x[trip_id].value() == 1:
                        timetable_by_line_direction[timetable_key]["trips"].append(trip)

                        # Check which vehicles are used for this trip
                        for vehicle in self.__sttvs.getFleet():
                            if self.__z[trip_id, vehicle.getID()].value() == 1:
                                timetable_by_line_direction[timetable_key]["vehicles"].add(vehicle.getID())
        
            # Now, print the timetable for each line and direction
            for timetable_key, data in timetable_by_line_direction.items():
                # Sort the trips by start time
                trips_sorted = sorted(data["trips"], key=lambda trip: trip.getStartTime())

                print(f"\nGenerated Timetable for {timetable_key}:")

                # Print the sorted timetable for the line and direction
                for trip in trips_sorted:
                    # Get the time window for the trip
                    start_time = trip.getStartTime()
                    for i in range(len(time_windows) - 1):
                        if time_windows[i] <= start_time < time_windows[i+1]:
                            time_window = f"{seconds_to_time(time_windows[i])} - {seconds_to_time(time_windows[i+1])}"
                            break

                    # Print the trip information
                    print(f"  Trip ID: {trip.getID()}, Time Window: {time_window}, Start: {seconds_to_time(start_time)}, End: {seconds_to_time(trip.getEndTime())}")
            
                # Print the vehicles used for this line and direction
                print("  Vehicles used:")
                for vehicle_id in data["vehicles"]:
                    print(f"    Vehicle ID: {vehicle_id}")
        else:
            print("No optimal solution found.")


    def writeLPFile(self, filename):
        self.__model.writeLP(filename)
