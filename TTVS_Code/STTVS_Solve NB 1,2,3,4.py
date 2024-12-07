import pulp

from SeniorTTVS import SeniorTTVS

class STTVS_Solve:

    def __init__(self, sttvs):
        self.__sttvs = sttvs
        self.__model = pulp.LpProblem("STTVS", pulp.LpMinimize)
        self.__constraints = []

    def generateVariables(self):

        fleet = self.__sttvs.getFleet()  # Lade die Fahrzeugflotte
        directions = self.__sttvs.getDirections()  # Lade die Fahrtrichtungen

        # Binary variable x_t: 1 if trip t is covered, 0 otherwise
        self.__x = {
            trip.getID(): pulp.LpVariable(f"x_{trip.getID()}", cat="Binary")
            for d in directions for trip in d.getTrips()
        }

        # Binary variable z_t_v: 1 if trip t is assigned to vehicle v, 0 otherwise
        self.__z = {
            (trip.getID(), vehicle.getID()): pulp.LpVariable(f"z_{trip.getID()}_{vehicle.getID()}", cat="Binary")
            for d in directions for trip in d.getTrips()
            for vehicle in fleet
        }


        #for i in range(1, len(tH)):
         #   print("Time Window: [" + str(tH[i-1]) + "," + str(tH[i]) + "]")

        #dirs = self.__sttvs.getDirections()

        #for d in dirs:
         #   for i in range(1, len(tH)):
          #      hw = d.getMaxHeadway(i-1) # maximum headway of time window i-1
           #     print(d.getType() + "-direction of line " + str(d.getLine()) + " has maximum headway " + str(hw) + " for the " + str(i-1) + "-th time Window")

            #trips = d.getTrips()
