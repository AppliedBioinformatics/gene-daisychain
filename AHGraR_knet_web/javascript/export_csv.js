// Export graph data in csv format
// Each row represents one relation, e.g. one homology relation of geneA to geneB
function export_table(){
var cy= $('#cy').cytoscape('get'); // now we have a global reference to `cy`
cy.edges().forEach(function(edge){
console.log(edge);
});
}
