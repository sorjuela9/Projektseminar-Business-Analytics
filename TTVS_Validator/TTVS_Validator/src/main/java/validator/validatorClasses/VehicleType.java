package validator.validatorClasses;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

@JsonInclude(JsonInclude.Include.NON_NULL)
public class VehicleType{
    private final String vehicleTypeName;
    private final double usageCost;
    private final double pullInOutCost;
    private final IceInfo iceInfo;
    private final ElectricInfo electricInfo;
    @JsonIgnore
    private boolean isElectric;


    public VehicleType(@JsonProperty("vehicleTypeName") String vehicleTypeName,
                       @JsonProperty("usageCost") double usageCost,
                       @JsonProperty("pullInOutCost") double pullInOutCost,
                       @JsonProperty("iceInfo") IceInfo iceInfo,
                       @JsonProperty("electricInfo") ElectricInfo electricInfo) {
        this.vehicleTypeName = vehicleTypeName;
        this.usageCost = usageCost;
        this.pullInOutCost = pullInOutCost;
        this.iceInfo = iceInfo;
        this.electricInfo = electricInfo;

        if(iceInfo == null){
            this.isElectric = true;
        }
        else{
            this.isElectric = false;
        }
    }

    public String getVehicleTypeName() {
        return vehicleTypeName;
    }

    public double getUsageCost() {
        return usageCost;
    }

    public double getPullInOutCost() {
        return pullInOutCost;
    }

    public IceInfo getIceInfo() {
        return iceInfo;
    }

    public ElectricInfo getElectricInfo() {
        return electricInfo;
    }

    @JsonIgnore
    public boolean isElectric() {
        return isElectric;
    }

    public void setElectric(boolean electric) {
        isElectric = electric;
    }
}
