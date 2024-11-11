package validator.validatorClasses;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

public class JsonDeadheadArc {
    private DeadheadArc deadheadArc;

    @JsonCreator
    public JsonDeadheadArc(@JsonProperty("deadheadArc") DeadheadArc deadheadArc) {
        this.deadheadArc = deadheadArc;
    }

    public JsonDeadheadArc(){
        deadheadArc = null;
    }

    public DeadheadArc getDeadheadArc() {
        return deadheadArc;
    }
}
