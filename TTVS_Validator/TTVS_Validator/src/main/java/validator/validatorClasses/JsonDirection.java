package validator.validatorClasses;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

public class JsonDirection {
    private Direction direction;

    @JsonCreator
    public JsonDirection(@JsonProperty("direction") Direction direction){
        this.direction = direction;
    }

    public Direction getDirection(){
        return direction;
    }
}
