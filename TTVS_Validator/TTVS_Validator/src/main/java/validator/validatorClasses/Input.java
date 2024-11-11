package validator.validatorClasses;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

public class Input {
    private int[] timeHorizon;
    private List<JsonNetworkNode> nodes;
    private List<JsonDeadheadArc> deadheadArcs;
    private List<JsonDirection> directions;
    private Fleet fleet;
    private GlobalCost globalCost;
    private List<JsonVehicleBlock> vehicleBlockList;
    private SolutionReport reportSol;

    @JsonCreator
    public Input(@JsonProperty("timeHorizon") int[] timeHorizon,
                 @JsonProperty("nodes") List<JsonNetworkNode> nodes,
                 @JsonProperty("deadheadArcs") List<JsonDeadheadArc> deadheadArcs,
                 @JsonProperty("directions") List<JsonDirection> directions,
                 @JsonProperty("fleet") Fleet fleet,
                 @JsonProperty("globalCost") GlobalCost globalCost,
                 @JsonProperty("vehicleBlockList") List<JsonVehicleBlock> vehicleBlockList,
                 @JsonProperty("reportSol") SolutionReport reportSol){
        this.timeHorizon = timeHorizon;
        this.nodes = nodes;
        this.deadheadArcs = deadheadArcs;
        this.directions = directions;
        this.fleet = fleet;
        this.globalCost = globalCost;
        this.vehicleBlockList = vehicleBlockList;
        this.reportSol = reportSol;
    }

    public List<JsonDeadheadArc> getDeadheadArcs() {
        return deadheadArcs;
    }

    public List<JsonNetworkNode> getNodes() {
        return nodes;
    }

    public int[] getTimeHorizon() {
        return timeHorizon;
    }

    public List<JsonDirection> getDirections() {
        return directions;
    }

    public GlobalCost getGlobalCost() {
        return globalCost;
    }

    public Fleet getFleet() {
        return fleet;
    }

    public List<JsonVehicleBlock> getVehicleBlockList() {
        return vehicleBlockList;
    }

    public SolutionReport getReportSol() {
        return reportSol;
    }

    public void setTimeHorizon(int[] timeHorizon) {
        this.timeHorizon = timeHorizon;
    }

    public void setNodes(List<JsonNetworkNode> nodes) {
        this.nodes = nodes;
    }

    public void setDeadheadArcs(List<JsonDeadheadArc> deadheadArcs) {
        this.deadheadArcs = deadheadArcs;
    }

    public void setDirections(List<JsonDirection> directions) {
        this.directions = directions;
    }

    public void setFleet(Fleet fleet) {
        this.fleet = fleet;
    }

    public void setGlobalCost(GlobalCost globalCost) {
        this.globalCost = globalCost;
    }

    public void setVehicleBlockList(List<JsonVehicleBlock> vehicleBlockList) {
        this.vehicleBlockList = vehicleBlockList;
    }

    public void setReportSol(SolutionReport reportSol) {
        this.reportSol = reportSol;
    }

    public void removeTrips(int delta){
        for(JsonDirection jsonDirection : this.getDirections()){
            for(JsonTrip jsonTrip : jsonDirection.getDirection().getTrips()){

                if(jsonTrip.getTrip().getMainStopArrivalTime() < this.timeHorizon[0] - delta){
                    jsonDirection.getDirection().getTrips().remove(jsonTrip);
                }

                else if(jsonTrip.getTrip().getMainStopArrivalTime() > this.timeHorizon[timeHorizon.length-1] - delta){
                    jsonDirection.getDirection().getTrips().remove(jsonTrip);
                }
            }
        }
    }

    public void setInitialFinalTrips(int delta){
        for(JsonDirection jsonDirection : this.getDirections()){
            for(JsonTrip jsonTrip : jsonDirection.getDirection().getTrips()){

                if(jsonTrip.getTrip().getMainStopArrivalTime() < this.timeHorizon[1]
                        && Math.abs(jsonTrip.getTrip().getMainStopArrivalTime() - this.timeHorizon[0]) < delta){
                    jsonTrip.getTrip().setIsInitialFinalTT("initial");
                }

                else if(jsonTrip.getTrip().getMainStopArrivalTime() < this.timeHorizon[this.timeHorizon.length-2]
                        && Math.abs(jsonTrip.getTrip().getMainStopArrivalTime() - this.timeHorizon[this.timeHorizon.length-1]) < delta){
                    jsonTrip.getTrip().setIsInitialFinalTT("final");
                }
            }
        }
    }
}
