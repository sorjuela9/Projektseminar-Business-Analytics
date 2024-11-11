package validator;

import validator.validatorClasses.*;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.*;

/**
 * Class that implement the validation of a solution for a VS scheduling problem, for the purpose of the MINOA Research
 * challenge, as described at https://minoa-itn.fau.de/?page_id=968
 * @author Lorenzo Frangioni
 * @version 1.1 04/2021
 */
public class VSCost {
    private static int availableElectricVehicle;
    private static FileWriter writer;
    private static Input outputFile;
    private static boolean writeOnFile;
    public static boolean isAdmissible;

    private static final int startOfDay = 0;
    private static final int endOfDay = 97200;

    /**
     * Method that start the validation of the VS, used to handle the validation in the online version
     * @param root the path to the folder where the json file containing the solution is, the file must contains output in its name
     * @param answerFile the path of the file where the log file is
     * @return the VS cost of the solution provided
     * @throws IOException if answerFile == null
     */
    public static double start(File root, File answerFile) throws IOException{
    	//the total cost of the solution
        double vsCost = 0;

        //the file gave in input (the output.json file)
        File sourceFile = null;

        for(String pathname : Objects.requireNonNull(root.list())){
            if(pathname.toLowerCase().contains("output")){
                sourceFile = new File(root + "\\" + pathname);
            }
        }

        if(sourceFile != null){
            try {
                writer = new FileWriter(answerFile, true);
                
                ObjectMapper mapper = new ObjectMapper();

                writeOnFile = true;
                vsCost = start(mapper.readValue(sourceFile, Input.class));
            } catch (IOException e) {
                writer.write("Exception occurred: " + e.getMessage());
            } finally {
                writer.close();
            }
        }

        try {
            sourceFile.delete();
        } catch(NullPointerException e) {
            write("output file is missing, output file must contain \"output\" in the name");
            writer.close();
        }

        writeOnFile = false;
        return vsCost;
    }


    public static double start(File solution){
        ObjectMapper mapper = new ObjectMapper();

        try{
            return start(mapper.readValue(solution, Input.class));
        } catch (IOException e) {
            e.printStackTrace();
        }

        return 0;
    }


    /**
     * Method that start the validation of the VS, used to handle the validation during the ranking of the challenge
     * @param solution the representation of the json file containing the solution
     * @return the VS cost of the solution provided
     */
    public static double start(Input solution){
        double vsCost = 0;
        outputFile = solution;
        availableElectricVehicle = outputFile.getFleet().getVehicleList().get(1).getVehicleType().getElectricInfo().getNumberVehicle();

        double[] vehicleBlockCosts = new double[outputFile.getVehicleBlockList().size()];
        write("Number of utilized vehicles: " + vehicleBlockCosts.length + "\n");

        isAdmissible = isAdmissible(outputFile);
        //if all vehicle block are feasible
        if (isAdmissible){
            int i = 0;
            for (JsonVehicleBlock jsonVehicleBlock : outputFile.getVehicleBlockList()) {
                double tmpCost = computeVehicleBlockCost(jsonVehicleBlock.getVehicleBlock());
                vehicleBlockCosts[i] = tmpCost;
                vsCost += tmpCost;
                i++;
            }
            for (i = 0; i < vehicleBlockCosts.length; i++) {
                write("Vehicle type: " + outputFile.getVehicleBlockList().get(i).getVehicleBlock().getVehicleType().toUpperCase(Locale.ROOT)
                        + "\tVSCost:\t" + vehicleBlockCosts[i] + "\n");
            }

            vsCost = Math.round(vsCost * 1000d) / 1000d;
            write("Total cost of the VS:\t" + vsCost + "\n");
        }
        else{
            write("There is a not feasible vehicle block\n");
        }

        return vsCost;
    }


    /**
     * method that compute the cost of a single vehicle block, this method does not compute the feasibility of the vehicle block
     * @param vehicleBlock the vehicleBlock for which we want to compute the cost
     * @return the cost of the vehicleBlock
     */
    private static double computeVehicleBlockCost(VehicleBlock vehicleBlock){
        //list that contains all the trips performed by the solution
    	List<JsonTrip> tripList = new ArrayList<>();
        for(JsonDirection jsonDirection : outputFile.getDirections()){
            tripList.addAll(jsonDirection.getDirection().getTrips());
        }

        double usageCost = 0;
        double breakTimeCost =  outputFile.getGlobalCost().getBreakCostCoefficient();
        double pullInPullOutCost = 0;
        double co2Cost = 0;
        double cost;

        // data i need to use to calculate the VS cost of the vehicle block
        long timeOfService = 0;
        long timeOfDeadhead = 0;
        long timeOfPaidBreak = 0;

        // set the usageCost, the pullInPullOutCost and the co2Cost according to the specification in the json file
        for(JsonVehicleType jsonVehicleType : outputFile.getFleet().getVehicleList()){
            if(jsonVehicleType.getVehicleType().getVehicleTypeName().equalsIgnoreCase(vehicleBlock.getVehicleType())){
                usageCost = jsonVehicleType.getVehicleType().getUsageCost();
                pullInPullOutCost = jsonVehicleType.getVehicleType().getPullInOutCost();
                if(jsonVehicleType.getVehicleType().isElectric()){
                    co2Cost = 0;
                }
                else{
                    co2Cost = jsonVehicleType.getVehicleType().getIceInfo().getEmissionCoefficient();
                }
            }
        }

        // for every activity in the vehicle block I need to increase the variables accordingly to the type of activity
        for(Activity elem : vehicleBlock.getActivityList()){

        	// if this activity is a trip I need to increase the timeOfService of the vehicleBlock
            if((elem.getClass() == ActivityTrip.class)){
                int tmp = ((ActivityTrip) elem).getTripId();
                for(JsonTrip jTrip : tripList){
                    if(jTrip.getTrip().getTripId() == tmp){
                        Trip tripTmp = jTrip.getTrip();
                        timeOfService += tripTmp.getEndTime() - tripTmp.getStartTime();
                    }
                }
            }
            
            // if this activity is a break I need to increase the timeOfPaidBreak only if the vehicle isn't charging and
            // if the vehicle is taking a break for more time than minStoppingTime
            else if(elem.getClass() == ActivityBreak.class){

                //if the break take place in the depot the timeOfPaidBreak must not be increased, otherwise it should be
                //if the vehicle is not recharging
                if(!elem.getStartNode().equalsIgnoreCase("dep")){
                    // the node where the break take place
                    JsonNetworkNode node = outputFile.getNodes().stream()
                            .filter(jsonNetworkNode -> (jsonNetworkNode.getNode().getName().equalsIgnoreCase(elem.getStartNode())))
                            .reduce((a,b) -> {
                                throw new IllegalArgumentException("found too much nodes with the same name!");
                            }).get();

                    // the minStoppingTime of the node in the same time window when the break take place doesn't count in the timeOfPaidbreak
                    int minStoppingTimeInNode = node.getNode().getBreakingTimes().get(breakTimeHorizonIndex((ActivityBreak) elem)).getStoppingTime().getMinStoppingTime();
                    int timeOfCharge = timeOfCharge((ActivityBreak) elem);

                    timeOfPaidBreak += elem.getEndTime() - elem.getStartTime() - Math.max(timeOfCharge, minStoppingTimeInNode);

                }
            }
            // otherwise the activity is a deadheadTrip and therefore I increase the time spent on deadheadTrips
            else{
                timeOfDeadhead += elem.getEndTime() - elem.getStartTime();
            }
        }

        cost = (usageCost) + (breakTimeCost * timeOfPaidBreak) + (pullInPullOutCost * timeOfDeadhead) + (co2Cost * timeOfService);

        return Math.round(cost * 1000d) / 1000d;
    }


