import matplotlib.pyplot as plt
import pandas as pd

# Daten aus der Tabelle
data_in = [
    {"Trip ID": 120222, "Time Window": "09:15 - 12:00", "Start Time": "09:40", "End Time": "09:55", "Vehicle ID": 3},
    {"Trip ID": 120270, "Time Window": "09:15 - 12:00", "Start Time": "09:56", "End Time": "10:11", "Vehicle ID": 2},
    {"Trip ID": 120336, "Time Window": "09:15 - 12:00", "Start Time": "10:18", "End Time": "10:33", "Vehicle ID": 3},
    {"Trip ID": 120393, "Time Window": "09:15 - 12:00", "Start Time": "10:37", "End Time": "10:52", "Vehicle ID": 2},
    {"Trip ID": 120459, "Time Window": "09:15 - 12:00", "Start Time": "10:59", "End Time": "11:14", "Vehicle ID": 3},
    {"Trip ID": 120522, "Time Window": "09:15 - 12:00", "Start Time": "11:20", "End Time": "11:35", "Vehicle ID": 2},
    {"Trip ID": 120588, "Time Window": "09:15 - 12:00", "Start Time": "11:42", "End Time": "11:57", "Vehicle ID": 3},
    {"Trip ID": 120663, "Time Window": "12:00 - 14:00", "Start Time": "12:07", "End Time": "12:22", "Vehicle ID": 2},
    {"Trip ID": 120738, "Time Window": "12:00 - 14:00", "Start Time": "12:32", "End Time": "12:47", "Vehicle ID": 3},
    {"Trip ID": 120798, "Time Window": "12:00 - 14:00", "Start Time": "12:52", "End Time": "13:07", "Vehicle ID": 2},
    {"Trip ID": 120873, "Time Window": "12:00 - 14:00", "Start Time": "13:17", "End Time": "13:32", "Vehicle ID": 3},
    {"Trip ID": 120948, "Time Window": "12:00 - 14:00", "Start Time": "13:42", "End Time": "13:57", "Vehicle ID": 2},
    {"Trip ID": 121023, "Time Window": "14:00 - 18:43", "Start Time": "14:07", "End Time": "14:22", "Vehicle ID": 3},
    {"Trip ID": 121089, "Time Window": "14:00 - 18:43", "Start Time": "14:29", "End Time": "14:44", "Vehicle ID": 2},
    {"Trip ID": 121155, "Time Window": "14:00 - 18:43", "Start Time": "14:51", "End Time": "15:06", "Vehicle ID": 3},
    {"Trip ID": 121221, "Time Window": "14:00 - 18:43", "Start Time": "15:13", "End Time": "15:28", "Vehicle ID": 2},
    {"Trip ID": 121287, "Time Window": "14:00 - 18:43", "Start Time": "15:35", "End Time": "15:50", "Vehicle ID": 3},
    {"Trip ID": 121353, "Time Window": "14:00 - 18:43", "Start Time": "15:57", "End Time": "16:12", "Vehicle ID": 2},
    {"Trip ID": 121419, "Time Window": "14:00 - 18:43", "Start Time": "16:19", "End Time": "16:34", "Vehicle ID": 3},
    {"Trip ID": 121485, "Time Window": "14:00 - 18:43", "Start Time": "16:41", "End Time": "16:56", "Vehicle ID": 2},
    {"Trip ID": 121551, "Time Window": "14:00 - 18:43", "Start Time": "17:03", "End Time": "17:18", "Vehicle ID": 3},
    {"Trip ID": 121617, "Time Window": "14:00 - 18:43", "Start Time": "17:25", "End Time": "17:40", "Vehicle ID": 2},
    {"Trip ID": 121683, "Time Window": "14:00 - 18:43", "Start Time": "17:47", "End Time": "18:02", "Vehicle ID": 3},
    {"Trip ID": 121749, "Time Window": "14:00 - 18:43", "Start Time": "18:09", "End Time": "18:24", "Vehicle ID": 2},
    {"Trip ID": 121803, "Time Window": "14:00 - 18:43", "Start Time": "18:27", "End Time": "18:42", "Vehicle ID": 3},
]

