package validator.validatorClasses;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;
import java.util.Objects;

public class VehicleBlock{
    private String vehicleType;
    private List<Activity> activityList;

    @JsonCreator
    public VehicleBlock(@JsonProperty("vehicleTypeName") String type,
                        @JsonProperty("activityList") List<Activity> a){
        this.vehicleType = type;
        this.activityList = a;
    }

    public VehicleBlock(){
        this(null,null);
    }

    public String getVehicleType(){
        return vehicleType;
    }


    public List<Activity> getActivityList() {
        return activityList;
    }

    @JsonProperty("activityList")
    public void setActivityList(List<Activity> activityList) {
        this.activityList = activityList;
    }

    @JsonProperty("vehicleTypeName")
    public void setVehicleType(String vehicleType) {
        this.vehicleType = vehicleType;
    }

    @Override
    public String toString(){
        return "VehicleBlock: {" + "\n" +
               "vehicleType: " + this.vehicleType + "\n";
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        VehicleBlock that = (VehicleBlock) o;
        return Objects.equals(vehicleType, that.vehicleType) &&
                Objects.equals(activityList, that.activityList);
    }

    @Override
    public int hashCode() {
        return Objects.hash(vehicleType, activityList);
    }
}