    /**
     * method that compute the feasibility of the solution given in input
     * @param input the solution of the PTN problem
     * @return true iff all vehicle blocks in the solution are feasible, false otherwise
     */
    private static boolean isAdmissible(Input input){

        //the list of nodes in the Public Transportation network
        List<Node> nodes = new ArrayList<>();

        //list of deadhead arcs in the PTN
        List<JsonDeadheadArc> deadheadArcs = input.getDeadheadArcs();

        //map the tripId with the corresponding trip
        Map<Integer, Trip> tripHashMap = initializeTripHashMap();

        //map the direction with the corresponding trips
        Map<Direction, List<Trip>> tripDirectionHashMap = initializeTripDirectionHashMap();


        //map the node name with the number of available parking, slow charging and fast charging spots
        Map<String, List<Integer>> parkingSpotHashMap = new HashMap<>();
        Map<String, List<Integer>> slowChargeHashMap = new HashMap<>();
        Map<String, List<Integer>> fastChargeHashMap = new HashMap<>();

        //PTN timeHorizon array
        int[] timeHorizon = input.getTimeHorizon();

        //for every node in the PTN initialize the list of parking, slow charging and fast charging spots
        for(JsonNetworkNode elem : input.getNodes()){
            nodes.add(elem.getNode());
            parkingSpotHashMap.put(elem.getNode().getName(), new ArrayList<>());
            slowChargeHashMap.put(elem.getNode().getName(), new ArrayList<>());
            fastChargeHashMap.put(elem.getNode().getName(), new ArrayList<>());
        }

        // for each node in the PTN, for every minute of service set the exact number of available parking, slow charging
        // and fast charging spots
        for (Node node : nodes) {
            for (int i = 0; i < (timeHorizon[timeHorizon.length - 1] - timeHorizon[0]) / 60; i++) {
                //set the value for minute i
                parkingSpotHashMap.get(node.getName()).add(i, node.getBreakCapacity());
                slowChargeHashMap.get(node.getName()).add(i, node.getSlowChargeCapacity());
                fastChargeHashMap.get(node.getName()).add(i, node.getFastChargeCapacity());
            }
        }

        //the vehicle block number i'm looking at
        int vehicleBlockNumber = 0;

        System.out.println("Min deadhead start time = " + minDeadheadStartTime());
        System.out.println("Max deadhead end time = " + maxDeadheadEndTime() + "\n");

        //check electric feasibility of the solution
        for (JsonVehicleBlock block : input.getVehicleBlockList()) {

            //parse the json object in a vehicle block object
            VehicleBlock vehicleBlock = block.getVehicleBlock();

            // if the selected vehicle block is electric
            if (vehicleBlock.getVehicleType().toLowerCase().contains("electric")) {

                //decrease the number of available electric vehicles
                availableElectricVehicle -= 1;

                //there is a fixed number of electric vehicle that the solution can contains
                if(availableElectricVehicle < 0){
                    write("Used to many electric vehicles");
                    return false;
                }

                write("analyzing autonomy constrains of the vehicle block number: " + vehicleBlockNumber);

                //electric autonomy
                double autonomy = 1;

                //residual autonomy of the vehicle, start equals the autonomy
                double residualAutonomy = autonomy;

                //complementary autonomy (starts at 0 -> autonomy - residualAutonomy = 0)
                double complementaryAutonomy = 0;

                double fastRechargeCoefficient = input.getFleet().getPhi();

                //the time that the vehicle need to take a full recharges (0% -> 100%)
                long maximumChargingTime = 1;

                long minimumChargingTime = 86400;

                //set the variables according to the values passed in the json file
                for(JsonVehicleType jsonVehicleType : input.getFleet().getVehicleList()){
                    if(jsonVehicleType.getVehicleType().getVehicleTypeName().equalsIgnoreCase(vehicleBlock.getVehicleType())){
                        autonomy = jsonVehicleType.getVehicleType().getElectricInfo().getVehicleAutonomy();
                        residualAutonomy = autonomy;
                        maximumChargingTime = jsonVehicleType.getVehicleType().getElectricInfo().getMaxChargingTime();
                        minimumChargingTime = jsonVehicleType.getVehicleType().getElectricInfo().getMinChargingTime();
                    }
                }

                //for every activity in the selected vehicle block
                for (Activity activity : vehicleBlock.getActivityList()){

                    //if the activity is a trip the residual autonomy will decrease
                    if(activity.getClass() == ActivityTrip.class){
                        //get information about the selected trip
                        Trip tmpTrip = tripHashMap.get(((ActivityTrip) activity).getTripId());
                        //decrease the residual autonomy accordingly to the length of the trip
                        residualAutonomy = residualAutonomy - tmpTrip.getLengthTrip();
                        //increase the complementary autonomy accordingly to the length of the trip
                        complementaryAutonomy += tmpTrip.getLengthTrip();
                        write("Residual autonomy after a trip = " + residualAutonomy);
                    }

                    //if the activity is a break, and the vehicle is charging the residual autonomy will increase
                    if(activity.getClass() == ActivityBreak.class){

                        //for every type of break in the break activity
                        // QUA VIENE CONTROLLATA ANCHE CHE LA DURATA DELLA RICARICA NON SI PROTRAGGA PER PIU' TEMPO DEL NECESSARIO
                        for (int i = 0; i < ((ActivityBreak) activity).getBreakActivities().size(); i++) {
                            BreakActivity tmp = ((ActivityBreak) activity).getBreakActivities().get(i).getBreakActivity();

                            int minutesOfCharge, estimatedMinutesForCompleteCharge;

                            //if the break take place in a fast charge spot and the vehicle is charging
                            if(tmp.getTypeSpot().equalsIgnoreCase("fastCharging") && tmp.isCharging){
                                //the number of km gained with the recharges
                                double partialRecharge = (autonomy * ((tmp.getEndTime() - tmp.getStartTime())/(fastRechargeCoefficient * (double)maximumChargingTime)));

                                // estimatedMinutesForCompleteCharge (sia fast che slow) sono una sottostima del tempo di ricarica necessario
                                estimatedMinutesForCompleteCharge = (int) (((fastRechargeCoefficient * maximumChargingTime) * (complementaryAutonomy/autonomy))/60);
                                minutesOfCharge = (tmp.getEndTime() - tmp.getStartTime())/60;

                                if(minutesOfCharge > estimatedMinutesForCompleteCharge + 1){
                                    write("During a break in node " + activity.getStartNode() + " between " +
                                            activity.getStartTime() + " and " + activity.getEndTime() + " for a duration of " +
                                            minutesOfCharge + " minutes, the vehicle block " + vehicleBlockNumber +
                                            " recharged for too long\nA fast charge of duration : " + (estimatedMinutesForCompleteCharge + 1)
                                            +" minutes is sufficient\n");
                                    return false;
                                }

                                if(minutesOfCharge < (minimumChargingTime/60)){
                                    write("During a break in node " + activity.getStartNode() + " between " +
                                            activity.getStartTime() + " and " + activity.getEndTime() + " for a duration of " +
                                            minutesOfCharge + " minutes, the vehicle block " + vehicleBlockNumber +
                                            " recharged for too little, must recharge for at least " + minimumChargingTime/60 + " minutes");
                                    return false;
                                }


                                //the vehicle recharged completely
                                if(partialRecharge >= complementaryAutonomy){
                                    complementaryAutonomy = 0;
                                    residualAutonomy = autonomy;
                                }
                                //the residual autonomy of the vehicle increase but not reach the full autonomy
                                else{
                                    complementaryAutonomy -= partialRecharge;
                                    residualAutonomy += partialRecharge;
                                }

                                write("-------\n" + "fast charge gained: " + partialRecharge + "\n-------");
                                write("residual autonomy = " + residualAutonomy);
                            }

                            //if the break take place in a slow charge spot and the vehicle is charging
                            if(tmp.getTypeSpot().equalsIgnoreCase("slowCharging") && tmp.isCharging){
                                //the number of km gained with the recharges
                                double partialRecharge = autonomy * ((tmp.getEndTime()- tmp.getStartTime())/(double)maximumChargingTime);

                                estimatedMinutesForCompleteCharge = (int) ((maximumChargingTime * (complementaryAutonomy/autonomy))/60);
                                minutesOfCharge = (tmp.getEndTime() - tmp.getStartTime())/60;

                                if(minutesOfCharge > estimatedMinutesForCompleteCharge + 1){
                                    write("During a break in node " + activity.getStartNode() + " between " +
                                            activity.getStartTime() + " and " + activity.getEndTime() + " for a duration of " +
                                            minutesOfCharge + " minutes, the vehicle block " + vehicleBlockNumber +
                                            " recharged for too long\nA slow charge of duration : " + (estimatedMinutesForCompleteCharge + 1)
                                            +" minutes is sufficient\n");
                                    return false;
                                }

                                if(minutesOfCharge < (minimumChargingTime/60)){
                                    write("During a break in node " + activity.getStartNode() + " between " +
                                            activity.getStartTime() + " and " + activity.getEndTime() + " for a duration of " +
                                            minutesOfCharge + " minutes, the vehicle block " + vehicleBlockNumber +
                                            " recharged for too little, must recharge for at least " + minimumChargingTime/60 + " minutes");
                                    return false;
                                }

                                //the vehicle recharged completely
                                if(partialRecharge >= complementaryAutonomy){
                                    complementaryAutonomy = 0;
                                    residualAutonomy = autonomy;
                                }
                                //the residual autonomy of the vehicle increase but not reach the full autonomy
                                else{
                                    complementaryAutonomy -= partialRecharge;
                                    residualAutonomy += partialRecharge;
                                }

                                write("-------\n" + "slow charge gained: " + partialRecharge + "\n-------");
                                write("residual autonomy = " + residualAutonomy);
                            }


                        }
                    }

                    //if the activity is a deadhead, the residual autonomy will decrease
                    if(activity.getClass() == Deadhead.class){

                        //for every deadhead arc in the PTN
                        for(JsonDeadheadArc jsonDeadheadArc : deadheadArcs){
                            //if the selected deadhead arc have the same code as the one in the vehicle block
                            if(jsonDeadheadArc.getDeadheadArc().getDeadheadArcCode() == ((Deadhead) activity).getDeadheadArcCode()){
                                //the residual autonomy decrease
                                residualAutonomy -= jsonDeadheadArc.getDeadheadArc().getArcLength();
                                complementaryAutonomy += jsonDeadheadArc.getDeadheadArc().getArcLength();
                                write("Residual autonomy after a deadhead = " + residualAutonomy);
                            }
                        }
                    }
                    //the autonomy of the vehicle reached 0
                    if(residualAutonomy < 0){
                        write("Residual autonomy of vehicle block "+vehicleBlockNumber+ " reached 0");
                        return false;
                    }
                }
                write("\n");
            }
            
            //look at the next vehicle block
            vehicleBlockNumber++;
        }

        //check the parking, slow charge and fast charge spot for every vehicle block
        for(JsonVehicleBlock block : input.getVehicleBlockList()){
            VehicleBlock vehicleBlock = block.getVehicleBlock();

            //for each activity n the vehicle block
            for(Activity activity : vehicleBlock.getActivityList()){

                //if the selected activity is a break
                if(activity.getClass() == ActivityBreak.class){

                    //the node where the break take place, the same for every break activity
                    String node = activity.getStartNode();

                    //for every break in the break activity
                    for (int i = 0; i < ((ActivityBreak) activity).getBreakActivities().size(); i++) {
                    	//the start time of the break
                        int startTime = ((ActivityBreak) activity).getBreakActivities().get(i).getBreakActivity().getStartTime();
                        //the end time of the break
                        int endTime = ((ActivityBreak) activity).getBreakActivities().get(i).getBreakActivity().getEndTime();
                        //minute of break
                        int stopTime = (endTime-startTime) / 60;

                        //for every minute that the vehicle is taking a break decrease the right spot in the right minute
                        for (int j = 0; j < stopTime; j++) {

                            //if the vehicle is taking a break in a parking spot
                            if(((ActivityBreak) activity).getBreakActivities().get(i).getBreakActivity().getTypeSpot().equalsIgnoreCase("parking")){
                                int availableParkingSpot = parkingSpotHashMap.get(node).get(((startTime - timeHorizon[0])/60) + j);
                                parkingSpotHashMap.get(node).set((((startTime - timeHorizon[0])/60) + j), availableParkingSpot-1);
                            }
                            
                            //if the vehicle is taking a break in a slow charge spot
                            else if(((ActivityBreak) activity).getBreakActivities().get(i).getBreakActivity().getTypeSpot().equalsIgnoreCase("slowCharging")){
                                int availableSlowChargeSpot = slowChargeHashMap.get(node).get(((startTime - timeHorizon[0])/60) + j);
                                slowChargeHashMap.get(node).set((((startTime - timeHorizon[0])/60) + j), availableSlowChargeSpot-1);
                            }

                            //if the vehicle is taking a break in a fast charge spot
                            else{
                                int availableFastChargeSpot = fastChargeHashMap.get(node).get(((startTime - timeHorizon[0])/60) + j);
                                fastChargeHashMap.get(node).set((((startTime - timeHorizon[0])/60) + j), availableFastChargeSpot-1);
                            }


                        }
                    }
                }
            }
        }

        //for junior category the control of the parking spots are disabled
        boolean isJuniorCategory = false;
        if(input.getGlobalCost().getAlpha0() == 0
                && input.getGlobalCost().getAlpha1() == 0
                && input.getGlobalCost().getAlpha2() == 0
                && input.getFleet().getPhi() == 0){
            isJuniorCategory = true;
        }

        //check the various parking slot capacity iff the participant team belongs to Senior or Professional category
        if(!isJuniorCategory){

        	//for every node in the PTN
            for(String node : parkingSpotHashMap.keySet()){
                List<Integer> parkingSpot = parkingSpotHashMap.get(node);
                List<Integer> slowChargeSpot = slowChargeHashMap.get(node);
                List<Integer> fastChargeSpot = fastChargeHashMap.get(node);

                //for every minute in the PTN
                for (int i = 0; i < parkingSpot.size(); i++) {
                	//if there number of vehicles stopped in a parking spot in the node in a determinate minute exceed the number of available parking spots
                    if(parkingSpot.get(i) < 0){
                        write("Exceeded parking capacity in  " + node + " at second: " +(timeHorizon[0] + (i*60)) + "\n");
                        return false;
                    }
                    
                    //if there number of vehicles stopped in a slow charge spot in the node in a determinate minute exceed the number of available slow charge spots
                    else if(slowChargeSpot.get(i) < 0){
                        write("Exceeded slow charge spot capacity in " + node + " at second: " +(timeHorizon[0] + (i*60)) + "\n");
                        return false;
                    }
                    
                    //if there number of vehicles stopped in a fast charge spot in the node in a determinate minute exceed the number of available fast charge spots
                    else if(fastChargeSpot.get(i) < 0){
                        write("Exceeded fast charge spot capacity in " + node + " at second: " +(timeHorizon[0] + (i*60)) + "\n");
                        return false;
                    }
                }
            }
        }

        vehicleBlockNumber = 0;

        for (int i = 0; i < input.getVehicleBlockList().size(); i++) {
            JsonVehicleBlock vehicleBlock = input.getVehicleBlockList().get(i);
            List<Activity> activities = vehicleBlock.getVehicleBlock().getActivityList();

            //check the feasibility of every couple of activity in the vehicle block
            for (int j = 1; j < activities.size(); j++) {
                if(!compatible(activities.get(j-1), activities.get(j), tripDirectionHashMap, tripHashMap))
                    return false;
            }

            //check the feasibility of every break in the vehicle block
            for (int j = 1; j < activities.size() - 1; j++) {
                Activity activity1 = activities.get(j - 1);
                Activity activity2 = activities.get(j);
                Activity activity3 = activities.get(j + 1);

                //if i'm looking at a break
                if(activity2.getClass() == ActivityBreak.class){
                    boolean betweenTrip = false;

                    //if the break is between two trips
                    if((activity1.getClass() == activity3.getClass()) && activity1.getClass() == ActivityTrip.class){
                        betweenTrip = true;
                    }

                    if(!feasibleBreak((ActivityBreak) activity2, betweenTrip)){
                        return false;
                    }
                }
            }

            //if the vehicle block does not start or end with a deadhead it's not feasible
            if(!startAndEndWithDeadhead(vehicleBlock, vehicleBlockNumber++)){
                return false;
            }
        }

        //all vehicle blocks are feasible
        return true;
    }



