package validator.validatorClasses;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

public class StoppingTime{
    private final int minStoppingTime;
    private final int maxStoppingTime;

    @JsonCreator
    public StoppingTime(@JsonProperty("minStoppingTime") int min,
                        @JsonProperty("maxStoppingTime") int max){
        this.minStoppingTime = min;
        this.maxStoppingTime = max;
    }

    public StoppingTime(){
        this(0, 0);
    }

    //getter methods

    public int getMinStoppingTime(){
        return this.minStoppingTime;
    }
    //EFFECTS: restituisce il minimo tempo di fermata

    public int getMaxStoppingTime(){
        return this.maxStoppingTime;
    }
    //EFFECTS: restituisce il massimo tempo di fermata

    @Override
    public boolean equals(Object obj){
        if (obj == this)
            return true;

        if(!(obj instanceof StoppingTime))
            return false;

        StoppingTime tmp = (StoppingTime) obj;

        return tmp.getMinStoppingTime() == this.minStoppingTime &&
               tmp.getMaxStoppingTime() == this.maxStoppingTime;
    }

    @Override
    public String toString(){
        return "StoppingTime: {" + "\n" +
               "MinStoppingTime: " + this.minStoppingTime + "\n" +
               "MaxStoppingTime: " + this.maxStoppingTime + "\n";
    }
}
