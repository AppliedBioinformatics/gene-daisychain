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
gene_nodes_data[gene_nodes[i].data("id")]=[gene_nodes[i].data("id"), gene_nodes[i].data("name"),gene_nodes[i].data("species"),gene_nodes[i].data("contig"),gene_nodes[i].data("start"), gene_nodes[i].data("stop"), gene_nodes[i].data("description")];
};
var protein_nodes_data = {};
for (i = 0; i < protein_nodes.length; ++i){
protein_nodes_data[protein_nodes[i].data("id")]=[protein_nodes[i].data("id"),protein_nodes[i].data("name"),protein_nodes[i].data("species")]
};
// Iterate through gene homologs. For each id, collect all homologs and the perc. match
var hmlg_dict = {};
for (i = 0; i < homolog_edges.length; ++i){
source_id = homolog_edges[i].data("source");
target_id = homolog_edges[i].data("target");
console.log(homolog_edges[i].data);
if ("undefined" == typeof source_id || "undefined" == typeof target_id){continue;};
if (source_id.startsWith("g"))
{
var source = gene_nodes_data[source_id][0];
var target = gene_nodes_data[target_id][0];
}
else
{
var source = protein_nodes_data[source_id][0];
var target = protein_nodes_data[target_id][0];
}

if(source in hmlg_dict)
{
hmlg_dict[source].push(target);
}
else
{
hmlg_dict[source] = [target];
};
if(target in hmlg_dict)
{
hmlg_dict[target].push(source);
}
else
{
hmlg_dict[target] = [source];
};

};

}
}
