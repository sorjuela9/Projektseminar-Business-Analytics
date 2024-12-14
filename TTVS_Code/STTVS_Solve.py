import pulp
import pandas as pd
from SeniorTTVS import SeniorTTVS

class STTVS_Solve:

    def __init__(self, sttvs):
        self.__sttvs = sttvs
        self.__model = pulp.LpProblem("STTVS", pulp.LpMinimize)
        

    def generateVariables(self):
        fleet = self.__sttvs.getFleet()  # Load the fleet
        directions = self.__sttvs.getDirections()  # Load the directions
        trips = [trip for direction in directions for trip in direction.getTrips()]  # Extract all trips
        nodes = self.__sttvs.getNodes()
        deadhead_arcs = self.__sttvs.getDeadheadArcs()
        


    
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
            (i.getID(), j.getID(), vehicle.getID()): pulp.LpVariable(f"s_{i.getID()}_{j.getID()}_{vehicle.getID()}", cat="Binary")
            for d in directions for i in d.getTrips() for j in d.getTrips()
            if i != j for vehicle in fleet
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

        # Vehicle usage costs
        vehicle_costs = pulp.lpSum(
            vehicle.getUsageCost() * self.__y[vehicle.getID()]
            for vehicle in fleet
        )

    
    
        # Break costs
        #break_costs = pulp.lpSum(
        #    self.__s[trip_i.getID(), trip_j.getID(), vehicle.getID()] *
        #    self.__sttvs.getBreakCostCoefficient() *
        #    (trip_j.getStartTime() - trip_i.getEndTime() - nodes[trip_i.getEndNode()].getMinMaxStoppingTimes(0)[0])
        #    for direction in directions
        #    for trip_i, trip_j in self.calculate_in_line_compatibility(direction.getTrips(), directions, nodes)
        #    for vehicle in fleet
        #)

       

        # Deadhead costs
        # deadhead_costs = pulp.lpSum(
        #     self.__s[i, j, vehicle.getID()] * vehicle.getPullInOutCost()
        #     for vehicle in fleet for (i, j) in self.__s.keys() if vehicle.getID() == self.__s[i, j]
        # )

        # CO2 costs (only for Combustion Vehicles)
        # co2_costs = pulp.lpSum(
        #     self.__z[trip_id, vehicle.getID()] * vehicle.getEmissionCoefficient()
        #     for vehicle in fleet if isinstance(vehicle, CombustionVehicle)
        #     for trip_id in {t for t, v in self.__z.keys() if v == vehicle.getID()}
        # )

        # Define the objective function
        self.__model += (
            vehicle_costs 
            # + break_costs 
            # + deadhead_costs 
            # + co2_costs
        ), "Minimize total operating costs"

    
    def find_time_window(self, time):
        # Retrieve the time horizon (list of time boundaries)
        time_horizon = self.__sttvs.getTimeHorizon()  
    
        # Initialize the time window index to -1 (default if no matching time window is found)
        time_window_index = -1  
    
        # Loop through the time horizon to find the correct time window for the given time
        for i in range(1, len(time_horizon)):  
            # Check if the given time falls within the time window [time_horizon[i-1], time_horizon[i])
            if time >= time_horizon[i - 1] and time < time_horizon[i]:
                time_window_index = i - 1  # Set the index of the time window
                break  # Exit the loop as soon as the correct time window is found

        
        return time_window_index
    
    def calculate_in_line_compatibility(self, trips, directions, nodes):
   
        in_line_compatible = {}
        direction_map = {trip.getID(): direction for direction in directions for trip in direction.getTrips()}

        for trip_i in trips:
            compatible_trips = []
            direction_i = direction_map[trip_i.getID()]
            end_node_i = direction_i.getEndNode()
            arrival_time_i = trip_i.getMainStopArrivalTime()
            time_window_idx_i = self.find_time_window(arrival_time_i)  # Get the time window index for trip i

            for trip_j in trips:
                if trip_i.getID() == trip_j.getID():  # A trip cannot be its own successor
                    continue
                if trip_j.getInitialFinal() == "initial":  # Initial trips cannot be successors
                    continue

                direction_j = direction_map[trip_j.getID()]
                if direction_i != direction_j:  # In-line requires the same direction
                    continue

                start_node_j = direction_j.getStartNode()
                if end_node_i == start_node_j:  # Check if end node of i matches start node of j
                    arrival_time_j = trip_j.getMainStopArrivalTime()
                    time_window_idx_j = self.find_time_window(arrival_time_j)  # Get the time window index for trip j

                    # Check if the time windows are compatible
                    if time_window_idx_j == time_window_idx_i or time_window_idx_j == time_window_idx_i + 1:
                        # Get stopping times for the current time window
                        node = self.__sttvs.getNodeByID(end_node_i)
                        min_stop, max_stop = node.getMinMaxStoppingTimes(time_window_idx_i)
                        time_diff = trip_j.getStartTime() - trip_i.getEndTime()

                        if min_stop <= time_diff <= max_stop:
                            compatible_trips.append(trip_j.getID())

            # Store all compatible trips for trip i
            in_line_compatible[trip_i.getID()] = compatible_trips
        return in_line_compatible
    
    def calculate_out_line_compatibility(self, trips, directions, nodes, deadhead_arcs):
    
        out_line_compatible = {}
        direction_map = {trip.getID(): direction for direction in directions for trip in direction.getTrips()}

        for trip_i in trips:
            compatible_trips = []
            direction_i = direction_map[trip_i.getID()]
            end_node_i = direction_i.getEndNode()
            arrival_time_i = trip_i.getMainStopArrivalTime()
            time_window_idx_i = self.find_time_window(arrival_time_i)  # Get the time window index for trip i

            for trip_j in trips:
                # A trip cannot be its own successor
                if trip_i.getID() == trip_j.getID():
                    continue
                # Initial and final trips cannot be outline successors
                if trip_j.getInitialFinal() in ["initial", "final"]:
                    continue

                direction_j = direction_map[trip_j.getID()]
                # Out-line compatibility requires different directions
                if direction_i == direction_j:
                    continue

                start_node_j = direction_j.getStartNode()
                if start_node_j and end_node_i:
                    arrival_time_j = trip_j.getMainStopArrivalTime()
                    time_window_idx_j = self.find_time_window(arrival_time_j)  # Get the time window index for trip j

                    # Calculate Pull-In and Pull-Out times for deadhead arcs
                    pull_in_time = 0
                    pull_out_time = 0

                    for arc in deadhead_arcs:
                        if arc.getTerminalNode() == end_node_i and arc.getType() == "in":
                            pull_in_time = arc.getTravelTimes(time_window_idx_i)
                            break

                    for arc in deadhead_arcs:
                        if arc.getTerminalNode() == start_node_j and arc.getType() == "out":
                            pull_out_time = arc.getTravelTimes(time_window_idx_j)
                            break

                    # Get minimum depot time

                    node_i = self.__sttvs.getNodeByID(end_node_i) 
                    if node_i:
                        min_depot_time = node_i.getMinMaxStoppingTimes(time_window_idx_i)[0]
                    else:
                        continue  # If no valid node is found, skip

                    # Calculate the time difference between trips
                    time_diff = trip_j.getStartTime() - trip_i.getEndTime()

                    # Check if the time difference is sufficient for compatibility
                    if time_diff >= pull_in_time + min_depot_time + pull_out_time:
                        compatible_trips.append(trip_j.getID())

            # Store all compatible trips for trip i
            out_line_compatible[trip_i.getID()] = compatible_trips
        return out_line_compatible


    def calculate_incompatible_potential_successors(self, trips, in_line_compatible, out_line_compatible):
    
        tips_dict = {}

        for trip in trips:
            trip_id = trip.getID()
            # Combine all compatible trips for trip i
            all_compatible = set(in_line_compatible.get(trip_id, [])) | set(out_line_compatible.get(trip_id, []))
            # Incompatible trips are those not in the compatible sets
            tips_dict[trip_id] = [t.getID() for t in trips if t.getID() not in all_compatible and t.getID() != trip_id]
        return tips_dict
    
    
    
    
    
    
        
    def generateConstraints(self):
        # Zählvariablen für die Abschnitte
        first_trip_count = 0
        last_trip_count = 0
        max_headway_count = 0
        link_x_z_count = 0
        incompatibility_count = 0
        vehicle_usage_count = 0
        vehicle_usage_count_11 = 0


        directions = self.__sttvs.getDirections() 
        vehicles = self.__sttvs.getFleet()
        fleet = self.__sttvs.getFleet()
        tH = self.__sttvs.getTimeHorizon()
        nodes = self.__sttvs.getNodes()
        deadhead_arcs = self.__sttvs.getDeadheadArcs()

        for node_id in range(len(nodes)):  # Durch alle Knoten iterieren
            node = self.__sttvs.getNodeByID(node_id)
        # 1. Ensure the first trip of each timetable is an initial trip
        for direction in directions:
            initial_trips = [trip for trip in direction.getTrips() if trip.getInitialFinal() == "initial"]
            self.__model += pulp.lpSum(
                self.__x[trip.getID()] for trip in initial_trips
            ) == 1, f"FirstTrip_timetable_{direction.getLine()}_{direction.getType()}"
            first_trip_count +=1

        #2.  Ensure the last trip of each timetable is a final trip
        for direction in directions:
            final_trips = [trip for trip in direction.getTrips() if trip.getInitialFinal() == "final"]
            self.__model += pulp.lpSum(
                self.__x[trip.getID()] for trip in final_trips
            ) == 1, f"LastTrip_timetable_{direction.getLine()}_{direction.getType()}"
            last_trip_count +=1

        # 3. Constraint: -x[i] + Sum(x[j] for j in T_d \ T_ini if a(j) - a(i) <= Iij_max) >= 0
        #constraint_counter = 0
        
        # Ensure that each trip (except the last in its direction) has at least one successor trip within the maximum headway.
        for direction in directions:
            trips = direction.getTrips()  # All trips in the current direction
            not_final_trips = [trip for trip in trips if trip.getInitialFinal() != "final"]  # Exclude final trips
            not_initial_trips = [trip for trip in trips if trip.getInitialFinal() != "initial"]  # Exclude initial trips

            for trip_i in not_final_trips:
                a_i = trip_i.getMainStopArrivalTime()  # Arrival time of trip_i at the main stop
                tw_trip_i = self.find_time_window(a_i)  # Time window of trip_i

                # Maximum headway for the current trip_i's time window
                hw_trip_i = direction.getMaxHeadway(tw_trip_i)

                # Find all trips j that are potential successors of i and within the maximum headway
                related_trips = []
                for trip_j in not_initial_trips:
                    if trip_j.getID() == trip_i.getID():  # Skip self-pairing
                        continue

                    a_j = trip_j.getMainStopArrivalTime()  # Arrival time of trip_j
                    tw_trip_j = self.find_time_window(a_j)  # Time window of trip_j

                    # Check if trip_j is in the same or the next time window relative to trip_i
                    if tw_trip_j == tw_trip_i or tw_trip_j == tw_trip_i + 1:
                        # Adjust the maximum headway if trip_j is in the next time window
                        hw_trip_j = hw_trip_i
                        if tw_trip_j == tw_trip_i + 1:
                            hw_next = direction.getMaxHeadway(tw_trip_j)  # Headway for the next time window
                            hw_trip_j = max(hw_trip_i, hw_next)

                        # Ensure trip_j starts within the maximum headway of trip_i
                        if 0 < (a_j - a_i) <= hw_trip_j:
                            related_trips.append(trip_j)

                # Add the constraint for trip_i
                # If trip_i is included in the timetable (x[trip_i] == 1), 
                # then at least one successor trip_j (x[trip_j] == 1) must be selected.
                if related_trips:
                    self.__model += (
                        -self.__x[trip_i.getID()] + pulp.lpSum(self.__x[trip_j.getID()] for trip_j in related_trips) >= 0,
                        f"MaxHeadwayConstraint_{trip_i.getID()}"
                    )
                    max_headway_count +=1
                
                    
        # 4. Link trip coverage (x) with vehicle assignment (z)
        for direction in directions:
            for trip in direction.getTrips():
                trip_id = trip.getID()

                # If a trip is assigned to a vehicle, it is considered covered
                self.__model += self.__x[trip_id] == pulp.lpSum(self.__z[trip_id, vehicle.getID()] for vehicle in fleet), \
                            f"Link_x_z_{trip_id}"
                link_x_z_count +=1
        #Constraint 5-7 no longer necessary, 8 too many constraints
        
       
        # Calculate the incompatible successors for all trips
        in_line_compatible = self.calculate_in_line_compatibility(trips, directions, nodes)
        out_line_compatible = self.calculate_out_line_compatibility(trips, directions, nodes, deadhead_arcs)
        incompatible_successors = self.calculate_incompatible_potential_successors(trips, in_line_compatible, out_line_compatible)

        # 9. Ensure that vehicles do not cover incompatible trips
        for trip_i in trips:
            trip_i_id = trip_i.getID()
            incompatible_trip_ids = incompatible_successors.get(trip_i_id, [])
            num_incompatible = len(incompatible_trip_ids)

            if num_incompatible > 0:  # Only add constraint if there are incompatible trips
                for vehicle in vehicles:
                    vehicle_id = vehicle.getID()
                    # Add the aggregated constraint for vehicle v and trip i
                    self.__model += (
                        num_incompatible * self.__z[trip_i_id, vehicle_id] +
                        pulp.lpSum(self.__z[trip_j_id, vehicle_id] for trip_j_id in incompatible_trip_ids) <= num_incompatible,
                        f"Constraint_9_{trip_i_id}_Vehicle_{vehicle_id}"
                    )
                    incompatibility_count += 1
        
        # 10. Ensure a vehicle is marked as used if it is assigned to at least one trip
        num_trips = sum(len(direction.getTrips()) for direction in directions)
        for vehicle in fleet:
            vehicle_id = vehicle.getID()

            self.__model += pulp.lpSum(self.__z[trip.getID(), vehicle_id] for direction in directions for trip in direction.getTrips()) <= \
                            num_trips * self.__y[vehicle_id], \
                            f"VehicleUsage_{vehicle_id}"
            vehicle_usage_count +=1

        # 11. if a vehicle is used it must be assigned at least one trip
        num_trips = sum(len(direction.getTrips()) for direction in directions) 
        for vehicle in fleet:
             vehicle_id = vehicle.getID()

        self.__model += (-num_trips * self.__y[vehicle_id] + pulp.lpSum(self.__z[trip.getID(), vehicle_id] for direction in directions for trip in direction.getTrips()) <= 0,
                         f"Constraint_11_Vehicle_{vehicle_id}")
        vehicle_usage_count_11 += 1

        # Ausgabe der Gesamtzahl der Nebenbedingungen pro Abschnitt
        print(f"Total constraints in section 1 (First trips): {first_trip_count}")
        print(f"Total constraints in section 2 (Last trips): {last_trip_count}")
        print(f"Total constraints in section 3 (Max Headway): {max_headway_count}")
        print(f"Total constraints in section 4 (Link x-z): {link_x_z_count}")
        print(f"Total constraints in section 9 (Incompatibilities): {incompatibility_count}")
        print(f"Total constraints in section 10 (Vehicle usage): {vehicle_usage_count}")
        print(f"Total constraints in section 11 (Vehicle usage - constraint 11): {vehicle_usage_count_11}")

        # sijv ∈ {0, 1} which is supposed to be equal to one if Trip j is the immediate successor of trip i run by vehicle v and supposed to be equal to zero otherwise.              
        for trip_i in trips:
            for trip_j in trips:
                if trip_i.getID() != trip_j.getID() and trip_j.getID() not in incompatible_trip_ids:
                    for vehicle in fleet:
                        # Restriction for s_ijv
                        self.__model += (
                            self.__s[trip_i.getID(), trip_j.getID(), vehicle.getID()] >=
                            self.__z[trip_i.getID(), vehicle.getID()] +
                            self.__z[trip_j.getID(), vehicle.getID()] - 1
                            - pulp.lpSum(
                                self.__z[k.getID(), vehicle.getID()]
                                for k in trips if trip_i.getEndTime() <= k.getStartTime() <= trip_j.getStartTime()
                            ),
                            f"Constraint_s_{trip_i.getID()}_{trip_j.getID()}_{vehicle.getID()}"
                        )
 
                 
        # For each trip `j` and each vehicle `v`, we define the constraint for f_{j,v}
        for trip_j in trips:  # Iterate over all trips
            for vehicle in fleet:  # Iterate over all vehicles
                # Calculate valid sum by summing only over trips that are compatible (not in the incompatible IDs)
                sum_f = pulp.lpSum(
                    self.__s[(trip_i.getID(), trip_j.getID(), vehicle.getID())]
                    for trip_i in trips
                    if trip_i.getID() not in incompatible_trip_ids and trip_i.getID() != trip_j.getID()
                )

                # Constraint to define f_{j,v}: Vehicle v ends with trip j
                self.__model += self.__f[(trip_j.getID(), vehicle.getID())] == (
                    self.__z[(trip_j.getID(), vehicle.getID())] - sum_f
                )

       

        # Similarly, for each trip `i` and each vehicle `v`, we define the constraint for l_{i,v}
        for trip_i in trips:  # Iterate over all trips
            for vehicle in fleet:  # Iterate over all vehicles
                # Calculate valid sum by summing only over trips that are compatible as predecessors
                sum_l = pulp.lpSum(
                    self.__s[(trip_i.getID(), trip_j.getID(), vehicle.getID())]
                    for trip_j in trips
                    if trip_j.getID() not in incompatible_trip_ids and trip_j.getID() != trip_i.getID()
                )

                # Constraint to define l_{i,v}: Vehicle v starts with trip i
                self.__model += self.__l[(trip_i.getID(), vehicle.getID())] == (
                    self.__z[(trip_i.getID(), vehicle.getID())] - sum_l
                )

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

        

    def solve(self):
        
        self.__model.solve(pulp.PULP_CBC_CMD(msg=True, timeLimit=900, threads=2))
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
