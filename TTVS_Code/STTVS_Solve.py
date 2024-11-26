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
        # break_costs = pulp.lpSum(
        #     self.__s[i, j, vehicle.getID()] * self.__sttvs.getBreakCostCoefficient()
        #     for (i, j) in self.__s.keys() for vehicle in fleet if vehicle.getID() == self.__s[i, j]
        # )

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

    
    def generateConstraints(self):
        directions = self.__sttvs.getDirections() 
        vehicles = self.__sttvs.getFleet()
        fleet = self.__sttvs.getFleet()
        tH = self.__sttvs.getTimeHorizon()

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
            for i in range(1, len(tH)):
                hw = direction.getMaxHeadway(i-1) # maximum headway of time window i-1
                #print(d.getType() + "-direction of line " + str(d.getLine()) + " has maximum headway " + str(hw) + " for the " + str(i-1) + "-th time Window")

        #    trips = d.getTrips()
        #     for t in trips:
        #        print("Trip " + str(t.getID()) + " has start time " + str(t.getStartTime()) + " and end time " + str(t.getEndTime()) + ".")
        for direction in directions:
                trips = direction.getTrips()  # Get all trips for the current direction
                line_name = direction.getLine()
                direction_type = direction.getType()

                for i, trip_i in enumerate(trips):
                    a_i = trip_i.getStartTime()  # Start time of trip i

                    # Identify the time window for trip_i
                    tw = next(
                        (idx for idx in range(len(tH) - 1) if tH[idx] <= a_i < tH[idx + 1]),
                        None
                    )
                    if tw is None:
                        raise ValueError(f"Trip {trip_i.getID()} has a start time outside defined time horizons.")

                    # Find all trips j such that a(j) - a(i) <= hw
                    related_trips = [
                        trip_j for j, trip_j in enumerate(trips)
                        if j != i and (trip_j.getStartTime() - a_i) <= hw #max_headway
                    ]

                    # Add constraint: -x_i + sum(x_j for related j) >= 0
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

        # 8. Ensure a vehicle is marked as used if it is assigned to at least one trip
        num_trips = sum(len(direction.getTrips()) for direction in directions)
        for vehicle in fleet:
            vehicle_id = vehicle.getID()

            self.__model += pulp.lpSum(self.__z[trip.getID(), vehicle_id] for direction in directions for trip in direction.getTrips()) <= \
                            num_trips * self.__y[vehicle_id], \
                            f"VehicleUsage_{vehicle_id}"
                    
                  
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