    /*
   possible couples:
       deadhead - trip
       deadhead - break
       deadhead - deadhead
       trip - deadhead
       trip - break
       trip - trip
       break - trip
       break - deadhead
       break - break  -- technically is an error
    */
    /**
     * method that check the compatibility between two activities of the same vehicle block
     * @param activity1 the activity that happens chronologically first
     * @param activity2 the activity that happens chronologically second
     * @param tripDirectionMap map containing for every direction relative list of trips
     * @param tripHashMap map that containing for every tripId the relative trip
     * @return true iff the two activities are compatible, false otherwise
     */
    private static boolean compatible(Activity activity1, Activity activity2, Map<Direction, List<Trip>> tripDirectionMap, Map<Integer, Trip> tripHashMap){

        if(activityOutDay(activity1) || activityOutDay(activity2)){
            write("There is an activity that start before " + startOfDay + " or end after " + endOfDay);
            return false;
        }

        //trip - ...
        if(activity1.getClass() == ActivityTrip.class){

            //trip - trip
            if(activity2.getClass() == ActivityTrip.class){
                String endNodeTrip1 = null, startNodeTrip2 = null;
                long endTimeTrip1 = -1, startTimeTrip2 = -1;
                int timeHorizonIndexTrip1 = -1, timeHorizonArrivalTimeTrip1 = -1;
                int firstTripId = -1, secondTripId = -1;

                //looking for each direction information about the trips
                for(Direction direction : tripDirectionMap.keySet()){
                    //if in this direction there is the trip equals the first one of the couple in the vehicle block
                    if(tripDirectionMap.get(direction).contains(tripHashMap.get(((ActivityTrip) activity1).getTripId()))){
                        endNodeTrip1 = direction.getEndNode();
                        endTimeTrip1 = tripHashMap.get(((ActivityTrip) activity1).getTripId()).getEndTime();
                        firstTripId = tripHashMap.get((((ActivityTrip) activity1).getTripId())).getTripId();
                        timeHorizonIndexTrip1 = tripTimeHorizonIndex(tripHashMap.get((((ActivityTrip) activity1).getTripId())));
                        timeHorizonArrivalTimeTrip1 = timeHorizonArrivalTime(tripHashMap.get((((ActivityTrip) activity1).getTripId())));
                    }
                    //if in this direction there is the trip equals the second one of the couple in the vehicle block
                    if(tripDirectionMap.get(direction).contains(tripHashMap.get(((ActivityTrip) activity2).getTripId()))){
                        startNodeTrip2 = direction.getStartNode();
                        startTimeTrip2 = tripHashMap.get(((ActivityTrip) activity2).getTripId()).getStartTime();
                        secondTripId = tripHashMap.get((((ActivityTrip) activity2).getTripId())).getTripId();
                    }
                }

                //if I couldn't find any information about the trips
                if(endNodeTrip1 == null || startNodeTrip2 == null){
                    write("Node error with a trip\n");
                    return false;
                }

                //if the second trip does not start in the same spot as the first trip end
                if(!endNodeTrip1.equalsIgnoreCase(startNodeTrip2)) {
                    write("There is a couple of adjacent trip such that endNodeTrip1 != startNodeTrip2" +
                            "\nTrip1 id: " + firstTripId + "\tTrip2 id: " + secondTripId);
                    return false;
                }

                //if one of the trips does not belong at the time horizon
                if(!(endTimeTrip1 >= 0 && startTimeTrip2 >= 0)){
                    write("Time error with a trip, one trip between" +
                            "\n" + firstTripId + " and " + secondTripId + " have a startTime < 0, please check your solution");
                    return false;
                }

                // ----- NEW -----
                final String finalEndNodeTrip = endNodeTrip1;
                JsonNetworkNode tmp = outputFile.getNodes().stream()
                        .filter(jsonNetworkNode -> (jsonNetworkNode.getNode().getName().equalsIgnoreCase(finalEndNodeTrip)))
                        .reduce((a, b) -> {
                            throw new IllegalArgumentException("found to many nodes with the same name!");
                        }).get();

                int minStoppingTime = outputFile.getNodes().get(outputFile.getNodes().indexOf(tmp)).getNode()
                        .getBreakingTimes().get(timeHorizonArrivalTimeTrip1).getStoppingTime().getMinStoppingTime();

                if(minStoppingTime > 0){
                    write("There is a couple (trip, trip) with" +
                            "\ntrip1 id: " + firstTripId + "\ttrip2 id: " + secondTripId +
                            "\nendTimetrip1: " + endTimeTrip1 + "\tstartTimeTrip2: " + startTimeTrip2 +
                            "\nendNodeTrip1: " + endNodeTrip1 +"\tstartNodeTrip2: " + startNodeTrip2 +
                            "\nTaking place in a time window where minStoppingTime of node " + endNodeTrip1 +" = " + minStoppingTime +
                            "\nThere should be a break between the two trips of at least " + minStoppingTime + " seconds");
                    return false;
                }
                // ----- END NEW ----

                //if the second trip does not start when the first one ends
                if(!(endTimeTrip1 == startTimeTrip2)) {
                    write("endTimeTrip1 != startTimeTrip2" +
                            "\ntrip1 id: " + firstTripId + "\ttrip2 id: " + secondTripId +
                            "\nendTimeTrip1 = " + endTimeTrip1 + "\tstartTimeTrip2 = " + startTimeTrip2);
                    return false;
                }

                return true;
            }

            //trip - break
            else if(activity2.getClass() == ActivityBreak.class){
                //for each direction
                for(Direction direction : tripDirectionMap.keySet()){
                    //if the selected direction contains the trip with tripId equals the one I am looking at
                    if(tripDirectionMap.get(direction).contains(tripHashMap.get(((ActivityTrip) activity1).getTripId()))){
                        //if the end node of the trip is not the same as the start node of the break
                        if(!(direction.getEndNode().equalsIgnoreCase(activity2.getStartNode()))){
                            write("There is a couple (trip, break) such that endNodeTrip != startNodeBreak" +
                                    "\nTrip id: " + tripHashMap.get(((ActivityTrip) activity1).getTripId()).getTripId());
                            return false;
                        }

                        //if the break does not start when the trip end
                        if(tripHashMap.get(((ActivityTrip) activity1).getTripId()).getEndTime() != ((ActivityBreak) activity2).getBreakActivities().get(0).getBreakActivity().getStartTime()){
                            write("There is a couple (trip, break) such that endTimeTrip != startTimeBreak" +
                                    "\nTrip id: " + tripHashMap.get(((ActivityTrip) activity1).getTripId()).getTripId());
                            return false;
                        }
                    }
                }

                return true;
            }

            //trip - deadhead
            else if(activity2.getClass() == Deadhead.class){
                //for each direction
                for(Direction direction : tripDirectionMap.keySet()){
                    //if the selected direction contains the trip with tripId equals the one I am looking at
                    if(tripDirectionMap.get(direction).contains(tripHashMap.get(((ActivityTrip) activity1).getTripId()))){
                        //if the deadhead trip does not start when the trip ends
                        if(tripHashMap.get(((ActivityTrip) activity1).getTripId()).getEndTime() != activity2.getStartTime()){
                            write("There is a couple (trip, deadheadTrip) such that endTimeTrip != startTimeDeadhead" +
                                    "\nTrip id: " + tripHashMap.get(((ActivityTrip) activity1).getTripId()).getTripId());
                            return false;
                        }

                        //for every deadhead arc in the PTN
                        for(JsonDeadheadArc deadheadArc : outputFile.getDeadheadArcs()){
                            //if the deadhead arc I'm looking at have the same code as the one in the vehicle block
                            if(deadheadArc.getDeadheadArc().getDeadheadArcCode() == ((Deadhead) activity2).getDeadheadArcCode()){
                                //if the deadhead does not start where the trip ends and the deadhead type isn't "pullIn"
                                if(!(deadheadArc.getDeadheadArc().getDeadheadType().equalsIgnoreCase("pullIn"))){
                                    write("There is a couple (trip, deadheadTrip) such that deadheadType != \"pullIn\"");
                                    return false;
                                }
                                if(!(deadheadArc.getDeadheadArc().getTerminalNode().equalsIgnoreCase(direction.getEndNode()))){
                                    write("There is a couple (trip, deadheadTrip) such that endNodeTrip != endNodeDeadhead");
                                    return false;
                                }
                            }
                        }
                    }
                }

                return true;
            }
        }

        //break - ...
        else if(activity1.getClass() == ActivityBreak.class){

            //break - trip
            if(activity2.getClass() == ActivityTrip.class){
                //for every possible direction
                for(Direction direction : tripDirectionMap.keySet()){
                    //if the list of trips associated at the selected direction contains the information about the trip
                    if(tripDirectionMap.get(direction).contains(tripHashMap.get(((ActivityTrip) activity2).getTripId()))){
                        //if the trip does not start where the break take place
                        if(!(direction.getStartNode().equalsIgnoreCase(activity1.getEndNode()))){
                            write("There is a couple (break, trip) such that breakEndNode != tripStartNode\n");
                            return false;
                        }

                        //if the trip does not start when the break activity finish
                        if(((ActivityBreak) activity1).getBreakActivities().get(((ActivityBreak) activity1).getBreakActivities().size()-1).getBreakActivity().getEndTime()
                                !=
                                tripHashMap.get(((ActivityTrip) activity2).getTripId()).getStartTime()){
                            write("There is a couple (break, trip) such that breakEndTime != tripStartTime\n");
                            return false;
                        }
                    }
                }

                return true;
            }


            //break - break
            else if(activity2.getClass() == ActivityBreak.class){
                write("There is a couple (break, break)\n" +
                        "This type of succession of activities isn't allowed, please add stoppingTimes to the list of the break");
                return false;
            }

            //break - deadhead
            else if(activity2.getClass() == Deadhead.class){

                //se il break non sta avvenendo al deposito devo effettuare una sosta solo per ricaricare
                if(!activity1.getStartNode().equalsIgnoreCase("dep")){
                    if(!onlyForCharge((ActivityBreak) activity1)){
                        write("Break in node: " + activity1.getStartNode() + ", taking place at time: "
                                + activity1.getStartTime() + " - " + activity1.getEndTime() + " is taking place before a deadhead trip, " +
                                "but it isn't entirely dedicated to the recharge of an electric vehicle\nHence the solution isn't admissible");
                        return false;
                    }
                }


                //for every deadhead arc
                for(JsonDeadheadArc jsonDeadheadArc : outputFile.getDeadheadArcs()){

                    //if the selected deadhead arc have the same arcCode as the one in the vehicle block
                    if(jsonDeadheadArc.getDeadheadArc().getDeadheadArcCode() == ((Deadhead) activity2).getDeadheadArcCode()){

                        //if the deadhead is a pull out, hence the vehicle is leaving the depot
                        if(jsonDeadheadArc.getDeadheadArc().getDeadheadType().equalsIgnoreCase("pullOut")){

                            //if the break did not take place in the depot
                            if(!activity1.getEndNode().equalsIgnoreCase("dep")){
                                write("There is a couple (break, deadheadTrip) such that breakNode != \"dep\" ^ deadheadType = \"pullOut\"");
                                return false;
                            }
                        }

                        //in this case the deadhead is a pull in, hence the vehicle is going to the depot
                        //if the break did not take place in the same node in the other terminal of the deadhead arc
                        else if (!jsonDeadheadArc.getDeadheadArc().getTerminalNode().equalsIgnoreCase(activity1.getEndNode())){
                            write("There is a couple (break, deadheadTrip) such that breakEndNode != deadheadTerminalNode\n");
                            return false;
                        }
                    }
                }

                //if the deadhead does not start when the break ends
                if(((ActivityBreak) activity1).getBreakActivities().get(((ActivityBreak) activity1).getBreakActivities().size()-1).getBreakActivity().getEndTime()
                        !=
                        activity2.getStartTime()){
                    write("There is a couple (break, deadheadTrip) such that breakEndTime != deadheadStartTime\n");
                    return false;
                }

                return true;
            }
        }

        //deadhead - ...
        else if(activity1.getClass() == Deadhead.class){
            //since in the vehicle block there only is the deadheadArcCode and some information about times there is a need
            //to store every information in a new deadheadArc, in this case I can search it just on time

            DeadheadArc deadheadArc = computeDeadheadArc((Deadhead) activity1);


            //deadhead - trip
            if(activity2.getClass() == ActivityTrip.class){
                for(Direction direction : tripDirectionMap.keySet()){
                    if(tripDirectionMap.get(direction).contains(tripHashMap.get(((ActivityTrip) activity2).getTripId()))){
                        //if deadheadArc is a pull out, hence the vehicle is leaving the depot
                        //and the terminal node of the deadhead is not the same as the start node of the trip
                        assert deadheadArc != null;
                        if(deadheadArc.getDeadheadType().equalsIgnoreCase("pullOut") && !deadheadArc.getTerminalNode().equalsIgnoreCase(direction.getStartNode())){
                            write("There is a couple (deadhead,trip) such that:" +
                                    "\ndeadhead type -> pullOut" +
                                    "\ndeadhead terminal node: " + deadheadArc.getTerminalNode() + " != trip start node: " + direction.getStartNode() +
                                    "\ndeadhead started at " + activity1.getStartTime() + " and ended at " + activity1.getEndTime());
                            return false;
                        }

                        //if deadheadArc is a pull in, hence the vehicle is returning to the depot, and the terminal node of the deadhead
                        //is not the same as the end node of the trip
                        else if(deadheadArc.getDeadheadType().equalsIgnoreCase("pullIn") && !deadheadArc.getTerminalNode().equalsIgnoreCase(direction.getEndNode())){
                            write("There is a couple (deadhead,trip) such that:" +
                                    "\ndeadhead type -> pullIn" +
                                    "\ndeadhead terminal node: " + deadheadArc.getTerminalNode() + " != trip end node: " + direction.getEndNode() +
                                    "\ndeadhead started at " + activity1.getStartTime() + " and ended at " + activity1.getEndTime());
                            return false;
                        }
                    }
                }
                return true;
            }

            //deadhead - break
            else if(activity2.getClass() == ActivityBreak.class){
                //if the deadhead is a pull out, hence the vehicle is leaving the depot
                //and the node where the break take place isn't the terminal node of the deadhead
                assert deadheadArc != null;
                if(deadheadArc.getDeadheadType().equalsIgnoreCase("pullOut") && !activity2.getStartNode().equalsIgnoreCase(deadheadArc.getTerminalNode())){
                    write("There is a couple (deadheadTrip, break) such that deadhead type -> pullOut, break node != dep\n");
                    return false;
                }
                //the deadhead is a pull in, hence the vehicle is returning to the depot
                else if(deadheadArc.getDeadheadType().equalsIgnoreCase("pullIn")){
                    //if the node where the break take place isn't the depot
                    if(!activity2.getEndNode().equalsIgnoreCase("dep")){
                        write("There is a couple (deadheadTrip, break) such that:" +
                                "\ndeadhead type -> pullIn" +
                                "\ndeadhead terminal node: " + deadheadArc.getTerminalNode() + " != break node: " + activity2.getStartNode() +
                                "\ndeadhead start at " + activity1.getEndTime());
                        return false;
                    }

                    //
                    if(!activity2.getStartNode().equalsIgnoreCase("dep") && !onlyForCharge((ActivityBreak) activity2)){
                        write("Break in node: " + activity2.getStartNode() + ", taking place during time: "
                                + activity2.getStartTime() + " - " + activity2.getEndTime() + " is taking place after a deadhead trip, " +
                                "but it isn't entirely dedicated to the recharge of an electric vehicle\nHence the solution isn't admissible");
                        return false;
                    }

                    //if the break does not start when the deadhead trip ends
                    if(activity1.getEndTime() != activity2.getStartTime()){
                        write("There is a couple (deadheadTrip, break) such that deadhead endTime != break startTime\n");
                        return false;
                    }
                }

                return true;
            }

            //deadhead - deadhead
            else if(activity2.getClass() == Deadhead.class){
                //looking upon all possible deadhead arcs
                for(JsonDeadheadArc jsonDeadheadArc : outputFile.getDeadheadArcs()){
                    //if the selected deadhead arc have the same code as the one in the vehicle block
                    if(jsonDeadheadArc.getDeadheadArc().getDeadheadArcCode() == ((Deadhead) activity2).getDeadheadArcCode()){
                        //if both deadhead arc have the same type (pullIn - pullIn or pullOut - pullOut)
                        assert deadheadArc != null;
                        if(deadheadArc.getDeadheadType().equalsIgnoreCase(jsonDeadheadArc.getDeadheadArc().getDeadheadType())){
                            write("There is a couple (deadheadTrip, deadheadTrip) that have the same type (pullIn - pullIn || pullOut - pullOut)\n");
                            return false;
                        }
                        else if(activity1.getEndTime() != activity2.getStartTime()){
                            write("There is a couple (deadheadTrip, deadheadTrip) such that deadhead1 endTime != deadhead2 startTime\n");
                            return false;
                        }
                        return true;
                    }
                }
            }
        }

        write("One activity have illegal type, activity class -> " + activity1.getClass().toString() + "other activity class -> " + activity2.getClass().toString());
        return false;
    }

