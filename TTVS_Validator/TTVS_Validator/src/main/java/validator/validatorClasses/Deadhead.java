package validator.validatorClasses;

import validator.VSCost;
import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonRootName;

@JsonRootName("deadhead")
public class Deadhead implements Activity{
    private int startTime;
    private int endTime;
    private final String startNode;
    private final String endNode;
    private final int deadheadArcCode;

    @JsonCreator
    public Deadhead(@JsonProperty("startingTime") int st,
                    @JsonProperty("endingTime") int et,
                    @JsonProperty("startNode") String sn,
                    @JsonProperty("endNode") String en,
                    @JsonProperty("deadheadArcCode") int dhac){
        this.startTime = st;
        this.endTime = et;
        this.startNode = sn;
        this.endNode = en;
       this.deadheadArcCode = dhac;
    }

    public Deadhead(){
        this(0, 0, null, null, 0);
    }


    public int getDeadheadArcCode() {
        return deadheadArcCode;
    }

    public void setEndTime(int endTime) {
        this.endTime = endTime;
    }

    public void setStartTime(int startTime) {
        this.startTime = startTime;
    }

    public int mainStopTime(){
        int result;
        DeadheadArc deadheadArc = VSCost.computeDeadheadArc(this);

        if(deadheadArc.getDeadheadType().equalsIgnoreCase("pullIn")){
            result = this.startTime;
        }
        else{
            result = this.endTime;
        }

        return result;
    }

    @Override
    public int getStartTime() {
        return startTime;
    }

    @Override
    public int getEndTime() {
        return endTime;
    }

    @Override
    @JsonIgnore
    public String getStartNode() {
        return startNode;
    }

    @Override
    @JsonIgnore
    public String getEndNode() {
        return endNode;
    }
}
