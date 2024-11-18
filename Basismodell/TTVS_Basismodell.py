import json
from pulp import LpProblem, LpVariable, lpSum, LpMinimize, LpStatus
from Vehicle import Vehicle

# Load the JSON data and create vehicle instances
with open("Small_Input_S.json", 'r') as f:
    data = json.load(f)
vehicles = Vehicle.load_vehicles_from_json('Small_Input_S.json')
max_vehicles = len(vehicles)
vehicle_ids = range(max_vehicles)

# Extract trips from JSON data
trips = []
for direction_entry in data["directions"]:
    direction = direction_entry["direction"]
    trips_data = direction.get("trips", [])
    for trip_entry in trips_data:
        trip = trip_entry["trip"]
        trip_data = {
            'tripId': trip['tripId'],
            'startTime': trip['startTime'],
            'endTime': trip['endTime']
        }
        trips.append(trip_data)

# Cost parameters (placeholders)
break_cost = 1  # Placeholder for break costs
deadhead_cost = 1  # Placeholder for deadhead trip costs
additional_deadhead_cost = 1  # Placeholder for additional deadhead trip costs
co2_cost = 1  # Placeholder for CO2 cost during trips
initial_deadhead_cost = 1  # Placeholder for initial deadhead trip cost
final_deadhead_cost = 1  # Placeholder for final deadhead trip cost

# Decision Variables
# Binary variable x_t: 1 if trip t is covered; 0 otherwise
x = {trip["tripId"]: LpVariable(f"x_{trip['tripId']}", cat="Binary") for trip in trips}

# Binary variable y_v: 1 if vehicle v is used; 0 otherwise
y = {v_id: LpVariable(f"y_{v_id}", cat="Binary") for v_id in vehicle_ids}

# Binary variable z_t_v: 1 if vehicle v is assigned to trip t; 0 otherwise
z = {(trip["tripId"], v_id): LpVariable(f"z_{trip['tripId']}_{v_id}", cat="Binary") 
     for trip in trips for v_id in vehicle_ids}

# Binary variable s_i_j_v: 1 if trip j is the successor of trip i for vehicle v; 0 otherwise
s = {(i["tripId"], j["tripId"], v_id): LpVariable(f"s_{i['tripId']}_{j['tripId']}_{v_id}", cat="Binary") 
     for i in trips for j in trips if i["tripId"] != j["tripId"] for v_id in vehicle_ids}

# Binary variable f_i_v and l_i_v: 1 if trip i is the first/last trip for vehicle v; 0 otherwise
f = {(trip["tripId"], v_id): LpVariable(f"f_{trip['tripId']}_{v_id}", cat="Binary") 
     for trip in trips for v_id in vehicle_ids}
l = {(trip["tripId"], v_id): LpVariable(f"l_{trip['tripId']}_{v_id}", cat="Binary") 
     for trip in trips for v_id in vehicle_ids}


# Create the model
model = LpProblem("Vehicle_Assignment_Optimization", LpMinimize)

# Objective Function: Minimize total operating cost (only fixed vehicle costs here)
model += (
    lpSum(vehicles[v_id].getUsageCost() * y[v_id] for v_id in vehicle_ids)
    # Break costs for successor trips
    #+ lpSum(s[i, j, v_id] * break_cost for (i, j,v_id) in s if i != j for v_id in vehicle_ids)
    # Deadhead costs for non-service trips
    #+ lpSum(s[i, j, v_id] * pull_in_cost for (i, j,v_id) in s if i != j for v_id in vehicle_ids)
    # CO2 emission costs for combustion vehicles
    #+ lpSum(z[i, v_id] * co2_emission_cost for i in x for v_id in vehicle_ids if "Combustion" in v_id)
    # Initial and final deadhead costs
    #+ lpSum(f[i, v_id] * pull_in_cost + l[i, v_id] * pull_out_cost 
    #        for i in x for v_id in vehicle_ids)
), "Minimize total operating costs"



# Constraints

# 1. Ensure that at least one trip is marked as an initial and one as a final trip per direction (if directions are relevant)
for direction_entry in data["directions"]:
    initial_trips = [trip_entry["trip"]["tripId"] for trip_entry in direction_entry["direction"]["trips"][:1]]  # First trip as initial
    final_trips = [trip_entry["trip"]["tripId"] for trip_entry in direction_entry["direction"]["trips"][-1:]]  # Last trip as final

    # Initial trip constraint
    for trip_id in initial_trips:
        model += lpSum(z[trip_id, v_id] for v_id in vehicle_ids) == 1, f"InitialTrip_{trip_id}"

    # Final trip constraint
    for trip_id in final_trips:
        model += lpSum(z[trip_id, v_id] for v_id in vehicle_ids) == 1, f"FinalTrip_{trip_id}"

# . Trip Coverage Constraint: Ensure each trip is covered by exactly one vehicle
for trip in trips:
    trip_id = trip["tripId"]
    model += lpSum(z[trip_id, v_id] for v_id in vehicle_ids) == 1, f"TripCoverage_{trip_id}"

# 4. Link Constraints between x and z: A trip is assigned to a vehicle if it is covered
for trip in trips:
    trip_id = trip["tripId"]
    model += x[trip_id] == lpSum(z[trip_id, v_id] for v_id in vehicle_ids), f"Link_x_z_{trip_id}"

# 8. Vehicle Usage Constraints: A vehicle is marked as used if assigned to at least one trip
for v_id in vehicle_ids:
    model += lpSum(z[trip["tripId"], v_id] for trip in trips) <= len(trips) * y[v_id], f"VehicleUsage_{v_id}"

# . Mindestens ein Fahrzeug muss verwendet werden
model += lpSum(y[v_id] for v_id in vehicle_ids) >= 1, "AtLeastOneVehicleUsed"


# Solve the model
model.solve()


# Output results
print("Status:", LpStatus[model.status])
print("Objective value:", model.objective.value())


# Output only uncovered trips
covered_trips = [trip_id for trip_id, var in x.items() if var.value() == 1]
print(f"Number of covered trips: {len(covered_trips)}")

uncovered_trips = [trip_id for trip_id, var in x.items() if var.value() == 0]
if uncovered_trips:
    print("Uncovered trips:", uncovered_trips)
else:
    print("All trips are covered.")

# Output only used vehicles
used_vehicles = [v_id for v_id, var in y.items() if var.value() == 1]
print("Used vehicles and their types:")
for v_id in used_vehicles:
    vehicle_type = vehicles[v_id].getType()  
    print(f"Vehicle ID: {v_id}, Type: {vehicle_type}")
