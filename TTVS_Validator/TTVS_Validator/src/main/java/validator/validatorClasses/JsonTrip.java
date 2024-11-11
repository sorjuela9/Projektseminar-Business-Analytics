package validator.validatorClasses;

import com.fasterxml.jackson.annotation.JsonProperty;

public class JsonTrip {
    protected final Trip trip;

    public JsonTrip(@JsonProperty("trip") Trip trip){
        this.trip = trip;
    }

    public Trip getTrip() {
        return trip;
    }
}