    private static boolean activityOutDay(Activity activity1) {
        return activity1.getStartTime() < startOfDay || activity1.getEndTime() > endOfDay;
    }

    /**
     * method that compute the feasibility of a break
     * @param activityBreak the break to check
     * @param betweenTrips boolean set to true if the activity is between two trips, false otherwise
     * @return True if, betweenTrips = true and, in the time window where the break take place, minStoppingTime <= activityBreak.duration <= maxStoppingTime.
     * or if betweenTrips = false and activityBreak.duration < maxStoppingTime
     * False otherwise
     */
    private static boolean feasibleBreak(ActivityBreak activityBreak, boolean betweenTrips){
        int timeHorizonIndex = breakTimeHorizonIndex(activityBreak);

        if(timeHorizonIndex == -1){
            write("A problem occurred with break at node: " + activityBreak.getStartNode()  +
                    " that start at " + activityBreak.getStartTime() + " and end at " + activityBreak.getEndTime() +
                    "\nThe break does not belong to the time horizon");
            return false;
        }

        Node tmp = outputFile.getNodes().stream()
                .filter(jsonNetworkNode -> (jsonNetworkNode.getNode().getName().equalsIgnoreCase(activityBreak.getStartNode())))
                .reduce((a, b) -> {
                    throw new IllegalArgumentException("found to many nodes with the same name");
                }).get().getNode();

        int totalStopTime = activityBreak.getEndTime() - activityBreak.getStartTime();
        int maxStopTime = tmp.getBreakingTimes().get(timeHorizonIndex).getStoppingTime().getMaxStoppingTime();
        int minStopTime = tmp.getBreakingTimes().get(timeHorizonIndex).getStoppingTime().getMinStoppingTime();

        //check if the break last more than maxStoppingTime
        if(totalStopTime > maxStopTime){
            write("Break at node: " + activityBreak.getStartNode()  +" that start at " + activityBreak.getStartTime()
                    + " and end at " + activityBreak.getEndTime() + " exceed the maximum stopping time at the node by "
                    + (totalStopTime - maxStopTime) + " seconds");
            return false;
        }

        //if the break fall between two trips or took place in the deopt check if last less than minStoppingTime
        if(betweenTrips || activityBreak.getStartNode().equalsIgnoreCase("dep")){
            if(totalStopTime < minStopTime){
                write("Break at node: " + activityBreak.getStartNode()  + " that start at " + activityBreak.getStartTime()
                        + " and end at " + activityBreak.getEndTime() + " isn't long enough, the stop need to be prolonged by "
                        + (totalStopTime - maxStopTime) + " seconds");
                return false;
            }
        }

        //the break is feasible
        return true;
    }


