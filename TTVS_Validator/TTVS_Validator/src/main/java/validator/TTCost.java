package validator;

import validator.validatorClasses.*;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.List;

/**
 * Class that implement the validation of a solution for a Time Tabling (TT) problem, for the purpose of the MINOA Research
 * challenge, as described at https://minoa-itn.fau.de/?page_id=968
 * @author Lorenzo Frangioni
 * @version 1.1 04/2021
 */
public class TTCost {
    private static Input outputFile = null;
    private static Input inputFile = null;
    private static FileWriter writer;
    private static boolean writeOnFile;
    public static boolean isAdmissible;
    public static String category;


    /**
     * Method that start the validation of the TT scheduling of the solution provided, used to handle the validation in
     * the online version
     * @param instanceFolder the folder containing the json file of the input and the output
     * @param answerFile the file where the feasibility and the cost of the solution will be written
     * @return the tt cost of the solution, if the participant team is senior or junior always return 0
     * @throws IOException if answerFile can not be created or written
     */
    /*
    public static double start(File instanceFolder, File answerFile) throws IOException {
        isAdmissible = false;
        ObjectMapper mapper = new ObjectMapper();

        double ttCost = 0d;

        answerFile.createNewFile();
        File outputFilePath = null;
        File inputFilePath = null;

        //search for input and output files
        for(String pathname : instanceFolder.list()){
            if(pathname.toLowerCase().contains("output")){
                outputFilePath = new File(instanceFolder + "\\" + pathname);
            }
            else if(pathname.toLowerCase().contains("input")){
                inputFilePath = new File(instanceFolder + "\\" + pathname);
            }
        }

        if(outputFilePath != null && inputFilePath != null){
            try {
                writer = new FileWriter(answerFile, true);
                writeOnFile = true;
                ttCost = start(mapper.readValue(inputFilePath, Input.class), mapper.readValue(outputFilePath, Input.class));
            } catch (IOException e) {
                System.out.println("Exception occurred: " + e.getMessage());
                writer.write("Exception occurred: " + e.getMessage());
            } finally {
                writer.close();
            }
        }

        try{
            inputFilePath.delete();
            if(!isAdmissible){
                outputFilePath.delete();
            }
        }
        catch(NullPointerException e){
            if(inputFilePath == null) {
                write("inputFile is missing, couldn't delete it\n");
                writer.close();
            }
        }

        writeOnFile = false;
        return ttCost;
    }
    */

    /**
     * Method that start the validation of the TT scheduling of the solution provided, used to handle the validation in
     * the desktop version
     * @param inputInstance the representation of the input of the problem
     * @param solution the solution of the problem in inputInstance
     * @return the tt cost of the solution, if the participant team is senior or junior always return 0
     * @thorws IOException if writer can't write on file
     */
    public static double start(Input inputInstance, Input solution){
        inputFile = inputInstance;
        outputFile = solution;

        category = getCategory();

        isAdmissible = isAdmissible();

        write("TT is feasible: " + isAdmissible + "\n");


        double ttCost = 0d;

        // if the partecipating team belongs to the professional category there is the need to compute the TT cost of
        // the solution provided
        if(category.equalsIgnoreCase("professional")) {
            if (isAdmissible) {
                ttCost = computeTTCost();

                write("TT cost: " + ttCost + "\n\n");

            }
        }
        return ttCost;
    }