#            for t in trips:
#                print("Trip " + str(t.getID()) + " has start time " + str(t.getStartTime()) + " and end time " + str(t.getEndTime()) + ".")

        print("TODO")

    def generateConstraints(self):
        print("TODO..........")
        tH = self.__sttvs.getTimeHorizon()
        directions = self.__sttvs.getDirections()
        # 1. Ensure the first trip of each timetable is an initial trip
        for direction in directions:
            initial_trips = [trip for trip in direction.getTrips() if trip.getInitialFinal() == "initial"]
            constraint = pulp.lpSum(self.__x[trip.getID()] for trip in initial_trips) == 1
            self.__model += constraint, f"FirstTrip_timetable_{direction.getLine()}_{direction.getType()}"
            self.__constraints.append(constraint)

        # 2.  Ensure the last trip of each timetable is a final trip
        for direction in directions:
            final_trips = [trip for trip in direction.getTrips() if trip.getInitialFinal() == "final"]
            constraint = pulp.lpSum(
                self.__x[trip.getID()] for trip in final_trips ) == 1
            self.__model += constraint, f"LastTrip_timetable_{direction.getLine()}_{direction.getType()}"
            self.__constraints.append(constraint)

        # 3. Constraint: -x[i] + Sum(x[j] for j in T_d \ T_ini if a(j) - a(i) <= Iij_max) >= 0
        for direction in directions:
            trips = direction.getTrips()
            line_name = direction.getLine()
            direction_type = direction.getType()

            not_final_trips = [trip for trip in direction.getTrips() if trip.getInitialFinal() != "final"]
            not_initial_trips = [trip for trip in direction.getTrips() if trip.getInitialFinal() != "initial"]

            for trip_i in not_final_trips:
                a_i = trip_i.getMainStopArrivalTime()
                tw_trip_i = next((idx for idx in range(len(tH) - 1) if tH[idx] < a_i <= tH[idx + 1]), None)
                if tw_trip_i is None:
                    raise ValueError(f"Trip {trip_i.getID()} has a start time outside defined time horizons.")

                hw_trip_i = direction.getMaxHeadway(tw_trip_i)
                related_trips = []
                #Different
                for trip_j in not_initial_trips:
                    if trip_j.getID() == trip_i.getID():
                        continue

                    a_j = trip_j.getMainStopArrivalTime()
                    tw_trip_j = next((idx for idx in range(len(tH) - 1) if tH[idx] < a_j <= tH[idx + 1]), None)
                    if tw_trip_j is None:
                        continue

                    if tw_trip_j == tw_trip_i:
                        hw_trip_j = hw_trip_i
                    elif tw_trip_j == tw_trip_i + 1:
                        hw_next = direction.getMaxHeadway(tw_trip_j)
                        hw_trip_j = max(hw_trip_i, hw_next)
                    else:
                        continue

                    if 0 < (a_j - a_i) <= hw_trip_j:
                        related_trips.append(trip_j)

                constraint = -self.__x[trip_i.getID()] + pulp.lpSum(
                    self.__x[trip_j.getID()] for trip_j in related_trips) >= 0
                self.__model += constraint, f"MaxHeadwayConstraint_Line{line_name}_Dir{direction_type}_Trip{trip_i.getID()}"
                self.__constraints.append(constraint)


        # 4. Link trip coverage (x) with vehicle assignment (z)
        fleet = self.__sttvs.getFleet()
        for direction in directions:
           for trip in direction.getTrips():
               trip_id = trip.getID()  # If a trip is assigned to a vehicle, it is considered covered
               constraint = self.__x[trip_id] == pulp.lpSum(self.__z[trip_id, vehicle.getID()] for vehicle in fleet)
               self.__model += constraint, f"Link_x_z_{trip_id}"
               self.__constraints.append(constraint)

    def solve(self):
        self.__model.solve()
        directions = self.__sttvs.getDirections()
        fleet = self.__sttvs.getFleet()

        # Function to convert seconds into HH:MM format
        def seconds_to_time(seconds):
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours:02}:{minutes:02}"

        # Output the covered trips
        covered_trips = []
        inBound_trips = []
        outBound_trips = []
        for direction in directions:
            for trip in direction.getTrips():
                trip_id = trip.getID()
                if pulp.value(self.__x[trip_id]) == 1:
                    covered_trips.append(trip_id)
                    if direction.getType() == "in":
                        inBound_trips.append(trip_id)
                    elif direction.getType() == "out":
                        outBound_trips.append(trip_id)

        # Print the covered trips with start and end times and assigned vehicle
        print("Covered Trips:")
        for trip_id in covered_trips:
            for direction in directions:
                for trip in direction.getTrips():
                    if trip.getID() == trip_id:
                        start_time = seconds_to_time(trip.getStartTime())
                        end_time = seconds_to_time(trip.getEndTime())
                        assigned_vehicle = None
                        for vehicle in fleet:
                            if pulp.value(self.__z[trip_id, vehicle.getID()]) == 1:
                                assigned_vehicle = vehicle.getID()
                                break
                        print(
                            f"Direction: {direction.getType()} ,Trip ID: {trip_id}, Start Time: {start_time}, End Time: {end_time}, Assigned Vehicle: {assigned_vehicle}")

        print(f"Number of covered trips: {len(covered_trips)}")
        print(f"Number of inBound trips: {len(inBound_trips)}")
        print(f"Number of outBound trips: {len(outBound_trips)}")



        # Print the covered trips
        #print("Covered Trips:", covered_trips)
        #print(f"Number of covered trips: {len(covered_trips)}")


    def writeLPFile(self, filename):
        self.__model.writeLP(filename)

    def printConstraints(self):
        for constraint in self.__constraints:
            print(constraint)
    def printVariableValues(self):
        for variable in self.__model.variables():
            print(f"{variable.name} = {variable.varValue}")

    def printModelInfo(self):
        print("Model Information:")
        print(f"Number of Rows (Constraints): {len(self.__model.constraints)}")
        print(f"Number of Columns (Variables): {len(self.__model.variables())}")