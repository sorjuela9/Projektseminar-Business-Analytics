package validator.validatorClasses;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonRootName;

@JsonRootName("breakTimeWindows")
public class BreakActivity {
    private final String typeSpot;
    private int startTime;
    private int endTime;
    public final Boolean isCharging;

    @JsonCreator
    public BreakActivity(@JsonProperty("startTime") int startTime,
                         @JsonProperty("endTime") int endTime,
                         @JsonProperty("typeSpot") String a,
                         @JsonProperty("isCharging") Boolean charge){
        this.typeSpot = a;
        this.startTime = startTime;
        this.endTime = endTime;
        this.isCharging = charge;
    }

    public BreakActivity(){
        this.typeSpot = null;
        this.startTime = 0;
        this.endTime = 0;
        isCharging = false;
    }

    public String getTypeSpot() {
        return typeSpot;
    }

    public int getStartTime() {
        return startTime;
    }

    public int getEndTime() {
        return endTime;
    }

    public Boolean getIsCharging() {
        return isCharging;
    }

    public void setStartTime(int startTime) {
        this.startTime = startTime;
    }

    public void setEndTime(int endTime) {
        this.endTime = endTime;
    }
}
