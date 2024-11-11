package validator.validatorClasses;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

public class JsonVehicleType {
    private final VehicleType vehicleType;

    @JsonCreator
    public JsonVehicleType(@JsonProperty("vehicleType") VehicleType vehicleType) {
        this.vehicleType = vehicleType;
    }

    public VehicleType getVehicleType() {
        return vehicleType;
    }
}
