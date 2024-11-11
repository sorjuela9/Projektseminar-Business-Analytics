package validator.validatorClasses;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

public class Direction {
    private final String lineName;
    private final String directionType;
    private final String startNode;
    private final String endNode;
    private final List<JsonHeadway> headways;
    private final List<JsonTrip> trips;

    @JsonCreator
    public Direction(@JsonProperty("lineName") String lineName,
                     @JsonProperty("directionType") String directionType,
                     @JsonProperty("startNode") String startNode,
                     @JsonProperty("endNode") String endNode,
                     @JsonProperty("headways") List<JsonHeadway> headways,
                     @JsonProperty("trips")List<JsonTrip> trips){
        this.lineName = lineName;
        this.directionType = directionType;
        this.startNode = startNode;
        this.endNode = endNode;
        this.headways = headways;
        this.trips = trips;
    }

    public String getLineName() {
        return lineName;
    }

    public String getDirectionType() {
        return directionType;
    }

    public String getStartNode() {
        return startNode;
    }

    public String getEndNode() {
        return endNode;
    }

    public List<JsonHeadway> getHeadways() {
        return headways;
    }

    public List<JsonTrip> getTrips() {
        return trips;
    }
}
