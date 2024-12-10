import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd

# Beispiel: Haltestellen und Fahrstrecken mit Beschriftungen
nodes = ['A', 'B', 'C', 'D', 'E']  # Haltestellen
edges = {
    'Bus1': [('A', 'B', '8:00'), ('B', 'C', '8:15')],
    'Bus2': [('C', 'D', '9:00'), ('D', 'E', '9:20')],
    'Bus3': [('A', 'D', '8:30')]
}

# Farben für die Busse
bus_colors = {'Bus1': 'red', 'Bus2': 'blue', 'Bus3': 'green'}

# Erstellen eines Graphen
G = nx.DiGraph()  # Gerichteter Graph
G.add_nodes_from(nodes)

# Hinzufügen der Kanten mit Labels
edge_labels = {}
for bus, trips in edges.items():
    for u, v, label in trips:
        G.add_edge(u, v)
        edge_labels[(u, v)] = label

# Positionierung der Knoten
pos = nx.spring_layout(G)

# Zeichnen der Haltestellen (Knoten)
nx.draw_networkx_nodes(G, pos, node_color='lightgray', node_size=500)

# Zeichnen der Verbindungen (Fahrstrecken) mit Farben für verschiedene Busse
for bus, trips in edges.items():
    nx.draw_networkx_edges(
        G,
        pos,
        edgelist=[(u, v) for u, v, _ in trips],
        edge_color=bus_colors[bus],
        width=2,
        label=bus
    )

# Beschriftung der Knoten
nx.draw_networkx_labels(G, pos, font_size=10, font_color="black")

# Beschriftung der Verbindungen
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='darkblue')

# Legende für die Busse
plt.legend(handles=[plt.Line2D([0], [0], color=color, lw=2, label=bus) for bus, color in bus_colors.items()], loc='upper left')

# Anzeigen des Graphen
plt.title("Fahrplan Graph mit Beschrifteten Verbindungen")
plt.show()

# Tabellarische Darstellung der Verbindungen mit Zeiten
# Erstellen eines DataFrames mit Pandas für eine bessere Anzeige
data = []
for bus, trips in edges.items():
    for u, v, time in trips:
        data.append([bus, u, v, time])

df = pd.DataFrame(data, columns=['Bus', 'Start', 'Ziel', 'Abfahrtszeit'])

# Anzeige der Tabelle
print("\nFahrplanübersicht:")
print(df)

