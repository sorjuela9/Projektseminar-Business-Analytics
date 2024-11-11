package validator.validatorClasses;

import com.fasterxml.jackson.annotation.JsonSubTypes;
import com.fasterxml.jackson.annotation.JsonTypeInfo;

@JsonTypeInfo   (use = JsonTypeInfo.Id.NAME,include = JsonTypeInfo.As.WRAPPER_OBJECT)
@JsonSubTypes({ @JsonSubTypes.Type(value = ActivityBreak.class, name = "break"),
                @JsonSubTypes.Type(value = ActivityTrip.class, name = "activityTrip"),
                @JsonSubTypes.Type(value = Deadhead.class, name = "deadhead")})
public interface Activity{

    public int getStartTime();

    public int getEndTime();

    public String getStartNode();

    public String getEndNode();
}
