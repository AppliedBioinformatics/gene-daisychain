
// initialize and generate the network
function generateNetworkGraph(jsonFileName) {
    var json_File= jsonFileName;
   //console.log("Dataset file path: "+ json_File);

    // Include this file's contents on the page at runtime using jQuery and a callback function.
   jQuery.getScript(json_File, function() {
     //console.log(json_File +" file included...");
     // Initialize the cytoscapeJS container for Network View.
     initializeNetworkView();

     // Highlight nodes with hidden, connected nodes using Shadowing.
     blurNodesWithHiddenNeighborhood();

     // Set the default layout.
//     setDefaultLayout();
     // update "cy" legend with some stats.
     updateCyLegend();
     // Show only homolog/synteny edges of selected cluster size
    changeSensitivity();
   });
  }

// initialize the network
function initializeNetworkView() {
   networkJSON= graphJSON; // using the dynamically included graphJSON object directly.

   // Define the stylesheet to be used for nodes & edges in the cytoscape.js container.
    networkStylesheet= cytoscape.stylesheet()
      .selector('node')
        .css({
          'content': 'data(name)',
          'text-background-color': 'black',
          'text-background-opacity': '0', // default: '0' (disabled).
          'text-wrap': 'wrap', // for manual and/or autowrapping the label text.
          'text-max-width':'60px',
          'border-style': 'solid', // node border, can be 'solid', 'dotted', 'dashed' or 'double'.
          'border-width': '4px',
          'border-color': function(node){return color_node(node.data('species'), node.data('chromosome')); },//function(node){if (node.data('type') == 'Protein'){return "green";} else {return "blue";}},
          'font-size': '8px', // '8px',
          'shape': function(node){if (node.data('type') == 'Protein'){return "diamond";} else{return "ellipse";};}, //'ellipse',
          'width': '60px', // '18px',
          'height': '36px', // '18px',
          'background-color': function(node){if (node.data('type') == 'Protein'){return "#ffe3c1";} else {return "#ffffe0";}},
          /** Using 'data(conceptColor)' leads to a "null" mapping error if that attribute is not defined 
           * in cytoscapeJS. Using 'data[conceptColor]' is hence preferred as it limits the scope of 
           * assigning a property value only if it is defined in cytoscapeJS as well. */
          'display': "show", // 'element' (show) or 'none' (hide).
          'text-opacity': '1', // to make the label visible by default.
          'text-halign': 'center',
          'text-valign': 'center'
         })
      .selector('edge')
        .css({
          'content': function(edge){
          edge_type = edge.data('type');
          if (edge_type=="5_NB"){return "5'";};
          if (edge_type=="3_NB"){return "3'";};
          if (edge_type=="HOMOLOG"){return "Homolog";}
          if (edge_type=="CODING"){return "Coding";};}, // label for edges (arrows).
          'font-size': '8px',
          'curve-style': function(edge){
          if (edge.data('type') == 'HOMOLOG'){return "bezier";}
          if (edge.data('type') == 'CODING'){return "bezier";}
          else {return "unbundled-bezier";}}, /* options: bezier (curved) (default), unbundled-bezier (curved with manual control points), haystack (straight edges) */
          'control-point-step-size': '10px', // specifies the distance between successive bezier edges.
          'control-point-distance': '20px', /* overrides control-point-step-size to curves single edges as well, in addition to parallele edges */
          'control-point-weight': '50', // '0': curve towards source node, '1': curve towards target node.
          'width': function(edge)
          {if (edge.data('type') == 'HOMOLOG')
          {return "2";}
          else{return "1";}}, // 'mapData(relationSize, 70, 100, 2, 6)',
          'line-color': function(edge){if (edge.data('type') != 'HOMOLOG' ){return 'black';}else{
          perc_match = parseFloat(edge.data('perc_match'));
          if(isNaN(perc_match)){perc_match = 0;};
          return "rgb("+(((100-perc_match)*255)/100)+","+((perc_match/100)*255)+", 0)";
          }},
          'line-style': 'solid', // 'solid' or 'dotted' or 'dashed'
          'target-arrow-shape': function(edge){if (edge.data('type') == 'HOMOLOG'){return "none";} else {return "triangle";}},
          'target-arrow-color': 'black',
          'mid-source-arrow-shape': function(edge){if (edge.data('type') != 'HOMOLOG' || typeof edge.data('ls_score') == 'undefined')
          {return "none";} else {return "circle";}},
          'mid-source-arrow-color': function(edge){if (edge.data('type') != 'HOMOLOG'){return 'black';}else{
          var ls_score = parseInt(edge.data('ls_score'));
          console.log("ls_score"+edge.data('ls_score'));
          if(ls_score >= 8){return "darkgreen";}
          else if((5 <= ls_score) && (ls_score < 8)){return "yellow";}
          else if((2 <= ls_score) && (ls_score < 5)){return "orange";}
          else{return "red";};
          }},
          'display': 'show', // 'element' (show) or 'none' (hide).
          'text-opacity': '1' // to make the label visible by default.
        })
      .selector('.highlighted')
        .css({
          'background-color': '#61bffc',
          'line-color': '#61bffc',
          'target-arrow-color': '#61bffc',
          'transition-property': 'background-color, line-color, target-arrow-color',
          'transition-duration': '0.5s'
        })
      .selector(':selected')
        .css({ // settings for highlighting nodes in case of single click or Shift+click multi-select event.
        'background-color': function(node){if (node.data('type') == 'Protein'){return "#efb269";} else {return "#fcfc8a";}}
        })
      .selector('.BlurNode')
        .css({ // settings for using shadow effect on nodes when they have hidden, connected nodes.
              'shadow-blur': '25', // disable for larger network graphs, use x & y offset(s) instead.
              'shadow-color': 'black',
              'shadow-opacity': '0.9'
        }).selector('.HideThis')
        .css({ // settings to hide node or edge
              'display': 'none'
        }).selector('.ShowItAll')
        .css({ // settings to show all nodes and edges
              'display': 'element'
        });

// On startup
$(function() { // on dom ready
  // load the cytoscapeJS network
  load_reload_Network(networkJSON, networkStylesheet/*, true*/);
  
}); // on dom ready
}

  // Show shadow effect on nodes with connected, hidden elements in their neighborhood.
  function blurNodesWithHiddenNeighborhood() {
    var cy= $('#cy').cytoscape('get'); // now we have a global reference to `cy`

    cy.nodes().forEach(function( ele ) {
    var thisElement= ele;
    var eleID, connected_hiddenNodesCount= 0;
    try { // Retrieve the nodes in this element's neighborhood.
//         var neighborhood_nodes= thisElement.neighborhood().nodes();

         eleID= thisElement.id(); // element ID.
         // Retrieve the directly connected nodes in this element's neighborhood.
         var connected_edges= thisElement.connectedEdges();
         // Get all the relations (edges) with this concept (node) as the source.
//         var connected_edges= thisElement.connectedEdges().filter('edge[source = '+eleID+']');

         var connected_hidden_nodes= connected_edges.connectedNodes().filter('node[conceptDisplay = "none"]');
         // Find the number of hidden, connected nodes.
         connected_hiddenNodesCount= connected_hidden_nodes.length;

         if(connected_hiddenNodesCount > 1) {
            // Show shadow around nodes that have hidden, connected nodes.
            thisElement.addClass('BlurNode');
          }
      }
    catch(err) { 
          console.log("Error occurred while adding Shadow to concepts with connected, hidden elements. \n"+"Error Details: "+ err.stack);
         }
   });
  }
