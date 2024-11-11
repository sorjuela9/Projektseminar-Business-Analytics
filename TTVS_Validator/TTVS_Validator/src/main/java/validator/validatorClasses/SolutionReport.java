package validator.validatorClasses;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonRootName;

@JsonRootName("reportSol")
public class SolutionReport {
    private final JsonCpuType[] cpuTypes;
    private final float upperBound;
    private final float lowerBound;
    private final float executionTime;

    @JsonCreator
    public SolutionReport(@JsonProperty("listCpuType")JsonCpuType[] cpuTypes,
                          @JsonProperty("upperBound")float upperBound,
                          @JsonProperty("lowerBound")float lowerBound,
                          @JsonProperty("executionTime")float executionTime) {
        this.cpuTypes = cpuTypes;
        this.upperBound = upperBound;
        this.lowerBound = lowerBound;
        this.executionTime = executionTime;
    }

    public float getExecutionTime() {
        return executionTime;
    }

    public float getLowerBound() {
        return lowerBound;
    }

    public float getUpperBound() {
        return upperBound;
    }

    public JsonCpuType[] getCpuTypes() {
        return cpuTypes;
    }
}