    /**
     * Method that compute the TT cost of the solution
     * @return the TT cost of the solution provided
     */
    private static double computeTTCost(){

        //the cost of a single direction
        double directionTTCost;
        //the total cost of the TT
        double totalTTCost = 0;

        //for every direction in the list of directions in the output file
        for(JsonDirection direction : outputFile.getDirections()){
            write("Direction: " + direction.getDirection().getLineName() + "\tType: " + direction.getDirection().getDirectionType());

            //the number of achieved headway different from ideal headway
            int nonIdealHeadway = 0;
            directionTTCost = 0;
            //the list of trips in the direction
            List<JsonTrip> jsonTrips = direction.getDirection().getTrips();

            //for each couple of trips in the direction
            for (int i = 0; i < jsonTrips.size()-1; i++){
                //the achieved headway is the difference between the main stop arrival time of two consecutive trips
                int achievedHeadway = (int)(jsonTrips.get(i + 1).getTrip().getMainStopArrivalTime() - jsonTrips.get(i).getTrip().getMainStopArrivalTime());
                int idealHeadway;

                //the time timeWindow where the trips belongs
                int firstTripTimeHorizonIndex = tripTimeHorizonIndex(jsonTrips.get(i));
                int secondTripTimeHorizonIndex = tripTimeHorizonIndex(jsonTrips.get(i+1));

                //if both trips have their main stop arrival time in the same timeWindow the ideal headway is the one write in the json file
                if(firstTripTimeHorizonIndex == secondTripTimeHorizonIndex && firstTripTimeHorizonIndex != -1){
                    idealHeadway = direction.getDirection().getHeadways().get(firstTripTimeHorizonIndex).getHeadway().getIdealHeadway();
                }
                //if the two consecutive trips have their main stop arrival times in different time window the ideal headway is the convex combination
                //between the two adjacent ideals headway of the direction
                else if(firstTripTimeHorizonIndex != -1 && secondTripTimeHorizonIndex != -1){
                    double firstTripConv = ((double)outputFile.getTimeHorizon()[firstTripTimeHorizonIndex+1] - (double)jsonTrips.get(i).getTrip().getMainStopArrivalTime())/(double) achievedHeadway;
                    double firstTripIdealHeadway = direction.getDirection().getHeadways().get(firstTripTimeHorizonIndex).getHeadway().getIdealHeadway();

                    double secondTripConv = ((double)jsonTrips.get(i+1).getTrip().getMainStopArrivalTime() - (double) outputFile.getTimeHorizon()[secondTripTimeHorizonIndex])/(double) achievedHeadway;
                    double secondTripIdealHeadway = direction.getDirection().getHeadways().get(secondTripTimeHorizonIndex).getHeadway().getIdealHeadway();

                    double value = (firstTripConv*firstTripIdealHeadway) + (secondTripConv*secondTripIdealHeadway);

                    idealHeadway = (int) Math.round(value);
                }
                //the method tripTimeHorizonIndex(...) returned -1 therefore at least one trip have a wrong main stop arrival time
                else{
                    write("trip " + jsonTrips.get(i) + " has mainStopArrival time at" + jsonTrips.get(i).getTrip().getMainStopArrivalTime() + " therefore in index " + firstTripTimeHorizonIndex +
                            " in the timeHorizon\n" +
                            "trip " + jsonTrips.get(i + 1) + " has mainStopArrival time at" + jsonTrips.get(i).getTrip().getMainStopArrivalTime() + " therefore in index " + firstTripTimeHorizonIndex +
                            " in the timeHorizon");
                    return 0d;
                }

                //error != 0 if and only the achieved headway is different from the ideal headway
                double error = (double)abs(achievedHeadway - idealHeadway) / (double) idealHeadway;

                if(error != 0)
                    nonIdealHeadway++;

                //increase the cost of the direction
                directionTTCost = directionTTCost + directionCost(error);
            }

            write("TT cost of the direction:\t" + directionTTCost + "\nNon ideal headways in the direction\\Total headways:\t" + nonIdealHeadway +  "\\" + (jsonTrips.size()-1) + "\n\n");


            //increase the total cost of the TT
            totalTTCost = totalTTCost + directionTTCost;
        }

        return totalTTCost;
    }


    /**
     * Compute the index of the time horizon where a mainStopArrivalTime of a trip belongs
     * @param trip the trip for which we are interested in know the timeHorizon index
     * @return the timeHorizon index of the trip given in input, such that 0 <= timeHorizon index <= timeHorizon.length,
     * -1 if the trip does not belong to the timeHorizon
     */
    private static int tripTimeHorizonIndex(JsonTrip trip){
        //for every index in the timeHorizon
        for (int i = 1; i < outputFile.getTimeHorizon().length; i++) {
            //if timeHorizon[i-1] <= trip.mainStopArrivalTime <= timeHorizon[i] then the trip belongs to timeHorizon[i-1]
            if(trip.getTrip().getMainStopArrivalTime() <= outputFile.getTimeHorizon()[i] && trip.getTrip().getMainStopArrivalTime() >= outputFile.getTimeHorizon()[i-1])
                return i-1;
        }

        write("trip " + trip.getTrip().getTripId() + " main stop arrival time does not belong to the time horizon, impossible compute directions TT cost");
        return -1;
    }


