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
var gene_nodes_data = {};
for (i = 0; i < gene_nodes.length; ++i){
gene_nodes_data[gene_nodes[i].data("id")]=[gene_nodes[i].data("name"),gene_nodes[i].data("species"),gene_nodes[i].data("contig"),gene_nodes[i].data("start"), gene_nodes[i].data("stop"), gene_nodes[i].data("description")];
};
var protein_nodes_data = {};
for (i = 0; i < protein_nodes.length; ++i){
protein_nodes_data[protein_nodes[i].data("id")]=[protein_nodes[i].data("name"),protein_nodes[i].data("species")]
};
// Iterate through gene homologs
for (i = 0; i < homolog_edges.length; ++i){
console.log(gene_nodes_data[homolog_edges[i].data("source")}]);
}
//console.log(gene_nodes_data);
//console.log(protein_nodes_data);
//console.log(coding_edges);
//console.log(nb5_edges);
//console.log(nb3_edges);
console.log(homolog_edges);

}