    /**
     * Method that compute the index of the time horizon where a mainStopArrivalTime of a trip belongs
     * @param trip the trip for which we are interested in know the timeHorizon index
     * @return the timeHorizon index of the trip given in input, such that 0 <= timeHorizon index <= timeHorizon.length,
     * -1 if the trip does not belong to the timeHorizon
     */
    private static int tripTimeHorizonIndex(Trip trip){
        //for every index in the timeHorizon
        for (int i = 1; i < outputFile.getTimeHorizon().length; i++) {
            //if timeHorizon[i-1] <= trip.mainStopArrivalTime <= timeHorizon[i] then the trip belongs to timeHorizon[i-1]
            if(trip.getMainStopArrivalTime() <= outputFile.getTimeHorizon()[i] && trip.getMainStopArrivalTime() >= outputFile.getTimeHorizon()[i-1])
                return i-1;
        }

        write("trip " + trip.getTripId() + " main stop arrival time does not belong to the time horizon, impossible compute directions TT cost ");

        return -1;
    }

    /**
     * Method that compute the index of the time horizon where the endNodeArrivalTime of a trip belongs
     * @param trip the trip for which we are interested in know the timeHorizon index
     * @return the timeHorizon index of the trip given in input, such that 0 <= timeHorizon index <= timeHorizon.length,
     * -1 if the trip does not belong to the timeHorizon
     */
    private static int timeHorizonArrivalTime(Trip trip){
        return getTimeHorizonIndex(trip.getEndTime());
    }

