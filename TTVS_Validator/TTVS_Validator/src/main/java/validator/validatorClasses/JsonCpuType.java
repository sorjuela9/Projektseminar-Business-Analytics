package validator.validatorClasses;

import com.fasterxml.jackson.annotation.JsonProperty;

public class JsonCpuType {
    private final CpuType cpuType;

    public JsonCpuType(@JsonProperty("cpuType") CpuType cpuType){
        this.cpuType = cpuType;
    }

    public CpuType getCpuType() {
        return cpuType;
    }
}
