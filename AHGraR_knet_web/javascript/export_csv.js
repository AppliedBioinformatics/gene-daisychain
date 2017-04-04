// Export graph data in csv format
// First part contains one gene description per row, last column contains ID(s) of homologs
// Next part is the same for proteins#
// Last part describes local gene arrangements, i.e. 5' and 3' relations
// Function export_Table is called from saveCSV (former saveJSON) button
function export_table(){
console.log("Export table");
var cy= $('#cy').cytoscape('get'); // now we have a global reference to `cy`
// Collect all visible genes
var gene_nodes = cy.filter(function(i,ele){
            if (ele.isNode() && ele.data('type') == "Gene" && ele.visible())
            {return true;}
            else {return false;}
            });
// Collect all visible proteins
var protein_nodes = cy.filter(function(i,ele){
            if (ele.isNode() && ele.data('type') == "Protein" && ele.visible())
            {return true;}
            else {return false;}
            });
// Collect all visible 5' edges
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
// Collect all visible 3' edges
var homolog_edges = cy.filter(function(i,ele){
            if (ele.isEdge() &&  ele.data('type') == "HOMOLOG" && ele.visible())
            {return true;}
            else {return false;}
            });
// Extract gene node data from gene nodes
// Dict-like format of object: "id":["id","name","assembly","contig","start","stop","annotation"]
var gene_nodes_data = {};
for (i = 0; i < gene_nodes.length; ++i){
gene_nodes_data[gene_nodes[i].data("id")]=[gene_nodes[i].data("id"), gene_nodes[i].data("name"),
gene_nodes[i].data("species"),gene_nodes[i].data("contig"),gene_nodes[i].data("start"),
gene_nodes[i].data("stop"), gene_nodes[i].data("description")];
};
// Extract protein node data from protein nodes
// Dict-like format of object: "id":["id","name","assembly"]
var protein_nodes_data = {};
for (i = 0; i < protein_nodes.length; ++i){
protein_nodes_data[protein_nodes[i].data("id")]=[protein_nodes[i].data("id"),protein_nodes[i].data("name"),
protein_nodes[i].data("species")]
};
// Create another dict-like structure storing for each gene or protein ID all homologs (as ID and percentage match)
var hmlg_dict = {};
// Scan through all HOMOLOG edges, for each source add the target node to its list of homolog nodes
for (i = 0; i < homolog_edges.length; ++i){
source_id = homolog_edges[i].data("source");
target_id = homolog_edges[i].data("target");
perc_match = homolog_edges[i].data("perc_match");
console.log(homolog_edges[i]);
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
};
if(source in hmlg_dict)
{
hmlg_dict[source].push(target+":"+perc_match);
}
else
{
hmlg_dict[source] = [target+":"+perc_match];
};
if(target in hmlg_dict)
{
hmlg_dict[target].push(source+":"+perc_match);
}
else
{
hmlg_dict[target] = [source+":"+perc_match];
};
};
console.log(hmlg_dict);
}

