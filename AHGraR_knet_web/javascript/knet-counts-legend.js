
  // Refresh network legend whenever nodes are hidden individually or in group or in case of "Show All" or "Show Links".
  function updateCyLegend() {
	var cy= $('#cy').cytoscape('get');
    var gene_count = 0;
    var gene_hidden_count = 0;
    var protein_count = 0;
    var protein_hidden_count = 0;
    cy.nodes().forEach(function( node )
    {
        if (node.data('type')=="Gene" && node.visible())
        {
        gene_count +=1;
        };
        if (node.data('type')=="Gene" && !node.visible())
        {
        gene_hidden_count +=1;
        };
        if (node.data('type')=="Protein" && node.visible())
        {
        protein_count +=1;
        };
        if (node.data('type')=="Protein" && !node.visible())
        {
        protein_hidden_count +=1;
        };
        
    });
	var cyLegend= "Showing "+gene_count+" genes ("+gene_hidden_count+" hidden) and "+protein_count+" proteins ("+protein_hidden_count+" hidden)";


//	console.log(cyLegend);
	$('#countsLegend span').text(cyLegend); // update
   }
