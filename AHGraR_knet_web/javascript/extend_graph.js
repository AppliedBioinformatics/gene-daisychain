// Extend the graph by adding new nodes and/or edges
// Add data to networkJSON

function addPath(node, rel_type)
{
    // Show cancel button
    $('#cancel_extend_graph').show();
    var cy= $('#cy').cytoscape('get'); // now we have a global reference to `cy`
    node_id = node.id();
    node_x = node.position("x");
    node_y = node.position("y");
    var wsconn = get_wsconn();
    wsconn.onopen = function () {wsconn.send("PAQURY_RELA_"+project_id+"_WEB_"+node_id+"_"+rel_type);};
    wsconn.onmessage = function (evt){
        // Hide cancel button
        $('#cancel_extend_graph').hide();
        new_graph_data = JSON.parse(evt.data);
        new_node_data = new_graph_data.nodes;
        new_edge_data = new_graph_data.edges;
        var angle_rotation = (2 * Math.PI)/new_node_data.length;
        var angle = 0;
        if (new_node_data.length == 0){
        window.alert("No new nodes found.");
        };
        if (new_node_data.length >= 100){
        window.alert("Number of nodes exceeds limit(100).");
        };
        new_node_data.forEach(function(val)
        {
            new_node = cy.add({group: "nodes","data":val.data, position:
                { x: node_x+(50*Math.cos(angle)), y: node_y+(50*Math.sin(angle)) }});
            angle += angle_rotation;
        });
        new_edge_data.forEach(function(val)
        {
            new_edge = cy.add({group: "edges","data":val.data});
        });
        // Add qtips
        add_qtips();
        changeSensitivity();
        // Update show/hide
        show_hide_refresh();
        updateCyLegend();

    }

};

function cancelGraphExtend(){
        // Hide cancel button
        $('#cancel_extend_graph').hide();
        // Cancel Websocket connection
        close_wsconn();

};
