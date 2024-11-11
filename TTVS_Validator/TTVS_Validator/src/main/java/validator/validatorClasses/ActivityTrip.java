package validator.validatorClasses;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonRootName;

@JsonRootName("activityTrip")
public class ActivityTrip implements Activity{
    @JsonIgnore
    private int startTime;
    @JsonIgnore
    private int endTime;
    @JsonIgnore
    private final String startNode;
    @JsonIgnore
    private final String endNode;
    private final int tripId;

    @JsonCreator
    public ActivityTrip(@JsonProperty("startTime") int st,
                        @JsonProperty("endTime") int et,
                        @JsonProperty("startNode") String sn,
                        @JsonProperty("endNode") String en,
                        @JsonProperty("tripId") int tripId) {
        this.startTime = st;
        this.endTime = et;
        this.startNode = sn;
        this.endNode = en;
        this.tripId = tripId;
    }

    public ActivityTrip(int tripId){
        this(0, 0, null, null, tripId);
    }

    public ActivityTrip(){
        this(0, 0, null, null ,0);
    }



    public int getTripId() {
        return tripId;
    }

    @Override
    @JsonIgnore
    public int getStartTime() {
        return startTime;
    }

    @Override
    @JsonIgnore
    public int getEndTime() {
        return endTime;
    }

    @Override
    public String getStartNode() {
        return startNode;
    }

    @Override
    public String getEndNode() {
        return endNode;
    }

    @JsonProperty
    public void setStartTime(int startTime){
        this.startTime = startTime;
    }

    @JsonProperty
    public void setEndTime(int endTime) {
        this.endTime = endTime;
    }
}
