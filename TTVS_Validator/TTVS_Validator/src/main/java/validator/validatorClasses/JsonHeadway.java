package validator.validatorClasses;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

public class JsonHeadway {
    private final Headway headway;

    @JsonCreator
    public JsonHeadway(@JsonProperty("headway") Headway headway) {
        this.headway = headway;
    }

    public Headway getHeadway() {
        return headway;
    }
}
