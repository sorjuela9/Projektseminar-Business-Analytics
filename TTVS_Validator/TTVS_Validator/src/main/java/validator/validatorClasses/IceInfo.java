package validator.validatorClasses;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

public class IceInfo {
    private final double emissionCoefficient;

    @JsonCreator
    public IceInfo(@JsonProperty("emissionCoefficient") double emissionCoefficient) {
        this.emissionCoefficient = emissionCoefficient;
    }

    public double getEmissionCoefficient() {
        return emissionCoefficient;
    }
}