    /**
     * Method that compute the cost for the TT cost function, given the difference between the achieved headway and the
     * ideal headway this method return the cost of the violation.
     * @param error the difference between the idealHeadway and the achievedHeadway
     * @return the cost of the violation, if error == 0 then return 0
     */
    private static double directionCost(double error){
        //error = 0 if and only if the achieved headway between two consecutive trips is exactly the ideal headway
        if(error == 0)
            return 0;

        double alpha0 = outputFile.getGlobalCost().getAlpha0();
        double alpha1 = outputFile.getGlobalCost().getAlpha1();
        double alpha2 = outputFile.getGlobalCost().getAlpha2();

        //otherwise the cost for an achieved headway not equal to the ideal headway is given with the formula below
        return alpha2*(error*error) + alpha1*error + alpha0;
    }


    /**
     * method that compute the absolute value of n
     * @param n an int
     * @return -n if n < 0, n otherwise
     */
    private static int abs(int n){
        if(n < 0)
            return -n;
        return n;
    }


    /**
     * class that implement the quick sort algorithm
     */
    private static class QuickSort {
        private static int partition(int[] arr, int low, int high) {
            int pivot = arr[high];
            int index = (low - 1);
            for (int j = low; j < high; j++) {
                if (arr[j] < pivot) {
                    index++;
                    int temp = arr[index];
                    arr[index] = arr[j];
                    arr[j] = temp;
                }
            }
            int temp = arr[index + 1];
            arr[index + 1] = arr[high];
            arr[high] = temp;
            return index + 1;
        }

        public static void sort(int[] arr, int low, int high) {
            if (low < high) {
                int pi = partition(arr, low, high);
                sort(arr, low, pi - 1);
                sort(arr, pi + 1, high);
            }
        }
    }

    //

    /**
     * Recursive method that search if an integer n belongs to an array a.
     * For an array a the first call must be binarySearch(a, n, 0, a.length-1)
     * @param a an array of int in which the search takes place
     * @param n the number to search
     * @param sx the index of the leftmost element in the portion of the array
     * @param dx the index of the rightmost element in the portion of the array
     * @return true if n belongs to the array a, false otherwise
     */
    private static boolean binarySearch(int[] a, int n, int sx, int dx){
        if(dx >= sx){
            int mid = sx + ((dx-sx)/2);
            if(a[mid] == n)
                return true;
            else if(a[mid] > n)
                return binarySearch(a, n, sx, mid - 1);
            else
                return binarySearch(a, n, mid + 1, dx);
        }
        return false;
    }


    /**
     * Recursive method that search if an integer n belongs to an array a and return the index of the array where n belongs.
     * For an array a the first call must be binarySearch(a, n, 0, a.length-1)
     * @param a an array of int in which the search takes place
     * @param n the number to search
     * @param sx the index of the leftmost element in the portion of the array
     * @param dx the index of the rightmost element in the portion of the array
     * @return i if a[i] == n, -1 if for all 0 <= i <= a.length-1 a[i] != n
     */
    private static int positionBinarySearch(int[] a, int n, int sx, int dx){
        if(dx >= sx){
            int mid = sx + ((dx-sx)/2);
            if(a[mid] == n)
                return mid;
            else if(a[mid] > n)
                return positionBinarySearch(a, n, sx, mid - 1);
            else
                return positionBinarySearch(a, n, mid + 1, dx);
        }
        return -1;
    }


