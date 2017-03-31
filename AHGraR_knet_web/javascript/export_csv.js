// Export graph data in csv format
// Each row represents one relation, e.g. one homology relation of geneA to geneB
function export_table(){
console.log("Export table");
var cy= $('#cy').cytoscape('get'); // now we have a global reference to `cy`
var gene_nodes = cy.filter(function(i,ele){
            if (ele.isNode() && ele.data('type') == "Gene" && ele.visible())
            {return true;}
            else {return false;}
            });
var protein_nodes = cy.filter(function(i,ele){
            if (ele.isNode() && ele.data('type') == "Protein" && ele.visible())
            {return true;}
            else {return false;}
            });
var coding_edges = cy.filter(function(i,ele){
            if (ele.isEdge() &&  ele.data('type') == "CODING" && ele.visible())
            {return true;}
            else {return false;}
            });
var nb5_edges = cy.filter(function(i,ele){
            if (ele.isEdge() &&  ele.data('type') == "5_NB" && ele.visible())
            {return true;}
            else {return false;}
            });
var nb3_edges = cy.filter(function(i,ele){
            if (ele.isEdge() &&  ele.data('type') == "3_NB" && ele.visible())
            {return true;}
            else {return false;}
            });
var homolog_edges = cy.filter(function(i,ele){
            if (ele.isEdge() &&  ele.data('type') == "HOMOLOG" && ele.visible())
            {return true;}
            else {return false;}
            });
console.log(gene_nodes.data());
console.log(protein_nodes);
console.log(coding_edges);
console.log(nb5_edges);
console.log(nb3_edges);
console.log(homolog_edges);

}
