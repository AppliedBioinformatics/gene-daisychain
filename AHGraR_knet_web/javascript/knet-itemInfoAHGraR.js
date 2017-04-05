  /** Item Info.: display information about the selected concept(s)/ relation(s) including attributes, 
   * co-accessions and evidences.
   * @type type
   */
   function showItemInfo(selectedElement) {
    var itemInfo= "";

    try {
         var cy= $('#cy').cytoscape('get');
         // Display the Item Info table in its parent div.
         document.getElementById("itemInfo_Table").style.display= "inline";
         // Display item information in the itemInfo <div> in a <table>.
         var table= document.getElementById("itemInfo_Table").getElementsByTagName('tbody')[0]; // get the Item Info. table.
         // Clear the existing table body contents.
         table.innerHTML= "";
         if(selectedElement.isNode()) 
         {
            conID= selectedElement.id(); // id
            conValue= selectedElement.data('value'); // value
            // Unselect other concepts.
            cy.$(':selected').nodes().unselect();
            // Explicity select (highlight) the concept.
            cy.$('#'+conID).select();
            
            var row= table.insertRow(0); // create a new, empty row.
            // Insert new cells in this row.
            var cell1= row.insertCell(0);
            var cell2= row.insertCell(1);
            // Store the necessary data in the cells.
            cell1.innerHTML= "Node Type:";
            cell2.innerHTML= selectedElement.data('type'); 
            
            row= table.insertRow(1);
            cell1= row.insertCell(0);
            cell2= row.insertCell(1);
            cell1.innerHTML= "Name:";
            cell2.innerHTML= selectedElement.data('name');
            
            row= table.insertRow(2);
            cell1= row.insertCell(0);
            cell2= row.insertCell(1);
            cell1.innerHTML= "Species:";
            cell2.innerHTML= selectedElement.data('species');

            
            if (selectedElement.data('type') == "Gene")
            {

                row= table.insertRow(3);
                cell1= row.insertCell(0);
                cell2= row.insertCell(1);
                cell1.innerHTML= "Contig:";
                cell2.innerHTML= selectedElement.data('contig');

                row= table.insertRow(4);
                cell1= row.insertCell(0);
                cell2= row.insertCell(1);
                cell1.innerHTML= "Annotation:";
                cell2.innerHTML= selectedElement.data('description');

                row= table.insertRow(5);
                cell1= row.insertCell(0);
                cell2= row.insertCell(1);
                cell1.innerHTML= "Start:";
                cell2.innerHTML= selectedElement.data('start');
                
                row= table.insertRow(6);
                cell1= row.insertCell(0);
                cell2= row.insertCell(1);
                cell1.innerHTML= "Stop:";
                cell2.innerHTML= selectedElement.data('stop');

                gene_name = selectedElement.data("name");
                nt_seq = selectedElement.data("nt_seq");
                fasta_format_seq = ">"+gene_name+"<br>"+nt_seq+"<br>"
                row= table.insertRow(7);
                cell1= row.insertCell(0);
                cell2= row.insertCell(1);
                cell1.innerHTML= "Nucleotide sequence:";
                cell2.innerHTML=  '<button type="button" onclick=loadFASTA(fasta_format_seq)>Click Me!</button>' ;

                row= table.insertRow(8);
                cell1= row.insertCell(0);
                cell2= row.insertCell(1);
                cell1.innerHTML= "BLAST nt sequence:";
                cell2.innerHTML=  '<button type="button" onclick=blastNtFASTA(nt_seq)>Click Me!</button>' ;



            }
            if (selectedElement.data('type') == "Protein")
            {
                protein_name = selectedElement.data("name");
                prot_seq = selectedElement.data("aa_seq");
                fasta_format_seq = ">"+protein_name+"<br>"+prot_seq+"<br>"
                row= table.insertRow(3);
                cell1= row.insertCell(0);
                cell2= row.insertCell(1);
                cell1.innerHTML= "Coding sequence:";
                cell2.innerHTML=  '<button type="button" onclick=loadFASTA(fasta_format_seq)>Click Me!</button>' ;
                
                row= table.insertRow(4);
                cell1= row.insertCell(0);
                cell2= row.insertCell(1);
                cell1.innerHTML= "BLAST:";
                cell2.innerHTML=  '<button type="button" onclick=blastProtFASTA(prot_seq)>Click Me!</button>' ;
            }
  
           }
        }
    catch(err) {
          itemInfo= "Selected element is neither a Concept nor a Relation"; 
          itemInfo= itemInfo +"<br/>Error details:<br/>"+ err.stack; // error details
          console.log(itemInfo);
         }
//    $("#infoDialog").html(itemInfo); // display in the dialog box.
   }

 // Function to load Coding Sequence
 function loadFASTA(seq)
 {
    var fastaShow = window.open("", "FASTA sequence", "width=200,height=100,menubar=no");
    fastaShow.document.write(fasta_format_seq);
 };
 
 function blastNtFASTA(seq)
 {

   window.open("https://blast.ncbi.nlm.nih.gov/Blast.cgi?PROGRAM=blastn&PAGE_TYPE=BlastSearch&BLAST_SPEC=&QUERY="+seq+"&LINK_LOC=blasttab&LAST_PAGE=blastp&QUERY=%22%20fasta_seq%20%22", "", "width=200,height=100");
 };

 function blastProtFASTA(seq)
 {
   window.open("https://blast.ncbi.nlm.nih.gov/Blast.cgi?PAGE=Proteins&PROGRAM=blastp&BLAST_PROGRAMS=blastp&QUERY="+seq+"&LINK_LOC=protein&PAGE_TYPE=BlastSearch", "", "width=200,height=100");
 };
 
 // Open the Item Info pane when the "Item Info" option is selected for a concept or relation.
 function openItemInfoPane() {
//  myLayout.show('east', true); // to unhide (show) and open the pane.
//  myLayout.slideOpen('east'); // open the (already unhidden) Item Info pane.

  // $("#itemInfo").css("display","block"); // show the Item Infon div
  var effect = 'slide';
  // Set the options for the effect type chosen
  var options = { direction: 'right' };
  // Set the duration (default: 400 milliseconds)
  var duration = 500;
  if($('#itemInfo').css("display")==="none") {
     $('#itemInfo').toggle(effect, options, duration);
    // $('#itemInfo').slideToggle(500);
    }
 }

 /*$("#btnCloseItemInfoPane").click(function() {
     console.log("Close ItemInfo pane...");
     $("#itemInfo").hide();
 });*/
 
 function closeItemInfoPane() {
  $("#itemInfo").hide();
 }

  // Remove shadow effect from nodes, if it exists.
  function removeNodeBlur(ele) {
    var thisElement= ele;
    try {
      if(thisElement.hasClass('BlurNode')) {
         // Remove any shadow created around the node.
         thisElement.removeClass('BlurNode');
        }
/*      thisElement.neighborhood().nodes().style({'opacity': '1'});
      thisElement.neighborhood().edges().style({'opacity': '1'});*/
     }
    catch(err) {
          console.log("Error occurred while removing Shadow from concepts with connected, hidden elements. \n"+"Error Details: "+ err.stack);
         }
  }

  // Show hidden, connected nodes connected to this node & also remove shadow effect from nodes, wheere needed.
  function showLinks(ele) {
    var selectedNode= ele;
    // Remove css style changes occurring from a 'tapdragover' ('mouseover') event.
//    resetRelationCSS(selectedNode);

    // Show concept neighborhood.
//    selectedNode.neighborhood().nodes().show();
//    selectedNode.neighborhood().edges().show();
    selectedNode.connectedEdges().connectedNodes().show();
    selectedNode.connectedEdges().show();

    // Remove shadow effect from the nodes that had hidden nodes in their neighborhood.
    removeNodeBlur(selectedNode);

    // Remove shadow effect from connected nodes too, if they do not have more hidden nodes in their neighborhood.
    selectedNode.connectedEdges().connectedNodes().forEach(function( elem ) {
        var its_connected_hidden_nodes= elem.connectedEdges().connectedNodes().filter('node[conceptDisplay = "none"]');
        var its_connected_hiddenNodesCount= its_connected_hidden_nodes.length;
        console.log("connectedNode: id: "+ elem.id() +", label: "+ elem.data('value') +", its_connected_hiddenNodesCount= "+ its_connected_hiddenNodesCount);
        if(its_connected_hiddenNodesCount </*<=*/ 1) {
//        if(its_connected_hiddenNodesCount /*<*/=== 0/*1*/) {
           removeNodeBlur(elem);
//           elem.connectedEdges().show();
          }
    });

    try { // Relayout the graph.
//         rerunGraphLayout(/*selectedNode.neighborhood()*/selectedNode.connectedEdges().connectedNodes());
         // Set a circle layout on the neighborhood.
         var eleBBox= selectedNode.boundingBox(); // get the bounding box of thie selected concept (node) for the layout to run around it.
         // Define the neighborhood's layout.
         var mini_circleLayout= { name: 'circle', radius: 2/*0.01*/, boundingBox: eleBBox,
                avoidOverlap: true, fit: true, handleDisconnected: true, padding: 10, animate: false, 
                counterclockwise: false, rStepSize: 1/*0.01*/, ready: /*undefined*/function() { cy.center(); cy.fit(); }, 
                stop: undefined/*function() { cy.center(); cy.fit(); }*/ };

         // Set the layout only using the hidden concepts (nodes).
//         console.log("Node neighborhood.filter(visible) size: "+ selectedNode.neighborhood().filter('node[conceptDisplay = "none"]').length);
//         if(selectedNode.neighborhood().length > 5/*2*/) {
              selectedNode.neighborhood().filter('node[conceptDisplay = "none"]').layout(mini_circleLayout);
//             }
        }
    catch(err) { console.log("Error occurred while setting layout on selected element's neighborhood: "+ err.stack); }
  }

  // Set the given name (label) for the selected concept.
  function useAsPreferredConceptName(new_conceptName) {
   try {
     var cy= $('#cy').cytoscape('get'); // now we have a global reference to `cy`
     cy.nodes().forEach(function(ele) {
      if(ele.selected()) {
         console.log("Selected concept: "+ ele.data('displayValue')/*ele.data('value')*/ +"; \t Use new preferred name (for concept Label): "+ new_conceptName);
         /*ele.data('Value', new_conceptName);*/
         ele.data('displayValue', new_conceptName);
         if(ele.style('text-opacity') === '0') {
            ele.style({'text-opacity': '1'}); // show the concept Label.
           }
        }
     });
    }
   catch(err) {
          console.log("Error occurred while altering preferred concept name. \n"+"Error Details: "+ err.stack);
         }
  }
