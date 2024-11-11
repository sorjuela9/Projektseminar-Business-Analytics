package validator.validatorClasses;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

public class Node{
    /** the unique name of the node */
    private String nodeName;
    /**the total spot where vehicle can take a break */
    private int breakCapacity;
    /**the total spot where electric vehicle can perform a slow charge */
    private int slowChargeCapacity;
    /**the total spot where electric vehicle can perform a fast charge */
    private int fastChargeCapacity;
    private final List<JsonBreakingTimes> breakingTimes;
    //initialize this
    @JsonCreator
    public Node(@JsonProperty("nodeName") String name,
                @JsonProperty("breakCapacity") int breakCapacity,
                @JsonProperty("fastChargeCapacity") int fastChargeCapacity,
                @JsonProperty("slowChargeCapacity") int slowChargeCapacity,
                @JsonProperty("breakingTimes") List<JsonBreakingTimes> breakingTimes){

        if(name == null)
            throw new NullPointerException();

        if(breakCapacity < 0 || fastChargeCapacity < 0 || slowChargeCapacity < 0)
            throw new IllegalArgumentException("there is a negative break capacity for node " + name);

        this.nodeName = name;
        this.breakCapacity = breakCapacity;
        this.fastChargeCapacity = fastChargeCapacity;
        this.slowChargeCapacity = slowChargeCapacity;
        this.breakingTimes = breakingTimes;
    }
    //REQUIRES: name != null
    //THROW: if name == null throw NullPointerException
    //MODIFY: this
    //EFFECTS: initialize this with the value passed as input

    // getter methods

    /**
    *   return the name of the node
    */
    @JsonProperty("nodeName")
    public String getName(){
        return this.nodeName;
    }

    /**
    *   return the break capacity of the node, that is the total number
    *   of vehicle that can simultaneously take a break in that node
    */
    public int getBreakCapacity(){
        return this.breakCapacity;
    }
    //EFFECTS:

    /**
    *   return the fast charge capacity of the node, that is the total number
    *   of vehicle that can simultaneously take a fast charge in that node
    */
    public int getFastChargeCapacity(){
        return this.fastChargeCapacity;
    }

    /**
    *   return the slow charge capacity of the node, that is the total number
    *   of vehicle that can simultaneously take a slow charge in that node
    */
    public int getSlowChargeCapacity(){
        return this.slowChargeCapacity;
    }

    /**
    *   return the list of stopping times for all time windows
    */
    public List<JsonBreakingTimes> getBreakingTimes(){

        return this.breakingTimes;
    }

    //setter methods

    /**
    *   modify the node name with a new name
    *   @param name -> the new name of the node, must be != null
    */
    public void setName(String name) throws NullPointerException{
        if(name == null)
            throw new NullPointerException();
        this.nodeName = name;
    }
    //REQUIRES: name != null
    //THROW: if name == null throw NullPointerException
    //MODIFY: this.name

    /**
    *   change the breakCapacity of the node with the new capacity
    *   @param newCapacity -> the new break capacity of the node, must be >= 0
    */
    public void setBreakCapacity(int newCapacity) throws IllegalArgumentException{
        if(newCapacity < 0)
            throw new IllegalArgumentException();
        this.breakCapacity = newCapacity;
    }
    //REQUIRES: newCapacity >= 0
    //THROW: if newCapacity < 0 throw NegativeArgumentException
    //MODIFY: this.breakCapacity

    /**
    *   change the fastChargeCapacity of the node with the new capacity
    *   @param newCapacity -> the new number of fast charge columns of the node
    */
    public void setFastChargeCapacity(int newCapacity) throws IllegalArgumentException{
        if(newCapacity < 0)
            throw new IllegalArgumentException();
        this.fastChargeCapacity = newCapacity;
    }
    //REQUIRES: newCapacity >= 0
    //THROW: if newCapacity < 0 throw NegativeArgumentException
    //MODIFY: this.fastChargeCapacity

    /**
    *   change the slowChargeCapacity of the node with the new capacity
    */
    public void setSlowChargeCapacity(int newCapacity) throws NegativeArgumentException{
        if(newCapacity < 0)
            throw new NegativeArgumentException();
        this.slowChargeCapacity = newCapacity;
    }
    //REQUIRES: newCapacity >= 0
    //THROW: if newCapacity < 0 throw NegativeArgumentException
    //MODIFY: this.slowChargeCapacity


    @Override
    public boolean equals(Object obj){
        if(obj == this)
            return true;

        if(!(obj instanceof Node))
            return false;

        Node tmp = (Node) obj;

        return tmp.getName().equals(this.nodeName) &&
               tmp.getBreakCapacity() == this.breakCapacity &&
               tmp.getFastChargeCapacity() == this.fastChargeCapacity &&
               tmp.getSlowChargeCapacity() == this.slowChargeCapacity;
    }

    @Override
    public String toString(){
        return "Node:{\n" +
               "Name : " + this.nodeName + "\n" +
               "BreakCapacity: " + this.breakCapacity + "\n" +
               "fastChargeCapacity: " + this.fastChargeCapacity + "\n" +
               "slowChargeCapacity: " + this.slowChargeCapacity + "\n";
    }

}

class NegativeArgumentException extends RuntimeException{
    public NegativeArgumentException(){
        super();
    }

    public NegativeArgumentException(String s){
        super(s);
    }
}
