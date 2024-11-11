package validator.validatorClasses;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

public class JsonNetworkNode {
    private Node node;

    @JsonCreator
    public JsonNetworkNode(@JsonProperty("node") Node node){
        this.node = node;
    }

    public JsonNetworkNode(){
        node = null;
    }
    public Node getNode() {
        return node;
    }
}