    /**
     * Method that check if the trips of the given direction in the output file are a subset of the ones in the input file
     * @param direction a direction in the json output file
     * @return true iff every trip that belong to the direction given in input to the method belongs to the same direction
     * in the json input file, false otherwise
     */
    private static boolean inputOutputSameTrip(Direction direction){
        if(direction == null)
            throw new NullPointerException();

        //array that contains the trip ids of the direction given from the output.json file
        int[] directionTrip = new int[direction.getTrips().size()];

        int i = 0;
        for(JsonTrip trip: direction.getTrips()){
            directionTrip[i] = trip.getTrip().getTripId();
            i++;
        }

        //sort the array of trip ids
        QuickSort.sort(directionTrip, 0, directionTrip.length-1);

        //the array of trips ids of the direction given in input
        int[] inputFileDirectionTrip;
        for(JsonDirection inputDirection : inputFile.getDirections()){
            //if inputDirection is the same as direction (the one given in the output file)
            if(inputDirection.getDirection().getStartNode().equalsIgnoreCase(direction.getStartNode()) && inputDirection.getDirection().getEndNode().equalsIgnoreCase(direction.getEndNode())){

                inputFileDirectionTrip = new int[inputDirection.getDirection().getTrips().size()];
                i = 0;
                //fill inputFileDirectionTrip with the trips id
                for(JsonTrip trip : inputDirection.getDirection().getTrips()){
                    inputFileDirectionTrip[i] = trip.getTrip().getTripId();
                    i++;
                }
                //sort the array of trip ids of the direction given by the input file
                QuickSort.sort(inputFileDirectionTrip, 0, inputFileDirectionTrip.length-1);

                int n;
                //for every trip id in the array that contains the trip of the direction given by the output file
                for (int j = 0; j < directionTrip.length; j++) {
                    n = directionTrip[j];
                    int pos = positionBinarySearch(inputFileDirectionTrip, n, 0, inputFileDirectionTrip.length - 1);
                    //if the trip with id = n isn't in the array that contains all the potential trip for the direction
                    //the solution isn't admissible
                    if (pos == -1){
                        write("Trip " + n + " isn't in the input file!\n");
                        return false;
                    }
                    else{
                        int finalN = n;
                        Trip outputTrip = direction.getTrips().stream()
                                .filter(jsonTrip -> jsonTrip.getTrip().getTripId() == finalN)
                                .reduce((a, b) -> {
                                    throw new IllegalArgumentException("too much trips with the same id");
                                }).get().getTrip();
                        Trip inputTrip = inputDirection.getDirection().getTrips().stream()
                                .filter(jsonTrip -> jsonTrip.getTrip().getTripId() == finalN)
                                .reduce((a, b) -> {
                                    throw new IllegalArgumentException("too much trips with the same id");
                                }).get().getTrip();

                        if(!inputTrip.equals(outputTrip)){
                            write("Trip " + inputTrip.getTripId() + " in output file is different from the one in the input file!");
                            return false;
                        }
                    }
                }
            }
        }

        return true;
    }


    /**
     * method that check if every trip of every direction is been performed by exactly one vehicle block
     * @return true iff every trip of every direction is been performed by exactly one vehicle block, false otherwise
     */
    private static boolean performedTrip(){
        //the number of total trips
        int count = 0;

        for(JsonDirection jsonDirection : outputFile.getDirections()){
            count += jsonDirection.getDirection().getTrips().size();
        }

        //array that contains all the trip ids given in the solution
        int[] tripPerformed = new int[count];
        //array that associate at every trip the number of times is been performed
        int[] howManyTimes = new int[count];

        count -= 1;

        //initialize the array that contains all the trip ids
        for(JsonDirection jsonDirection : outputFile.getDirections()){
            for (int i = 0; i < jsonDirection.getDirection().getTrips().size(); i++) {
                tripPerformed[count-i] = jsonDirection.getDirection().getTrips().get(i).getTrip().getTripId();
                howManyTimes[count-i] = 0;
            }
            count -= jsonDirection.getDirection().getTrips().size();
        }

        //sort the array
        QuickSort.sort(tripPerformed, 0, tripPerformed.length-1);

        //for every vehicle block in the output file
        for(JsonVehicleBlock jsonVehicleBlock : outputFile.getVehicleBlockList()){
            //for every activity of the selected vehicle block
            for(Activity activity : jsonVehicleBlock.getVehicleBlock().getActivityList()){
                //if the activity is a trip
                if(activity.getClass() == ActivityTrip.class){
                    //increase the number of times the trip was performed
                    int indexOfTrip = positionBinarySearch(tripPerformed, ((ActivityTrip) activity).getTripId(), 0, tripPerformed.length-1);
                    if(indexOfTrip == -1){
                        write("couldn't find trip: " + ((ActivityTrip) activity).getTripId() + " in the input file!");
                        return false;
                    }
                    howManyTimes[indexOfTrip] += 1;
                }
            }
        }

        for (int i = 0; i < howManyTimes.length; i++) {
            if(howManyTimes[i] > 1){
                write("Trip " + tripPerformed[i] + " was performed by more than one vehicle block");
                return false;
            }
            else if(howManyTimes[i] < 1){
                write("Trip " + tripPerformed[i] + " was not performed by any vehicle block");
                return false;
            }
        }

        return true;
    }


