package validator.validatorClasses;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

public class JsonBreak {
    private final BreakActivity breakTimeWindow;

    @JsonCreator
    public JsonBreak(@JsonProperty("breakTimeWindow") BreakActivity breakActivity){
        this.breakTimeWindow = breakActivity;
    }

    @JsonProperty("breakTimeWindow")
    public BreakActivity getBreakActivity() {
        return breakTimeWindow;
    }
}