    /**
     * Method that compute the index of the time horizon where the deadhead take place, for pullIn deadheads this mean
     * when the deadhead starts, for pullOut ones this mean when the deadhead ends
     * @param deadhead the deadhead for which we are interested in know the timeHorizon index
     * @return the timeHorizon index of the deadhead given in input, -1 if the deadhead does not belong to the timeHorizon
     */
    //TODO aggiustare
    private static int timeHorizonDeadhead(Deadhead deadhead){
        int result = -1;
        DeadheadArc deadheadArc = computeDeadheadArc(deadhead);
        assert deadheadArc != null;

        if(activityOutDay(deadhead)){
            result = -1;
        }
        else if(deadhead.mainStopTime() < outputFile.getTimeHorizon()[0]){
            result = 0;
        }
        else if(deadhead.mainStopTime() > outputFile.getTimeHorizon()[outputFile.getTimeHorizon().length - 1]){
            result = deadheadArc.getTravelTimes().size() - 1;
        }
        else{
            result = getTimeHorizonIndex(deadhead.mainStopTime());
        }


        return result;
    }

    private static JsonDeadheadArc computeJsonDeadheadArc(Deadhead deadhead){
        JsonDeadheadArc deadheadArc = null;
        for (JsonDeadheadArc jsonDeadheadArc : outputFile.getDeadheadArcs()) {
            if ((deadhead.getDeadheadArcCode() == jsonDeadheadArc.getDeadheadArc().getDeadheadArcCode()))
                deadheadArc = jsonDeadheadArc;
        }
        return deadheadArc;
    }