    /**
     * Method that check, for a given direction of the json output file, if the first trip is set as "initial" and the
     * last one is set as "final"
     * @param direction the direction that need to be checked
     * @return true if the first trip of the direction is set as "initial" and the last one as "final", false otherwise
     */
    private static boolean initialFinalTrips(Direction direction){
        if(!direction.getTrips().get(0).getTrip().getIsInitialFinalTT().equalsIgnoreCase("initial")){
            write("First trip of the direction " + direction.getLineName() + " " + direction.getDirectionType() + " is not signed as \"initial\"\n");
            return false;
        }
        if(!direction.getTrips().get(direction.getTrips().size()-1).getTrip().getIsInitialFinalTT().equalsIgnoreCase("final")){
            write("Last trip of the direction " + direction.getLineName() + " " + direction.getDirectionType() + " is not signed as \"final\"\n");
            return false;
        }
        return true;
    }


    /**
     * Method that check if the solution has feasible headways
     * @return true iff for every achievedHeadway of every direction:
     * minHeadway <= achievedHeadway || achievedHeadway <= maxHeadway
     */
    private static boolean headwayAdmissible(){
        List<JsonTrip> trips;

        //for every direction in the output file
        for(JsonDirection direction : outputFile.getDirections()){

            //the list with all the trips
            trips = direction.getDirection().getTrips();

            int timeHorizonTrip1, timeHorizonTrip2;
            long actualheadway;

            //for every trip in the tripList of the direction
            for (int i = 1; i < trips.size(); i++) {

                //index of the time horizon where the first trip belongs (aka the time window where the trip belongs)
                timeHorizonTrip1 = tripTimeHorizonIndex(trips.get(i-1));

                //index of the time horizon where the second trip belongs (aka the time window where the trip belongs)
                timeHorizonTrip2 = tripTimeHorizonIndex(trips.get(i));

                //the achieved headway
                actualheadway = trips.get(i).getTrip().getMainStopArrivalTime() - trips.get(i-1).getTrip().getMainStopArrivalTime();

                //if both trips belong to the same time window
                if(timeHorizonTrip1 == timeHorizonTrip2){

                    //the achieved headway must be less than the max headway for that direction in the time window where the trips belongs
                    if(actualheadway > direction.getDirection().getHeadways().get(timeHorizonTrip1).getHeadway().getMaxHeadway()){
                        write("Headway between two consecutive trips grater than max headway\n" +
                                "First trip:\t" + trips.get(i-1).getTrip().getTripId() + "\tsecond trip:\t" + trips.get(i).getTrip().getTripId());
                        return false;
                    }

                    //for professional participants the achieved headway must be grater than min headway for that direction in the time window where the trips belongs
                    if(getCategory().equalsIgnoreCase("professional")){
                        if(actualheadway < direction.getDirection().getHeadways().get(timeHorizonTrip1).getHeadway().getMinHeadway()){
                            write("Headway between two consecutive trips less than minimum headway\n" +
                                    "First trip:\t" + trips.get(i-1).getTrip().getTripId() + "\tsecond trip:\t" + trips.get(i).getTrip().getTripId());
                            return false;
                        }
                    }
                }

                //the two trips does not belong to the same time window, hence their index in the time horizon aren't the same
                else{

                    //the achieved headway must be less than the max between the max headway of the two time windows
                    //achievedHeadway < max(maxHeadway(timeWindow1), maxHeadway(timeWindow2))
                    if(actualheadway > Math.max(direction.getDirection().getHeadways().get(timeHorizonTrip1).getHeadway().getMaxHeadway(), direction.getDirection().getHeadways().get(timeHorizonTrip2).getHeadway().getMaxHeadway())){
                        write("Headway between two consecutive trips grater than max headway\n" +
                                "First trip:\t" + trips.get(i-1).getTrip().getTripId() + "\tsecond trip:\t" + trips.get(i).getTrip().getTripId());
                        return false;
                    }

                    //for professional participants the achieved headway must be grater than the max between the min headway of the two time windows
                    //achievedHeadway > max(minHeadway(timeWindow1), minHeadway(timeWindow2))
                    if(getCategory().equalsIgnoreCase("professional")){
                        if (actualheadway < Math.max(direction.getDirection().getHeadways().get(timeHorizonTrip1).getHeadway().getMinHeadway(), direction.getDirection().getHeadways().get(timeHorizonTrip2).getHeadway().getMinHeadway())){
                            write("Headway between two consecutive trips less than minimum headway\nFirst trip:\t" + trips.get(i - 1).getTrip().getTripId() + "\tsecond trip:\t" + trips.get(i).getTrip().getTripId());
                            return false;
                        }
                    }
                }
            }
        }
        return true;
    }

