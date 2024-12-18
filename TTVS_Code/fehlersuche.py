import gurobipy as gp

# Gurobi-Modell erstellen und Datei laden
model = gp.read("model.lp")  # Lade das LP-File

# Prüfe auf Infeasibility und führe die Analyse aus
model.optimize()
if model.status == gp.GRB.INFEASIBLE:
    model.computeIIS()
    model.write("infeasible.ilp")
    print("IIS wurde als 'infeasible.ilp' gespeichert.")
else:
    print("Das Modell ist nicht unlösbar oder konnte optimiert werden.")
