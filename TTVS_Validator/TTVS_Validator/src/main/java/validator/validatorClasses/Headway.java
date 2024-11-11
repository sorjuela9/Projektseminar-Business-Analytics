package validator.validatorClasses;

import com.fasterxml.jackson.annotation.JsonProperty;

public class Headway {
    private final int minHeadway;
    private final int idealHeadway;
    private final int maxHeadway;

    public Headway(@JsonProperty("minHeadway") int minHeadway,
                       @JsonProperty("idealHeadway") int idealHeadway,
                       @JsonProperty("maxHeadway") int maxHeadway){
        this.minHeadway = minHeadway;
        this.idealHeadway = idealHeadway;
        this.maxHeadway = maxHeadway;
    }

    public int getMinHeadway() {
        return minHeadway;
    }

    public int getIdealHeadway() {
        return idealHeadway;
    }

    public int getMaxHeadway() {
        return maxHeadway;
    }
}