    /*
    //method that returns true if the output file contains an admissible solution, for the junior category of participants, for the problem in the input file
    private static boolean isJuniorAdmissible(){
        //Map<Direction, List<Trip>> tripDirectionHashMap = new HashMap<>();
        for(JsonDirection direction : outputFile.getDirections()){
            if(!inputOutputSameTrip(direction.getDirection()))
                return false;

            if(!initialFinalTrips(direction.getDirection()))
                return false;

        }

        return headwayAdmissible() && performedTrip();
    }

    //method that returns ture if the output file contains an admissible solution, for the junior category of participants, for the problem in the input file
    private static boolean isSeniorAdmissible(){
        //Map<Direction, List<Trip>> tripDirectionHashMap = new HashMap<>();
        for(JsonDirection direction : outputFile.getDirections()){
            if(!inputOutputSameTrip(direction.getDirection()))
                return false;

            if(!initialFinalTrips(direction.getDirection()))
                return false;
        }


        return headwayAdmissible() && performedTrip();
    }
    */

    //method that returns ture if the output file contains an admissible solution, for the junior category of participants, for the problem in the input file
    private static boolean isAdmissible(){
        //Map<Direction, List<Trip>> tripDirectionHashMap = new HashMap<>();
        for(JsonDirection direction : outputFile.getDirections()){
            if(!inputOutputSameTrip(direction.getDirection()))
                return false;

            if(!initialFinalTrips(direction.getDirection()))
                return false;
            /*
            tripDirectionHashMap.put(direction.getDirection(), new ArrayList<>());

            for (JsonTrip jsonTrip : direction.getDirection().getTrips()){
                tripDirectionHashMap.get(direction.getDirection()).add(jsonTrip.getTrip());
            }
             */
        }



        return headwayAdmissible() && performedTrip();
    }


    /**
     * method that compute the category of the participant team
     * @return "Junior" if the participant team belongs to the Junior category,
     *         "Senior" if the participant team belongs to the Senior category,
     *         "Professional" otherwise
     */
    public static String getCategory(){
        if(outputFile.getFleet().getPhi() != 0){
            if(outputFile.getGlobalCost().getAlpha0() != 0 || outputFile.getGlobalCost().getAlpha1() != 0 || outputFile.getGlobalCost().getAlpha2() != 0){
                return "professional";
            }
            else{
                return "senior";
            }
        }
        else{
            return "junior";
        }
    }

    /**
     * Method that write a string s on a file if the validation start online or on the terminal if the validation start
     * locally
     * @param s the string that need to be written
     */
    private static void write(String s){
        if(writeOnFile){
            try {
                writer.write(s);
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
        else{
            System.out.println(s);
        }
    }
}
