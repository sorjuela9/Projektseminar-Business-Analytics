package validator.validatorClasses;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

public class ElectricInfo {
    private final int numberVehicle;
    private final double vehicleAutonomy;
    private final int minChargingTime;
    private final int maxChargingTime;

    @JsonCreator
    public ElectricInfo(@JsonProperty("numberVehicle") int numberVehicle,
                        @JsonProperty("vehicleAutonomy")double vehicleAutonomy,
                        @JsonProperty("minChargingTime") int minChargingTime,
                        @JsonProperty("maxChargingTime") int maxChargingTime) {
        this.numberVehicle = numberVehicle;
        this.vehicleAutonomy = vehicleAutonomy;
        this.minChargingTime = minChargingTime;
        this.maxChargingTime = maxChargingTime;
    }

    public int getMaxChargingTime() {
        return maxChargingTime;
    }

    public int getMinChargingTime() {
        return minChargingTime;
    }

    public double getVehicleAutonomy() {
        return vehicleAutonomy;
    }

    public int getNumberVehicle() {
        return numberVehicle;
    }
}