data_out = [
    {"Trip ID": 122288, "Time Window": "09:15 - 12:00", "Start Time": "09:16", "End Time": "09:36", "Vehicle ID": 3},
    {"Trip ID": 122383, "Time Window": "09:15 - 12:00", "Start Time": "09:35", "End Time": "09:55", "Vehicle ID": 2},
    {"Trip ID": 122493, "Time Window": "09:15 - 12:00", "Start Time": "09:57", "End Time": "10:17", "Vehicle ID": 3},
    {"Trip ID": 122588, "Time Window": "09:15 - 12:00", "Start Time": "10:16", "End Time": "10:36", "Vehicle ID": 2},
    {"Trip ID": 122698, "Time Window": "09:15 - 12:00", "Start Time": "10:38", "End Time": "10:58", "Vehicle ID": 3},
    {"Trip ID": 122793, "Time Window": "09:15 - 12:00", "Start Time": "10:57", "End Time": "11:17", "Vehicle ID": 2},
    {"Trip ID": 122903, "Time Window": "09:15 - 12:00", "Start Time": "11:19", "End Time": "11:39", "Vehicle ID": 3},
    {"Trip ID": 123013, "Time Window": "09:15 - 12:00", "Start Time": "11:41", "End Time": "12:01", "Vehicle ID": 2},
    {"Trip ID": 123133, "Time Window": "12:00 - 14:00", "Start Time": "12:05", "End Time": "12:25", "Vehicle ID": 3},
    {"Trip ID": 123253, "Time Window": "12:00 - 14:00", "Start Time": "12:29", "End Time": "12:49", "Vehicle ID": 2},
    {"Trip ID": 123378, "Time Window": "12:00 - 14:00", "Start Time": "12:54", "End Time": "13:14", "Vehicle ID": 3},
    {"Trip ID": 123503, "Time Window": "12:00 - 14:00", "Start Time": "13:19", "End Time": "13:39", "Vehicle ID": 2},
    {"Trip ID": 123628, "Time Window": "12:00 - 14:00", "Start Time": "13:44", "End Time": "14:04", "Vehicle ID": 3},
    {"Trip ID": 123748, "Time Window": "14:00 - 18:43", "Start Time": "14:08", "End Time": "14:28", "Vehicle ID": 2},
    {"Trip ID": 123858, "Time Window": "14:00 - 18:43", "Start Time": "14:30", "End Time": "14:50", "Vehicle ID": 3},
    {"Trip ID": 123968, "Time Window": "14:00 - 18:43", "Start Time": "14:52", "End Time": "15:12", "Vehicle ID": 2},
    {"Trip ID": 124078, "Time Window": "14:00 - 18:43", "Start Time": "15:14", "End Time": "15:34", "Vehicle ID": 3},
    {"Trip ID": 124188, "Time Window": "14:00 - 18:43", "Start Time": "15:36", "End Time": "15:56", "Vehicle ID": 2},
    {"Trip ID": 124298, "Time Window": "14:00 - 18:43", "Start Time": "15:58", "End Time": "16:18", "Vehicle ID": 3},
    {"Trip ID": 124408, "Time Window": "14:00 - 18:43", "Start Time": "16:20", "End Time": "16:40", "Vehicle ID": 2},
    {"Trip ID": 124518, "Time Window": "14:00 - 18:43", "Start Time": "16:42", "End Time": "17:02", "Vehicle ID": 3},
    {"Trip ID": 124628, "Time Window": "14:00 - 18:43", "Start Time": "17:04", "End Time": "17:24", "Vehicle ID": 2},
    {"Trip ID": 124733, "Time Window": "14:00 - 18:43", "Start Time": "17:25", "End Time": "17:45", "Vehicle ID": 3},
    {"Trip ID": 124833, "Time Window": "14:00 - 18:43", "Start Time": "17:45", "End Time": "18:05", "Vehicle ID": 2},
    {"Trip ID": 124938, "Time Window": "14:00 - 18:43", "Start Time": "18:06", "End Time": "18:26", "Vehicle ID": 3},
]




# Zeitkonvertierungsfunktion
def time_to_minutes(time_str):
    h, m = map(int, time_str.split(":"))
    return h * 60 + m

# DataFrames erstellen
df_in = pd.DataFrame(data_in)
df_in["Start (min)"] = df_in["Start Time"].apply(time_to_minutes)
df_in["End (min)"] = df_in["End Time"].apply(time_to_minutes)
df_in["Direction"] = "in"

df_out = pd.DataFrame(data_out)
df_out["Start (min)"] = df_out["Start Time"].apply(time_to_minutes)
df_out["End (min)"] = df_out["End Time"].apply(time_to_minutes)
df_out["Direction"] = "out"

# Beide zusammenfügen
df_combined = pd.concat([df_in, df_out], ignore_index=True)

bar_height = 0.5  # Anpassung der Höhe der Balken
fig, ax = plt.subplots(figsize=(200, 1.5))

colors = {"in": "blue", "out": "coral"}
added_labels = set()  # Set zum Verfolgen, ob die Richtung schon zur Legende hinzugefügt wurde

for _, row in df_combined.iterrows():
    label = row["Direction"] if row["Direction"] not in added_labels else None
    ax.barh(
        row["Vehicle ID"],
        row["End (min)"] - row["Start (min)"],
        left=row["Start (min)"],
        color=colors[row["Direction"]],
        edgecolor="black",
        label=label,  # Nur einmal Label setzen
        height=bar_height  # Balkenhöhe einstellen  
    )
    if label:  # Richtung zur Set hinzufügen, sobald sie einmal zur Legende hinzugefügt wurde
        added_labels.add(label)

# Achsen und Legende
ax.set_xlabel("Time (minutes)")
ax.set_ylabel("Vehicle ID")
ax.set_yticks(range(2, 4, 1)) 
ax.set_xticks(range(510, 1141, 60))  # Alle 15 Minuten
ax.set_xticklabels([f"{i//60:02}:{i%60:02}" for i in range(510, 1141, 60)], rotation=45)
ax.grid(True, linestyle="--", alpha=0.7)
ax.legend(title="Direction")  # Legende nur mit den Linienfarben


plt.tight_layout()
plt.show()