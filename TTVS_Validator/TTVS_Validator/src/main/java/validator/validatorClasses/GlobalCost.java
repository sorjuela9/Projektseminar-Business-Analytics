package validator.validatorClasses;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonRootName;

@JsonRootName("globalCost")
public class GlobalCost {
    private final double breakCostCoefficient;
    private final double alpha2;
    private final double alpha1;
    private final double alpha0;
    private final double gamma;

    @JsonCreator
    public GlobalCost(@JsonProperty("breakCostCoefficient") double breakCostCoefficient,
                      @JsonProperty("alpha2") double alpha2,
                      @JsonProperty("alpha1") double alpha1,
                      @JsonProperty("alpha0") double alpha0,
                      @JsonProperty("gamma") double gamma) {
        this.breakCostCoefficient = breakCostCoefficient;
        this.alpha2 = alpha2;
        this.alpha1 = alpha1;
        this.alpha0 = alpha0;
        this.gamma = gamma;
    }

    public double getGamma() {
        return gamma;
    }

    public double getAlpha0() {
        return alpha0;
    }

    public double getAlpha1() {
        return alpha1;
    }

    public double getAlpha2() {
        return alpha2;
    }

    public double getBreakCostCoefficient() {
        return breakCostCoefficient;
    }
}
