package validator.validatorClasses;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

public class CpuType {
    private final String description;
    private final int numberCpu;
    private final int cpuIntegerIndex;
    private final double cpuFloatIndex;

    @JsonCreator
    public CpuType(@JsonProperty("description") String description,
                   @JsonProperty("numberCpu")int numberCpu,
                   @JsonProperty("cpuIntegerIndex")int cpuIntegerIndex,
                   @JsonProperty("cpuFloatIndex")double cpuFloatIndex) {
        this.description = description;
        this.numberCpu = numberCpu;
        this.cpuIntegerIndex = cpuIntegerIndex;
        this.cpuFloatIndex = cpuFloatIndex;
    }

    public String getDescription() {
        return description;
    }

    public int getNumberCpu() {
        return numberCpu;
    }

    public int getCpuIntegerIndex() {
        return cpuIntegerIndex;
    }

    public double getCpuFloatIndex() {
        return cpuFloatIndex;
    }
}
