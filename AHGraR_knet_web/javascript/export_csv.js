// Export graph data in csv format
// Each row represents one relation, e.g. one homology relation of geneA to geneB
function export_table(){
console.log("Export table");
var cy= $('#cy').cytoscape('get'); // now we have a global reference to `cy`
var gene_nodes = cy.elements('node[type="Gene"],:visible');
var protein_nodes = cy.elements('node[type="Protein",:visible]');
console.log(gene_nodes);
console.log(protein_nodes);

}
