package validator.validatorClasses;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.Objects;

public class Trip {
    @JsonProperty("tripId")
    private final int tripId;
    @JsonProperty("startTime")
    private long startTime;
    @JsonProperty("endTime")
    private long endTime;
    @JsonProperty("mainStopArrivalTime")
    private long mainStopArrivalTime;
    @JsonProperty("lengthTrip")
    private final double lengthTrip;
    @JsonProperty("isInitialFinalTT")
    private String isInitialFinalTT;

    @JsonCreator
    public Trip(@JsonProperty("tripId") int tripId,
                @JsonProperty("startTime")long startTime,
                @JsonProperty("endTime")long endTime,
                @JsonProperty("mainStopArrivalTime")long mainStopArrivalTime,
                @JsonProperty("lengthTrip")double lengthTrip,
                @JsonProperty("isInitialFinalTT")String isInitialFinalTT) {
        this.tripId = tripId;
        this.startTime = startTime;
        this.endTime = endTime;
        this.mainStopArrivalTime = mainStopArrivalTime;
        this.lengthTrip = lengthTrip;
        this.isInitialFinalTT = isInitialFinalTT;
    }

    public Trip(Trip trip) {
        this(trip.getTripId(),
                trip.getStartTime(),
                trip.getEndTime(),
                trip.getMainStopArrivalTime(),
                trip.getLengthTrip(),
                trip.getIsInitialFinalTT());
    }

    public int getTripId(){
        return tripId;
    }

    public long getStartTime() {
        return startTime;
    }

    public long getEndTime() {
        return endTime;
    }

    public long getMainStopArrivalTime() {
        return mainStopArrivalTime;
    }

    public double getLengthTrip() {
        return lengthTrip;
    }

    public String getIsInitialFinalTT() {
        return isInitialFinalTT;
    }

    public void setEndTime(long endTime) {
        this.endTime = endTime;
    }

    public void setStartTime(long startTime) {
        this.startTime = startTime;
    }

    public void setMainStopArrivalTime(long mainStopArrivalTime) {
        this.mainStopArrivalTime = mainStopArrivalTime;
    }

    public void setIsInitialFinalTT(String isInitialFinalTT) {
        this.isInitialFinalTT = isInitialFinalTT;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Trip trip = (Trip) o;
        return tripId == trip.tripId &&
                startTime == trip.startTime &&
                endTime == trip.endTime &&
                mainStopArrivalTime == trip.mainStopArrivalTime &&
                Double.compare(trip.lengthTrip, lengthTrip) == 0 &&
                isInitialFinalTT.equals(trip.isInitialFinalTT);
    }

    @Override
    public int hashCode() {
        return Objects.hash(tripId, startTime, endTime, mainStopArrivalTime, lengthTrip, isInitialFinalTT);
    }

    @Override
    public String toString() {
        return "Trip{" +
                "tripId=" + tripId +
                ", startTime=" + startTime +
                ", endTime=" + endTime +
                ", mainStopArrivalTime=" + mainStopArrivalTime +
                ", lenghtTrip=" + lengthTrip +
                ", isInitialFinalTT='" + isInitialFinalTT + '\'' +
                '}';
    }
}
