package validator.validatorClasses;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

public class DeadheadArc{
    private final int deadheadArcCode;
    private final String terminalNode;
    private final String deadheadType;
    private final double arcLength;
    private final List<Integer> travelTimes;

    /**
    *   A DeadheadArc is a trip from a Node to the depot, that is a pull-in or pull-out trip
    *   @param code -> the unique code of the DeadheadArc
    *   @param terminalNode -> the node where the DeadheadArc begin/end
    *   @param arcLength -> the distance between the node and the depot
    */
    @JsonCreator
    public DeadheadArc(@JsonProperty("deadheadArcCode") int code,
                       @JsonProperty("terminalNode") String terminalNode,
                       @JsonProperty("deadheadType") String deadheadType,
                       @JsonProperty("arcLength") double arcLength,
                       @JsonProperty("travelTimes") List<Integer> travelTimes){
        this.deadheadArcCode = code;
        this.terminalNode = terminalNode;
        this.deadheadType = deadheadType;
        this.arcLength = arcLength;
        this.travelTimes = travelTimes;
    }

    public DeadheadArc(){
        this(-1, null, null, -1, null);
    }

    //getter methods
    /**
    *   method to get the code of the DeadheadArc
    *   @return the code of the DeadheadArc
    */
    public int getDeadheadArcCode(){
        return this.deadheadArcCode;
    }
    //EFFECTS: restituisce il codice univoco dell'arco

    public String getTerminalNode(){
        return this.terminalNode;
    }
    //EFFECTS: restituisce l'unico nodo a cui l'arco fa riferimento

    public double getArcLength(){
        return this.arcLength;
    }
    //EFFECTS: restituisce la distanza fra il nodo ed il deposito, ossia la lunghezza
    //          dell'arco che unisce il nodo al deposito



    @Override
    public boolean equals(Object obj){
        if(obj == this)
            return true;

        if(!(obj instanceof DeadheadArc))
            return false;

        DeadheadArc tmp = (DeadheadArc) obj;

        return tmp.getDeadheadArcCode() == this.deadheadArcCode &&
               tmp.getTerminalNode().equals(this.terminalNode) &&
               Double.compare(tmp.arcLength, this.arcLength) == 0;
    }

    @Override
    public String toString(){
        return "DeadheadArc: {\n" +
               "deadheadArcCode: " + this.deadheadArcCode + "\n" +
               "node: " + this.terminalNode.toString() + "\n" +
               "arcLength: " + this.arcLength;
    }

    public String getDeadheadType() {
        return deadheadType;
    }

    public List<Integer> getTravelTimes() {
        return travelTimes;
    }
}
