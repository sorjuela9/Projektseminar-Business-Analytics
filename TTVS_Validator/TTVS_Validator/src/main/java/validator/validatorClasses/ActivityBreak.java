package validator.validatorClasses;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonRootName;

import java.util.ArrayList;
import java.util.List;

@JsonRootName("break")
public class ActivityBreak implements Activity{
    private int startTime;
    private int endTime;
    private String nameNode;
    private List<JsonBreak> breakTimeWindows;

    @JsonCreator
    public ActivityBreak(@JsonProperty("startTime") int st,
                         @JsonProperty("endTime") int et,
                         @JsonProperty("nameNode") String node,
                         @JsonProperty("breakTimeWindows") List<JsonBreak> breakActivities){
        this.startTime = breakActivities.get(0).getBreakActivity().getStartTime();
        this.endTime = breakActivities.get(breakActivities.size() - 1).getBreakActivity().getEndTime();
        this.nameNode = node;
        this.breakTimeWindows = new ArrayList<JsonBreak>(breakActivities);
    }

    public ActivityBreak(){
        this(0, 0, null, null);
    }

    @JsonProperty("breakTimeWindows")
    public List<JsonBreak> getBreakActivities(){
        return breakTimeWindows;
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
    @JsonProperty("nameNode")
    public String getStartNode() {
        return nameNode;
    }

    @Override
    @JsonIgnore
    public String getEndNode() {
        return nameNode;
    }

    public void setEndTime(int endTime) {
        this.endTime = endTime;
    }

    public void setStartTime(int startTime) {
        this.startTime = startTime;
    }

    public void setNameNode(String nameNode) {
        this.nameNode = nameNode;
    }

    @JsonProperty("breakTimeWindows")
    public void setBreakTimeWindows(List<JsonBreak> breakTimeWindows) {
        this.breakTimeWindows = breakTimeWindows;
    }
}
