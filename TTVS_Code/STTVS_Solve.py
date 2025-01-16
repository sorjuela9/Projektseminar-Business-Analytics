import pulp 
import time
import pandas as pd
from SeniorTTVS import SeniorTTVS
from Vehicle import CombustionVehicle, ElectricVehicle
from pulp import GUROBI
from pulp import GUROBI_CMD
from pathlib import Path
import re
import os
class STTVS_Solve:

    def __init__(self, sttvs):
        self.__sttvs = sttvs
        self.__model = pulp.LpProblem("STTVS", pulp.LpMinimize)
        log_filename = f"gurobi_{int(time.time())}.log"
        self.__log_file = log_filename  # Log-Datei, in der die Ausgabe gespeichert wird
        self.__trips = []
        self.__directions = []

    def generateVariables(self):
        fleet = self.__sttvs.getFleet()  # Load the fleet
        self.__directions = self.__sttvs.getDirections()  # Load the directions
        #trips = [trip for direction in directions for trip in direction.getTrips()]  # Extract all trips
        
        for direction in self.__directions:
            for trip in direction.getTrips():
                self.__trips.append(trip)
        
        nodes = self.__sttvs.getNodes()
        deadhead_arcs = self.__sttvs.getDeadheadArcs()
        


    
        # Binary variable x_t: 1 if trip t is covered, 0 otherwise
        self.__x = {
            trip.getID(): pulp.LpVariable(f"x_{trip.getID()}", cat="Binary") 
            for d in self.__directions for trip in d.getTrips()
        }
    
        # Binary variable y_v: 1 if vehicle v is used, 0 otherwise
        self.__y = {
            vehicle.getID(): pulp.LpVariable(f"y_{vehicle.getID()}", cat="Binary") 
            for vehicle in fleet
        }
    
        # Binary variable z_t_v: 1 if trip t is assigned to vehicle v, 0 otherwise
        self.__z = {
            (trip.getID(), vehicle.getID()): pulp.LpVariable(f"z_{trip.getID()}_{vehicle.getID()}", cat="Binary")
            for d in self.__directions for trip in d.getTrips()
            for vehicle in fleet
        }
    
        

    def generateObjectiveFunction(self):
        fleet = self.__sttvs.getFleet()
        directions = self.__sttvs.getDirections() 
        vehicles = self.__sttvs.getFleet()
        tH = self.__sttvs.getTimeHorizon()
        nodes = self.__sttvs.getNodes()
        deadhead_arcs = self.__sttvs.getDeadheadArcs()
        #combustionVehicles = self.__sttvs.getFleet()


        # Vehicle usage costs
        vehicle_costs = pulp.lpSum(
            vehicle.getUsageCost() * self.__y[vehicle.getID()]
            for vehicle in fleet
        )
        
        # CO2 costs for trip durations
        co2_trip_costs = pulp.lpSum(
            # Emission cost per unit of time * trip duration * decision variable z_iv
            vehicle.getEmissionCoefficient() * (trip.getEndTime() - trip.getStartTime()) * self.__z[(trip.getID(), vehicle.getID())]
            for vehicle in fleet
            for direction in directions
            for trip in direction.getTrips()
            #if isinstance(vehicle, CombustionVehicle)
            if vehicle.getType() =="ICE"
        )

        # Define the objective function
        self.__model += (
            vehicle_costs 
            + co2_trip_costs 
            
        ), "Minimize total costs"
    

    
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

     # Version 1 for T^ips with two separate definitions for inline and outline compatibility:  
    
    def calculate_in_line_compatibility(self, trips, directions, nodes):
    
        inline_compatible = {}

        for trip_i in self.__trips:
            inline_compatible[trip_i.getID()] = []
            direction_i = trip_i.getDirection()  
            line_i = direction_i.getLine()
            end_node_i = direction_i.getEndNode()
            end_time_i = trip_i.getEndTime()
            time_window_idx_i = self.find_time_window(end_time_i)

            for trip_j in self.__trips:
                if trip_i.getID() == trip_j.getID():
                    continue   

                direction_j = trip_j.getDirection()  # Use direction information
                line_j = direction_j.getLine()
                start_node_j = direction_j.getStartNode()
                start_time_j = trip_j.getStartTime()

                if end_node_i == start_node_j:
                    min_stop = self.__sttvs.getNodeByID(end_node_i).getMinMaxStoppingTimes(time_window_idx_i)[0]
                    time_diff = start_time_j - end_time_i

                    if time_diff >= min_stop:# and end_time_i <= start_time_j: 
                        inline_compatible[trip_i.getID()].append(trip_j.getID())

        return inline_compatible
    
    def calculate_out_line_compatibility(self, trips, directions, nodes, deadhead_arcs):
    
        outline_compatible = {}
        
        for trip_i in self.__trips:
            compatible_trips = []
            direction_i = trip_i.getDirection()
            end_node_i = direction_i.getEndNode()
            arrival_time_i = trip_i.getMainStopArrivalTime()
            time_window_idx_i = self.find_time_window(trip_i.getEndTime())  # Get the time window index for trip i

            for trip_j in self.__trips:
                # A trip cannot be its own successor
                if trip_i.getID() == trip_j.getID():
                    continue

                direction_j = trip_j.getDirection()
             
                start_node_j = direction_j.getStartNode()
                if start_node_j and end_node_i:
                    arrival_time_j = trip_j.getMainStopArrivalTime()
                    time_window_idx_j = self.find_time_window(trip_j.getStartTime())  # Get the time window index for trip j
                    time_window_idx_j = self.find_time_window(trip_j.getStartTime())  # Get the time window index for trip j

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

                    
                    min_depot_time = self.__sttvs.getNodeByID(0).getMinMaxStoppingTimes(time_window_idx_i)[0]
                    

                    # Calculate the time difference between trips
                    time_diff = trip_j.getStartTime() - trip_i.getEndTime()

                    # Check if the time difference is sufficient for compatibility
                    if time_diff >= pull_in_time + min_depot_time + pull_out_time:
                        compatible_trips.append(trip_j.getID())

            # Store all compatible trips for trip i
            outline_compatible[trip_i.getID()] = compatible_trips
        return outline_compatible
 
    

    def calculate_incompatible_potential_successors(self, trips, in_line_compatible, out_line_compatible):
        incompatible_trips = {}

        for trip_i in self.__trips:
            trip_i_id = trip_i.getID()
            direction_i = trip_i.getDirection()  # Use direction information
            # Retrieve compatible trips
            #compatible = set(in_line_compatible.get(trip_i_id, [])) | set(out_line_compatible.get(trip_i_id, []))
            compatible = set(in_line_compatible.get(trip_i_id, [])) 
            compatible=compatible.union(set(out_line_compatible.get(trip_i_id, [])))
             
            # Incompatible trips: All trips that are not compatible and not trip_i itself
            # Note: We check start time of j relative to start time of i (not end time) per the new model
            

            incompatible_trips[trip_i_id] = [
                trip_j.getID() for trip_j in self.__trips
                if trip_j.getID() != trip_i_id and trip_j.getID() not in compatible and
                (trip_j.getStartTime() - trip_i.getStartTime() >= 0)
            ]

        return incompatible_trips
        
    def generateConstraints(self):
        # Zählvariablen für die Abschnitte
        first_trip_count = 0
        last_trip_count = 0
        max_headway_count = 0
        link_x_z_count = 0
        incompatibility_count = 0
        vehicle_usage_count = 0
       

        directions = self.__sttvs.getDirections() 
        vehicles = self.__sttvs.getFleet()
        fleet = self.__sttvs.getFleet()
        tH = self.__sttvs.getTimeHorizon()
        nodes = self.__sttvs.getNodes()
        deadhead_arcs = self.__sttvs.getDeadheadArcs()

        
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
                        if 0 <= (a_j - a_i) <= hw_trip_j:
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
        
        # Calculate the incompatible successors for all trips

        #Version 1 for T^ips needs:
        in_line_compatible = self.calculate_in_line_compatibility(trips, directions, nodes)
        out_line_compatible = self.calculate_out_line_compatibility(trips, directions, nodes, deadhead_arcs)
        incompatible_successors = self.calculate_incompatible_potential_successors(trips, in_line_compatible, out_line_compatible)
        
        # 5. Ensure that vehicles do not cover incompatible trips
        for trip_i in self.__trips:
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
            



        # 6. Ensure a vehicle is marked as used if it is assigned to at least one trip
        num_trips = sum(len(direction.getTrips()) for direction in directions)
        for vehicle in fleet:
            vehicle_id = vehicle.getID()

            self.__model += pulp.lpSum(self.__z[trip.getID(), vehicle_id] for direction in directions for trip in direction.getTrips()) <= \
                            num_trips * self.__y[vehicle_id], \
                            f"VehicleUsage_{vehicle_id}"
            vehicle_usage_count +=1

       
        
        # total constrains per section
        print(f"Total constraints in section 1 (First trips): {first_trip_count}")
        print(f"Total constraints in section 2 (Last trips): {last_trip_count}")
        print(f"Total constraints in section 3 (Max Headway): {max_headway_count}")
        print(f"Total constraints in section 4 (Link x-z): {link_x_z_count}")
        print(f"Total constraints in section 5 (Incompatibilities): {incompatibility_count}")
        print(f"Total constraints in section 6 (Vehicle usage): {vehicle_usage_count}")
    
      
        

    def solve(self):
        '''
        self.__model.solve(pulp.GUROBI_CMD(
            options=[ #Hier kann man alles noch anpassen
                "Threads=4",  # Use 4 threads 
                "Presolve=2",  # Aggressive presolve
                "Cuts=2",  # Use aggressive cuts
                "Heuristics=0.5",  # balanced heuristic for faster feasible solutions
                "MIPFocus=1",  # Focus on finding feasible solutions quickly
                "TimeLimit=600"  # 1-hour time limit 
                #"MIPGap=0.01"  # Accept solutions within 1% of optimality
            ]
        ))

        
        #self.__model.solve(PULP_CBC_CMD(
            #msg=True,          
            #threads=4,         
            #timeLimit=50,    
            #options=[
                #"ratio=0.01",  # Akzeptiere Lösungen innerhalb 1% der Optimalität
                #"preprocess",  # Schalte Vorverarbeitung ein
                #"strongcuts"   # Aktiviere aggressive Schnitte
            #]
        #))
        '''
        
        self.__model.solve(pulp.GUROBI_CMD(
            options=[ #Hier kann man alles noch anpassen
                "Threads=4",  # Use 4 threads 
                #"Presolve=2",  # Aggressive presolve
                #"Cuts=2",  # Use aggressive cuts
                "Heuristics=0.25",  # balanced heuristic for faster feasible solutions
                "MIPFocus=1",  # Focus on finding feasible solutions quickly
                "TimeLimit=3600",  # 1-hour time limit 
                #"MIPGap=0.01"  # Accept solutions within 1% of optimality
            ]
        ))
        '''
        self.__model.solve(pulp.GUROBI_CMD(
            options=[
                ("Threads", 4),       # Nutze 4 Threads
                ("Heuristics", 0.25),  # Ausgewogene Heuristik
                ("MIPFocus", 1),      # Fokus auf schnelle Lösungen
                ("TimeLimit", 3600),  # 1 Stunde Zeitlimit
                ("LogFile", self.__log_file),  # Sicherstellen, dass die Log-Datei gespeichert wird
            ],msg=True,
           
        ))
        
        
        gap = self.extract_gap_from_log(self.__log_file)

        '''
        
        directions = self.__sttvs.getDirections() 

        # Function to convert seconds into HH:MM format
        def seconds_to_time(seconds):
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours:02}:{minutes:02}"
        
        # Check if an optimal solution has been found
        if pulp.LpStatus[self.__model.status] == 'Optimal':
            if gap == 0:
                print("Optimal solution found.")
            else:
                print(f"Feasible solution found with gap: {gap}%")
        
        
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

                    # Determine the vehicle that will serve the trip
                    assigned_vehicle = None
                    for vehicle in self.__sttvs.getFleet():
                        if self.__z[trip.getID(), vehicle.getID()].value() == 1:
                            assigned_vehicle = vehicle.getID()
                            break

                    # Output of trip information together with the associated vehicle
                    print(f"  Trip ID: {trip.getID()}, Time Window: {time_window}, "
                        f"Start: {seconds_to_time(start_time)}, End: {seconds_to_time(trip.getEndTime())}, "
                        f"Vehicle: {assigned_vehicle if assigned_vehicle is not None else 'None'}")
        
                # Print the vehicles used for this line and direction
                print("  Vehicles used:")
                for vehicle_id in data["vehicles"]:
                    vehicle = None
    
                    for v in self.__sttvs.getFleet():
                        if v.getID() == vehicle_id:
                            vehicle = v
                            break
                    print(f"    Vehicle ID: {vehicle_id}, Type: {vehicle.getType()}")
        
        elif pulp.LpStatus[self.__model.status] == 'Infeasible':
            print("No feasible solution exists.")
        elif pulp.LpStatus[self.__model.status] == 'Unbounded':
            print("The model is unbounded.")
        else:
            print("No solution found within the given constraints.")
         #Lösche die Log-Datei, nachdem der Gap-Wert extrahiert wurde
        if os.path.exists(self.__log_file):
            os.remove(self.__log_file)
            

    def extract_gap_from_log(self,log_filename):
         #Gap-Wert aus der Log-Datei extrahieren
        try:
            with open(log_filename, "r") as file:
                log_output = file.read()
                    
            # Alle Vorkommen des Musters (Zahl vor %) suchen
            gap_matches = re.findall(r"(\d+\.\d+)%", log_output)
            
            if gap_matches:
                # Letzten Gap-Wert aus der Liste extrahieren
                gap = float(gap_matches[-1])  # Der Wert vor dem letzten Prozentzeichen
                return gap  # Gebe den Gap-Wert zurück
            else:
                return None  # Kein Gap gefunden
        except FileNotFoundError:
                return None  # Log-Datei nicht gefunden

    def writeLPFile(self, filename):
        self.__model.writeLP(filename)
