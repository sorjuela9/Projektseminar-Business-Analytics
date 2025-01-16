import json
from datetime import timedelta
from collections import defaultdict

# Hilfsfunktion, um die Zeit in Sekunden in eine Uhrzeit umzuwandeln
def seconds_to_time(seconds):
    return str(timedelta(seconds=seconds))

# Laden der JSON-Datei
#file_path = 'TTVS_Instances/Small_Input_S.json'  
#file_path = 'TTVS_Instances/Medium_Input_S.json'
#file_path = 'TTVS_Instances/Large_Input_S.json'
#file_path = "TTVS_Instances/1line_6timeWindow_input_S.json"
#file_path = "TTVS_Instances/1line_input_S.json"
#file_path = "TTVS_Instances/2lines_input_S.json"
#file_path = "TTVS_Instances/2lines_6_timeWindows_input_S.json"
#file_path = "TTVS_Instances/3lines_input_S.json"
#file_path = "TTVS_Instances/3linesTriangle_input_S.json"
file_path = "TTVS_Instances/5lines_input_S.json"
#file_path = "TTVS_Instances/8lines_input_S.json"
#file_path = "TTVS_Instances/Toy_Example_Input_S.json"

with open(file_path, 'r') as file:
    data = json.load(file)


# Gesamtzahl der Trips und Knoten
total_trips = 0


# Iteration durch alle Richtungen (inBound und outBound)
for direction in data['directions']:
    trips = direction['direction']['trips']
    
    # Zählen der Trips
    total_trips += len(trips)
    
    
# Gesamtzahl der Knoten zählen
total_nodes = len(data["nodes"])


# Ausgabe der Gesamtzahl an Trips und Knoten
print(f"Gesamtzahl der Trips: {total_trips}")
print(f"Gesamtzahl der Knoten: {total_nodes}")


# Zeitfenster
time_windows = data["timeHorizon"]

# Hilfsfunktion, um ein Zeitfenster zu bestimmen
def get_time_window(start_time, time_windows):
    for i, time in enumerate(time_windows):
        if start_time <= time:
            return i
    return len(time_windows)  # Falls es nach dem letzten Zeitfenster liegt

# Diese Funktion erstellt eine Tabelle für eine Linie und gibt sie aus
def create_table_for_line(line_name, direction_type, trips, time_windows):
    # Erstelle zwei leere Tabellen für inBound und outBound
    time_window_table = defaultdict(list)

    # Für jeden Trip in der Richtung die Zeitfenster zuordnen
    for trip in trips:
        trip_id = trip['trip']['tripId']
        start_time = trip['trip']['startTime']
        end_time = trip['trip']['endTime']
        start_time_str = seconds_to_time(start_time)
        end_time_str = seconds_to_time(end_time)

        # Bestimme das Zeitfenster
        time_window_idx = get_time_window(start_time, time_windows)

        # Trip zu der Tabelle hinzufügen
        trip_info = f"ID:{trip_id} ({start_time_str} - {end_time_str})"
        time_window_table[time_window_idx].append(trip_info)

    return time_window_table

# Nach Richtung sortieren (inBound / outBound)
in_bound_lines = []  # Für Linien mit Richtung "inBound"
out_bound_lines = []  # Für Linien mit Richtung "outBound"

for direction in data['directions']:
    line_name = direction['direction']['lineName']
    direction_type = direction['direction']['directionType']
    trips = direction['direction']['trips']

    if direction_type == "inBound":
        in_bound_lines.append((line_name, trips))
    elif direction_type == "outBound":
        out_bound_lines.append((line_name, trips))

# Tabellen für inBound und outBound erstellen
in_bound_tables = {}
out_bound_tables = {}

for line_name, trips in in_bound_lines:
    in_bound_tables[line_name] = create_table_for_line(line_name, "inBound", trips, time_windows)

for line_name, trips in out_bound_lines:
    out_bound_tables[line_name] = create_table_for_line(line_name, "outBound", trips, time_windows)

# Tabelle mit Anzahl der Trips für jede Linie erstellen
def create_trip_count_table_for_line(line_name, time_windows, in_bound_table, out_bound_table):
    print(f"Tabelle für Linie: {line_name}")
    print(f"{'Time Window':<15} {'inBound':<10} {'outBound':<10}")
    print("-" * 50)

    for idx in range(len(time_windows)):
        # Anzahl der Trips in jedem Zeitfenster für inBound und outBound
        in_bound_count = len(in_bound_table.get(idx, []))
        out_bound_count = len(out_bound_table.get(idx, []))

        # Umwandlung der Zeitfenster in Uhrzeitformat
        start_time_str = seconds_to_time(time_windows[idx])
        
        # Ausgabe der Anzahl der Trips
        print(f"{start_time_str:<15} {in_bound_count:<10} {out_bound_count:<10}")
    print("\n" + "=" * 50 + "\n")

# Ausgabe der Trip Count Tabellen für jede Linie
for line_name in in_bound_tables.keys():
    in_bound_table = in_bound_tables[line_name]
    out_bound_table = out_bound_tables.get(line_name, {})
    create_trip_count_table_for_line(line_name, time_windows, in_bound_table, out_bound_table)