    /**
     * Method that return the deadhead arc that is executed by the deadhead given in input
     * @param deadhead the activity for which we are interested in know the deadhead arc
     * @return a DeadheadArc object such that DeadheadArc.arcCode == deadhead.arcCode, null if such DeadheadArc does not
     * exist
     */
    public static DeadheadArc computeDeadheadArc(Deadhead deadhead) {
       return computeJsonDeadheadArc(deadhead).getDeadheadArc();
    }


    /**
     * Method that compute the index the time horizon index of a break
     * @param activityBreak the break for which we are interested in known the timeHorizon index
     * @return the timeHorizon index of the break given in input, such that 0 <= timeHorizon index <= timeHorizon.length,
     * -1 if the break does not start in the timeHorizon
     */

    private static int breakTimeHorizonIndex(ActivityBreak activityBreak){
        return getTimeHorizonIndex(activityBreak.getStartTime());
    }

    /**
     * Method that return the index where time belongs
     * @param time the second when the activity is performed
     * @return i such that, timeHorizon[i] < time < timeHorizon[i - 1], -1 otherwise
     */
    private static int getTimeHorizonIndex(long time) {
        int result = -1;
        for (int i = 1; i < outputFile.getTimeHorizon().length; i++) {
            if(time >= outputFile.getTimeHorizon()[i - 1]
                    && time <= outputFile.getTimeHorizon()[i]){
                result = i-1;
                break;
            }
        }
        return result;
    }


    /**
     * Method that initialize a map tripId -> trip
     * @return a map containing an association tripId -> trip for every and only the trips in the solution
     */
    private static Map<Integer, Trip> initializeTripHashMap(){
        Map<Integer, Trip> tripHashMap= new HashMap<>();

        for(JsonDirection jsonDirection : outputFile.getDirections()) {
            for(JsonTrip jTrip : jsonDirection.getDirection().getTrips()) {
                tripHashMap.put(jTrip.getTrip().getTripId(),jTrip.getTrip());
            }
        }
        return tripHashMap;
    }


