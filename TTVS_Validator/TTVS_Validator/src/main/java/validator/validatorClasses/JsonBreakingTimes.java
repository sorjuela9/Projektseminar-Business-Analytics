package validator.validatorClasses;

import com.fasterxml.jackson.annotation.JsonProperty;

public class JsonBreakingTimes {
    private final StoppingTime stoppingTime;

    public JsonBreakingTimes(@JsonProperty("stoppingTime") StoppingTime stoppingTime){
        this.stoppingTime = stoppingTime;
    }

    public JsonBreakingTimes() {
        stoppingTime = null;
    }

    public StoppingTime getStoppingTime(){
        return stoppingTime;
    }
}
