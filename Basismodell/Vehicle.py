# Sven Mallach (2024)
import json

class Vehicle:
    def __init__(self, ID, typ, uc, pioc):
        self.__id = ID
        self.__type = typ
        self.__usageCost = uc
        self.__pullInOutCost = pioc

    def getID(self):
        return self.__id

    def getType(self):
        return self.__type

    def getUsageCost(self):
        return self.__usageCost

    def getPullInOutCost(self):
        return self.__pullInOutCost

    @staticmethod
    def load_vehicles_from_json(json_file):
        vehicles = []
        with open(json_file, 'r') as f:
            data = json.load(f)

        for vehicle_data in data["fleet"]["vehicleList"]:
            vt_data = vehicle_data["vehicleType"]
            vehicle_type_name = vt_data["vehicleTypeName"]

            if "iceInfo" in vt_data:
                vehicle = CombustionVehicle(
                    ID=vehicle_data.get("ID", ""),
                    typ=vehicle_type_name,
                    uc=vt_data["usageCost"],
                    pioc=vt_data["pullInOutCost"],
                    ec=vt_data["iceInfo"]["emissionCoefficient"]
                )
            elif "electricInfo" in vt_data:
                electric_info = vt_data["electricInfo"]
                vehicle = ElectricVehicle(
                    ID=vehicle_data.get("ID", ""),
                    typ=vehicle_type_name,
                    uc=vt_data["usageCost"],
                    pioc=vt_data["pullInOutCost"],
                    num=electric_info["numberVehicle"],
                    auto=electric_info["vehicleAutonomy"],
                    maxCT=electric_info["maxChargingTime"],
                    minCT=electric_info["minChargingTime"]
                )

            vehicles.append(vehicle)

        return vehicles


class CombustionVehicle(Vehicle):
    def __init__(self, ID, typ, uc, pioc, ec):
        super().__init__(ID, typ, uc, pioc)
        self.__emissionCoefficient = ec

    def getEmissionCoefficient(self):
        return self.__emissionCoefficient


class ElectricVehicle(Vehicle):
    def __init__(self, ID, typ, uc, pioc, num, auto, maxCT, minCT):
        super().__init__(ID, typ, uc, pioc)
        self.__number = num
        self.__autonomy = auto
        self.__maxChargingTime = maxCT
        self.__minChargingTime = minCT

    def getNumger(self):
        return self.__number

    def getAutonomy(self):
        return self.__autonomy

    def getMaxChargingTime(self):
        return self.__maxChargingTime

    def getMinChargingTime(self):
        return self.__minChargingTime


vehicles = Vehicle.load_vehicles_from_json('Small_Input_S.json')

for v in vehicles:
    print(f"Vehicle ID: {v.getID()}, Type: {v.getType()}, Usage Cost: {v.getUsageCost()}")
