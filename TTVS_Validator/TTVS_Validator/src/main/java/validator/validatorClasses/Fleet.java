package validator.validatorClasses;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

public class Fleet {
    private final List<JsonVehicleType> vehicleList;
    private final double phi;

    public Fleet(@JsonProperty("vehicleList") List<JsonVehicleType> vehicleList,
                 @JsonProperty("phi") double phi){
        this.vehicleList = vehicleList;
        this.phi = phi;
    }

    public List<JsonVehicleType> getVehicleList() {
        return vehicleList;
    }

    public double getPhi() {
        return phi;
    }
}
