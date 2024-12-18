import pulp 
#from pulp import PULP_CBC_CMD
import pandas as pd
from SeniorTTVS import SeniorTTVS
from Vehicle import CombustionVehicle, ElectricVehicle
from pulp import GUROBI
from pulp import GUROBI_CMD
#import matplotlib.pyplot as plt
#import networkx as nx

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
            if isinstance(vehicle, CombustionVehicle)
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

        for trip_i in trips:
            inline_compatible[trip_i.getID()] = []
            direction_i = trip_i.getDirection()  
            line_i = direction_i.getLine()
            end_node_i = direction_i.getEndNode()
            end_time_i = trip_i.getEndTime()
            time_window_idx_i = self.find_time_window(end_time_i)

            for trip_j in trips:
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
        
        for trip_i in trips:
            compatible_trips = []
            direction_i = trip_i.getDirection()
            end_node_i = direction_i.getEndNode()
            #arrival_time_i = trip_i.getMainStopArrivalTime()
            #time_window_idx_i = self.find_time_window(arrival_time_i)  # Get the time window index for trip i
            time_window_idx_i = self.find_time_window(trip_i.getEndTime())

            for trip_j in trips:
                # A trip cannot be its own successor
                if trip_i.getID() == trip_j.getID():
                    continue

                direction_j = trip_j.getDirection()
             
                start_node_j = direction_j.getStartNode()
                if start_node_j and end_node_i:
                    arrival_time_j = trip_j.getMainStopArrivalTime()
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

        for trip_i in trips:
            trip_i_id = trip_i.getID()
            direction_i = trip_i.getDirection()  # Use direction information
            # Retrieve compatible trips
            compatible = set(in_line_compatible.get(trip_i_id, [])) | set(out_line_compatible.get(trip_i_id, []))

            # Incompatible trips: All trips that are not compatible and not trip_i itself
            # Note: We check start time of j relative to start time of i (not end time) per the new model
            

            incompatible_trips[trip_i_id] = [
                trip_j.getID() for trip_j in trips
                if trip_j.getID() != trip_i_id and trip_j.getID() not in compatible and
                (trip_j.getStartTime() - trip_i.getStartTime() >= 0)
            ]

        return incompatible_trips
    '''    

    #  Version 2 for T^ips with a single combined definition:
    def calculate_incompatible_potential_successors(self, trips, directions, nodes, deadhead_arcs):
        T_ips = {}

        for trip_i in trips:
            trip_i_id = trip_i.getID()
            T_ips[trip_i_id] = []
        
            # Information of the current trip
            direction_i = trip_i.getDirection()
            end_node_i = direction_i.getEndNode()
            end_time_i = trip_i.getEndTime()
            start_time_i = trip_i.getStartTime()
            tw_idx_i = self.find_time_window(end_time_i)

            # Deadhead pull-In time for the endnode of i
            pull_in_time = 0
            for arc in deadhead_arcs:
                if arc.getTerminalNode() == end_node_i and arc.getType() == "in":
                    pull_in_time = arc.getTravelTimes(tw_idx_i)
                    break

            # Minimum stop time at the depot
            depot_min_stop = self.__sttvs.getNodeByID(0).getMinMaxStoppingTimes(tw_idx_i)[0]

            for trip_j in trips:
                if trip_i_id == trip_j.getID():
                    continue

                # Information of the successor trip
                start_node_j = trip_j.getDirection().getStartNode()
                start_time_j = trip_j.getStartTime()
                tw_idx_j = self.find_time_window(start_time_j)

                # Deadhead Pull-Out time for the startnode of trip j
                pull_out_time = 0
                for arc in deadhead_arcs:
                    if arc.getTerminalNode() == start_node_j and arc.getType() == "out":
                        pull_out_time = arc.getTravelTimes(tw_idx_j)
                        break

                # Check condition: st(j) - st(i) >= 0
                if start_time_j - start_time_i < 0:
                    continue  # Überspringe diesen Trip, wenn er kein potenzieller Nachfolger ist

                # Check T¹-condition: too early for inline-compatible
                if end_node_i == start_node_j:
                    min_stop = self.__sttvs.getNodeByID(end_node_i).getMinMaxStoppingTimes(tw_idx_i)[0]
                    if start_time_j - end_time_i < min_stop:
                        T_ips[trip_i_id].append(trip_j.getID())
                        continue

                # check T³-condition: too early for outline-compatible
                if end_node_i != start_node_j:
                    if start_time_j - end_time_i < pull_in_time + depot_min_stop + pull_out_time:
                        T_ips[trip_i_id].append(trip_j.getID())

        return T_ips
    '''
    
        
    
        
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

        #Version 1 for T^ips needs:
        in_line_compatible = self.calculate_in_line_compatibility(trips, directions, nodes)
        out_line_compatible = self.calculate_out_line_compatibility(trips, directions, nodes, deadhead_arcs)
        incompatible_successors = self.calculate_incompatible_potential_successors(trips, in_line_compatible, out_line_compatible)

        # Version 2 needs:
        #incompatible_successors = self.calculate_incompatible_potential_successors(trips, directions, nodes, deadhead_arcs)

        for i, trip_i in enumerate(trips):
                if i < 3:  # Nur die ersten 10 Trips ausgeben
                    trip_i_id = trip_i.getID()
                    incompatible_trip_ids = incompatible_successors.get(trip_i_id, [])
                    print("Trip " + str(trip_i_id) + " has " + str(len(incompatible_trip_ids)) + " incompatible potential successor trips."+ str(incompatible_trip_ids))
        
        
        # 9. Ensure that vehicles do not cover incompatible trips
        for direction in directions:
            for trip_i in direction.getTrips():
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

       
        
        # total constrains per section
        print(f"Total constraints in section 1 (First trips): {first_trip_count}")
        print(f"Total constraints in section 2 (Last trips): {last_trip_count}")
        print(f"Total constraints in section 3 (Max Headway): {max_headway_count}")
        print(f"Total constraints in section 4 (Link x-z): {link_x_z_count}")
        print(f"Total constraints in section 9 (Incompatibilities): {incompatibility_count}")
        print(f"Total constraints in section 10 (Vehicle usage): {vehicle_usage_count}")
    
      
        

    def solve(self):
        
        #self.__model.solve(pulp.GUROBI_CMD(
        #options=[ #Hier kann man alles noch anpassen
        #"Threads=4",  # Use 4 threads 
        #"Presolve=2",  # Aggressive presolve
        #"Cuts=2",  # Use aggressive cuts
        #"Heuristics=0.5",  # balanced heuristic for faster feasible solutions
        #"MIPFocus=1",  # Focus on finding feasible solutions quickly
        #"TimeLimit=3600",  # 1-hour time limit 
        #"MIPGap=0.01"  # Accept solutions within 1% of optimality
    #]
    #))
        self.__model.solve(pulp.GUROBI_CMD(
            options=[
                ("Threads", 4),       # Nutze 4 Threads
                ("Presolve", 2),      # Aggressives Presolve
                ("Cuts", 2),          # Aggressive Cuts
                ("Heuristics", 0.5),  # Ausgewogene Heuristik
               # ("MIPFocus", 1),      # Fokus auf schnelle Lösungen
                ("TimeLimit", 3600),  # 1 Stunde Zeitlimit
                ("MIPGap", 0.01)      # Akzeptiere Lösungen innerhalb 1% der Optimalität
            ]
        ))

        
        #self.__model.solve(PULP_CBC_CMD(
        #    msg=True,          
        #    threads=4,         
        #    timeLimit=3600,    
        #    options=[
        #        "ratio=0.01",  # Akzeptiere Lösungen innerhalb 1% der Optimalität
        #        "preprocess",  # Schalte Vorverarbeitung ein
        #        "strongcuts"   # Aktiviere aggressive Schnitte
        #    ]
        #))

        
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
                    print(f"    Vehicle ID: {vehicle_id}")

                   
            '''
            def visualize_timetable(timetable_by_line_direction):
                # Farben für die Fahrzeuge (kann noch erweitert werden)
                vehicle_colors = {}
                available_colors = ['red', 'blue', 'green', 'orange', 'purple', 'cyan']
                color_index = 0

                # Initialisieren des Graphen
                G = nx.DiGraph()

                # Edges und Nodes aus timetable_by_line_direction extrahieren
                edge_labels = {}
                for timetable_key, data in timetable_by_line_direction.items():
                    for trip in data["trips"]:
                        start_node = trip.getStartStation()
                        end_node = trip.getEndStation()
                        start_time = trip.getStartTime()
                        end_time = trip.getEndTime()
                        trip_id = trip.getID()

                        # Füge Haltestellen als Nodes hinzu
                        G.add_node(start_node)
                        G.add_node(end_node)

                        # Füge die Fahrt als Edge hinzu
                        G.add_edge(start_node, end_node)

                        # Label der Kante: Zeit und Trip-ID
                        edge_labels[(start_node, end_node)] = f"{trip_id}: {seconds_to_time(start_time)} - {seconds_to_time(end_time)}"

                        # Farbcodierung für Fahrzeuge
                        for vehicle_id in data["vehicles"]:
                            if vehicle_id not in vehicle_colors:
                                vehicle_colors[vehicle_id] = available_colors[color_index % len(available_colors)]
                                color_index += 1

                # Positionierung der Knoten
                pos = nx.spring_layout(G)

                # Zeichnen der Haltestellen (Nodes)
                nx.draw_networkx_nodes(G, pos, node_color='lightgray', node_size=700)

                # Zeichnen der Verbindungen (Edges) mit Farben für verschiedene Fahrzeuge
                for vehicle_id, color in vehicle_colors.items():
                    vehicle_edges = [
                        (u, v) for u, v in G.edges if vehicle_id in timetable_by_line_direction[timetable_key]["vehicles"]
                    ]
                    nx.draw_networkx_edges(G, pos, edgelist=vehicle_edges, edge_color=color, width=2, label=vehicle_id)

                # Beschriftung der Haltestellen (Nodes)
                nx.draw_networkx_labels(G, pos, font_size=10, font_color="black")

                # Beschriftung der Verbindungen (Edges)
                nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='darkblue')

                # Legende für Fahrzeuge
                plt.legend(handles=[
                    plt.Line2D([0], [0], color=color, lw=2, label=vehicle_id) for vehicle_id, color in vehicle_colors.items()
                ], loc='upper left')

                # Titel und Anzeige
                plt.title("Fahrplanvisualisierung")
                plt.show()

            # Aufruf der Visualisierungsfunktion mit deinem Fahrplandatensatz
            visualize_timetable(timetable_by_line_direction)
        '''       
        else:
            print("No optimal solution found.")


    def writeLPFile(self, filename):
        self.__model.writeLP(filename)