    /**
     * Method that initialize a map Direction -> TripsOfTheDirection
     * @return a map containing, for every direction in the PTN, an association Direction -> List<Trip> such that if
     * trip T belongs to List<Trip> then trip T belongs to Direction.getTrips()
     */
    private static Map<Direction, List<Trip>> initializeTripDirectionHashMap(){
        Map<Direction, List<Trip>> tripDirectionHashMap = new HashMap<>();

        for(JsonDirection direction : outputFile.getDirections()){
            tripDirectionHashMap.put(direction.getDirection(), new ArrayList<>());

            for (JsonTrip jsonTrip : direction.getDirection().getTrips()){
                tripDirectionHashMap.get(direction.getDirection()).add(jsonTrip.getTrip());
            }
        }

        return tripDirectionHashMap;
    }


    /**
     * Method that check, given T the total amount of break time, and TC the total amount of time spent for recharge
     * an electric vehicle in the break, if T == TC
     * @param activityBreak the break that need to be checked
     * @return true iff , T == TC, false otherwise
     */
    private static boolean onlyForCharge(ActivityBreak activityBreak){
        int timeOfBreak = activityBreak.getEndTime() - activityBreak.getStartTime();
        int timeOfCharge = 0;

        for(JsonBreak jsonBreak : activityBreak.getBreakActivities()){
            if((jsonBreak.getBreakActivity().getTypeSpot().equalsIgnoreCase("slowcharging") || jsonBreak.getBreakActivity().getTypeSpot().equalsIgnoreCase("fastcharging"))
            && (jsonBreak.getBreakActivity().isCharging)){
                timeOfCharge += (jsonBreak.getBreakActivity().getEndTime() - jsonBreak.getBreakActivity().getStartTime());
            }
        }

        return timeOfCharge == timeOfBreak;
    }


    /**
     * Method that check if a vehicle block starts and ends with a deadhead trip
     * @param vehicleBlock the vehicle block that need to be checked
     * @return true iff vehicleBlock.activity(0) = deadhead && vehicleBlock.activity(last) = deadhead, false otherwise
     */
    private static boolean startAndEndWithDeadhead(JsonVehicleBlock vehicleBlock, int vehicleBlockNumber){
        boolean admissible = true;
        if(vehicleBlock.getVehicleBlock().getActivityList().get(0).getClass() != Deadhead.class){
            write("Vehicle block " + vehicleBlockNumber + " does not start with a deadhead trip");
            admissible = false;
        }
        else{
            Deadhead deadhead = (Deadhead) vehicleBlock.getVehicleBlock().getActivityList().get(0);
            int timeHorizonIndex = timeHorizonDeadhead(deadhead);
            JsonDeadheadArc deadheadArc = computeJsonDeadheadArc(deadhead);
            if(timeHorizonIndex == -1){
                write("Deadhead does not belong to the time horizon");
                return false;
            }
            else{
                if(outputFile.getDeadheadArcs().get(outputFile.getDeadheadArcs().indexOf(deadheadArc)).getDeadheadArc().getTravelTimes().get(timeHorizonIndex) != (deadhead.getEndTime() - deadhead.getStartTime())){
                    write("The first deadhead of vehicle block " + vehicleBlockNumber + " has a non valid travel time");
                    return false;
                }
            }
        }
        if(vehicleBlock.getVehicleBlock().getActivityList().get(vehicleBlock.getVehicleBlock().getActivityList().size() -1).getClass() != Deadhead.class){
            write("Vehicle block " + vehicleBlockNumber + " does not end with a deadhead trip");
            admissible =  false;
        }
        else{
            Deadhead deadhead = (Deadhead) vehicleBlock.getVehicleBlock().getActivityList().get(vehicleBlock.getVehicleBlock().getActivityList().size() -1);
            int timeHorizonIndex = timeHorizonDeadhead(deadhead);
            JsonDeadheadArc deadheadArc = computeJsonDeadheadArc(deadhead);
            if(timeHorizonIndex == -1){
                write("Deadhead does not belong to the time horizon");
                return false;
            }
            else{
                if(outputFile.getDeadheadArcs().get(outputFile.getDeadheadArcs().indexOf(deadheadArc)).getDeadheadArc().getTravelTimes().get(timeHorizonIndex) != (deadhead.getEndTime() - deadhead.getStartTime())){
                    write("The last deadhead of vehicle block " + vehicleBlockNumber + " has a non valid travel time");
                    return false;
                }
            }
        }

        return admissible;
    }


    /**
     * Method that compute the total amount of time spent from a vehicle charging
     * @param activityBreak the break in which we are interested in check the total timo of charge
     * @return the amount of time a vehicle recharged during the break, 0 if the vehicle did not recharged
     */
    private static int timeOfCharge(ActivityBreak activityBreak){
        int timeOfCharge = 0;

        for(JsonBreak jsonBreak : activityBreak.getBreakActivities()){
            if((jsonBreak.getBreakActivity().getTypeSpot().equalsIgnoreCase("slowcharging") || jsonBreak.getBreakActivity().getTypeSpot().equalsIgnoreCase("fastcharging")) &&
                    jsonBreak.getBreakActivity().isCharging){
                timeOfCharge += jsonBreak.getBreakActivity().getEndTime() - jsonBreak.getBreakActivity().getStartTime();
            }
        }
        return timeOfCharge;
    }

    /**
     * Method that write a string s on a file if the validation start online or on the terminal if the validation start
     * locally
     * @param s the string that need to be written
     */
    private static void write(String s){
        if(writeOnFile){
            try {
                writer.write(s + "\n");
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
        else{
            System.out.println(s);
        }
    }

    /**
     * Method that compute when start the first deadhead in the solution
     * @return the start time of the first deadhead performed in the solution
     */
    private static int minDeadheadStartTime(){
        int minStartTime = outputFile.getTimeHorizon()[outputFile.getTimeHorizon().length - 1];

        for(JsonVehicleBlock jsonVehicleBlock : outputFile.getVehicleBlockList()){
            for(Activity activity : jsonVehicleBlock.getVehicleBlock().getActivityList()){
                if(activity.getClass() == Deadhead.class && activity.getStartTime() < minStartTime){
                    minStartTime = activity.getStartTime();
                }
            }
        }

        return minStartTime;
    }

    /**
     * Method that compute when ends the last deadhead in the solution
     * @return the end time of the last deadhead performed in the solution
     */
    private static int maxDeadheadEndTime() {
        int maxEndTime = outputFile.getTimeHorizon()[0];

        for(JsonVehicleBlock jsonVehicleBlock : outputFile.getVehicleBlockList()){
            for(Activity activity : jsonVehicleBlock.getVehicleBlock().getActivityList()){
                if(activity.getClass() == Deadhead.class && activity.getEndTime() > maxEndTime){
                    maxEndTime = activity.getEndTime();
                }
            }
        }

        return maxEndTime;
    }
}
