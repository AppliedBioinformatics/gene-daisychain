// Export graph data in csv format
// Each row represents one relation, e.g. one homology relation of geneA to geneB
function export_table(){
console.log("Export table");
var cy= $('#cy').cytoscape('get'); // now we have a global reference to `cy`
var gene_nodes = cy.filter(function(i,ele){console.log(ele); return false;});

console.log(gene_nodes);


}
