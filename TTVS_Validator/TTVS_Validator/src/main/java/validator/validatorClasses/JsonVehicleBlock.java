package validator.validatorClasses;

import com.fasterxml.jackson.annotation.JsonProperty;

public class JsonVehicleBlock{
    private VehicleBlock vehicleBlock;

    public JsonVehicleBlock(@JsonProperty("vehicleBlock") VehicleBlock vehicleBlock){
        this.vehicleBlock = vehicleBlock;
    }

    public JsonVehicleBlock(){
        vehicleBlock = null;
    }

    public VehicleBlock getVehicleBlock() {
        return vehicleBlock;
    }
}
